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

# Import own modules
from OwnConstants import *


class MP3InfoContainer:
    """
    Class to hold a file's extracted mp3 information
    """
    
    def __init__(self):
        """
        The Class constructor
        Initializes the needed variables
        Args:
          None
        """
        self.title = ''
        self.artist = ''
        self.album = ''
        self.year = ''
        self.comment = ''
        self.genre = ''


    def addTitle(self, title):
        """
        Function to add title
        Args:
          title = The song's title
          
        Returns: True when done
        """
        self.title = title.strip('\n')
        return True

    
    def addArtist(self, artist):
        """
        Function to add artist
        Args:
          artist = name of artist
          
        Returns: True when done
        """
        self.artist = artist.strip('\n')
        return True
    

    def addAlbum(self, album):
        """
        Function to add album title
        Args:
          album = The albums title
          
        Returns: True when done
        """
        self.album = album.strip('\n')
        return True
    

    def addYear(self, year):
        """
        Function to add year of album release 
        Args:
          year = The year the album was released
          
        Returns: True when done
        """
        self.year = year.strip('\n')
        return True
        

    def addComment(self, comment):
        """
        Function to add comment
        Args:
          comment = The comment extracted from the ID3 tag
          
        Returns: True when done
        """
        self.comment = comment.strip('\n')
        return True
    

    def addGenre(self, genre):
        """
        Function to add genre
        Args:
          genre = The song's genre
          
        Returns: True when done    
        """
        # Convert from byte to int
        self.genre = genre
        return True
        

    def printIt(self):
        """
        Debug function to print all info
        Args:
          None
          
        Returns: None
        """
        print(self.title)
        print(self.artist)
        print(self.album)
        print(self.year)
        print(self.comment)
        print(self.genre)


class Id3Utils:
    """
    Class for extracting information from ID3 tags
    """

    # ID3v2 frame IDs mapped to MP3InfoContainer fields
    ID3V2_FRAME_MAP = {
        'TIT2': 'title',
        'TPE1': 'artist',
        'TALB': 'album',
        'TDRC': 'year',
        'TYER': 'year',
        'TCON': 'genre',
    }
    
    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        pass


    def decodeSyncsafe(self, data):
        """
        Decode a 4-byte syncsafe integer (7 bits per byte)
        Args:
          data = 4 bytes

        Returns: decoded integer
        """
        return (data[0] << 21) | (data[1] << 14) | (data[2] << 7) | data[3]


    def decodeTextFrame(self, data):
        """
        Decode a text frame's data bytes
        Args:
          data = frame data (encoding byte + text bytes)

        Returns: decoded string
        """
        if len(data) < 1:
            return ''

        encoding = data[0]
        text_data = data[1:]

        if encoding == 0:
            # Latin-1
            return text_data.rstrip(b'\x00').decode('latin-1')
        elif encoding == 1:
            # UTF-16 with BOM
            try:
                if len(text_data) >= 2:
                    if text_data[:2] == b'\xff\xfe':
                        return text_data[2:].decode('utf-16-le').rstrip('\x00')
                    elif text_data[:2] == b'\xfe\xff':
                        return text_data[2:].decode('utf-16-be').rstrip('\x00')
                return text_data.decode('utf-16').rstrip('\x00')
            except (UnicodeDecodeError, ValueError):
                return text_data.decode('latin-1', errors='replace').rstrip('\x00')
        elif encoding == 2:
            # UTF-16BE without BOM
            try:
                return text_data.decode('utf-16-be').rstrip('\x00')
            except (UnicodeDecodeError, ValueError):
                return text_data.decode('latin-1', errors='replace').rstrip('\x00')
        elif encoding == 3:
            # UTF-8
            try:
                return text_data.decode('utf-8')
            except (UnicodeDecodeError, ValueError):
                return text_data.decode('latin-1', errors='replace')
        else:
            # Default to latin-1
            return text_data.decode('latin-1', errors='replace')


    def parseId3v2(self, path):
        """
        Function to parse ID3v2 tag from a file
        Args:
          path = path to file

        Returns: a MP3InfoContainer object holding the data found
                 or False if no ID3v2 tag found
        """
        try:
            fp = open(path, "rb", 0)

            # Read the 10-byte ID3v2 header
            header = fp.read(10)
            if len(header) < 10 or header[:3] != b"ID3":
                fp.close()
                return False

            # Decode tag size (syncsafe 4-byte integer)
            tag_size = self.decodeSyncsafe(header[6:10])

            # Read entire tag data
            tag_data = fp.read(tag_size)
            fp.close()

        except IOError:
            return False

        # Parse frames from tag data
        mp3_info = MP3InfoContainer()
        offset = 0
        found_fields = set()

        while offset < len(tag_data) - 10:
            # Read frame header
            frame_id = tag_data[offset:offset + 4]

            # Stop on padding (null bytes)
            if frame_id[0:1] == b'\x00':
                break

            # Frame size (syncsafe in v2.4, regular in v2.3)
            frame_size = (tag_data[offset + 4] << 24) | (tag_data[offset + 5] << 16) | (tag_data[offset + 6] << 8) | tag_data[offset + 7]

            # Skip frame header (10 bytes) and read frame data
            frame_data_start = offset + 10
            frame_data = tag_data[frame_data_start:frame_data_start + frame_size]

            # Decode frame if it's one we care about
            frame_id_str = frame_id.decode('ascii', errors='ignore')
            if frame_id_str in self.ID3V2_FRAME_MAP:
                field = self.ID3V2_FRAME_MAP[frame_id_str]
                if field not in found_fields:
                    value = self.decodeTextFrame(frame_data)
                    if value:
                        if field == 'title':
                            mp3_info.addTitle(value)
                        elif field == 'artist':
                            mp3_info.addArtist(value)
                        elif field == 'album':
                            mp3_info.addAlbum(value)
                        elif field == 'year':
                            mp3_info.addYear(value)
                        elif field == 'genre':
                            mp3_info.addGenre(value)
                        found_fields.add(field)

            # Move to next frame
            offset += 10 + frame_size

        # Only return if we found at least a title or artist
        if found_fields:
            return mp3_info

        return False


    def parseId3v1(self, path):
        """
        Function to parse ID3v1 tag from a file
        Args:
          path = path to file

        Returns: a MP3InfoContainer object holding the data found
                 or False if no ID3v1 tag found
        """
        try:
            # Fetch the ID3 data field
            fp = open(path, "rb", 0)
            fp.seek(-128, 2)
            id3data = fp.read(128)
            fp.close()

        except IOError:
            return False

        # Parse and clean data
        if id3data[:3] == b"TAG":
            mp3_info = MP3InfoContainer()
            mp3_info.addTitle(id3data[3:33].replace(b'\00',b'').strip().decode('latin-1'))
            mp3_info.addArtist(id3data[33:63].replace(b'\00',b'').strip().decode('latin-1'))
            mp3_info.addAlbum(id3data[63:93].replace(b'\00',b'').strip().decode('latin-1'))
            mp3_info.addYear(id3data[93:97].replace(b'\00',b'').strip().decode('latin-1'))
            mp3_info.addComment(id3data[97:126].replace(b'\00',b'').strip().decode('latin-1'))
            mp3_info.addGenre(id3data[127:128][0])

            # Return mp3 info object
            return mp3_info
        else:
            return False


    def parseFile(self, path):
        """
        Function to parse a given file. Tries ID3v2 first, falls back to ID3v1
        Args:
          path = path to file
          
        Returns: a MP3InfoContainer object holding the data found
                 or False if data cannot be extracted
        """
        # Try ID3v2 first (at beginning of file)
        mp3_info = self.parseId3v2(path)
        if mp3_info:
            return mp3_info

        # Fall back to ID3v1 (at end of file)
        return self.parseId3v1(path)


# Test script
if __name__ == '__main__':
    t = Id3Utils()
    mp3 = t.parseFile(sys.argv[1])
    if mp3:
        mp3.printIt()
