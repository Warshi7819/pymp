###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pygame and wxPython  #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import 3rdparty modules
import pygame
import pygame.mixer

# Import standard modules
import time, threading
import os

# Import own modules
from OwnConstants import *
from StreamPlayer import StreamPlayer
from file_streaming import HttpStreamingClient

import wx
from GuiUtils import InformDialog

class pymedia_controller(threading.Thread):
    """
    Class to control the playing of audio using
    pygame asyncronously. Rewritten for new api
    """

    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        threading.Thread.__init__(self)
        self.daemon = True

        # State variables!
        self.RUN = false
        self.STOP = true
        self.song = None
        self.RELOAD = true
        self.DESTROY = false
        self.PAUSE = false
        self.IS_STREAM = false
        self._stream_start_time = 0

        # Stream player state (for HTTP/SHOUTcast streams)
        self.stream_player = None
        self.metadata_client = None

        self.info = {}
        # initialize info dictionary
        self.updateInfo({"type": TYPE_FLUSH})


    def updateInfo(self, info_data):
        """
        Method to update info
        Args:
          info_data = dictionary holding info from stream

        Returns: None
        """
        if info_data != None:
            # Test if we are buffering
            if info_data["type"] == TYPE_BUFFERING:
                self.info["buffer_status"] = info_data["buffer_status"]

            # Test if we have song information from stream
            elif info_data["type"] == TYPE_SONG_INFO:
                if self.info["song_info"] == False:
                    self.info["song_info"] = {}
                    self.info["song_info"]["song"] = ""
                    self.info["song_info"]["artist"] = ""

                self.info["song_info"]["song"] = info_data["song"]
                self.info["song_info"]["artist"] = info_data["artist"]


            elif info_data["type"] == TYPE_FLUSH:
                self.info["buffer_status"] = False
                self.info["song_info"] = False

        else:
            # We are not currently buffering!
            self.info["buffer_status"] = False


    def readInfo(self):
        """
        Method to read info
        Args:
          None

        Returns: None
        """
        return self.info

    def run(self):
        """
        Thread to play audio using pygame library
        Args:
          None

        Returns: None
        """

        while(not self.DESTROY):
            try:
                time.sleep(0.5)
                # If we have a song, load and play it
                if self.RELOAD and self.song:
                    self.STOP = false
                    self.RELOAD = false
                    self.PAUSE = false

                    song_path = self.song

                    # Check if this is an HTTP/SHOUTcast stream
                    if song_path.lower().startswith('http://') or song_path.lower().startswith('https://'):
                        self.IS_STREAM = true
                        self._start_stream(song_path)

                    # Strip file:// prefix for local files
                    elif song_path.lower().startswith('file://'):
                        song_path = song_path[7:]
                        self.IS_STREAM = false

                        try:
                            pygame.mixer.music.load(song_path)
                            pygame.mixer.music.play()
                            self.RUN = true
                        except Exception as e:
                            if DEBUG:
                                print(e)
                            self.STOP = true
                            self.song = None

                    # Unknown URI scheme
                    else:
                        if DEBUG:
                            print("Unsupported URI scheme: %s" % song_path)
                        self.STOP = true
                        self.song = None

                # If song is loaded, monitor playback
                if self.RELOAD == false and self.song:

                    if self.IS_STREAM:
                        # Monitor stream player
                        while self.RUN and not self.DESTROY:
                            if self.stream_player and not self.stream_player.isBusy():
                                # Stream ended
                                break
                            if self.PAUSE:
                                time.sleep(0.1)
                                continue
                            time.sleep(0.2)
                    else:
                        # Monitor pygame music playback
                        while self.RUN and not self.DESTROY:
                            if not pygame.mixer.music.get_busy():
                                # Song finished
                                break
                            if self.PAUSE:
                                time.sleep(0.1)
                                continue
                            time.sleep(0.2)

                    # Close/unload
                    try:
                        if self.IS_STREAM:
                            self._stop_stream()
                        else:
                            pygame.mixer.music.stop()
                            pygame.mixer.music.unload()
                    except Exception:
                        pass


                #  Finished playing song, reset player
                self.STOP = true
                self.song = None
                self.IS_STREAM = false

                # Reset info gathered
                self.updateInfo({"type": TYPE_FLUSH})

            except Exception as e:
                if DEBUG:
                    print(e)
                # Reset player
                self.STOP = true
                self.song = None
                self.RUN = false
                self.IS_STREAM = false
                self._stop_stream()

    def _start_stream(self, url):
        """
        Start an HTTP/SHOUTcast stream with two connections:
        1. ffmpeg connects directly to the URL for audio decoding/playback
        2. HttpStreamingClient (metadata_only=True) connects for metadata extraction

        Args:
          url = The stream URL

        Returns: None
        """
        # Create a metadata callback that feeds into updateInfo
        def onMetadata(info):
            self.updateInfo({
                "type": TYPE_SONG_INFO,
                "artist": info.get("artist", ""),
                "song": info.get("song", ""),
            })

        try:
            # Connection 2: HttpStreamingClient for metadata only
            # Connects to the same URL, scans for StreamTitle=,
            # extracts artist/song. Audio data is discarded.
            self.metadata_client = HttpStreamingClient(
                url,
                metadata_only=True,
                metadata_callback=onMetadata,
            )
            self.metadata_client.start()

            # Connection 1: ffmpeg connects directly to the URL
            # Handles HTTP, ICY protocol, strips metadata, decodes audio,
            # outputs clean PCM to pygame for continuous playback.
            self.stream_player = StreamPlayer(url)
            self.stream_player.start()
            self._stream_start_time = time.time()

            self.RUN = true

        except Exception as e:
            if DEBUG:
                print("Failed to start stream: %s" % str(e))
            self.stream_player = None
            self.metadata_client = None
            self.STOP = true
            self.song = None
            wx.CallAfter(
                InformDialog,
                None, (0, 0),
                "Stream Error",
                "Failed to start stream: %s" % str(e),
            )

    def _stop_stream(self):
        """
        Stop the stream player and metadata reader.

        Returns: None
        """
        if self.stream_player:
            try:
                self.stream_player.stop()
            except Exception:
                pass
            self.stream_player = None

        if self.metadata_client:
            try:
                self.metadata_client.close()
            except Exception:
                pass
            self.metadata_client = None


    def pause(self):
        """
        Method to pause playing
        Args:
          None

        Returns: None
        """
        if self.PAUSE:
            if self.IS_STREAM:
                if self.stream_player:
                    self.stream_player.unpause()
            else:
                pygame.mixer.music.unpause()
            self.PAUSE = false
        else:
            if self.IS_STREAM:
                if self.stream_player:
                    self.stream_player.pause()
            else:
                pygame.mixer.music.pause()
            self.PAUSE = true

    def stopPlaying(self):
        """
        Method to stop playing
        Args:
          None

        Returns: None
        """
        # Stop stream player if active
        if self.IS_STREAM:
            self._stop_stream()

        # Stop pygame playback
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception:
            pass

        # Set RUN to false
        self.RUN = false

        # Wait until we have indeed stopped playing before returning
        while not self.STOP:
            time.sleep(0.05)

        # Reset player
        self.song = None
        self.RELOAD = true
        self.PAUSE = false
        self.RUN = true
        self.IS_STREAM = false

        return True

    def play(self, song):
        """
        Method to start playing a given song
        Args:
          song = An uri specifying a file (local, http or tcp/ip)

        Returns: True when done
        """
        self.stopPlaying()
        self.song = song

        # Return when self.STOP has become false again
        # or if self.song is set to none. If the latter happens
        # an exception has occured and self.STOP already has
        # been set to false and back to true again
        while self.STOP:
            if self.song == None:
                break
            time.sleep(0.02)

        return True

    def getBusy(self):
        """
        Method to figure out if we are currently playing anything
        Args:
          None

        Returns: True if busy, False otherwise
        """
        if self.STOP:
            return False
        else:
            return True

    def destroy(self):
        """
        Method to destroy thread. Stops playing and awaits the
        Termination of the thread
        Args:
          None

        Returns: True when done
        """
        self.DESTROY = true
        self._stop_stream()
        self.stopPlaying()

        return True

    def getPosition_t(self):
        """
        Method to get position of current track
        Args:
          None

        Returns: Number of seconds since last complete stop
                 If sound instance does not exist we aint playing,
                 return 0
        """
        try:
            if self.IS_STREAM:
                if self._stream_start_time > 0:
                    return time.time() - self._stream_start_time
            else:
                if pygame.mixer.music.get_busy():
                    return pygame.mixer.music.get_pos() / 1000.0
        except Exception:
            pass
        return 0


class pymedia_api:
    """
    Class to make the current underlying 3rdparty
    streaming software transparent. To incorporate a new
    media package into pyPlayer just make a wrapper class
    like this one and expose these functions. Then change the class
    loaded in the controller.py file
    """

    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        self.pymedia_o = None

    def play(self, song):
        """
        Method to play a song
        Args:
          song = URI describing which song to play

        Returns: ret value of called function
        """
        return self.pymedia_o.play(song)

    def readInfo(self):
        """
        Method to read info on buffer status
        and information fetched from audio streams
        Args:
          None

        Returns: The info gathered from a stream
        """
        return self.pymedia_o.readInfo()


    def stop(self):
        """
        Method to stop playing song
        Args:
          None

        Returns: ret value of called function
        """
        return self.pymedia_o.stopPlaying()

    def pause(self):
        """
        Method to pause playing
        Args:
          None

        Returns: ret value of called function
        """
        return self.pymedia_o.pause()

    def resume(self):
        """
        Method to resume a paused song
        Args:
          None

        Returns: ret value of called function
        """
        return self.pymedia_o.pause()

    def getBusy(self):
        """
        Method to determine if we are playing a song or not
        Args:
          None

        Returns: ret value of called function
        """
        return self.pymedia_o.getBusy()

    def getLength(self):
        """
        Method to determine number of seconds played
        Args:
          None

        Returns: ret value of called function
        """
        return self.pymedia_o.getPosition_t()

    def init(self):
        """
        Method to initialize object
        Args:
          None

        Returns: True when done
        """
        if self.pymedia_o == None:
            # Initialize pygame mixer
            # Initialize pygame mixer — match ffmpeg output format
            # (44100 Hz, s16, stereo, 2048 buffer for low latency)
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            self.pymedia_o = pymedia_controller()
            self.pymedia_o.start()

        return True

    def open(self):
        """
        TO BE REMOVED? Initially implemented to open
        cd drawer in CD mode only
        Args:
          None

        Returns: None
        """
        pass

    def destroy(self):
        """
        Function called to destroy object
        Args:
          None

        Returns: True when done
        """
        # Shutdown pymedia controller and
        # unreference object
        self.pymedia_o.destroy()
        self.pymedia_o = None
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        return True

    def getPlaylist(self):
        """
        Method to read playlist and return items in list
        Args:
          None

        Returns: list with songs (URI's)
        """
        # Test that playlist exists, if not create empty one!
        if not os.access('playlist.pypl', os.F_OK):
            fp = open('playlist.pypl','w', encoding='utf-8')
            fp.close()
            return []

        # open playlist and read content
        fp = open('playlist.pypl', 'r', encoding='utf-8')
        data = fp.readlines()
        fp.close()
        playlist = []
        key = 0
        # For each element extract filename, track name and artist
        for element in data:
            filename, track_name, artist = element.split('<')
            playlist.append([filename.strip('\n'), track_name.strip('\n'), artist.strip('\n')])
            key += 1

        # Return list
        return playlist
