###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import 3rdparty modules
import wx


class ScrollingLabel(wx.Window):
    """
    Custom label that shows text left-aligned and scrolls left
    only when the text is wider than the widget.
    """

    def __init__(self, parent, id=-1, label='', pos=wx.DefaultPosition,
                 size=wx.DefaultSize, fgcolor=None, bgcolor=None,
                 fps=15, ppf=1):
        """
        Class constructor
        Args:
          parent = The parent window
          id = The window id
          label = The initial label text
          pos = The window position
          size = The window size
          fgcolor = The foreground colour
          bgcolor = The background colour
          fps = The frames per second for scrolling
          ppf = The pixels per frame for scrolling
        """
        wx.Window.__init__(self, parent, id, pos, size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self._text = ''
        self._offset = 0
        self._ppf = ppf
        self._scrolling = False

        if fgcolor:
            self.SetForegroundColour(wx.Colour(fgcolor))
        if bgcolor:
            self.SetBackgroundColour(wx.Colour(bgcolor))

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
        self._timer.Start(1000 // fps)

    def SetText(self, text):
        """
        Method to set the label text
        Args:
          text = The text to display

        Returns: None
        """
        self._text = text
        self._offset = 0
        self._scrolling = False
        self.Refresh()

    def Start(self):
        """
        Method to start scrolling the text
        Args: None

        Returns: None
        """
        self._scrolling = True

    def Stop(self):
        """
        Method to stop scrolling the text
        Args: None

        Returns: None
        """
        self._scrolling = False
        self._offset = 0
        self.Refresh()

    def _get_text_width(self):
        """
        Method to get the width of the text in pixels
        Args: None

        Returns: The text width in pixels
        """
        mdc = wx.MemoryDC()
        mdc.SetFont(self.GetFont())
        w, h = mdc.GetTextExtent(self._text)
        mdc.SelectObject(wx.NullBitmap)
        return w

    def _on_paint(self, event):
        """
        Method to handle paint events
        Args:
          event = The paint event

        Returns: None
        """
        dc = wx.AutoBufferedPaintDC(self)
        w, h = self.GetSize()

        bg = self.GetBackgroundColour()
        if bg.IsOk():
            dc.SetBackground(wx.Brush(bg))
            dc.Clear()

        fg = self.GetForegroundColour()
        if fg.IsOk():
            dc.SetTextForeground(fg)
        dc.SetFont(self.GetFont())

        text_w = self._get_text_width()

        if not self._scrolling or text_w <= w:
            dc.DrawText(self._text, 0, 0)
        else:
            dc.DrawText(self._text, -self._offset, 0)

    def _on_timer(self, event):
        """
        Method to handle timer events for scrolling
        Args:
          event = The timer event

        Returns: None
        """
        if not self._scrolling:
            return

        w, h = self.GetSize()
        text_w = self._get_text_width()

        if text_w <= w:
            self._scrolling = False
            self._offset = 0
            self.Refresh()
            return

        self._offset += self._ppf

        if self._offset > text_w:
            self._offset = 0

        self.Refresh()

    def __del__(self):
        """
        Class destructor
        Args: None

        Returns: None
        """
        self._timer.Stop()
