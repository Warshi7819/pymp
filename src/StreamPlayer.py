###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import standard modules
import subprocess
import threading
import time
import shutil

# Import 3rdparty modules
import pygame
import pygame.mixer

# Import own modules
from OwnConstants import *

# PCM output format: signed 16-bit little-endian, stereo, 44100 Hz
PCM_FORMAT = "s16le"
PCM_RATE = 44100
PCM_CHANNELS = 2
BYTES_PER_SAMPLE = 2  # 16-bit = 2 bytes
# Chunk size in bytes: ~93ms of audio
CHUNK_SIZE = PCM_RATE * PCM_CHANNELS * BYTES_PER_SAMPLE * 93 // 1000
# Round to even number for stereo alignment
CHUNK_SIZE = CHUNK_SIZE + (CHUNK_SIZE % (PCM_CHANNELS * BYTES_PER_SAMPLE))


class StreamPlayer(threading.Thread):
    """
    FFmpeg-based audio stream player.

    Connects directly to a SHOUTcast/Icecast URL via ffmpeg.
    ffmpeg handles the HTTP connection, ICY protocol, metadata
    stripping, and audio decoding. PCM output is fed into a
    pygame.mixer.Channel for continuous playback.

    A separate HttpStreamingClient (metadata_only=True) handles
    artist/song metadata extraction from the same stream.
    """

    def __init__(self, url):
        """
        Class constructor.

        Args:
          url = The HTTP/SHOUTcast stream URL
        """
        threading.Thread.__init__(self)
        self.daemon = True

        self.url = url
        self.proc = None
        self.channel = None

        self.RUNNING = False
        self.THREAD_EXIT = False

    def start(self):
        """
        Start ffmpeg subprocess connected directly to the stream URL.

        Returns: None
        """
        if not shutil.which("ffmpeg"):
            raise Exception(
                "ffmpeg not found in PATH. "
                "Please install ffmpeg to play HTTP/SHOUTcast streams."
            )

        self.RUNNING = True

        cmd = [
            "ffmpeg",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-i", self.url,
            "-f", PCM_FORMAT,
            "-ac", str(PCM_CHANNELS),
            "-ar", str(PCM_RATE),
            "-loglevel", "quiet",
            "pipe:1",
        ]

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            self.RUNNING = False
            raise Exception("Failed to start ffmpeg: %s" % str(e))

        threading.Thread.start(self)

    def run(self):
        """
        Thread body: reads PCM from ffmpeg stdout and feeds to pygame.
        ffmpeg connects directly to the stream URL and handles everything
        (HTTP, ICY protocol, metadata stripping, audio decoding).

        Returns: None
        """
        try:
            self.channel = pygame.mixer.Channel(0)

            # Drain stderr in background to prevent pipe buffer deadlock
            stderr_drainer = threading.Thread(target=self._drain_stderr, daemon=True)
            stderr_drainer.start()

            # Read PCM continuously from ffmpeg stdout and play via pygame
            while self.RUNNING:
                data = self.proc.stdout.read(CHUNK_SIZE)
                if not data:
                    break
                sound = pygame.mixer.Sound(buffer=data)
                if not self.channel.get_busy():
                    self.channel.play(sound)
                else:
                    while self.channel.get_queue() and self.RUNNING:
                        time.sleep(0.01)
                    self.channel.queue(sound)

        except Exception as e:
            if DEBUG:
                print("StreamPlayer playback error: %s" % str(e))

        finally:
            self.RUNNING = False
            self.THREAD_EXIT = True

    def _drain_stderr(self):
        """
        Drains ffmpeg's stderr to prevent pipe buffer deadlock.

        Returns: None
        """
        try:
            while self.proc and self.proc.poll() is None:
                self.proc.stderr.read(4096)
        except Exception:
            pass

    def is_busy(self):
        """
        Check if the stream is still playing.

        Returns: True if playing, False otherwise
        """
        if self.RUNNING and not self.THREAD_EXIT:
            return True
        if self.channel and self.channel.get_busy():
            return True
        return False

    def stop(self):
        """
        Stop the stream player.

        Returns: None
        """
        self.RUNNING = False

        if self.channel:
            try:
                self.channel.stop()
            except Exception:
                pass

        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass

        while not self.THREAD_EXIT:
            time.sleep(0.05)

    def pause(self):
        if self.channel:
            self.channel.pause()

    def unpause(self):
        if self.channel:
            self.channel.unpause()
