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
import threading
import time
import queue
import random
import random
from socket import *

# Import own modules
from Pymedia_api_new import pymedia_api
from OwnConstants import *

class player_state:
    """
    A container to hold the state of the player
    """

    def __init__(self, mode):
        """
        Class constructor
        Args:
          None
        """
        self.RANDOM = false  
        self.REPEAT = false   
        self.PLAY = false
        self.PAUSE = false
        self.PLAYER_MODE = mode

# Setting the available players
PLAYER_MODES = [(pymedia_api, "MP3")]

class music_controller(threading.Thread):
    """
    The music event based controller
    """

    def __init__(self, event_queue, pl_container, status_queue):
        """
        The objects constructor
        Args:
          event_queue = The queue holding the events
          pl_container = The playlist object
          (OPT) status_queue = The queue on which we will return status info

        Returns: None
        """
        
        # init thread
        threading.Thread.__init__(self)

        # Hold on to the event_queue
        self.event_queue = event_queue
        self.status_queue = status_queue

        # init the state of the player
        self.current_mode = PLAYER_MODES[0][PLAYER_TEXTUAL_NAME]
        self.state = player_state(self.current_mode)

        # The players
        self.players = {}

        # The play list
        self.pl_container = pl_container
                
        # Displying playlist status
        self.PLAYLIST = false
        
        # Super duper hack to avoid pymedia to return garbage
        # information for 14 seconds
        self.DONTASK = 4

        # Create an instance of all player objects
        for player in PLAYER_MODES:
            self.players[player[PLAYER_TEXTUAL_NAME]] = player[PLAYER_OBJECT_NAME]()
            # Init the player
            self.players[self.state.PLAYER_MODE].init()
            # Clear playlist
            self.pl_container.play_list = []
            # Fetch the new players play list
            self.pl_container.play_list = self.players[self.state.PLAYER_MODE].get_playlist()
            # Reload playlist
            self.pl_container.refreshPlaylist()

        
    def send_status(self, message):
        """
        Method to send status messages to GUI
        Args:
          message = The message to send

        Returns: None
        """
        # Send status message
        if not self.status_queue == None:
            # Enqueue event executed and song playing
            if len(self.pl_container.play_list) == 0:
                message = ['empty']
                
            if message[0] == 'empty' or message[0] == 'quit' or message[0] == 'unknown' or message[0] == 'toggle': 
                self.status_queue.put([message, None, None, self.state])
            elif message[0] == 'update':
                self.status_queue.put([message])
                
            elif message[0] == 'buffering' or message[0] == 'update' or message[0] == 'random_repeat':
                self.status_queue.put([message])
                
            elif message[0] == 'play':
                self.status_queue.put([message, self.pl_container.play_list[self.pl_container.current][2], self.pl_container.play_list[self.pl_container.current][1], self.state])
            else:
                self.status_queue.put([message, self.pl_container.play_list[self.pl_container.current][2], self.pl_container.play_list[self.pl_container.current][1], self.state])

            
    def getRandom(self):
        """
        Method to get the random state
        Args:
          None

        Returns: The random state
        """
        return self.state.RANDOM

    def getRepeat(self):
        """
        Method to get the repeat state
        Args:
          None

        Returns: None
        """
        return self.state.REPEAT
    
    def run(self):
        """
        The main body og the controller thread
        Args:
          None

        Returns: None
        """

        while true:
            # Fetch event from event queue or wait for time-out
            try:
                event = self.event_queue.get(true, TRIGGER_UPDATE)
            except queue.Empty as e:
                # We have a time-out.
                if self.state.PLAY:
                    # If state is set to playing check that we are playing a song
                    if not self.players[self.state.PLAYER_MODE].get_busy():
                        # Song is finished. Jump to next
                        event = ['next']
                    else:
                        # Nothing should be done
                        event = ['nothing']
                else:
                    # Nothing should be done
                    event = ['nothing']
                    
            
            ####
            # Handle nothing event
            if event[0] == 'nothing':
                if self.state.PLAY:
                    # See if we have any info from the player object that we want to display
                    status_sent = False
                    info = self.players[self.state.PLAYER_MODE].read_info()
                    if info != None:
                        if info["buffer_status"] != False:
                            # We are buffering
                            self.send_status(['buffering', info["buffer_status"]])
                            status_sent = True
                            
                        elif info["song_info"] != False:
                            # We have song information from stream!
                            #print "controller:", info["song_info"]
                            self.send_status(['update', self.players[self.state.PLAYER_MODE].get_length(), info["song_info"]["artist"], info["song_info"]["song"]])
                            status_sent = True
                            
                    if not status_sent:
                        self.send_status(['update', self.players[self.state.PLAYER_MODE].get_length()])
                
            ####
            # Handle previouse event
            elif event[0] == 'prev':
                # Only execute next if we're not paused
                if not self.state.PAUSE:
                                     
                    # If random playing is enabled, this event kills it.
                    if self.state.RANDOM:
                        self.state.RANDOM = false
                        self.send_status(['random_repeat', self.state.RANDOM, self.state.REPEAT])
                    # If we have deleted some songs make sure that we still are in range
                    # of playlist
                    if self.pl_container.current >= len(self.pl_container.play_list):
                        self.pl_container.setCurrent(len(self.pl_container.play_list))
                        pass

                    # Fetch current song and decrement it
                    song = self.pl_container.current - 1

                    if song < 0:
                        if self.state.REPEAT:
                            song = len(self.pl_container.play_list) - 1
                        else:
                            song = 0
                    
                    if song >= 0 and song < len(self.pl_container.play_list):
                        self.pl_container.setCurrent(song)
                        if self.state.PLAY:
                            self.players[self.state.PLAYER_MODE].play(self.pl_container.play_list[self.pl_container.current][0])
                            self.state.PLAY = true
                            self.send_status(['play'])
                            
                        else:
                            # Send status
                            self.send_status(['stop'])
                    
            ####
            # Handle next event
            elif event[0] == 'next':
                # Only execute next if we're not paused
                if not self.state.PAUSE:
                    # Fetch current song and increment it
                    if self.state.RANDOM:
                        song = random.randint(0, len(self.pl_container.play_list) - 1)
                    else:
                        song = self.pl_container.current + 1
    
                    if song >= len(self.pl_container.play_list):
                        if self.state.REPEAT:
                            song = 0
                        else:
                            self.players[self.state.PLAYER_MODE].stop()
                            self.state.PAUSE = false
                            self.state.PLAY = false
                            self.pl_container.setCurrent(0)
                            if len(self.pl_container.play_list):
                                self.send_status(['stop'])
                            else:
                                self.send_status(['empty'])
                            
                        
                              
                    if song >= 0 and song < len(self.pl_container.play_list):
                        self.pl_container.setCurrent(song)
                        if self.state.PLAY:
                            self.players[self.state.PLAYER_MODE].play(self.pl_container.play_list[self.pl_container.current][0])
                            self.state.PLAY = true
                            self.send_status(['play'])
                        else:
                            # Send status
                            self.send_status(['stop'])

                    
            ####
            # Handle play event
            elif event[0] == 'play':
                
                # Test if it is paused. If so, just resume
                if self.state.PAUSE:
                    continue
                
                if self.state.RANDOM:
                    song = random.randint(0, len(self.pl_container.play_list) - 1)
                    self.players[self.state.PLAYER_MODE].play(self.pl_container.play_list[song][0])
                    self.pl_container.setCurrent(song)
                    self.state.PLAY = true
                        
                    # Send status
                    self.send_status(['play'])
                    
                else:
                    song = self.pl_container.current
                    if song >= 0 and song < len(self.pl_container.play_list):
                        self.players[self.state.PLAYER_MODE].play(self.pl_container.play_list[song][0])
                        self.pl_container.setCurrent(song)
                        self.state.PLAY = true
                        
                        # Send status
                        self.send_status(['play'])
                        
                            
                        
                    elif self.state.REPEAT and len(self.pl_container.play_list) > 0:
                        self.players[self.state.PLAYER_MODE].play(self.pl_container.play_list[0][0])
                        self.pl_container.setCurrent(0)
                        self.state.PLAY = true
                        
                        # Send status
                        self.send_status(['play'])
                        
                    else:
                        #print 'No more items to play!'
                        self.players[self.state.PLAYER_MODE].stop()
                        self.state.PLAY = false
                        self.pl_container.setCurrent(0)

                        # Send status
                        self.send_status(['empty'])
                        # Send status message
                

            elif event[0] == 'pause':
                if self.state.PLAY:
                    self.state.PLAY = false
                    self.state.PAUSE = true
                    self.players[self.state.PLAYER_MODE].pause()
                    # Send status
                    self.send_status(['pause'])
                elif self.state.PAUSE:
                    self.state.PLAY = true
                    self.state.PAUSE = false
                    self.players[self.state.PLAYER_MODE].resume()
                    # Send status
                    self.send_status(['play'])
                    
            elif event[0] == 'stop':
                if self.state.PLAY == true:
                    self.state.PLAY = false
                    self.players[self.state.PLAYER_MODE].stop()
                                    
                elif self.state.PAUSE == true:
                    self.players[self.state.PLAYER_MODE].stop()
                    self.state.PAUSE = false
                    self.state.PLAY = false
                
                # Send status
                self.send_status(['stop'])
                                
            elif event[0] == 'random':
                if self.state.RANDOM:
                    self.state.RANDOM = false
                    # send status
                    self.send_status(['random_repeat', self.state.RANDOM, self.state.REPEAT])
                else:
                    self.state.RANDOM = true
                    # send status
                    self.send_status(['random_repeat', self.state.RANDOM, self.state.REPEAT])
                    
                    
                    
            elif event[0] == 'repeat':
                if self.state.REPEAT:
                    self.state.REPEAT = false
                    # send status
                    self.send_status(['random_repeat', self.state.RANDOM, self.state.REPEAT])
                else:
                    self.state.REPEAT = true
                    # send status
                    self.send_status(['random_repeat', self.state.RANDOM, self.state.REPEAT])

            # Play song on position X in playlist
            elif event[0].isdigit():
                # Test if song is available in playlist
                song = int(event[0])
                if song >= 0 and song < len(self.pl_container.play_list):
                    # Start playing song
                    self.players[self.state.PLAYER_MODE].play(self.pl_container.play_list[song][0])
                    self.state.PLAY = true
                    self.pl_container.setCurrent(song)

                    # Send status
                    self.send_status(['play'])

                else:
                    self.state.PLAY = false

                    # Send status
                    self.send_status(['stop'])
        
            elif event[0] == 'status':
                    
                if self.state.STATUS:
                    self.state.STATUS = false
                else:
                    self.state.STATUS = true
                   
            elif event[0] == 'quit':
                #print "Executing quit"
                self.players[self.state.PLAYER_MODE].destroy()
                #print "Send quit status"
                # send status
                self.send_status(['quit'])
                #print "Breaking out of loop"
                break
            
            # Event unknown
            else:
                pass

            
