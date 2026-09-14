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
import sys
import os
import time
import threading
from http.client import HTTPConnection
from urllib.parse import quote, urlencode
import base64

# Import wxpython modules
import  wx
from wx.lib.stattext import GenStaticText


# Own modules
from Curry import curry
from sort import sortStringTuple
from OwnConstants import *
from GuiUtils import bitmapType, getSelected, InformDialog
from Utils import parsePls, parseM3u, parsePypl
from PympServerApi import PympServerConfigWindow
from Debug import Help
from Network import getLocalIp, Network, HttpUtils

class HttpStreamManager(wx.Frame):
    """
    Dialog to add http streams
    """
    
    def __init__(self, parent, position):
        """
        Class constructor.
        Args:
          parent = The parent window
          position = Position of dialog
        """
        wx.Frame.__init__(self, parent, -1, "Http Streaming", position,
                          (250,170), wx.CAPTION)
        
        self.parent = parent
        self.Bind(wx.EVT_CLOSE, self.close)

        # Fetch icon
        self.icon = wx.Icon("gi.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.setBackground()
        self.addButtons()
        self.addLabels()
        self.addInputFields()
        self.addDivider()
        self.playlistItems = []

        self.currentIndex = 0
        
        self.Show()
        

    def setBackground(self):
        """
        Method to set background
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
        self.loadButton = wx.Button(self, -1, "Load", (10, 50))
        self.Bind(wx.EVT_BUTTON, self.load, self.loadButton)
        self.loadButton.SetDefault()
        self.loadButton.SetSize(self.loadButton.GetBestSize())

        self.browseButton = wx.Button(self, -1, "Browse", (90, 50))
        self.Bind(wx.EVT_BUTTON, self.browse, self.browseButton)
        self.loadButton.SetDefault()
        self.loadButton.SetSize(self.browseButton.GetBestSize())
        
        self.closeButton = wx.Button(self, -1, "Close", (10, 110))
        self.Bind(wx.EVT_BUTTON, self.close, self.closeButton)
        self.closeButton.SetDefault()
        self.closeButton.SetSize(self.closeButton.GetBestSize())

    def addInputFields(self):
        """
        Method to add input fields
        Args:
          None

        Returns: None
        """
        self.addressText = wx.TextCtrl(self, -1, "", wx.Point(60,23),
                                       size=(150,-1))

    def addDivider(self):
        """
        Method to add a divider
        Args:
          None

        Returns: None
        """
        self.line = wx.StaticLine(self, -1, size = (225, -1),pos = (10,100), style=wx.LI_HORIZONTAL)
        
    def addLabels(self):
        """
        Method to add labels
        Args:
          None

        Returns: None
        """
        self.labelHeader = GenStaticText(self, -1, '', wx.Point(10,5))
        self.labelHeader.SetBackgroundColour("#D8D8D8")
        self.labelHeader.SetForegroundColour("#000000")
        self.labelHeader.SetLabel("Load songs from pypl, m3u or pls file:")

        self.addressLabel = GenStaticText(self, -1, '', wx.Point(10,25), (45, 15), wx.ST_NO_AUTORESIZE)
        self.addressLabel.SetBackgroundColour("#D8D8D8")
        self.addressLabel.SetForegroundColour("#000000")
        self.addressLabel.SetLabel("Address:")

        self.statusLabel = GenStaticText(self, -1, '', wx.Point(10, 80))
        self.statusLabel.SetBackgroundColour("#D8D8D8")
        self.statusLabel.SetForegroundColour("#0095F4")
        self.statusLabel.SetLabel("Waiting for input")
            
    def browse(self, event):
        """
        Method to browse the filesystem for playlists
        Args:
          event = The button event

        Returns: None
        """
        file = None
        # Import a playlist and append it to current
        dlg = wx.FileDialog(self, message="Choose a playlist",
                            defaultDir=self.parent.config.data["last-directory"], 
                            defaultFile="", wildcard="pypl file (*.pypl)|*.pypl|m3u file (*.m3u)|*.m3u|pls file (*.pls)|*.pls",
                            style=wx.FD_OPEN)
        
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a list of files that were selected.
            self.parent.config.data["last-directory"] = dlg.GetDirectory()
            file = dlg.GetPaths()
            

        # Destroy the dialog when done
        dlg.Destroy()

        if file:
            self.addressText.SetValue(file[0])
        
    def load(self, event):
        """
        Method to load a playlist from a http address
        Args:
          event = The button event

        Returns: None
        """
        address = self.addressText.GetValue()
        downloadManager = HttpPlaylistDownloadManager(self, address,
                                                      self.statusLabel)
        downloadManager.start()
        

    def disableInput(self):
        """
        Method to disable input while downloading
        Args:
          None

        Returns: None
        """
        self.loadButton.Enable(False)
        self.browseButton.Enable(False)
        self.closeButton.Enable(False)
        self.addressText.Enable(False)
        
    def enableInput(self):
        """
        Method to enable input when download has finished
        Args:
          None

        Returns: None
        """
        self.loadButton.Enable(True)
        self.browseButton.Enable(True)
        self.closeButton.Enable(True)
        self.addressText.Enable(True)
        
    def addAll(self):
        """
        Method to add all items extractet
        Args:
          None

        Returns: None
        """
        if len(self.playlistItems):
            # Traverse and add all elements
            for element in self.playlistItems:
                self.parent.plContainer.play_list.append(element)

            # Refresh playlist
            self.parent.playlistWidget.refreshPlaylist()

    def close(self, event=None):
        """
        Method to close the playlist loader
        Args:
          event = The close event

        Returns: None
        """
        self.GetParent().Enable()
        self.Destroy()

class HttpPlaylistDownloadManager(threading.Thread):
    """
    Class to handle the downloading of playlists
    """
    
    def __init__(self, parent, address, statusLabel):
        """
        Class constructor.
        Args:
          parent = The parent object
          address = The address to the playlist
          statusLabel = The status label that we will update with info

        Returns: None
        """
        threading.Thread.__init__(self)
        self.parent = parent
        self.address = address
        self.statusLabel = statusLabel
        
    def run(self):
        """
        The thread body. All wx GUI calls are wrapped in wx.CallAfter()
        because this runs on a background thread and wxPython 4.x requires
        GUI operations to happen on the main thread.
        """
        wx.CallAfter(self.parent.disableInput)
        # Verify input m3u or pls
        try:
            if not self.address.lower().startswith("http://"):
                # Not an http address. Assuming it's a local file
                if os.path.isfile(self.address):
                    if self.address.lower().endswith(".m3u"):
                        wx.CallAfter(self.statusLabel.SetLabel, "Parsing local file..")
                        data = parseM3u(self.address)
                        self.parent.playlistItems = data
                            
                    elif self.address.lower().endswith(".pls"):
                        wx.CallAfter(self.statusLabel.SetLabel, "Parsing local file..")
                        data = parsePls(self.address)
                        self.parent.playlistItems = data
                                                    
                    elif self.address.lower().endswith(".pypl"):
                        wx.CallAfter(self.statusLabel.SetLabel, "Parsing local file..")
                        data = parsePypl(self.address)
                        self.parent.playlistItems = data

                    else:
                        raise Exception("Only supports m3u and pls files")
                    
                    # No file and no http address. Raise exception
                else:
                    raise Exception("Input is not an http address or a file")

            # Download from the great stable internet
            else:
                # Update label
                wx.CallAfter(self.statusLabel.SetLabel, "Connecting to server..")

                net = Network()
                httpUtils = HttpUtils()

                # Parse url
                urlTuple = httpUtils.parseUrl(self.address)
                #http://www.shoutcast.com/sbin/shoutcast-playlist.pls?rn=1694&file=filename.pls

                conn = HTTPConnection("%s:%d" % (urlTuple[0], urlTuple[1]))
                conn.connect()
                
                conn.putrequest("GET", "/%s" % quote(urlTuple[2], "?/&="))
                conn.endheaders()

                r = conn.getresponse()
                
                if r.status == 401:
                    wx.CallAfter(self.statusLabel.SetLabel, "Authenticating")
                    conn.close()
                    conn = HTTPConnection("%s:%s" % (urlTuple[0], urlTuple[1]))
                    conn.connect()
                    # We need authentication
                    username, password = httpUtils.queryUser()
                    
                    base64string = base64.encodebytes(('%s:%s' % (username, password)).encode()).decode().strip()
                    conn.putrequest("GET", "/%s" % quote(urlTuple[2], "?/&="))
                    conn.putheader("Authorization", "Basic %s" % base64string)
                    conn.endheaders()
                    r = conn.getresponse()

                if r.status == 200:
                    wx.CallAfter(self.statusLabel.SetLabel, "Downloading")
                    data = r.read(r.length)
                    conn.close()
                else:
                    raise Exception("Server returned http code: %d" % r.status)
                
                fp = open("tmpPlaylistDownload.txt", "w")
                fp.write(data)
                fp.close()
                # Initialize data buffer
                data = []
                                    
                # Parse it
                if self.address.lower().endswith(".pls"):
                    data = parsePls("tmpPlaylistDownload.txt")
                            
                elif self.address.lower().endswith(".m3u"):
                    data = parseM3u("tmpPlaylistDownload.txt")
                        
                elif self.address.lower().endswith(".pypl"):
                    data = parsePypl("tmpPlaylistDownload.txt")

                self.parent.playlistItems = data
                    
        except Exception as e:
            wx.CallAfter(self.statusLabel.SetLabel, "Error: %s" % str(e))

        wx.CallAfter(self.statusLabel.SetLabel, "Parsing done.")

        # Add all songs to playlist
        wx.CallAfter(self.parent.addAll)

        # Enable input again
        wx.CallAfter(self.parent.enableInput)

    

class PlaylistGui(wx.Frame):
    """
    The playlist gui
    """
    
    def __init__(self, parent, plContainer, config, skin, eventQueue):
        """
        The class constructor
        Args:
          parent = The parent window
          plContainer = The playlist container
          config = The player config
          skin = The players skin
          eventQueue = The players event queue
        """
        self.parent = parent
        self.plContainer = plContainer
        self.config = config
        self.skin = skin
        self.eventQueue = eventQueue
        
        windowStyle = wx.FRAME_SHAPED | wx.SIMPLE_BORDER
        if not self.config.data["task-bar"]:
            # Turn off taskbar
            windowStyle = windowStyle | wx.FRAME_NO_TASKBAR
             
        if self.config.data["stay-on-top"]:
            # Set stay-on-top
            #windowStyle = windowStyle | wx.STAY_ON_TOP
            pass
        
        wx.Frame.__init__(self, self.parent, -1, "Playlist",
                          style = windowStyle)

        # Initialize drag position delta before binding mouse events
        self.delta = (0, 0)

        # Bind events
        self.Bind(wx.EVT_LEFT_DOWN,     curry(self.OnLeftDown, None))
        self.Bind(wx.EVT_MOTION,        curry(self.OnMouseMove, None))
        self.Bind(wx.EVT_LEFT_UP,       self.OnLeftUp)
        self.Bind(wx.EVT_PAINT,         self.OnPaint)
        self.Bind(wx.EVT_LEFT_DCLICK,   self.OnDoubleClick)
        
        # Set the background
        self.SetBackGroundImage(self.skin)
        self.addButtons()
        # create playlist widget
        self.playlistWidget = PlaylistWidget(self, self.skin, self.plContainer, self.eventQueue)

        # Create fileMenu
        self.createFileMenu()

        # Move window to correct
        self.Move(self.config.data["playlistPosition"])
        
    def addButtons(self):
        """
        Method to add buttons
        Args:
          None

        Returns: None
        """
        # Create hand cursor
        cursor = wx.Cursor(wx.CURSOR_HAND)
        
        # for each button, create it!
        for button in self.skin["playlistButton"]:
            type = bitmapType(button["imgUp"])
            imgUp = wx.Image(button["imgUp"], type).ConvertToBitmap()

            type = bitmapType(button["imgDown"])
            imgDown = wx.Image(button["imgDown"], type).ConvertToBitmap()
            
            c = wx.BitmapButton(self, -1, imgUp, (button["x"],button["y"]), imgUp.GetSize(), wx.BORDER_NONE)
            c.SetBackgroundColour("#000000")
            self.Bind(wx.EVT_BUTTON, curry(self.executeEvent, button["event"]), c)
            c.SetBitmapFocus(imgUp)
            c.SetBitmapPressed(imgDown)
            c.SetBitmapDisabled(imgUp)
            c.SetCursor(cursor)
               
            if "toolTip" in button:
                c.SetToolTip(button["toolTip"])

    # Method to execute the correct operation
    def executeEvent(self, operation, event):
        """
        Method to execute given event
        Args:
          operation = The operation to execute
          event = The button event

        Returns: None
        """
        exec("self.%s()" % operation)


    def createFileMenu(self):
        """
        Method to add the file menu to the gui
        Args:
          None

        Returns: None
        """
        self.fileMenu = wx.Menu()
        uniqueId = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self.addFiles, id=uniqueId)
        self.fileMenu.Append(uniqueId, "Add file")

        uniqueId = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self.addDirectory, id=uniqueId)
        self.fileMenu.Append(uniqueId, "Add directory")

    def showFileMenu(self, event=None):
        """
        Method to display the file menu
        Args:
          event = the ui event if any

        Returns: None
        """
        pos = (10,10)
        printDebug(pos)
        self.PopupMenu(self.fileMenu, pos)

    def addDirectory(self, event):
        """
        Method to create and display the DirDialog
        Args:
          event = The menu event

        Returns: None
        """
        dlg = wx.DirDialog(self, "Choose a directory:",
                           defaultPath=self.config.data["last-directory"],
                           style=wx.DD_DEFAULT_STYLE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.config.data["last-directory"] = path
            self.plContainer.addDirectory(path)
            self.playlistWidget.refreshPlaylist()

        # Destroy dialog
        dlg.Destroy()
        

    def addFiles(self, event):
        """
        Method to create and display the file dialog
        Args:
          event = The menu event

        Returns: None
        """
        dlg = wx.FileDialog(self, message="Choose files",
                            defaultDir=self.config.data["last-directory"], 
                            defaultFile="", wildcard="*.mp3",
                            style=wx.FD_OPEN | wx.FD_MULTIPLE)

        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a list of files that were selected.
            self.config.data["last-directory"] = dlg.GetDirectory()
            files = dlg.GetPaths()
            self.plContainer.addFiles(files)
            self.playlistWidget.refreshPlaylist()

        # Destroy the dialog
        dlg.Destroy()

    def addCD(self):
        """
        Method to add CD
        Args:
          None

        Returns: None
        """
        # Fire up dialog so the user can choose among available cd-roms
        InformDialog(self, self.GetPosition().Get(), "Info message",
                     "No CD support available yet")

    def addHttp(self):
        """
        Method to add http streams
        Args:
          None

        Returns: None
        """
        # Fire up dialog so that the user can insert an http address and
        # also tell us if it is an SHOUTcast or ordinary http stream
        httpManager = HttpStreamManager(self, self.GetPosition().Get())
        
    def addPympServer(self):
        """
        Method to add pymp server
        Args:
          None

        Returns: None
        """
        # Display pympServer window
        pympServerWindow = PympServerConfigWindow(self, self.GetPosition().Get())
        

    def importPlaylist(self):
        """
        Method to create and display a filedialog
        Args:
          None

        Returns: None
        """
        # Import a playlist and append it to current
        dlg = wx.FileDialog(self, message="Choose a playlist",
                            defaultDir=self.config.data["last-directory"], 
                            defaultFile="", wildcard="*.pypl",
                            style=wx.FD_OPEN)

        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a list of files that were selected.
            self.config.data["last-directory"] = dlg.GetDirectory()
            file = dlg.GetPaths()
            self.plContainer.importPlaylist(file)
            self.playlistWidget.refreshPlaylist()
            

        # Destroy the dialog when done
        dlg.Destroy()

    def clearPlaylist(self):
        """
        Method to clear playlist. It will stop the playing before
        clearing the list
        Args:
          None

        Returns: None
        """
        self.eventQueue.put(["stop"])
        self.plContainer.clearPlaylist()
        self.playlistWidget.refreshPlaylist()
        

    def savePlaylist(self, noDialog=False):
        """
        Method to save the playlist
        Args:
          noDialog = To show or not to show that is tha question

        Returns: None
        """
        self.plContainer.savePlaylist()
        
        if not noDialog:
            InformDialog(self, self.GetPosition().Get(), "Info message",
                         "Playlist saved")
            
    def close(self, evt=None):
        """
        Method to close the playlist gui
        Args:
          evt = The ui event

        Returns: None
        """
        self.playlistWidget.close()
        self.Destroy()
        
    def OnDoubleClick(self, evt):
        """
        Method to handle double clicks on the playlist itself
        not the list. Will set/unset the playlist's window shape.
        Args:
          evt = The mouse event

        Returns: None
        """
        
        if self.hasShape:
            self.SetShape(wx.Region())
            self.hasShape = False
        else:
            self.SetWindowShape()

    def SetBackGroundImage(self, skin):
        """
        Method to set background image
        Args:
          skin = The players skin

        Returns: None
        """
        if not "playlistBgImage" in skin:
            raise Exception("playlistBgImage not defined in skin definition")
        
        img_path = skin["playlistBgImage"]["path"]
        type = bitmapType(img_path)
        self.background = wx.Image(img_path, type).ConvertToBitmap()
        w, h = self.background.GetWidth(), self.background.GetHeight()
        self.SetClientSize( (w, h) )

        if wx.Platform == "__WXGTK__":
            # wxGTK requires that the window be created before you can
            # set its shape, so delay the call to SetWindowShape until
            # this event.
            self.Bind(wx.EVT_WINDOW_CREATE, self.parent.SetWindowShape)
        else:
            # On wxMSW and wxMac the window has already been created, so go for it.
            self.SetWindowShape()

        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.background, 0,0, True)
        self.SetBackgroundColour(wx.Colour(0, 0, 0))

    def SetWindowShape(self, *evt):
        """
        Method to set windows shape
        Args:
          evt = The ui event

        Returns: None
        """
        # Use the bitmap's mask to determine the region
        r = wx.Region(self.background)
        self.hasShape = self.SetShape(r)

    def OnPaint(self, evt):
        """
        Method that handles the paint event
        Args:
          evt = The paint event

        Returns: None
        """
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.background, 0,0, True)
        
    def toggleWindow(self, event=None):
        """
        Method to toggle window visibility
        Args:
          event = The ui event

        Returns: None
        """
        if self.IsShown():
            self.Hide()
        else:
            self.Show()
            self.SetFocus()
    
    def OnLeftUp(self, evt):
        """
        Method to handle mouse event left-up
        Args:
          evt = The mouse event

        Returns: None
        """
        if self.HasCapture():
            self.ReleaseMouse()

    def OnLeftDown(self, pos, evt):
        """
        Method to handle mouse event left-down
        Args:
          evt = The mouse event

        Returns: None
        """
        self.CaptureMouse()
        x, y = self.ClientToScreen(evt.GetPosition())
        if pos != None:
            x += pos[0]
            y += pos[1]
        originx, originy = self.GetPosition()
        dx = x - originx
        dy = y - originy
        self.delta = ((dx, dy))

    def OnMouseMove(self, pos, evt):
        """
        Method to handle mouse movement event
        Args:
          pos = The mouse position
          evt = The mouse event

        Returns: None
        """
        if evt.Dragging() and evt.LeftIsDown():
            x, y = self.ClientToScreen(evt.GetPosition())
            if pos != None:
                x += pos[0]
                y += pos[1]
                 
            fp = (x - self.delta[0], y - self.delta[1])
            try:
                self.config.data["position"] = fp
            except Exception as e:
                printDebug("Exception: %s" % str(e))
            self.Move(fp)


class PlaylistWidget(wx.Panel):
    """
    The class that defined the playlist GUI layout
    """
    
    def __init__(self, parent, skin, plContainer, eventQueue):
        """
        The class constructor
        Args:
          parent = The parent window
          skin = The player's skin
          plContainer = The playlist container
          eventQueue = The player's event queue
        """
        self.skin = skin
        self.plContainer = plContainer
        self.eventQueue = eventQueue
        
        wx.Panel.__init__(self, parent, -1, pos=(self.skin["scrollList"]["x"],
                                                 self.skin["scrollList"]["y"]),
                          size=(self.skin["scrollList"]["width"],
                                self.skin["scrollList"]["height"]),
                          style=wx.WANTS_CHARS)

        
        self.list = wx.ListCtrl(self, -1,
                                size = (self.skin["scrollList"]["width"],
                                        self.skin["scrollList"]["height"]),
                                pos=(0,0),
                                style=wx.LC_REPORT 
                                #| wx.BORDER_SUNKEN
                                | wx.BORDER_NONE
                                #| wx.LC_EDIT_LABELS
                                #| wx.LC_SORT_ASCENDING
                                #| wx.LC_NO_HEADER
                                #| wx.LC_VRULES
                                #| wx.LC_HRULES
                                #| wx.LC_SINGLE_SEL
                                )

        self.list.SetForegroundColour(self.skin["scrollList"]["fgColour"])
        self.list.SetBackgroundColour(self.skin["scrollList"]["bgColour"])

        # Variable to figure out if we should sort ascending or not
        self.asc = None

        # Bind needed events
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.list.Bind(wx.EVT_KEY_UP, self.onKeyUp)

        
    def close(self):
        """
        Method to close playlist gui
        Args:
          None

        Returns: None
        """
        self.Destroy()
        
    def populateList(self):
        """
        Method to populate playlist
        Args:
          None

        Returns: None
        """
        self.list.InsertColumn(0, "Artist")
        self.list.InsertColumn(1, "Title")

        key = 0
        # List all song in playlist
        for uri, title, artist in self.plContainer.play_list:
            # Insert item
            index = self.list.InsertItem(self.list.GetItemCount(), artist)
            self.list.SetItem(index, 0, artist)
            self.list.SetItem(index, 1, title)
            
            self.list.SetItemData(index, key)
            key += 1


    def onKeyUp(self, event):
        """
        Method to fetch key-up events and fire the correct action
        ARGS:
          event = The key event
        
        Returns: None
        """
        # Get keycode
        keycode = event.GetKeyCode()
        # Handle the delete key up signal
        if keycode == wx.WXK_DELETE:
            self.deleteSelected()
        
        
        
    def deleteSelected(self):
        """
        Method to delete selected files from playlist
        Remember to delete them in reversed order or HAVOC will rain
        Args:
          None
          
        Returns: None
        """
        selected = getSelected(self.list)

        for item in selected:
            # Remove from list and from the internal playlist as well
            self.list.DeleteItem(item)
            self.plContainer.play_list.pop(item)
            
        
   
    def getColumnText(self, index, col):
        """
        Method to get given item
        Args:
          index = A given item
          col = The given column

        Returns: The item based on index and column
        """
        item = self.list.GetItem(index, col)
        return item.GetText()


    def OnItemActivated(self, event):
        """
        Method to start playing selected song
        Args:
          event = The wx.EVT_LIST_ITEM_ACTIVATED event
    
        Returns: None
        """
        self.currentItem = event.GetItem().GetId()
        self.eventQueue.put(["%d" % self.currentItem])
        
    def OnColClick(self, event):
        """
        Method to handle the click on a column. The column clicked will be
        sorted
        Args:
          event = the ui event

        Returns: None
        """
        index = event.GetColumn()

        # Figure out the correct index we want to sort
        # in the playlist
        if index == 0:
            index = 2
        elif index == 1:
            index = 1

        if self.asc:
            if self.asc[0] == index:
                # Change sort order
                if self.asc[1]:
                    self.asc[1] = False
                else:
                    self.asc[1] = True
            else:
                self.asc = [index, False]
        else:
            self.asc = [index, False]
        
        sortStringTuple(self.plContainer.play_list, self.asc[0], self.asc[1])
        
        # clear and repopulate 
        self.refreshPlaylist()

    def refreshPlaylist(self):
        """
        Method to refresh playlist
        Args:
          None
        
        Returns: None
        """
        self.list.ClearAll()
        self.populateList()
        

    def OnSize(self, event):
        """
        Method to handle the sixe event
        Args:
          event = The size event

        Returns: None
        """
        w,h = self.GetClientSizeTuple()
        self.list.SetDimensions(0, 0, w, h)

    def OnColBeginDrag(self, event):
        printDebug("OnColBeginDrag\n")
        ## Show how to not allow a column to be resized
        #if event.GetColumn() == 0:
        #    event.Veto()
