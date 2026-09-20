###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import standard module
import os.path
from os import getcwd
# Import wxpython modules
import wx

# Import own modules
from Debug import Help
from ParseConfig import ParseConfig
from OwnConstants import *

class Config:
    """
    The config class
    """

    def __init__(self, parent):
        """
        Class constuctor. Reads config from file.
        Args:
          parent = The parent object
        """
        self.data = {}
        self.parent = parent
        if os.path.isfile("config.xml"):
            self.loadConfig()
        else:
            self.defaultConfig()

        self.configWindow = None

    def loadConfig(self):
        """
        Method that loads and parses the config
        Args:
          None

        Returns: None
        """
        # parse config xml
        if not os.access("config.xml", os.F_OK):
            printDebug("Setting default config")
            self.defaultConfig()
        else:
            configParser = ParseConfig()
            self.data = configParser.parseConfig("config.xml")
            printDebug(self.data)
            printDebug("data printed")
            
    def saveConfig(self):
        """
        Method that saves the player config to file
        Args:
          None

        Returns: None
        """
        # write xml
        fp = open("config.xml", "w")
        fp.write("<Config>\n")
        fp.write("<position x=\"%d\" y=\"%d\" />\n" % (self.data["position"][0],
                                                     self.data["position"][1]))
                 
        fp.write("<playlistPosition x=\"%d\" y=\"%d\" />\n" % (self.data["playlistPosition"][0],
                                                             self.data["playlistPosition"][1]))
                 
        fp.write("<configPosition x=\"%d\" y=\"%d\" />\n" % (self.data["configPosition"][0],
                                                             self.data["configPosition"][1]))

        fp.write("<aboutPosition x=\"%d\" y=\"%d\" />\n" % (self.data["aboutPosition"][0],
                                                           self.data["aboutPosition"][1]))
        

        
        
        fp.write("<skin path=\"%s\" /> " % self.data["skin"])
                 
        if self.data["debug-skin"]:
            fp.write("<debug-skin value=\"true\" />\n")
        else:
            fp.write("<debug-skin value=\"false\" />\n")

        if self.data["task-bar"]:
            fp.write("<task-bar value=\"true\" />\n")
        else:
            fp.write("<task-bar value=\"false\" />\n")

        if self.data["hotkeys"]:
            fp.write("<hotkeys value=\"true\" />\n")
        else:
            fp.write("<hotkeys value=\"false\" />\n")

        if self.data["stay-on-top"]:
            fp.write("<stay-on-top value=\"true\" />\n")
        else:
            fp.write("<stay-on-top value=\"false\" />\n")

        fp.write("<last-directory path=\"%s\" />\n" % self.data["last-directory"])

        fp.write("\n<!-- Player state -->\n")
        fp.write("<current-track value=\"%s\" />\n" % self.data["current-track"])

        if self.data["repeat"]:
            fp.write("<repeat value=\"true\" />\n")
        else:
            fp.write("<repeat value=\"false\" />\n")

        if self.data["random"]:
            fp.write("<random value=\"true\" />\n")
        else:
            fp.write("<random value=\"false\" />\n")
            
        
        fp.write("</Config>\n")

        fp.close()
                       
    def defaultConfig(self):
        """
        Method to set default config
        Args:
          None

        Returns: None
        """
        self.data = {}
        self.data["position"] = (0,0)
        self.data["playlistPosition"] = (0,0)
        self.data["configPosition"] = (0,0)
        self.data["aboutPosition"] = (0,0)
        self.data["skin"] = "skin\\default\\skin.xml"
        self.data["debug-skin"] = True
        self.data["hotkeys"] = True
        self.data["task-bar"] = False
        self.data["stay-on-top"] = True
        self.data["last-directory"] = getcwd()
        self.data["current-track"] = 0
        self.data["random"] = False
        self.data["repeat"] = False

    def close(self):
        """
        Method to close config window if it is open
        Args:
          None

        Returns: None
        """
        if self.configWindow:
            self.data["configPosition"] = self.configWindow.GetPosition().Get()
            self.configWindow.close()

    def showConfigWindow(self):
        """
        Method that creates and displays config window
        Args:
          None

        Returns: None
        """
        
        if self.configWindow == None:
            self.configWindow = ConfigWindow(self.parent, self)
        else:
            # Window allready present. Only set focus
            self.configWindow.setFocus()
 
class ConfigWindow(wx.Frame):

    def __init__(self, parent, config):
        """
        Class constructor
        Args:
          parent = The parent window
          config = The players config
        """
        self.config = config
        wx.Frame.__init__(self, parent, -1, "pyMP config")
        self.SetBackgroundColour("#000000")
        self.Bind(wx.EVT_CLOSE, self.close)

        # Fetch icon
        self.icon = wx.Icon("gi.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.drawConfig()
        if self.config.parent:
            self.config.parent.Disable()
        self.Move(self.config.data["configPosition"])
        self.Show()


    def drawConfig(self):
        """
        Method to draw the config window
        Args: None

        Returns: None
        """
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Skin selector
        skin_label = wx.StaticText(panel, label="Skin:")
        sizer.Add(skin_label, 0, wx.ALL, 5)

        # Scan skin directory for available skins
        skin_dirs = []
        if os.path.isdir("skin"):
            for name in sorted(os.listdir("skin")):
                if os.path.isfile(os.path.join("skin", name, "skin.xml")):
                    skin_dirs.append(name)

        self.skin_choice = wx.Choice(panel, choices=skin_dirs)
        sizer.Add(self.skin_choice, 0, wx.ALL | wx.EXPAND, 5)

        # Pre-select current skin
        current_skin = self.config.data.get("skin", "")
        current_name = ""
        for part in current_skin.replace("\\", "/").split("/"):
            if part in skin_dirs:
                current_name = part
                break
        if current_name:
            idx = skin_dirs.index(current_name)
            self.skin_choice.SetSelection(idx)

        # Restart note
        note = wx.StaticText(panel, label="Restart required for changes to take effect")
        note.SetForegroundColour("#888888")
        sizer.Add(note, 0, wx.ALL, 5)

        # Save button
        save_btn = wx.Button(panel, label="Save")
        save_btn.Bind(wx.EVT_BUTTON, self.OnSave)
        sizer.Add(save_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        self.Fit()
    

    def OnSave(self, evt):
        selected = self.skin_choice.GetStringSelection()
        if selected:
            self.config.data["skin"] = "skin" + os.sep + selected + os.sep + "skin.xml"
            self.config.saveConfig()
        self.close()

    def setFocus(self):
        """
        Method to set focus on config window
        Args:
          None

        Returns: None
        """
        
        self.SetFocus()
        
    def close(self, evt=None):
        """
        Method to close config window
        Args:
          evt = The close event

        Returns: None
        """
        self.config.data["configPosition"] = self.GetPosition().Get()
        if self.config.parent:
            self.config.parent.Enable()
        self.config.configWindow = None
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
