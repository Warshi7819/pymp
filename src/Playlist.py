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
import os
from os.path import join

import wx

# Import own modules
from OwnConstants import *
from Id3 import Id3Utils

class PlaylistContainer:
    """
    A container for holding refference to playlist
    """

    def __init__(self):
        """
        The class contstructor
        Args:
          None
        """

        self.play_list = []
        self.playlistGui = None
        self.id3Utils = Id3Utils()
        self.lastColour = None
        self.current = 0
        
        
    def addFiles(self, files):
        """
        Method to add files
        Args:
          files = The files we are going to add
          
        Returns: None
        """
        for filename in files:
            info = self.id3Utils.parseFile(filename)
            filename = 'file://%s' % filename
            
            if info != False:
                # Append info to current playlist
                self.play_list.append([filename, info.title, info.artist])
            else:
                # No id3 tag found, add default info
                self.play_list.append([filename, filename[filename.rfind('/') + 1:], 'unknown'])
            

    def addFile(self, filename):
        """
        Method to add one file. Used by pyPlayer_api
        Args:
          filename = The songs filename
        
        Returns: None
        """
        printDebug(filename)
        if os.access(filename, os.F_OK):
            info = self.id3Utils.parseFile(filename)
            filename = 'file://%s' % filename
            
            if info != False:
                # Append info to current playlist
                self.play_list.append([filename, info.title, info.artist])
            else:
                # No id3 tag found, add default info
                self.play_list.append([filename, filename[filename.rfind('/') + 1:], 'unknown'])
            return True
        else:
            return False
        
    def addDirectory(self, directory):
        """
        Method to add a directory
        Args:
          directory = The directory we want to add

    
        Returns: None
        """

        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                if name.endswith('.mp3'):
                    # Parse file and fetch id3 info
                    filename = join(root, name)
                    mp3Info = self.id3Utils.parseFile(filename)
                    filename = 'file://%s' % filename
                    if mp3Info != False:
                        self.play_list.append([filename, mp3Info.title, mp3Info.artist])
                    else:
                        self.play_list.append([filename, name, 'Unknown artist'])


    def addCD(self):
        printDebug("add cd")

    def addHttp(self):
        printDebug("add http")

    def addPympServer(self, playlist, address):
        """
        Method to add a pymp server
        Args:
          playlist = The downloaded playlist
          address = The address to the pympserver

        Returns: None
        """
        for element in playlist:
            element[0] = "tcp://%s:%d/%s" % (address[0], address[1], element[0])

            self.play_list.append(element)
            
    def addItem(self, uri, title, artist):
        """
        Method to add an item
        Args:
          uri = The songs uri
          title = The title
          artist = The artist

        Returns: None
        """
        self.play_list.append([uri, title, artist])

    def importPlaylist(self, playlists):
        """
        Method to umport a playlist
        Args:
          playlists = A list of playlists

        Returns: None
        """
        for playlist in playlists:
            if os.access(playlist, os.F_OK):
                # open playlist and read content
                fp = open(playlist, 'r', encoding='utf-8')
                data = fp.readlines()
                fp.close()
                # For each element extract filename, track name and artist
                for element in data:
                    filename, track_name, artist = element.split('<')
                    self.play_list.append([filename.strip('\n'), track_name.strip('\n'), artist.strip('\n')])
                


    def clearPlaylist(self):
        """
        Method to clear a playlist
        Args:
          None

        Returns: None
        """
        self.play_list = []

    def savePlaylist(self):
        """
        Method to save a playlist to file
        Args:
          None

        Returns: None
        """
        fp = open('playlist.pypl', 'w', encoding='utf-8')
        for element in self.play_list:
            fp.write('%s<%s<%s\n' % (element[0], element[1].replace('<',' '), element[2].replace('<',' ')))
        fp.close()

        printDebug("Playlist saved")

        
    def setCurrent(self, current):
        """
        Method to set current song to bold in playlist
        Args:
          current = The current song

        Returns: None
        """
        self.last = self.current
        self.current = current


        if not len(self.play_list):
            return
        # try to set colour on current song
        try:
            if self.last != None:
                if len(self.play_list) > self.last: 
                    # Deselect last one
                    item = self.playlistGui.playlistWidget.list.GetItem(self.last)
                    item.SetTextColour(self.lastColour)
                    self.playlistGui.playlistWidget.list.SetItem(item)
            if len(self.play_list) > current:
                # Select new one
                item = self.playlistGui.playlistWidget.list.GetItem(current)
                # Save the original colour of item to be used when deselecting
                self.lastColour = item.GetTextColour()
                # Set new colour
                item.SetTextColour(wx.BLUE)
                self.playlistGui.playlistWidget.list.SetItem(item)
        except Exception as e:
            printDebug("hehe, didn't work")
            printDebug(e)


    def refreshPlaylist(self):
        """
        Method to refresh the playlist
        Args:
          None

        Returns: None
        """
        self.playlistGui.playlistWidget.populateList()
