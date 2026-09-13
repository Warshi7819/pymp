###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:06 20.04.2006                  #
# License     : GNU General Public License (GPL)  #
###################################################
# Standard modules
import sys

# wxPython modules
import wx
from Search import PlaylistSearch

# Own modules
from GuiUtils import openAsBitmap
from sort import sortStringTuple

DEBUG = True

def printDebug(str):
    """
    Function to print debug info to screen. But only if debugging
    is turned on
    Args:
      str = The string to print

    Returns: None
    """
    if DEBUG:
        print(str)

class PlaylistWindow(wx.Frame):
    """
    Class implementing the playlist window
    """
    
    def __init__(self, parent):
        """
        The class constructor
        Args:
          parent = The parent frame
        """

        # Setup window
        wx.Frame.__init__(self, parent, -1, 'Playlist', size=(500, 300))
        self.search = PlaylistSearch()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        
        # Fetch and set icon
        self.icon = wx.Icon("gi.ico", wx.BITMAP_TYPE_ICO) 
        self.SetIcon(self.icon)

        # Create toolbar
        tb = self.CreateToolBar( wx.TB_HORIZONTAL
                                 | wx.NO_BORDER
                                 | wx.TB_FLAT
                                 | wx.TB_TEXT
                                 )


        # Set toolbar icon size to 16x16 pixels
        tb.SetToolBitmapSize((16,16))

        # Fetch all images needed for toolbar
        openFile = openAsBitmap("skin\\default\\audio_file.ico")
        openPlaylist = openAsBitmap("skin\\default\\audio_playlist.ico")
        openPympServer = openAsBitmap("skin\\default\\audio_home.ico")
        openCD = openAsBitmap("skin\\default\\audio_cd.ico")
        save = openAsBitmap("skin\\default\\audio_save.ico")
        flush = openAsBitmap("skin\\default\\audio_dustbin.ico")

        # Create all toolbar icons
        tb.AddSimpleTool(10, openFile, "New", "Add content from local disk. Directory or file(s)")
        self.Bind(wx.EVT_TOOL, self.onToolClick, id=10)

        tb.AddSimpleTool(11, openPlaylist, "Import playlist", "Open a .pls .m3u or a .pypl playlist")
        self.Bind(wx.EVT_TOOL, self.onToolClick, id=11)

        tb.AddSimpleTool(12, openPympServer, "Add pyMP server", "Add content from a pyMP server")
        self.Bind(wx.EVT_TOOL, self.onToolClick, id=12)

        tb.AddSimpleTool(13, openCD, "CD", "Add CD audio content to playlist")
        self.Bind(wx.EVT_TOOL, self.onToolClick, id=13)

        # Finalize toolbar
        tb.Realize()
        
        # Create playlist widget
        self.playlistPanel = PlaylistPanel(self, self.GetClientSize())
        
        # Create statusbar
        self.CreateStatusBar()


        # Display window
        self.Show()

    def onToolClick(self, event):
        """
        Method called when toolbar item is clicked. Execute correct
        action based on item id.
        Args:
          event = The EVT_TOOL event

        Returns: None
        """
        printDebug("tool %s clicked\n" % event.GetId())


    def OnCloseWindow(self, event):
        """
        Called when we receive window close event
        Args:
          event = the window event

        Returns: None
        """
        self.Destroy()


    def OnHotKeyfunction(self, event):
        """
        Called when hotkey event is pressed
        Args:
          event = A hotkey event

        Returns: None
        """
        print("halloa")

class PlaylistPanel(wx.Panel):


    def __init__(self, parent, panelSize):
        """
        The class constructor
        Args:
          parent = The parent window
        """
        
        wx.Panel.__init__(self, parent, -1, pos=(0,1), size=panelSize, style=wx.WANTS_CHARS)


        # Use listctrl to hold the data
        self.list = wx.ListCtrl(self, -1,
                                size=panelSize,
                                style = wx.LC_REPORT | wx.BORDER_NONE)
    
    
        # Set playlist colours
        self.list.SetForegroundColour("GREEN")
        self.list.SetBackgroundColour("BLACK")
        
        # Bind playlist events
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.list.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
    
        # Variable to figure out if we should sort ascending or not
        self.asc = None

        self.playlistItems = [["uri", "Hunting High and Low", "A-Ha"], ["uri", "Take On Me", "A-Ha"]]
        # populate playlist with current data
        self.populatePlaylist()
        
    
    def populatePlaylist(self):
        """
        Function to populate the playlist with the currently
        loaded items
        Args:
          None

        Returns: None
        """

        self.list.InsertColumn(0, "Artist")
        self.list.InsertColumn(1, "Title")
        self.list.InsertColumn(2, "Source")

        key = 0
        # List all song in playlist
        for uri, title, artist in self.playlistItems:
            # Insert item
            index = self.list.InsertItem(self.list.GetItemCount(), artist)
            self.list.SetStringItem(index, 0, artist)
            self.list.SetStringItem(index, 1, title)
            
            self.list.SetItemData(index, key)
            key += 1



    def refreshPlaylist(self):
        """
        Method to refresh playlist
        Args:
          None
        
        Returns: None
        """
        self.list.ClearAll()
        self.populatePlaylist()






    def OnKeyUp(self, event):
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
        
        sortStringTuple(self.playlistItems, self.asc[0], self.asc[1])
        
        # clear and repopulate 
        self.refreshPlaylist()


    def OnItemActivated(self, event):
        """
        Method to start playing selected song
        Args:
          event = The wx.EVT_LIST_ITEM_ACTIVATED event
    
        Returns: None
        """
        print("Item activated")
        self.currentItem = event.GetItem().GetId()
        print("Song: ", self.currentItem)
        #self.eventQueue.put(["%d" % self.currentItem])    
    

    def OnSize(self, event):
        """
        Method to handle the size event
        Args:
          event = The size event

        Returns: None
        """
        w,h = self.GetClientSizeTuple()
        self.list.SetDimensions(0, 0, w, h)




class __Test(wx.App):
    def OnInit(self):
        frame = PlaylistWindow(None)
        return True



if __name__ == "__main__":
    """
    Execute standalone test..
    """
    app = __Test(0)
    app.MainLoop()
