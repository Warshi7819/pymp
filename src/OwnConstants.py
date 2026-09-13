###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# This file should be included into every file 
# in project and hold global constants!

# Defining some ret values
true = 1
false = 0
failure = -1
DEBUG = True

# Application name and version
APPLICATION_NAME = "pyPlayer"
APPLICATION_VERSION = "1.0.0"
# Index on variables in list
PLAYER_OBJECT_NAME = 0
PLAYER_TEXTUAL_NAME = 1
# Update interval on controller thread
TRIGGER_UPDATE = 0.5
# Max filename size allowed for tcp/ip streaming
MAX_FILENAME_SIZE = 1024

# Tcp timeout constants
RECEIVE_TIMEOUT = 4
CONNECT_TIMEOUT = 4

# TCP STREAMING CONSTANTS
FILE_REQUEST = 11000
PLAYLIST_REQUEST = 11001
CHUNCK_SIZE = 2048

# HOTKEY VALUES
BACK = 12
NEXT = 10
WAIT = 13
PLAY = 14
DISPLAY = 15
STOP = 16

# INFO Types
NO_INFO = None
TYPE_BUFFERING = 1 # When we are buffering
TYPE_SONG_INFO = 2 # When we extract information from the stream
TYPE_FLUSH = 3     # When we want to flush info dictionary

# If we should enable client api to pyplayer or not
C_API = False
C_API_PORT = 18080

# Set constants
OK = 200
BAD_REQUEST = 400
SERVER_ERROR = 500

def printDebug(debugString):
    if DEBUG:
        print(debugString)
