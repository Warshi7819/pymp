#!/usr/bin/env python3
"""
Test script for SHOUTcast ICY metadata extraction.

Connects to a SHOUTcast stream, finds the first metadata boundary
by scanning for StreamTitle=, then skips exactly icy_metaint bytes
of audio before reading each subsequent metadata block.

Usage:
    python tests/test_metadata_extract.py [url] [duration]
"""

import socket
import select
import sys
import time
from urllib.parse import quote

STREAM_URL = "http://uk3.internet-radio.com:8405/live"
DURATION = 30
RECEIVE_TIMEOUT = 4
CHUNK_SIZE = 4096


def parse_url(url):
    url = url[7:]
    addr_end = url.find("/")
    address = url[:addr_end]
    path = url[addr_end + 1:]
    parts = address.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 80
    return host, port, path


def connect_and_get_headers(host, port, path):
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.settimeout(10)
    soc.connect((host, port))

    request = "GET /%s HTTP/1.1\r\n" % quote(path)
    request += "Host: %s\r\n" % host
    request += "Icy-MetaData: 1\r\n"
    request += "Connection: Keep-Alive\r\n"
    request += "\r\n"

    soc.send(request.encode())

    response = b""
    while b"\r\n\r\n" not in response:
        chunk = soc.recv(4096)
        if not chunk:
            raise Exception("Connection closed before headers received")
        response += chunk

    header_end = response.find(b"\r\n\r\n")
    header_data = response[:header_end].decode("ascii", errors="replace")
    initial_data = response[header_end + 4:]

    headers = {}
    for i, line in enumerate(header_data.split("\r\n")):
        if i == 0:
            continue
        colon = line.find(":")
        if colon != -1:
            headers[line[:colon].strip()] = line[colon + 1:].strip()

    print("icy-metaint: %s" % headers.get("icy-metaint", "NOT FOUND"))
    print("icy-name: %s" % headers.get("icy-name", "N/A"))
    print()
    return headers, initial_data, soc


def extract_metadata(raw_metadata):
    clean = raw_metadata.replace(b'\x00', b'')
    text = clean.decode('utf-8', errors='replace').strip()

    st_idx = text.find("StreamTitle=")
    if st_idx == -1:
        return "", text

    title = text[st_idx + 13:]
    end = title.find(";")
    if end != -1:
        title = title[:end]
    title = title.strip().strip("'\"")

    sep = title.find(" - ")
    if sep != -1:
        return title[:sep].strip(), title[sep + 3:].strip()
    else:
        return "", title


def find_first_sync(data):
    """Scan for StreamTitle= to find first metadata boundary. Returns (length_pos, meta_end_pos) or None."""
    marker = b"StreamTitle="
    pos = data.find(marker)
    if pos == -1:
        return None

    for offset in range(16):
        content_start = pos - offset
        if content_start < 1:
            continue
        length_byte_pos = content_start - 1
        if length_byte_pos < 0:
            continue

        length_byte = data[length_byte_pos]
        if length_byte == 0:
            continue

        metadata_block_size = length_byte * 16
        expected_content_start = length_byte_pos + 1
        expected_content_end = expected_content_start + metadata_block_size

        if expected_content_end > len(data):
            return None

        content = data[expected_content_start:expected_content_end]
        if b"StreamTitle=" in content:
            return length_byte_pos, expected_content_end

    return None


def recv_more(soc, data_buffer, needed):
    """Read from socket until we have 'needed' bytes in the buffer. Returns new buffer."""
    while len(data_buffer) < needed:
        ready = select.select([soc], [], [], RECEIVE_TIMEOUT)
        if ready[0]:
            chunk = soc.recv(CHUNK_SIZE)
            if not chunk:
                break
            data_buffer += chunk
        else:
            break
    return data_buffer


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else STREAM_URL
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else DURATION

    print("=" * 60)
    print("SHOUTcast Metadata Extraction Test")
    print("URL: %s" % url)
    print("Duration: %d seconds" % duration)
    print("=" * 60)
    print()

    host, port, path = parse_url(url)
    headers, initial_data, soc = connect_and_get_headers(host, port, path)

    icy_metaint = int(headers.get("icy-metaint", 0))
    if icy_metaint == 0:
        print("ERROR: No icy-metaint header found.")
        soc.close()
        return

    # Phase 1: Find first sync point
    print("--- Phase 1: Finding first metadata boundary ---")
    data_buffer = initial_data
    start_time = time.time()

    while time.time() - start_time < 10:
        result = find_first_sync(data_buffer)
        if result:
            length_pos, meta_end = result
            length_byte = data_buffer[length_pos]
            raw_meta = data_buffer[length_pos + 1:meta_end]
            audio_after = data_buffer[meta_end:]
            artist, song = extract_metadata(raw_meta)
            print("Found first metadata boundary!")
            print("  Length byte: %d (metadata block: %d bytes)" % (length_byte, length_byte * 16))
            print("  Raw metadata: %s" % repr(raw_meta[:80]))
            print("  Parsed - Artist: '%s'  Song: '%s'" % (artist, song))
            print()
            break

        ready = select.select([soc], [], [], RECEIVE_TIMEOUT)
        if ready[0]:
            chunk = soc.recv(CHUNK_SIZE)
            if not chunk:
                print("ERROR: Connection closed")
                soc.close()
                return
            data_buffer += chunk
    else:
        print("ERROR: Could not find first metadata boundary")
        soc.close()
        return

    # Phase 2: Skip exactly icy_metaint bytes, then read metadata block
    print("--- Phase 2: Position-based extraction ---")
    meta_count = 1
    fail_count = 0
    data_buffer = audio_after
    last_meta_time = time.time()

    while time.time() - start_time < duration:
        # Step 1: Skip exactly icy_metaint bytes of audio
        data_buffer = recv_more(soc, data_buffer, icy_metaint)
        if len(data_buffer) < icy_metaint:
            print("  Connection lost (only %d bytes remaining)" % len(data_buffer))
            break

        data_buffer = data_buffer[icy_metaint:]

        # Step 2: Read the length byte
        data_buffer = recv_more(soc, data_buffer, 1)
        if len(data_buffer) < 1:
            print("  Connection lost before length byte")
            break

        length_byte = data_buffer[0]
        data_buffer = data_buffer[1:]

        if length_byte == 0:
            last_meta_time = time.time()
            continue

        # Step 3: Read the full metadata block
        metadata_size = length_byte * 16
        data_buffer = recv_more(soc, data_buffer, metadata_size)
        if len(data_buffer) < metadata_size:
            print("  WARNING: Incomplete metadata block")
            fail_count += 1
            break

        raw_meta = data_buffer[:metadata_size]
        data_buffer = data_buffer[metadata_size:]

        # Step 4: Extract and display
        meta_count += 1
        artist, song = extract_metadata(raw_meta)
        elapsed = time.time() - last_meta_time
        status = "OK" if song else "PARSE FAIL"
        print("  [%d] (%.1fs) %s | Artist: '%s'  Song: '%s'" % (
            meta_count, elapsed, status, artist, song))
        if not song and not artist:
            print("         RAW: %s" % repr(raw_meta[:60]))
            fail_count += 1

        last_meta_time = time.time()

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("  Total metadata blocks extracted: %d" % meta_count)
    print("  Failed/unreadable: %d" % fail_count)
    print("  Stream duration: %.1f seconds" % (time.time() - start_time))
    if meta_count > 0 and fail_count == 0:
        print("  RESULT: ALL EXTRACTIONS SUCCESSFUL")
    elif meta_count > 0:
        print("  RESULT: %d/%d succeeded" % (meta_count - fail_count, meta_count))
    else:
        print("  RESULT: NO METADATA EXTRACTED")
    print("=" * 60)

    soc.close()


if __name__ == "__main__":
    main()
