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
import time
import queue
import threading
from socket import *
import pickle

# Import wxpython modules
import wx
from ScrollingLabel import ScrollingLabel

# Import own modules
from controller import music_controller
from Playlist import PlaylistContainer
from PlaylistGui import PlaylistGui
from OwnConstants import *


class UiHandler(threading.Thread):
    """
    Class that handles input from the user interface
    """
    
    def __init__(self, parent, config, skin):
        """
        Class constructor
        Args:
          parent = The parent window
          config = The player's config
          skin = The player's skin
        """
        # initialize threading
        threading.Thread.__init__(self)

        self.running = True
        
        # Hold on to parent 
        self.parent = parent

        # Hold on to config
        self.config = config

        # Hold on to skin
        self.skin = skin

        # Create event queue
        self.eventQueue = queue.Queue()

        # Create status queue
        self.statusQueue = queue.Queue()

        # Create playlist container
        self.plContainer = PlaylistContainer()

        # Prepare playlist
        self.playlistGui = PlaylistGui(parent, self.plContainer, self.config,
                                       self.skin, self.eventQueue)
        self.plContainer.playlistGui = self.playlistGui

        # Start music controller
        self.controller = music_controller(self.eventQueue, self.plContainer,
                                           self.statusQueue)
        self.controller.start()

        # Set player status
        self.setCurrentTrack(self.config.data["current-track"])
        if self.config.data["random"]:
            self.random()
            
        if self.config.data["repeat"]:
            self.repeat()

        # Fire up status catcher
        self.start()

        # Call stop on player to trigger gui update
        self.stop()
            
        

        # Start up pympClientApi
        if C_API:
            self.api = pympClientApi(self)
            self.api.start()
        

    def setLabel(self, label, text):
        """
        Method to set the text in the given label
        Args:
          label = The label we want to update
          text = The text we want to update with

        Returns: None
        """
        try:
            if label in self.parent.labels:
                widget = self.parent.labels[label]
                if isinstance(widget, ScrollingLabel):
                    wx.CallAfter(self._setTickerText, widget, text)
                else:
                    widget.SetLabel(text)
        except Exception as e:
            pass

    def _setTickerText(self, widget, text):
        """
        Method to set text on a ScrollingLabel widget from the GUI thread
        Args:
          widget = The ScrollingLabel widget
          text = The text to display

        Returns: None
        """
        widget.SetText(text)
        mdc = wx.MemoryDC()
        mdc.SetFont(widget.GetFont())
        textWidth, textHeight = mdc.GetTextExtent(text)
        mdc.SelectObject(wx.NullBitmap)
        if textWidth > widget.GetSize()[0]:
            widget.Start()
        else:
            widget.Stop()

    def run(self):
        """
        Thread that updates the gui labels based on events from
        the controller
        Args:
          None

        Returns: None
        """
        while self.running:
            try:
                event = self.statusQueue.get(True, 0.3)
            except queue.Empty:
                continue
            
            # Handle the event
            # Handle play update events
            if event[0][0] == 'play':
                self.setLabel('status', 'playing')
                self.setLabel('artist', '  %s' % event[1])
                self.setLabel('title', '    - %s' % event[2])
                self.setLabel('info', '')
                        
                # TODO Set current track to bold font
                # self.set_bold()
                
            # Handle duration update events
            elif event[0][0] == 'update':
                # Convert seconds --> minutes and seconds!
                time = event[0][1]
                minutes = int(time) // 60
                seconds = int(time) - (minutes * 60)
                if seconds < 10:
                    seconds = '0%d' % seconds
                else:
                    seconds = '%d' % seconds
                
                if minutes < 10:
                    minutes = '0%d' % minutes
                else:
                    minutes = '%d' % minutes 
                
                time_string = '%s:%s' % (minutes, seconds)
                self.setLabel('status', 'Playing [%s]' % time_string)
                
                if len(event[0]) == 4:
                    # We also have song information that are to override the playlist info
                    self.setLabel('artist', '  %s' % event[0][2])
                    self.setLabel('title', '    - %s' % event[0][3])
                    

            elif event[0][0] == 'buffering':
                self.setLabel('status', 'Buffering [%s]' % event[0][1])
            
            # Handle pause update events
            elif event[0][0] == 'pause':
                self.setLabel('status', 'Paused')
                self.setLabel('info', '')
                self.setLabel('artist', '  %s' % event[1])
                self.setLabel('title', '    - %s' % event[2])
            
            # Handle stop update events
            elif event[0][0] == 'stop':
                self.setLabel('status', 'Stopped')
                self.setLabel('info', '')
                self.setLabel('artist', '  %s' % event[1])
                self.setLabel('title', '    - %s' % event[2])
                
            # Handle toggle update events
            elif event[0][0] == 'toggle':
                self.setLabel('status', 'Player in %s mode' % event[3].PLAYER_MODE)
                self.setLabel('info', '')
                self.setLabel('artist', '')
                self.setLabel('title', '')
            
                # TODO Reload playlist
                # self.reload_playlist()
            
            # Handle empty update events
            elif event[0][0] == 'empty':
                self.setLabel('status', '')
                self.setLabel('info', 'Playlist is empty')
                self.setLabel('artist', '')
                self.setLabel('title', '')
            
            # Handle the toggeling of random and repeat!
            elif event[0][0] == 'random_repeat':
                random_repeat = ""
                if event[0][1] == True:
                    # Random is activated!
                    self.parent.toggleButton("random", True)
                else:
                    # Random is deactivated!
                    self.parent.toggleButton("random", False)
                
                if event[0][2] == True:
                    # Repeat is activated
                    self.parent.toggleButton("repeat", True)

                else:
                    # repeate is deactivated
                    self.parent.toggleButton("repeat", False)

            elif event[0][0] == 'quit':
                break
            # Handle info update events
            elif event[0][0] == 'info':
                self.setLabel('info', event[1])
            
            # Unknown event, print it for debugging purposes
            else:
                #print event
                pass

        #print "Gui updater exited"
        
    def play(self, num=None):
        """
        Method to tell the controller to start playing
        Args:
          (opt)num = The number of the song to start playing

        Returns: None
        """
        
        if not num:
            self.eventQueue.put(['play'])
        else:
            self.eventQueue.put(['%s' % num])
        
        
    def stop(self):
        """
        Method to tell the controller to stop playing
        Args:
          None

        Returns: None
        """
        self.eventQueue.put(['stop'])

    def pause(self):
        """
        Method to tell the controller to pause playing
        Args:
          None

        Returns: None
        """
        self.eventQueue.put(['pause'])

    def next(self):
        """
        Method to tell the controller to jump to the next song
        Args:
          None

        Returns: None
        """
        self.eventQueue.put(['next'])

    def prev(self):
        """
        Method to tell the controller to jump to the previouse song
        Args:
          None

        Returns: None
        """
        self.eventQueue.put(['prev'])

    def terminate(self):
        """
        Method to terminate gui
        Args:
          None

        Returns: None
        """
        self.parent.OnExit()

    def random(self):
        """
        Method to tell the controller to toggle random
        Args:
          None

        Returns: None
        """
        self.eventQueue.put(['random'])

    def repeat(self):
        """
        Method to tell the controller to toggle repeat
        Args:
          None

        Returns: None
        """
        self.eventQueue.put(['repeat'])
        
    def playlist(self):
        """
        Method to toggle playlist gui on/off
        Args:
          None

        Returns: None
        """
        self.playlistGui.toggleWindow()

    def savePlaylist(self, noDialog = False):
        """
        Method to save playlist
        Args:
          None

        Returns: None
        """
        self.playlistGui.savePlaylist(noDialog)
        
    def fetchPlaylist(self):
        """
        Method to fetch playlist and return it pickled
        Args:
          None

        Returns: The pickled playlist
        """
        try:
            data = pickle.dumps(self.plContainer.play_list)
        except Exception as e:
            #print e
            return None

        return data

    def fetchCurrentSong(self):
        """
        Method to fetch current song
        Args:
          None

        Returns: Current song
        """
        return self.plContainer.current

    def addFile(self, filename):
        """
        Method to add a file to the playlist
        Args:
          filename = The filename to add

        Returns: None
        """
        # Add file
        if self.plContainer.addFile(filename):
            # refresh playlist
            self.playlistGui.playlistWidget.refreshPlaylist()
           
    def minimize(self):
        """
        Method to minimize player window
        Args:
          None

        Returns: None
        """
        self.parent.OnMinimize()
        
    def configure(self):
        """
        Method to show the configure window
        Args:
          None

        Returns: None
        """
        self.parent.config.showConfigWindow()

    def about(self):
        """
        Method to show the about screen
        Args:
          None

        Returns: None
        """
        self.parent.about.showAboutWindow()
        
    def refreshPlaylist(self):
        """
        Method to refresh the playlist
        Args:
          None

        Returns: None
        """
        self.playlistGui.playlistWidget.refreshPlaylist()

    def toggleWindow(self):
        """
        Method to toggle visibility of parent window.
        The player itself.
        Args:
          None

        Returns: None
        """
        # Hide parent window
        self.parent.ToggleWindow()

    def setCurrentTrack(self, number):
        """
        Method to set current track
        Args:
          number = (int) The track to set
        """
        
        self.plContainer.setCurrent(number)



    def getCurrentTrack(self):
        """
        Method to get current track
        Args:
          None

        Return: (int) Current track 
        """
        
        return self.plContainer.current

    def getRandomStatus(self):
        """
        Method to get random status
        Args:
          None

        Return: Boolean telling us if random is toggled or not
        """
        
        return self.controller.getRandom()

    def getRepeatStatus(self):
        """
        Method to get repeat status
        Args:
          None

        Return: Boolean telling us if repeat is toggled or not
        """

        return self.controller.getRepeat()



        
    def close(self):
        """
        Method to close down the player. Closes the client api if it is
        started.
        Args:
          None

        Returns: None
        """
        self.config.data["playlistPosition"] = self.playlistGui.GetPosition().Get()

        # Close pympClientApi
        if C_API:
            address = (gethostbyname(gethostname()), 8308)
            c_soc = socket(AF_INET, SOCK_STREAM)
            c_soc.connect(address)
            command = "QUIT"
            command.ljust(1024)
            c_soc.send(command)
        
        # close playlist gui
        self.playlistGui.close()
        self.running = False
        self.eventQueue.put(['quit'])




class pympClientApi(threading.Thread):
    """
    The pymp client api. Can be used to control the pymp player over
    a tcp/ip connection.
    """

    def __init__(self, uiHandler):
        """
        Class constructor
        Args:
          uiHandler = The uihandler instance
        """
        threading.Thread.__init__(self)
        self.uiHandler = uiHandler
        self.address = (gethostbyname(gethostname()), 8308)
        
    def run(self):
        """
        The thread body that listens to requests and executes them
        Args:
          None

        Returns: None
        """
        s_soc = socket(AF_INET, SOCK_STREAM)
        s_soc.bind(self.address)
        s_soc.listen(5)
        
        while True:
            c_soc = None
            try:
                c_soc, addr = s_soc.accept()
                data = c_soc.recv(1024)

                # Strip padding from command
                data = data.rstrip()
                
                # Execute action
                if data == "play":
                    self.uiHandler.play()

                elif data == "prev":
                    self.uiHandler.prev()

                elif data == "pause":
                    self.uiHandler.pause()

                elif data == "stop":
                    self.uiHandler.stop()

                elif data == "next":
                    self.uiHandler.next()

                elif data == "repeat":
                    self.uiHandler.repeat()

                elif data == "random":
                    self.uiHandler.random()

                elif data.isdigit():
                    self.uiHandler.play(data)
                    
                elif data == "addFile":
                    data = c_soc.recv(1024)
                    # Strip padding
                    data = data.rstrip()
                    self.uiHandler.addFile(data)

                elif data == "fetchPlaylist":
                    # Return playlist
                    data = self.uiHandler.fetchPlaylist()
                    if data != None:
                        lengthString = "%d" % len(data)
                        
                        # padd data
                        lengthString = lengthString.ljust(1024)
                        c_soc.send(lengthString)
                        c_soc.send(data)
                        time.sleep(1)
                    else:
                        lengthString = "0"
                        # padd data
                        lengthString.ljust(1024)
                        c_soc.send(lengthString)
                        time.sleep(1)

                    
                    
                    
                elif data == "currentSong":
                    song = self.uiHandler.fetchCurrentSong()
                    song = "%d" % song
                    song.ljust(1024)
                    c_soc.send(song)
                    time.sleep(1)
                
                elif data == "QUIT":
                    c_soc.close()
                    break

                # Close connection
                c_soc.close()
        
            except Exception as e:
                #print "Exception: %s" % str(e)
                pass
            
