#!/usr/bin/env python3
"""
Test 2+3: Full pipeline — Buffer → ffmpeg → PCM.
Uses the REAL player code. No duplication.
"""

import sys, os, time, threading, subprocess, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from FileStreaming import HttpStreamingClient

STREAM_URL = "http://uk3.internet-radio.com:8405/live"
DURATION = 8

# PCM constants (same as StreamPlayer)
PCM_FORMAT = "s16le"
PCM_RATE = 44100
PCM_CHANNELS = 2
BYTES_PER_SAMPLE = 2
CHUNK_SIZE = PCM_RATE * PCM_CHANNELS * BYTES_PER_SAMPLE * 93 // 1000
CHUNK_SIZE = CHUNK_SIZE + (CHUNK_SIZE % (PCM_CHANNELS * BYTES_PER_SAMPLE))

def main():
    print("=" * 60)
    print("TEST 2+3: Full pipeline (real player code)")
    print("=" * 60)

    metadata_seen = []
    def on_meta(info):
        metadata_seen.append(info)

    # Start the real HttpStreamingClient
    client = HttpStreamingClient(
        STREAM_URL,
        metadata_only=False,
        metadata_callback=on_meta,
    )
    client.start()
    print("HttpStreamingClient started")

    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found")
        return

    # Wait for client to connect and start buffering
    time.sleep(3)

    # Collect all audio data from the buffer (same as StreamPlayer._feed_stdin)
    print("Collecting audio from buffer...")
    all_data = bytearray()
    start = time.time()
    while time.time() - start < DURATION:
        try:
            result = client.read()
            if result is None:
                break
            data = result[0]
            if data == 0:
                print("  Stream ended")
                break
            if data is None:
                time.sleep(0.05)
                continue
            all_data.extend(data)
        except Exception as e:
            print("  Read error: %s" % e)
            break

    print("  Collected %d bytes of audio" % len(all_data))
    client.close()

    if not all_data:
        print("ERROR: No audio data collected")
        return

    # Pipe all data to ffmpeg at once (same as StreamPlayer.run)
    print("Piping to ffmpeg...")
    cmd = [
        "ffmpeg",
        "-i", "pipe:0",
        "-f", PCM_FORMAT,
        "-ac", str(PCM_CHANNELS),
        "-ar", str(PCM_RATE),
        "-loglevel", "info",
        "pipe:1",
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Drain stderr
    stderr_lines = []
    def drain_stderr():
        for line in iter(proc.stderr.readline, b''):
            stderr_lines.append(line.decode('utf-8', errors='replace').strip())
    threading.Thread(target=drain_stderr, daemon=True).start()

    # Write all data at once, then close stdin
    proc.stdin.write(bytes(all_data))
    proc.stdin.close()
    print("  Wrote %d bytes to ffmpeg stdin" % len(all_data))

    # Read all PCM output
    pcm_data = proc.stdout.read()
    proc.wait(timeout=10)
    print("  PCM output: %d bytes (%.1f seconds)" % (len(pcm_data), len(pcm_data) / (PCM_RATE * PCM_CHANNELS * BYTES_PER_SAMPLE)))

    # Check audio quality at various offsets
    if pcm_data:
        for offset_s in [0, 1, 2, 5]:
            offset = offset_s * PCM_RATE * PCM_CHANNELS * BYTES_PER_SAMPLE
            if offset + 100 <= len(pcm_data):
                chunk = pcm_data[offset:offset+100]
                max_val = max(abs(int.from_bytes(chunk[i:i+2], 'little', signed=True)) for i in range(0, len(chunk)-1, 2))
                print("  PCM at %ds: max amplitude %d" % (offset_s, max_val))

    # Show ffmpeg errors
    if stderr_lines:
        print("  ffmpeg errors:")
        for line in stderr_lines:
            if any(w in line for w in ['Error', 'error', 'Invalid', 'aac', 'corrupt']):
                print("    %s" % line)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("  Metadata blocks: %d" % len(metadata_seen))
    for m in metadata_seen:
        print("    Artist: '%s'  Song: '%s'" % (m.get('artist',''), m.get('song','')))
    print("  Audio bytes collected: %d" % len(all_data))
    print("  PCM bytes output: %d" % len(pcm_data))
    if len(all_data) > 0 and len(pcm_data) > 0:
        # Check if there's actual audio (not just silence)
        mid = len(pcm_data) // 2
        sample = pcm_data[mid:mid+200]
        max_val = max(abs(int.from_bytes(sample[i:i+2], 'little', signed=True)) for i in range(0, len(sample)-1, 2))
        if max_val > 100:
            print("  RESULT: PASS - Full pipeline works, real audio detected")
        else:
            print("  RESULT: PASS - Pipeline works, but audio is silent")
    elif len(all_data) > 0:
        print("  RESULT: FAIL - Data goes in but no PCM comes out")
    else:
        print("  RESULT: FAIL - No data collected")
    print("=" * 60)

if __name__ == "__main__":
    main()
