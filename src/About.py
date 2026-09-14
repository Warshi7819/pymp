###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython!#
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import wxpython modules
import wx
import wx.lib.newevent
from Debug import Help
import time
import threading

# Import own modules
from GuiUtils import bitmapType
from ParseAbout import ParseAbout

class About:
    """
    About screen
    """
    
    def __init__(self, parent, config):
        """
        Class constructor
        Args:
          parent = The parent object
          config = The players config
        """
        self.parent = parent
        self.config = config
        self.aboutWindow = None

    def close(self):
        """
        Method to close about windows
        Args:
          None

        Returns: None
        """
        if self.aboutWindow:
            self.data["aboutPosition"] = self.aboutWindow.GetPosition().Get()
            self.aboutWindow.close()

    def showAboutWindow(self):
        """
        Method to display the about screen
        Args:
          None

        Returns: None
        """
        if self.aboutWindow == None:
            self.aboutWindow = AboutWindow(self, self.parent, self.config)
        else:
            # Window allready present. Only set focus
            self.aboutWindow.setFocus()



# This creates a new Event class and a EVT binder function
(UpdateScrollingText, EVT_UPDATE_SCROLLING_TEXT) = wx.lib.newevent.NewEvent()



class ScrollText(threading.Thread):
    """
    The thread that generates events at every scrollspeed interval
    """
    
    def __init__(self, parent, scrollspeed=0.1):
        """
        The constructor
        """
        threading.Thread.__init__(self)

        self.scrollspeed = scrollspeed
        self.parent = parent
        self.RUNNING = True
        self.STOPED = False
                
    def run(self):
        """
        The body of the thread. Fires update events every
        scrollspeed interval
        Args:
          None

        Returns: None
        """

        while self.RUNNING:
            time.sleep(self.scrollspeed)

            # Fire event via CallAfter for reliable cross-thread delivery
            wx.CallAfter(self.parent.scrollText)

        self.STOPED = True

    def stop(self):
        """
        Method to stop the scolling thread
        ARGS:
          None

        Returns: None
        """
        
        self.RUNNING = False
        while not self.STOPED:
            time.sleep(self.scrollspeed)

class AboutWindow(wx.Frame):
    """
    Class setting up and displaying about window
    """
    def __init__(self, parent, guiParent, config):
        """
        Class constructor:
        Args:
          parent = The parent object
          guiParent = The parent window
          config = The players config
        """
        
        self.config = config
        self.parent = parent
        self.guiParent = guiParent

        self.height = 300
        
        # Parse and get about info
        parser = ParseAbout()
        self.aboutText = parser.parseAbout("about.xml")

        type = bitmapType("About.bmp")
        img = wx.Image("About.bmp", type)
        # Replace gray background in text area with black
        data = img.GetData()
        new_data = bytearray(data)
        for i in range(0, len(new_data), 3):
            r, g, b = new_data[i], new_data[i+1], new_data[i+2]
            if r == g == b and r > 40:
                new_data[i] = 0
                new_data[i+1] = 0
                new_data[i+2] = 0
        img.SetData(bytes(new_data))
        bmp = img.ConvertToBitmap()
        
        wx.Frame.__init__(self, guiParent, -1, "pyMP about",
                          size=(bmp.GetWidth()+8,  bmp.GetHeight()+32))


        # Ensure that the window cannot be resized
        self.SetSizeHints(bmp.GetWidth()+8, bmp.GetHeight()+32, bmp.GetWidth()+8, bmp.GetHeight()+32)

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.close)
        
        # Fetch icon
        self.icon = wx.Icon("gi.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)


        wx.StaticBitmap(self, -1, bmp, (0,0), (bmp.GetWidth(), bmp.GetHeight()))
               
        # variables needed
        self.x = 21
        self.width = 289
        self.height = 15
        self.firstLineY = 95
        self.lastLineY = 372

        # Single panel that draws all scrolling text (StaticText can't do bg on Windows)
        self.textPanel = wx.Window(self, pos=(self.x, self.firstLineY), size=(self.width, self.lastLineY - self.firstLineY + self.height))
        self.textPanel.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.textPanel.SetBackgroundColour("#000000")
        self.textPanel.Bind(wx.EVT_PAINT, self.onPaint)

        # Initialize first text line
        self.aboutText["lines"][0]["running"] = True
        self.aboutText["lines"][0]["y"] = self.lastLineY
        self.aboutText["lines"][0]["fontSize"] = int(self.aboutText["lines"][0]["size"])
        
        self.Move(self.config.data["aboutPosition"])
        if self.guiParent:
            self.guiParent.Disable()
        self.Show()

        # Fire up scrolling thread
        self.scrollThread = ScrollText(self)
        self.scrollThread.start()

    def onPaint(self, evt):
        dc = wx.AutoBufferedPaintDC(self.textPanel)
        dc.SetBackground(wx.Brush("#000000"))
        dc.Clear()
        for line in self.aboutText["lines"]:
            if line["running"] or line["y"] > 0:
                fontSize = int(line["size"])
                font = wx.Font(fontSize, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
                dc.SetFont(font)
                color = wx.Colour(line["color"])
                dc.SetTextForeground(color)
                indent = int(line["indent"]) * 15
                dc.DrawText(line["value"], indent, line["y"] - self.firstLineY)

    def scrollText(self, evt = None):
        """
        Method that handles scroll text events
        Args:
          evt = The scroll event

        Returns: None
        """
        
        for line in self.aboutText["lines"]:
            if line["running"]:
                line["y"] -= 1
                if line["y"] < -int(line["size"]):
                    line["running"] = False

        # Find the last running line's index
        lastRunningIdx = -1
        for i, line in enumerate(self.aboutText["lines"]):
            if line["running"]:
                lastRunningIdx = i

        # Start the next line if there's enough gap
        if lastRunningIdx >= 0 and lastRunningIdx < len(self.aboutText["lines"]) - 1:
            prevLine = self.aboutText["lines"][lastRunningIdx]
            nextLine = self.aboutText["lines"][lastRunningIdx + 1]
            if not nextLine["running"]:
                prevFontSize = int(prevLine["size"])
                gap = prevFontSize + 4
                if prevLine["y"] < self.lastLineY - gap:
                    nextLine["y"] = self.lastLineY
                    nextLine["running"] = True

        # Restart only after the very last line has fully scrolled off
        lastLine = self.aboutText["lines"][-1]
        if not lastLine["running"] and lastLine["y"] < -int(lastLine["size"]):
            for line in self.aboutText["lines"]:
                line["running"] = False
                line["y"] = -int(line["size"])
            fontSize = int(self.aboutText["lines"][0]["size"])
            self.aboutText["lines"][0]["y"] = self.lastLineY + fontSize
            self.aboutText["lines"][0]["running"] = True

        self.textPanel.Refresh()
        

    def setFocus(self):
        """
        Method to set the focus on the about window
        Args:
          None

        Returns: None
        """
        self.SetFocus()

        
    def close(self, evt=None):
        """
        Method to close about window.
        Args:
          evt = The close event

        Returns: None
        """
        self.scrollThread.stop()
        

        self.config.data["aboutPosition"] = self.GetPosition().Get()
        if self.guiParent:
            self.guiParent.Enable()
        self.parent.aboutWindow = None
        self.Destroy()

        
    def toggleVisibility(self):
        """
        Method to toggle visibility
        Args:
          None

        Returns: None
        """
        if self.IsShown():
            self.Hide()
        else:
            self.Show()
