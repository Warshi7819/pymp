#!/usr/bin/env python3
"""
Test script for SHOUTcast ICY metadata extraction.

Uses the ACTUAL HttpStreamingClient from file_streaming.py —
no duplicate code. If this test passes clean, the player works.

Usage:
    python tests/test_metadata_extract.py [url] [duration]
"""

import sys
import os
import time
import threading

# Add src/ to path so we import the real player code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_streaming import HttpStreamingClient

STREAM_URL = "http://uk3.internet-radio.com:8405/live"
DURATION = 30


class DebugHttpStreamingClient(HttpStreamingClient):
    """Subclass that logs raw metadata bytes for debugging."""

    def __init__(self, *args, **kwargs):
        self.raw_log = []
        super().__init__(*args, **kwargs)

    def _process_metadata(self, raw_meta):
        # Log the raw bytes
        self.raw_log.append(raw_meta)
        # Call the real implementation
        super()._process_metadata(raw_meta)


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else STREAM_URL
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else DURATION

    print("=" * 60)
    print("SHOUTcast Metadata Extraction Test (Real Player Code)")
    print("URL: %s" % url)
    print("Duration: %d seconds" % duration)
    print("=" * 60)
    print()

    collected = []

    def on_metadata(info):
        collected.append({
            "artist": info.get("artist", ""),
            "song": info.get("song", ""),
            "time": time.time(),
        })

    # Use debug subclass to log raw metadata
    client = DebugHttpStreamingClient(
        url,
        metadata_only=True,
        metadata_callback=on_metadata,
    )

    print("--- Starting HttpStreamingClient (real player code) ---")
    start_time = time.time()
    client.start()

    # Wait for duration, printing metadata as it arrives
    last_count = 0
    while time.time() - start_time < duration:
        time.sleep(1)
        while last_count < len(collected):
            info = collected[last_count]
            elapsed = info["time"] - start_time
            raw = client.raw_log[last_count] if last_count < len(client.raw_log) else b''
            has_stream_title = b"StreamTitle=" in raw
            print("  [%d] (%.1fs) Artist: '%s'  Song: '%s'" % (
                last_count + 1, elapsed, info["artist"], info["song"]))
            print("       raw(%d bytes) has_streamtitle=%s: %s" % (
                len(raw), has_stream_title, repr(raw[:80])))
            last_count += 1

    client.close()
    while not client.THREAD_EXIT:
        time.sleep(0.05)

    # Print remaining
    while last_count < len(collected):
        info = collected[last_count]
        elapsed = info["time"] - start_time
        raw = client.raw_log[last_count] if last_count < len(client.raw_log) else b''
        has_stream_title = b"StreamTitle=" in raw
        print("  [%d] (%.1fs) Artist: '%s'  Song: '%s'" % (
            last_count + 1, elapsed, info["artist"], info["song"]))
        print("       raw(%d bytes) has_streamtitle=%s: %s" % (
            len(raw), has_stream_title, repr(raw[:80])))
        last_count += 1

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("  Total metadata blocks extracted: %d" % len(collected))
    print("  Stream duration: %.1f seconds" % (time.time() - start_time))

    if len(collected) > 0:
        bad = 0
        for i, info in enumerate(collected):
            raw = client.raw_log[i] if i < len(client.raw_log) else b''
            if b"StreamTitle=" not in raw:
                bad += 1
            elif info["artist"] == "" and info["song"] == "":
                bad += 1
        if bad == 0:
            print("  RESULT: ALL EXTRACTIONS CLEAN")
        else:
            print("  RESULT: %d/%d garbled" % (bad, len(collected)))
    else:
        print("  RESULT: NO METADATA EXTRACTED")
    print("=" * 60)


if __name__ == "__main__":
    main()
