#!/usr/bin/env python3
"""
Test 1: Does audio data reach the HttpStreamingClient buffer?
Uses the REAL player code — no duplication.
"""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_streaming import HttpStreamingClient

STREAM_URL = "http://uk3.internet-radio.com:8405/live"
DURATION = 8

def main():
    print("=" * 60)
    print("TEST 1: Buffer delivery (real HttpStreamingClient)")
    print("=" * 60)

    metadata_seen = []
    def on_meta(info):
        metadata_seen.append(info)

    client = HttpStreamingClient(
        STREAM_URL,
        metadata_only=False,
        metadata_callback=on_meta,
    )
    client.start()

    print("Started client, reading buffer for %d seconds..." % DURATION)
    start = time.time()
    reads_none = 0
    reads_data = 0
    total_bytes = 0
    first_bytes = []

    while time.time() - start < DURATION:
        result = client.read()
        if result is None:
            print("  client.read() returned None (should not happen)")
            break
        data = result[0]
        if data is None:
            reads_none += 1
            continue
        if data == 0:
            print("  Stream ended sentinel received")
            break
        reads_data += 1
        total_bytes += len(data)
        if len(first_bytes) < 5:
            first_bytes.append(data[:16])

    client.close()

    print()
    print("RESULTS:")
    print("  Metadata blocks seen: %d" % len(metadata_seen))
    for i, m in enumerate(metadata_seen):
        print("    [%d] Artist: '%s'  Song: '%s'" % (i+1, m.get('artist',''), m.get('song','')))
    print("  Buffer reads returning None (buffering): %d" % reads_none)
    print("  Buffer reads returning data: %d" % reads_data)
    print("  Total audio bytes received: %d" % total_bytes)
    print("  First bytes of data chunks:")
    for i, fb in enumerate(first_bytes):
        print("    [%d] %d bytes: %s" % (i+1, len(fb), fb.hex()))
        # Check for MP3 sync word (0xFF 0xFB or 0xFF 0xF3 etc)
        if len(fb) >= 2:
            if fb[0] == 0xFF and (fb[1] & 0xE0) == 0xE0:
                print("         -> Valid MP3 sync frame detected!")
            else:
                print("         -> NOT an MP3 sync frame (first 2 bytes: 0x%02X 0x%02X)" % (fb[0], fb[1]))

    print()
    if total_bytes > 0 and reads_data > 0:
        print("RESULT: PASS - Audio data is reaching the buffer")
    else:
        print("RESULT: FAIL - No audio data in the buffer")
    print("=" * 60)

if __name__ == "__main__":
    main()
