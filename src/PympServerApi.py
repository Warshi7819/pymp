###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
###################################################

# Import standard modules
import threading
import pickle
from socket import *
import struct

# Import 3rdparty modules
from wx.lib.stattext import GenStaticText
import  wx

# Import own modules
from OwnConstants import *


class DownloadPlaylistManager(threading.Thread):
    """
    Class that handles the downloading of a playlist
    from a pymp server
    """
    
    def __init__(self, pympServerApi, parent, value, labelStatus):
        """
        Class constructor
        Args:
          pympServerApi = The api that enables us to talk to the
                          pymp server
          parent = The parent object
          value = The address to the pymp server
          labelStatus = The label we will update as we progress
        """
        threading.Thread.__init__(self)
        self.parent = parent
        self.pympServerApi = pympServerApi
        self.labelStatus = labelStatus
        self.value = value

    def run(self):
        """
        The download thread's body
        Args:
          None

        Returns: None
        """
        self.pympServerApi.disableInput()
        if len(self.value) != 2:
            self.labelStatus.SetLabel("Format is 'ip:port' or 'hostname:port'")
            self.pympServerApi.enableInput()
            return

        try:
            address = ("%s" % self.value[0],int(self.value[1]))
        except Exception as e:
            self.labelStatus.SetLabel("Format is 'ip:port' or 'hostname:port'")
            self.parent.pympServerApi.enableInput()
            return
        
        try:
            self.labelStatus.SetLabel("connecting to %s:%d" % (address[0],
                                                               address[1]))
            # Connect to given server and fetch playlist
            c_soc = socket(AF_INET, SOCK_STREAM)
            c_soc.connect(address) 
            self.labelStatus.SetLabel("Sending request")
            
            # Send request
            c_soc.send(struct.pack('!I', PLAYLIST_REQUEST))
            self.labelStatus.SetLabel("Waiting for respons")

            # Fetch answer
            size = struct.unpack('!I', c_soc.recv(4))[0]
            received = 0
            data = ""
            if size > 0:
                while received < size:
                    if size - received <= CHUNCK_SIZE:
                        length = size - received
                    else:
                        length = CHUNCK_SIZE
                        
                    tmp = c_soc.recv(length)
                    data += tmp
                    fetched = len(tmp)
                    received += fetched
                    
                    self.labelStatus.SetLabel("Downloaded: %.2f %%" % ((float(received)/float(size)) * 100))
                    
                if data:
                    playlist = pickle.loads(data)
                    self.labelStatus.SetLabel("Adding %d songs to playlist" % len(playlist))
                    self.parent.plContainer.addPympServer(playlist, address)
                    self.parent.playlistWidget.refreshPlaylist()
                    self.labelStatus.SetLabel("%d songs added" % len(playlist))
                else:
                    self.labelStatus.SetLabel("Error occured")
                    
            else:
                self.labelStatus.SetLabel("No playlist received")

            c_soc.close()
            
        except Exception as e:
            self.labelStatus.SetLabel("Error occured: %s" % str(e))
            
        self.pympServerApi.enableInput()

class PympServerConfigWindow(wx.Frame):
    """
    The gui that enables the user loading the playlist from the
    pymp server.
    """
    
    def __init__(self, parent, position):
        """
        Class constructor.
        Args:
          parent = The parent window
          position = The window position
        """
        wx.Frame.__init__(self, parent, -1, "pyMP server", position,
                          (250,200), wx.CAPTION)

        self.parent = parent
        self.Bind(wx.EVT_CLOSE, self.close)

        # Fetch icon
        self.icon = wx.Icon("gi.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.setBackground()
        self.addButtons()
        self.addLabels()
        
        parent = self.GetParent()
        if parent:
            parent.Disable()
        self.Show()


    def setBackground(self):
        """
        Method to set the background colour
        Args:
          None

        Returns: None
        """
        self.SetBackgroundColour("#D8D8D8")
        self.SetForegroundColour("#000000")
        

    def addButtons(self):
        """
        Method to add buttons
        Args:
          None

        Returns: None
        """
        # Adding Load button
        self.loadButton = wx.Button(self, -1, "Load Playlist", (10, 50))
        self.Bind(wx.EVT_BUTTON, self.load, self.loadButton)
        self.loadButton.SetDefault()
        self.loadButton.SetSize(self.loadButton.GetBestSize())
        
        # Adding Close button
        self.doneButton = wx.Button(self, -1, "Done", (10, 130))
        self.Bind(wx.EVT_BUTTON, self.close, self.doneButton)
        self.doneButton.SetDefault()
        self.doneButton.SetSize(self.doneButton.GetBestSize())


    def addLabels(self):
        """
        Method to add labels
        Args:
          None

        Returns: None
        """
        self.labelHeader = GenStaticText(self, -1, '', wx.Point(10,5), (200, 15), wx.ST_NO_AUTORESIZE)
        self.labelHeader.SetBackgroundColour("#D8D8D8")
        self.labelHeader.SetForegroundColour("#000000")
        self.labelHeader.SetLabel("Fetch playlist from pymp server")

        self.labelHelper = GenStaticText(self, -1, '', wx.Point(10,25), (45, 15), wx.ST_NO_AUTORESIZE)
        self.labelHelper.SetBackgroundColour("#D8D8D8")
        self.labelHelper.SetForegroundColour("#000000")
        self.labelHelper.SetLabel("Address:")

        self.textField = wx.TextCtrl(self, -1, "", wx.Point(55,23),
                                     size=(150,-1))

        self.labelStatus = GenStaticText(self, -1, '', wx.Point(10,80))
                                         
        
        self.labelStatus.SetBackgroundColour("#D8D8D8")
        self.labelStatus.SetForegroundColour("#0095F4")
        self.labelStatus.SetLabel("Waiting for input..")
        
    def close(self, event):
        """
        Method to close gui
        Args:
          event = The close event

        Returns: None
        """
        parent = self.GetParent()
        if parent:
            parent.Enable()
        self.Destroy()


    def disableInput(self):
        """
        Method to disable input while loading playlist from server
        Args:
          None

        Returns: None
        """
        self.loadButton.Enable(False)
        self.doneButton.Enable(False)
        self.textField.Enable(False)
        
    def enableInput(self):
        """
        Method to enable input when we are done loading
        Args:
          None

        Returns: None
        """
        self.loadButton.Enable(True)
        self.doneButton.Enable(True)
        self.textField.Enable(True)


    def load(self, event):
        """
        Method to load a playlist when the button is pressed
        Args:
          event = The button event

        Returns: None
        """
        self.labelStatus.SetLabel("Connecting to pyMP server")
        
        # Parse input data and validate
        value = self.textField.GetValue().split(":")

        downloadManager = DownloadPlaylistManager(self, self.parent, value,
                                                  self.labelStatus)
                                                  
        downloadManager.start()
