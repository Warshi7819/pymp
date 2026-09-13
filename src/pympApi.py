###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Start Date  : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import Standard modules
from socket import *
import pickle
import time
import sys
import random

class PympApi:
    
    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        C_API_PORT = 8308
        self.address = (gethostbyname(gethostname()), C_API_PORT)

    def sendData(self, request, noReplay=True):
        """
        Method to send data over tcp/ip too pyMP
        Args:
          request        = The request we want to send
          (OPT)noReplay  = If we will await an answer or not
        
        Returns: The socket object if noReplay, else None
        """

        # Connect
        c_soc = socket(AF_INET, SOCK_STREAM)
        c_soc.connect(self.address)

        # Send requests
        for element in request:
            element = element.ljust(1024)
            c_soc.send(element)

        # Figure out if we should close connection or return socket
        if noReplay:
            c_soc.close()
            return None
        else:
            # The calling function will have to handle further
            # communication with serve
            return c_soc

    def play(self, num=None):
        """
        Method to send play event
        Args:
          (OPT)num = the position in the playlist
                     of the song we want to start playing
        
        Returns: None
        """
        if not num:
            event = ["play"]
        else:
            event = ["%d" % num]
        
        self.sendData(event)
        
    def prev(self):
        """
        Method to send prev event
        ARGS:
          None
        
        Returns: None
        """
        event = ["prev"]
        self.sendData(event)

    def pause(self):
        """
        Method to send pause event
        Args:
          None
        
        Returns: None
        """
        event = ["pause"]
        self.sendData(event)

    def stop(self):
        """
        Method to send stop event
        Args:
          None
        
        Returns: None
        """
        event = ["stop"]
        self.sendData(event)

    def next(self):
        """
        Method to send next event
        Args:
          None
        
        Returns: None
        """
        event = ["next"]
        self.sendData(event)

    def repeat(self):
        """
        Method to send repeat event
        Args:
          None
        
        Returns: None
        """
        event = ["repeat"]
        self.sendData(event)

    def random(self):
        """
        Method to send random event
        Args:
          None
        
        Returns: None
        """
        event = ["random"]
        self.sendData(event)

    def addFile(self, filename):
        """
        Method to add a file to the playlist
        playlist will automatically refresh if song is correctly added
        Args:
          filename = The filename of the song we want to add
        
        Returns: None
        """
        event = ["addFile", filename]
        self.sendData(event)

        
    def fetchPlaylist(self):
        """
        Method to fetch current playlist
        Args:
          None
        
        Returns: The playlist as a list or None if error occured
        """
        event = ["fetchPlaylist"]
        c_soc = self.sendData(event, False)

        # Receive answer
        length = c_soc.recv(1024)
        length = int(length.rstrip())
        print("GOGO")
        print("Length of data: %d" % length)
        if not length == 0:
            data = c_soc.recv(length)
            print("Data received: %d" % len(data))
            
            return pickle.loads(data)
        else:
            return None

    def fetchCurrentSong(self):
        """
        Method to fetch current songs position in playlist
        Args:
          None
        
        Returns: The position of current song
        """
        event = ["currentSong"]
        c_soc = self.sendData(event, False)
        song = c_soc.recv(1024)
        song = song.rstrip()

        return song

################## Regression test code ###################################
def executeRandomTest():
    api = PympApi()
    events = ["play()", "play(1)", "random()", "play()", "next()", "prev()",
              "repeat()", "fetchPlaylist()", "fetchCurrentSong()", "addFile(\"jalla\")"]

    # Starts a test that will run for 5,5 hours
    for element in range(1, 20000):
        command = events[random.randint(0,len(events)-1)]
        print(command)
        exec("print(api.%s)" % command)
        # Sleep a second between each command
        time.sleep(1)
        
if __name__ == "__main__":

    if len(sys.argv) == 2:
        if sys.argv[1].lower() == "random":
            executeRandomTest()
        else:
            print("Argument unknown. Start program with 'random' as option to start random test")
    else:
        # Run standard test.
        api = PympApi()
        api.play()
        time.sleep(2)
        api.play(1)
        time.sleep(1)
        api.random()
        time.sleep(1)
        api.next()
        time.sleep(1)
        api.repeat()
        time.sleep(1)
        api.prev()
        time.sleep(1)
        api.stop()
        time.sleep(1)
        api.play()
        time.sleep(1)
        api.pause()
        time.sleep(1)
        api.pause()
        time.sleep(1)
        print("Enter filename: ", end="")
        file = input()
        api.addFile(file)
        time.sleep(1)
        playlist = api.fetchPlaylist()
        print("playlist:")
        print(playlist)
        current = api.fetchCurrentSong()
        print(current)
#######################################################################
