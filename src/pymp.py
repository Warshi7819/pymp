###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# change directory to pyplayer directory
import sys, os
pyplayer_dir = sys.argv[0]
if pyplayer_dir.rfind('\\') != -1:
    pyplayer_dir = pyplayer_dir[:pyplayer_dir.rfind('\\')]
    os.chdir(pyplayer_dir)

# Add lib directory to path so that we can seperate all
# library files from the executeable when the code is frozen
sys.path.append('lib')

# Import standard modules
import threading
import time

# Import 3rdparty modules
import wx
import wx.adv
import wx.lib.buttons  as  buttons
from wx.lib.stattext import GenStaticText

# Import own modules
from ScrollingLabel import ScrollingLabel
from ParseSkin import ParseSkin
from UiHandler import UiHandler
from Debug import Help
from Config import Config
from About import About
from Curry import curry
from GuiUtils import bitmapType
from OwnConstants import *

class pyPlayerFrame(wx.Frame):
    """
    Class to draw the pyPlayer GUI, sub-classed of wxFrame
    """

    def __init__(self, parent):
        """
        The class constuctor
        Args:
          parent = The parent Frame
          skin = The dictionary containing the skin specification
        """
        
        self.parent = parent
        # Load config
        self.config = Config(self.parent)
        
        windowStyle = wx.FRAME_SHAPED | wx.SIMPLE_BORDER
        if not self.config.data["task-bar"]:
            # Turn off taskbar
            windowStyle = windowStyle | wx.FRAME_NO_TASKBAR
            
        if self.config.data["stay-on-top"]:
            # Set stay-on-top
            windowStyle = windowStyle | wx.STAY_ON_TOP
         
        wx.Frame.__init__(self, parent, -1, "pyMP 2.0.1", style = windowStyle)

        self.hasShape = False
        self.delta = (0,0)

        # Bind the needed events
        self.Bind(wx.EVT_LEFT_DCLICK,   self.OnDoubleClick)
        self.Bind(wx.EVT_LEFT_DOWN,     curry(self.OnLeftDown, None))
        self.Bind(wx.EVT_MOTION,        curry(self.OnMouseMove, None))
        self.Bind(wx.EVT_LEFT_UP,       self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_UP,      curry(self.ShowApplicationMenu, None))
        self.Bind(wx.EVT_PAINT,         self.OnPaint)

        # If config enables hotkeys, bind those too
        if self.config.data["hotkeys"]:
            # Bind next
            self.RegisterHotKey(NEXT, wx.MOD_CONTROL|wx.MOD_SHIFT, ord ('N'))
            self.Bind(wx.EVT_HOTKEY, self.OnHotKeyfunction, id=NEXT)

            # Bind back
            self.RegisterHotKey(BACK, wx.MOD_CONTROL|wx.MOD_SHIFT, ord ('B'))
            self.Bind(wx.EVT_HOTKEY, self.OnHotKeyfunction, id=BACK)

            # Bind play
            self.RegisterHotKey(PLAY, wx.MOD_CONTROL|wx.MOD_SHIFT, ord ('P'))
            self.Bind(wx.EVT_HOTKEY, self.OnHotKeyfunction, id=PLAY)

            # Bind wait/pause
            self.RegisterHotKey(WAIT, wx.MOD_CONTROL|wx.MOD_SHIFT, ord ('W'))
            self.Bind(wx.EVT_HOTKEY, self.OnHotKeyfunction, id=WAIT)

            # Bind hide
            self.RegisterHotKey(DISPLAY, wx.MOD_CONTROL|wx.MOD_SHIFT, ord ('D'))
            self.Bind(wx.EVT_HOTKEY, self.OnHotKeyfunction, id=DISPLAY)

            # Bind stop
            self.RegisterHotKey(STOP, wx.MOD_CONTROL|wx.MOD_SHIFT, ord ('S'))
            self.Bind(wx.EVT_HOTKEY, self.OnHotKeyfunction, id=STOP)

        
        # Fetch icon
        self.icon = wx.Icon("gi.ico", wx.BITMAP_TYPE_ICO) 
        
        # Fetch skin
        skin_parser = ParseSkin()
        self.skin = skin_parser.parseSkin(self.config.data["skin"])
        
        # Hold on to labels
        self.labels = {}

        # Set the background
        self.SetBackGroundImage(self, self.skin)
        
        # Create the buttons
        self.CreateButtons(self, self.skin)
        
        # Create the labels
        self.CreateLabels(self, self.skin)
        
        # Create menu
        self.CreateApplicationMenu(self, self.skin)
        
        
        # Create taskbar icon
        self.SetTaskbarIcon(self, self.skin)
        
        # Create taskbar menu
        self.CreateTaskbarMenu(self, self.skin)
        
        # Set window to last known position
        self.Move(self.config.data["position"])
        
        # Initiate aboutWindow
        self.about = About(self, self.config)
        
        # Create ui handler that will handle all events from gui
        self.uiHandler = UiHandler(self, self.config, self.skin)
        
        # Display everything
        self.Show()
        
    def SetBackGroundImage(self, parent, skin):
        """
        Method to draw the background
        Args:
          parent = The parent class
          skin = The dictionary containing the skin specification
          
        Returns: None
        """
        
        if not "bgImage" in skin:
            raise Exception("bgImage not defined in skin definition")

        img_path = skin["bgImage"]["path"]
        type = bitmapType(img_path)
        parent.background = wx.Image(img_path, type).ConvertToBitmap()
        w, h = parent.background.GetWidth(), parent.background.GetHeight()
        parent.SetClientSize( (w, h) )

        if wx.Platform != "__WXMAC__":
            # wxMac clips the tooltip to the window shape, YUCK!!!
            parent.SetToolTip("Right-click for menu")
            
        if wx.Platform == "__WXGTK__":
            # wxGTK requires that the window be created before you can
            # set its shape, so delay the call to SetWindowShape until
            # this event.
            parent.Bind(wx.EVT_WINDOW_CREATE, parent.SetWindowShape)
        else:
            # On wxMSW and wxMac the window has already been created, so go for it.
            parent.SetWindowShape()
            
        dc = wx.ClientDC(parent)
        dc.DrawBitmap(parent.background, 0,0, True)
        self.SetIcon(self.icon)

    def SetTaskbarIcon(self, parent, skin):
        """
        Method To set taskbar icon
        Args:
          parent = The parent class
          skin = The dictionary containing the skin specification
          
        Returns: None
        """
        
        parent.tbicon = wx.adv.TaskBarIcon()
        parent.tbicon.SetIcon(self.icon, "pyMP")
        parent.tbicon.Bind(wx.adv.EVT_TASKBAR_RIGHT_UP, self.ShowTaskbarMenu)
        parent.tbicon.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.ToggleWindow)

    def CreateButtons(self, parent, skin):
        """
        Method to draw the needed buttons
        Args:
          parent = The parent class
          skin = The dictionary containing the skin specification
          
        Returns: None
        """
        
        cursor = wx.Cursor(wx.CURSOR_HAND)
        
        # for each button, create it!
        for button in skin["button"]:
            type = bitmapType(button["imgUp"])
            imgUp = wx.Image(button["imgUp"], type).ConvertToBitmap()
            type = bitmapType(button["imgDown"])
            imgDown = wx.Image(button["imgDown"], type).ConvertToBitmap()
             
            c = wx.BitmapButton(self, -1, imgUp, (button["x"],button["y"]), imgUp.GetSize(), wx.BORDER_NONE)
            c.SetBackgroundColour("#000000")
            parent.Bind(wx.EVT_BUTTON, curry(self.ExecuteEvent, button["event"]), c)
            c.SetBitmapFocus(imgUp)
            c.SetBitmapPressed(imgDown)
            c.SetBitmapDisabled(imgUp)
            c.SetCursor(cursor)
               
            if "toolTip" in button:
                c.SetToolTip(button["toolTip"])


        self.toggleButtons = {}
        if "toggleButton" in skin:
            for button in skin["toggleButton"]:

                # Load images
                
                type = bitmapType(button["imgUp"])
                imgUp = wx.Image(button["imgUp"], type).ConvertToBitmap()
                
                type = bitmapType(button["imgDown"])
                imgDown = wx.Image(button["imgDown"], type).ConvertToBitmap()
                
                c = buttons.GenBitmapToggleButton(self, -1, imgUp, (button["x"], button["y"]))
                c.SetBackgroundColour("#000000")
                parent.Bind(wx.EVT_BUTTON, curry(self.ExecuteEvent, button["event"]), c)
                
                c.SetSize((imgUp.GetWidth(), imgUp.GetHeight()))
                c.SetBitmapFocus(imgUp)
                c.SetBitmapSelected(imgDown)
                c.SetCursor(cursor)
                c.SetUseFocusIndicator(False)
                c.SetBackgroundColour(button["bg"])
                c.SetForegroundColour(button["fg"])
                
                # Hold on to toggle buttons so that events can trigger them
                self.toggleButtons[button["event"]] = {}
                self.toggleButtons[button["event"]]["button"] = c
                self.toggleButtons[button["event"]]["imgUp"] = imgUp
                self.toggleButtons[button["event"]]["imgDown"] = imgDown
                
                if "toolTip" in button:
                    c.SetToolTip(button["toolTip"])
                

    def toggleButton(self, name, mode):
        """
        Method to toggle toggle buttons.
        Args:
          name = The name of the button
          mode = to be toggled or not to be toggled, that is the question

        Returns: None
        """
        
        if name in self.toggleButtons:
            self.toggleButtons[name]["button"].SetValue(mode)

    def CreateLabels(self, parent, skin):
        """
        Method to draw the needed labels
        Args:
          parent = The parent class
          skin = The dictionary containing the skin specification
    
        Returns: None
        """
        
        if "label" in skin:
            for label in skin["label"]:
                # Create a ticker or static label depending on skin spec
                if label.get("scrolling") == "yes":
                    parent.labels[label["type"]] = ScrollingLabel(parent, -1, '',
                        fgcolor=label["fg"],
                        bgcolor=label["bg"],
                        pos=wx.Point(label["x"], label["y"]),
                        size=(label["length"], label["height"]),
                        fps=15, ppf=1)
                else:
                    parent.labels[label["type"]] = GenStaticText(parent, -1, '', wx.Point(label["x"], label["y"]), (label["length"], label["height"]), wx.ST_NO_AUTORESIZE)
                    parent.labels[label["type"]].SetBackgroundColour(label["bg"])
                    parent.labels[label["type"]].SetForegroundColour(label["fg"])

                # Bind events
                parent.labels[label["type"]].Bind(wx.EVT_RIGHT_UP, curry(self.ShowApplicationMenu, parent.labels[label["type"]]))
                
                parent.labels[label["type"]].SetToolTip("Right-click for menu")
                parent.labels[label["type"]].Bind(wx.EVT_LEFT_DOWN, curry(self.OnLeftDown, (label["x"], label["y"])))
                parent.labels[label["type"]].Bind(wx.EVT_MOTION, curry(self.OnMouseMove, (label["x"], label["y"])))
                
                parent.labels[label["type"]].Bind(wx.EVT_LEFT_DCLICK,   self.OnDoubleClick)

    def CreateApplicationMenu(self, parent, skin):
        """
        Method to create the menu described by skin
        Args:
          parent = The parent class
          skin = The dictionary containing the skin specification

        Returns = None
        """
        
        parent.applicationMenu = wx.Menu()
        for element in skin["menuItem"]:
            
            if element["parent"] == False:
                uniqueId = wx.NewIdRef()
                parent.Bind(wx.EVT_MENU, curry(self.ExecuteEvent, element["event"]), id=uniqueId)
                parent.applicationMenu.Append(uniqueId, element["name"])
            else:
                subMenu = wx.Menu()
                for child in element["children"]:
                    uniqueId = wx.NewIdRef()
                    # Add this childe to sub-menu
                    subMenu.Append(uniqueId, child["name"])
                    parent.Bind(wx.EVT_MENU, curry(self.ExecuteEvent, child["event"]), id=uniqueId)
                         
                         
                uniqueId = wx.NewIdRef()
                # Add sub-menu
                parent.applicationMenu.AppendSubMenu(subMenu, element["name"])


    def ShowApplicationMenu(self, parent, event):
        """
        Method to display Application menu
        Args:
          event = The window event
          
        Returns: None
        """
        
        if parent == None:
            parent = self
            
        pos = event.GetPosition()
        parent.PopupMenu(self.applicationMenu, pos)
          

    def CreateTaskbarMenu(self, parent, skin):
        """
        Method to display Taskbar menu
        Args:
          event = The window event
          
        Returns = None
        """
        # same as the application menu, except this one also
        # has the show/hide option
        parent.taskbarMenu = wx.Menu()
        uniqueId = wx.NewIdRef()
        self.tbicon.Bind(wx.EVT_MENU, curry(self.ExecuteEvent, "toggleWindow"), id=uniqueId)
        parent.taskbarMenu.Append(uniqueId, "Show/Hide")
        
        # Parse skin
        for element in skin["menuItem"]:
            
            if element["parent"] == False:
                uniqueId = wx.NewIdRef()
                self.tbicon.Bind(wx.EVT_MENU, curry(self.ExecuteEvent, element["event"]), id=uniqueId)
                parent.taskbarMenu.Append(uniqueId, element["name"])
            else:
                subMenu = wx.Menu()
                for child in element["children"]:
                    uniqueId = wx.NewIdRef()
                    # Add this childe to sub-menu
                    subMenu.Append(uniqueId, child["name"])
                    self.tbicon.Bind(wx.EVT_MENU, curry(self.ExecuteEvent, child["event"]), id=uniqueId)
                    
                         
                uniqueId = wx.NewIdRef()
                # Add sub-menu
                parent.taskbarMenu.AppendSubMenu(subMenu, element["name"])
     
    def ShowTaskbarMenu(self, event):
        """
        Method to display Taskbar menu
        Args:
          event = The window event
          
        Returns: None
        """
        
        self.tbicon.PopupMenu(self.taskbarMenu)

    def ToggleWindow(self, event=None):
        """
        Method to toggel parent visibility
        Args:
          event = (opt) wxPython event
        """
        
        if self.IsShown():
            self.Hide()
        else:
            self.Show()
               
    def ShowWindow(self, event=None):
        """
        Method to display parent window
        Args:
          event = (opt) wxPython event
        """
        
        if not self.IsShown():
            self.Show()
            
    def OnMinimize(self):
        """
        Method to iconize the window
        Args:
          None

        Returns: None
        """
        self.Iconize(True)
        
    def ExecuteEvent(self, *event):
        """
        Method to execute events from sysTray, main frame and popup menu's
        Args:
          event = The window event
    
        Returns: None
        """
        
        event = event[0]
        if event == "terminate":
            self.OnExit()
            
        else:
            exec("self.uiHandler.%s()" % event)

        
    def SetWindowShape(self, *evt):
        """
        Method to set the window shape
        Args:
          evt = The event

        Returns: None
        """
        
        # Use the bitmap's mask to determine the region
        r = wx.Region(self.background)
        self.hasShape = self.SetShape(r)


    def OnDoubleClick(self, evt):
        """
        Method to handle double click
        Args:
          evt = The mouse event

        Returns: None
        """
        if self.config.data["debug-skin"]:
            if self.hasShape:
                self.SetShape(wx.Region())
                self.hasShape = False
            else:
                self.SetWindowShape()


    def OnPaint(self, evt):
        """
        Method to handle paint event
        Args:
          evt = The paint event

        Returns: None
        """
        
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.background, 0,0, True)
          
    def OnExit(self, evt=None):
        """
        Method called on exit of app. Cleans up.
        Args:
          evt = (opt) wxPython event

        Returns: None
        """
        
        # Save playlist, do not display dialog
        self.uiHandler.savePlaylist(True)
        
        # Update position of player window
        printDebug("updating position of main window")
        self.config.data["position"] = self.GetPosition().Get()

        # update current song and repeat/randon mode:
        self.config.data["current-track"] = self.uiHandler.getCurrentTrack()
        self.config.data["random"] = self.uiHandler.getRandomStatus()
        self.config.data["repeat"] = self.uiHandler.getRepeatStatus()
                  
        # Destroy ui instance
        printDebug("Destroying ui instance")
        self.uiHandler.close()

        # Save config
        printDebug("Saving config")
        self.config.saveConfig()
        self.config.close()
        
        # Close about
        self.about.close()
         
        # Destroy taskbar icon
        printDebug("Destroying tbicon")
        if self.tbicon != None:
            self.tbicon.Destroy()

        printDebug("Destroying main frame")
        # Destroy frame
        self.Close()
        
     
    def OnLeftUp(self, evt):
        """
        Method that captures when left mouse button is released
        Used to move window around
        Args:
          evt = the wxPython event

        Returns: None
        """
        
        if self.HasCapture():
            self.ReleaseMouse()

    def OnLeftDown(self, pos, evt):
        """
        Method that captures when left mouse button is pressed
        Used to move window around
        Args:
          evt = the wxPython event

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
        Method that captures when the mouse moves around
        Args:
          pos = The possition of the mouse
          evt = The mouse event

        Returns: None
        """
        
        if evt.Dragging() and evt.LeftIsDown():
            x, y = self.ClientToScreen(evt.GetPosition())
            if pos != None:
                x += pos[0]
                y += pos[1]
                 
            fp = (x - self.delta[0], y - self.delta[1])
            self.Move(fp)

    def OnHotKeyfunction(self, event):
        """
        Method to handle hotkey events
        Args:
          event = The hotkey event triggered

        Returns: None
        """
        id = event.GetId()

        if id == NEXT:
            self.uiHandler.next()
            
        elif id == BACK:
            self.uiHandler.prev()
            
        elif id == WAIT:
            self.uiHandler.pause()
            
        elif id == PLAY:
            self.uiHandler.play()
            
        elif id == DISPLAY:
            self.ToggleWindow()
            
        elif id == STOP:
            self.uiHandler.stop()

        else:
            printDebug("Hotkey not recognized: %s" % str(dir(event)))
                    
class pyPlayer(wx.App):
    def OnInit(self):
        frame = pyPlayerFrame(None)
        
        return True



if __name__ == "__main__":
    # Start application
    while True:
        #app = pyPlayer(1, 'log\\stdout.txt')
        app = pyPlayer(0)
        app.MainLoop()
        
        # parse config and see if this is a restart of some sort..
        # E.g new skin
        break
    printDebug("pymp exited")
