###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

def parsePypl(filename):
    """
    Function to parse a .pypl playlist
    Args:
      filename = the filename

    Returns: The list of songs extracted 
    """
    songs = []
    fp = open(filename, "r")

    line = fp.readline()
    while line:
        uri, title, artist = line.split("<")
        artist = artist.strip("\n")
        songs.append([uri, title, artist])
        line = fp.readline()

    return songs

def parseM3u(filename):
    """
    Function to parse m3u playlists
    ARGS:
      filename = the filename

    Returns: a list of [uri, song, artist] elements
    """
    songs = []
    artistSong = None
    fp = open(filename, "r")
    line = fp.readline()

    if not line.startswith("#EXTM3U"):
        raise Exception("The file does not appear to be an valid m3u file")

    while line:
        if line.startswith("#EXTM3U"):
            pass

        elif line.startswith("#EXTINF:"):
            # strip "header"
            line = line[8:].strip("\n")
            pos = line.find(",")
            time = line[:pos]
            artistSong = line[pos+1:]

        else:
            print(line)
            if artistSong == None:
                raise Exception("Parse error. Uri defined before #EXTINF")

            uri = line.strip("\n")
            if not uri.lower().startswith("http"):
                uri = "file://%s" % uri

            songs.append([uri, "", artistSong])
            artistSong = None
            
        # read next line
        line = fp.readline()
    
    return songs

def parsePls(filename):
    """
    Function to parse pls files
    Args:
      filename = The filename

    Returns: list of [uri, title, artist] elements
    """
    fp = open(filename, "r")
    line = fp.readline()
    entry = False
    uri = ""
    songs = []
    
    while line:
        if line.startswith("File"):
            if not entry:
                entry = True
                stopIndex = line.find("=")
                index = int(line[4:stopIndex])
                uri = line[stopIndex + 1:].strip("\n")
                
            else:
                raise Exception("Parse error. Two 'File' entries found before a 'Title' entry")

        elif line.startswith("Title"):
            if entry:
                stopIndex = line.find("=")
                artistSong = line[stopIndex + 1:].strip("\n")
                index = int(line[5:stopIndex])
                entry = False
                if not uri.lower().startswith("http"):
                    uri = "file://%s" % uri
                songs.append([uri, "", artistSong])
                
            else:
                raise Exception("Parse error. 'Title' entry found before a 'File' entry")

        line = fp.readline()

    # Handle File entry with no matching Title (common in SHOUTcast PLS)
    if entry and uri:
        if not uri.lower().startswith("http"):
            uri = "file://%s" % uri
        songs.append([uri, "Unknown", ""])

    return songs
