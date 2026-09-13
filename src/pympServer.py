###################################################
# Application : pyPlayer 1.0.4                    #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import standard modules
import struct, threading, time, os, sys
from socket import *
from os.path import isdir, join
import pickle
from Id3 import Id3Utils

CHUNCK_SIZE = 2048
FILE_REQUEST = 11000
PLAYLIST_REQUEST = 11001
MAX_FILENAME_SIZE = 1024


class ClientHandler(threading.Thread):
    """
    Thread to handle streaming of requested song!
    """
    def __init__(self, c_soc, chunksize, playlist, allowedFiles):
        """
        Class constructor.
        Args:
          c_soc = The client socket
          chuncksize = The tcp-ip chuncksize
          playlist = The playlist
          allowedFiles = The files extensions we are goint to share
        """
        threading.Thread.__init__(self)
        self.c_soc = c_soc
        self.chunksize = chunksize
        self.playlist = playlist
        self.allowedFiles = allowedFiles

    def run(self):
        """
        The main body of the thread. Listens for requests and handles them
        Args:
          None

        Returns: None
        """
        try:
            # Fetch type of request
            type = struct.unpack('!I', self.c_soc.recv(4))[0]

            # Execute right handler based on the type of request
            if type == FILE_REQUEST:
                self.handleFileRequest()

            elif type == PLAYLIST_REQUEST:
                self.handlePlaylistRequest()
                
            else:
                pass
                
        except Exception as e:
            pass


    def handleFileRequest(self):
        """
        Method to handle file request
        If file exists, stream it to client!
        Args:
          None
          
        Returns: None
        """
        try:
            # Fetch filename
            filename = self.c_soc.recv(MAX_FILENAME_SIZE)
            filename = filename.rstrip()
            print(filename)

            # Test that file is shared
            if not filename in self.allowedFiles:
                self.c_soc.send(struct.pack('!I', 0))
                print("Requested file is not shared!")
            
            # Test if filename exists
            elif not os.access(filename, os.F_OK):
                self.c_soc.send(struct.pack('!I', 0))
                print("File does not exist")
                
            else:
                size = None
                fp = None
                try:
                    size = os.stat(filename).st_size
                    fp = open(filename, 'rb')
                except Exception as e:
                    print(e)
                    # Shit happend trying to open file
                    self.c_soc.send(struct.pack('!I', -1))
                    print("Exception occured trying to open file")
                    size = None
                
                if size != None:
                    self.c_soc.send(struct.pack('!I', size))
            
                    data = ' '
                    # send file
                    while data:
                        data = fp.read(CHUNCK_SIZE)
                        self.c_soc.send(data)
                                        
                fp.close()
                self.c_soc.close()

        except Exception as e:
            print(e)


    def handlePlaylistRequest(self):
        """
        Method to handle playlist request
        Args:
          None
          
        Returns: None
        """
        # Fetch playlist
        try:
            data = None
            try:
                data = pickle.dumps(self.playlist)
            except Exception as e:
                print("pickle failed: %s" % str(e))
                data = None
        
        
            if data:
                size = len(data)
                print("Sending %d bytes" % size)
                self.c_soc.send(struct.pack('!I', size))
                self.c_soc.send(data)
            else:
                self.c_soc.send(struct.pack('!I', -1))
                
            self.c_soc.close()
        except Exception as e:
            print(e)

        
    


class pyMPServer:
    """
    The server that will serve the connecting clients
    """

    def __init__(self, rootDir, port):
        """
        The class constructor
        Args:
          (str)rootDir = The path to the directory we want to share.
                         All subdirectories will also be shared
          (int)port = The port the server will listen to

        Returns: None
        """
         # Get the address
        self.address = (gethostbyname(gethostname()), port)
        # Initialize playlist
        self.playlist = []
        self.allowedFiles = []
        # Make an Id3Utils instance
        self.id3Utils = Id3Utils()
        # Load playlist
        self.loadPlaylist(rootDir)
        # Start serving customers
        self.serve()
        


    def loadPlaylist(self, rootDir):
        """
        Method to load playlist data
        Args:
          (str)rootDir = The root directory of what we want to share
          
        Returns: None
        """
        print("Traversing: ", rootDir)
        for root, dirs, files in os.walk(rootDir, topdown=False):
            for name in files:
                if name.lower().endswith('.mp3'):
                    filename = join(root, name)
                    self.allowedFiles.append(filename)
                    # Extract mp3 info
                    info = self.id3Utils.parse_file(filename)
                    if info != False:
                        # Append info to current playlist
                        self.playlist.append([filename, info.title, info.artist])
                    else:
                        # No id3 tag found, add default info
                        self.playlist.append([filename, filename[filename.rfind('/') + 1:], 'unknown'])


        print("%d songs loaded into playlist" % len(self.playlist))
        
    def serve(self, chunk_size = 1024):
        """
        The server itself. When called it starts listening on a
        given port for requests
        Args:
          (OPT)chunk_size = The size of the chunks to read
        
        Returns: None
        """
        s_soc = socket(AF_INET, SOCK_STREAM)
        s_soc.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s_soc.bind(self.address)
        s_soc.listen(5)
            
        fp = open("customer.log", "a")
        
        while True:
            print("Server up and running")
            c_soc, addr = s_soc.accept()
            worker_thread = ClientHandler(c_soc, 2048, self.playlist,
                                          self.allowedFiles)
            worker_thread.start()

            # Log request to file
            t = time.localtime()
            time_formated = "%d:%d:%d %d.%d.%d" % (t[3], t[4], t[5], t[1], t[2], t[0])
            fp.write("TIME: %s Client: %s\n" % (time_formated, str(addr)))

        fp.close()


def usage():
    """
    Function to print usage
    Args:
      None

    Returns: None
    """
    print("\n\n\tUsage: pyMPServer <rootDirectory> <port>\n")
    print("\te.g pyMPServer c:\\ 77900, this will start the server")
    print("\tand make it listen to port 77900. Remember though that")
    print("\tthe server will share everything under the rootDirectory.") 
    

if __name__ == "__main__":
    # set default port number
    port = 18003
    rootDir = None
    # Test commandline arguments
    print(sys.argv)
    if len(sys.argv) == 3:
        try:
            rootDir = str(sys.argv[1])
            port = int(sys.argv[2])
        except Exception as e:
            usage()
            sys.exit(1)
            
    elif len(sys.argv) >2:
        usage()
        sys.exit(1)
        
    # Start server
    pyMPServer(rootDir, port)
