###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################
import wx


def bitmapType(filename):
    """
    Function to get the correct wx.BITMAP_TYPE based on filename
    Args:
      filename = The filename of the image
      
    Returns: The correct wx.BITMAP_TYPE
    """
    if filename.lower().endswith("ico"):
        return wx.BITMAP_TYPE_ICO

    elif filename.lower().endswith("gif"):
        return wx.BITMAP_TYPE_GIF

    elif filename.lower().endswith("bmp"):
        return wx.BITMAP_TYPE_BMP

    elif filename.lower().endswith("png"):
        return wx.BITMAP_TYPE_PNG
    else:
        raise Exception("Image type unknown: %s"% filename)

def openAsBitmap(file):
    imgType = bitmapType(file)
    img = wx.Image(file, imgType).ConvertToBitmap()
    return img
    
def getSelected(list):
    """
    Method to get selected items from a list
    Args:
      list = The list

    Returns: The selected items in reverse order
    """
    selected = []
    item = list.GetFirstSelected()
    while item != -1:
        selected.append(item)
        item = list.GetNextSelected(item)

    # Reverse list because the items must be deleted in reverse order.
    selected.reverse()
    return selected

class InformDialog(wx.Frame):
    """
    A simpler information dialog
    """
    def __init__(self, parent, position, title, message):
        """
        Class constructor. Generates and displays the dialog
        Args:
          parent = The parent window
          position = The position of the dialog
          title = The dialog title
          message = The message to display in the dialog

        Returns: None
        """

        wx.Frame.__init__(self, parent, -1, title, position,
                          (200,100), wx.CAPTION)

        self.SetBackgroundColour("#D8D8D8")
        self.SetForegroundColour("#000000")
        
        label = wx.StaticText(self, -1, message, wx.Point(10,10),
                              style = wx.ST_NO_AUTORESIZE)
        

        closeButton = wx.Button(self, -1, "OK", (10, 40))
        self.Bind(wx.EVT_BUTTON, self.close, closeButton)
        closeButton.SetDefault()
        closeButton.SetSize(closeButton.GetBestSize())

        parent = self.GetParent()
        if parent:
            parent.Disable()
        self.Show()
        
    def close(self, event):
        """
        Method to close dialog
        Args:
          event = The close event

        Returns: None
        """
        parent = self.GetParent()
        if parent:
            parent.Enable()
        self.Destroy()
