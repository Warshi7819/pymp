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
import struct, threading, time, os
from socket import *
from urllib.parse import quote
import random

# Import own modules
from OwnConstants import *
from Network import Network, HttpUtils
from Buffer import Buffer

class HttpStreamingClient(threading.Thread):
    """
    Class that handles the streaming over http and shoutCast
    """

    def __init__(self, media):
        """
        Class constructor initializes instance
        ARGS:
          (STRING) media = The media string
        """
        
        # Initialize threading
        threading.Thread.__init__(self)
        # Initialize needed variables
        self.THREAD_EXIT = False
        self.RUNNING = True
        self.chunk_size = 2048
        self.icy_header = {}
        self.bytes_passed = 0
        self.meta_data = None
        self.net = Network()
        self.httpUtils = HttpUtils()
        self.client_ip = gethostbyname(gethostname())

        # Make buffer instance
        self.buffer = Buffer(32)

        # Parse url string
        self.url = self.httpUtils.parseUrl(media)

    def run(self):
        """
        Thread to buffer data
        ARGS:
          None
    
        Returns: None 
        """

        c_soc = None
        
        try:
            statusHeader, headers, c_soc, data = self.httpUtils.sendGet(self.url)
            if statusHeader[0] == "ICY" and statusHeader[1] == "200":
                
                # We have a good signal. Parse rest of header
                stream = True
                                    
                if not "icy-metaint" in headers:
                    raise Exception("Information missing in header")
                            
                # If "ICY 200 OK" we start streaming
                if stream:
                    # Fetch intitial data chunck
                    if not data:
                        data = self.net.unblocking_receive(c_soc, self.chunk_size)
                    
                    bytes_since_meta = 0
                    streamed_bytes = 0
                    meta_data_left = 0
                    meta_data = ''
                    offset = 0

            
                    # Start buffering
                    while self.RUNNING:
                        streamed_bytes += len(data)
                                
                        if meta_data_left:
                            if len(data) >= meta_data_left:
                                meta_data += data[:meta_data_left]
                                data = data[meta_data_left:]
                                streamed_bytes = len(data)
                                meta_data_left = 0
                        
                            else:
                                meta_data_left -= len(data)
                                meta_data += data
                                data = ''

                        # Test if we have reached the metadata interval
                        if streamed_bytes > int(headers['icy-metaint']):
                    
                            index = len(data) - (streamed_bytes - int(headers['icy-metaint']))
                            header_length = data[index]*16
                    
                            # Handle the case where we WILL NOT be able to extract
                            # all metadata from the same chunck
                            if index+header_length+1 > len(data):
                                meta_data_left = header_length - len(data[index+1:])
                                meta_data = data[index+1:]
                                data = data[:index]
                                streamed_bytes = 0

                            # Handle the case where we WILL be able to extract
                            # all metadata from the same chunk
                            else:
                                data_before = data[:index]
                            
                                # Remember to add 1 because we do not want to include
                                # the byte telling us how long the header is!
                                meta_data = data[index+1 : index+header_length+1]
                                
                                streamed_bytes = len(data[index+header_length+1 : ])
                                data = data_before + data[index+header_length+1 : ]
                                meta_data_left = 0    
                            
                                
                        # Only insert data into buffer it there is something
                        # to insert
                        if len(data) > 0:
                            # if metadata and if we have all of it, send info with data package
                            if len(meta_data) > 0 and meta_data_left == 0:
                                # Extract song and artist from metadata
                                # TODO: Clean up this code
                                meta_data = meta_data.strip('\r').strip('\n')
                                artist_song = meta_data[meta_data.find("StreamTitle")+13:]
                                artist_song = artist_song[0:artist_song.find(";")-1]
                                seperator_index = artist_song.find(" - ")
                                artist = artist_song[0:seperator_index].strip()
                                song = artist_song[seperator_index + 3:].strip()
                            
                                self.put(data, {"type": TYPE_SONG_INFO, "artist": artist, "song": song})
                            else:
                                # No metadata available just know. Send only mp3 data
                                self.put(data)
                        else:
                            # No data to put in buffer
                            pass
                    
                        # Read more data
                        # tmp_size = random.randint(20, 2048)
                        # data = self.net.unblocking_receive(c_soc, tmp_size)
                        data = self.net.unblocking_receive(c_soc, self.chunk_size)
                        
        
            # Ordinary http streaming
            elif statusHeader[1] == "200":
                streamedBytes = 0
                printDebug("Streaming ordinary http")
                while self.RUNNING:
                    if streamedBytes < int(headers["Content-Length"]):
                        data = self.net.unblocking_receive(c_soc, self.chunk_size)
                        
                        if data:
                            streamedBytes += len(data)
                            self.put(data)
                    else:
                        self.put(0)
                        
            # Status not supported. Throw exception
            else:
                raise Exception("Web server returned code: %s" % statusHeader[1])
            
        except Exception as e:
            printDebug("Exception during shoutcast streaming: %s" % str(e))
        
        # Close stream, and set thread_exit
        if c_soc:
            c_soc.close()
        self.THREAD_EXIT = True
        # Finished streaming, send terminating 0
        self.put(0)
        
    def put(self, data, info=None):
        """
        Function to insert data into buffer
        ARGS:
          data = The audio element to insert
          
        Returns: None
        """
        return self.buffer.put(data, info)
      
    def read(self):
        """
        Function to read one element from buffer
        ARGS:
          None
          
        Returns: Data element in fifo order
        """
        return self.buffer.read()

            
    def close(self):
        """
        Function to close stream
        ARGS:
          None
        
        Returns: True when done
        """
        #print "Closed called"
        self.RUNNING = False
        # Wait on thread to terminate
        while not self.THREAD_EXIT:
            time.sleep(.02)
        # Clear buffer
        self.buffer.empty_buffer()
        return True
    


class audio_tcp_client(threading.Thread):
    """
    Class for streaming over tcp/ip from pymp server
    """
    
    def __init__(self, media):
        """
        Class constructor initializes instance
        ARGS:
          media = The media string
        """

        # Parse media string
        media = media[6:]
        self.filename = media[media.find('/') + 1:]
        # Extract hostname, port
        hostname, port = media[:media.find('/')].split(':')
        self.address = (hostname, int(port))
            
        # Initialize threading
        threading.Thread.__init__(self)
        # Initialize needed variables
        self.filesize = -1
        self.chunk_size = 2048
        self.RUNNING = True
        self.THREAD_EXIT = False
        self.net = Network()

        # Make buffer object
        self.buffer = Buffer(16)
        
    def run(self):
        """
        Thread to buffer data from pymp server
        ARGS:
          None
          
        Returns: None
        """
        
        try:            
            filename = self.filename
        
            # set limit on filename length
            if len(filename) > MAX_FILENAME_SIZE:
                #print 'Filename is to long!'
                # terminate stream with 0
                self.put(0)
                
            else:
                # Padd filename so it reaches 255 characters!
                filename = filename.ljust(MAX_FILENAME_SIZE)
            
                # connect to client and send request
                c_soc = socket(AF_INET, SOCK_STREAM)


                if not self.net.unblocking_connect(c_soc, self.address):
                    raise Exception("Cannot connect to server")
                           
                # send filename
                c_soc.send(struct.pack('!I', FILE_REQUEST))
                c_soc.send(filename)
                
                data = self.net.unblocking_receive(c_soc, 4)

                if len(data) == 4:
                    # fetch answer
                    size = struct.unpack('!I', data)[0]
                    #print "Server replay: %s" % size
                    if size <= 0:
                        self.put(0)
                    else:
                        # Server has file, begin streaming
                        #print "Begun streaming"
                        self.filesize = size
                        bytes_downloaded = 0
                        # Stream file over network
                        while(self.filesize > bytes_downloaded) and self.RUNNING:
                            data = self.net.unblocking_receive(c_soc, self.chunk_size)
                            if len(data):
                                bytes_downloaded += len(data)
                                self.put(data)

                # Finished streaming, terminate with 0
                c_soc.close()   
            
            
        except Exception as e:
            # Exception occured. Terminate audio stream
            printDebug(e)
            
            
        #print 'Finito streaming'
        self.THREAD_EXIT = True
        #print "Putting 0"
        self.put(0)

    def read(self):
        """
        Function to read one element from buffer
        ARGS:
          None
          
        Returns: Data element in fifo order
        """
        
        return self.buffer.read()

    def put(self, data, info=None):
        """
        Function to insert data into buffer
        ARGS:
          data = The audio element to insert
          
        Returns: None
        """
        
        return self.buffer.put(data)


    def close(self):
        """
        Function to close stream
        ARGS:
          None
          
        Returns: True when done
        """
        
        self.RUNNING = False
        # Wait on thread to terminate
        while not self.THREAD_EXIT:
            time.sleep(.02)
        # Clear buffer
        self.buffer.empty_buffer()
        return True


class audio_localfile_client(threading.Thread):
    """
    Class for streaming local files
    """
    
    def __init__(self, filename):
        """
        Class constructor
        ARGS:
          filename = The name of the file to steam
        """
        
        # Do some testing on media string 
        filename = filename[7:]
        # Test that file exists
        if not os.access(filename, os.F_OK):
            raise Exception('File: %s not found' % filename)
        

        threading.Thread.__init__(self)
        self.chunk_size = 2048
        self.filename = filename
        self.RUNNING = True
        self.THREAD_EXIT = False

        # Make buffer instance
        self.buffer = Buffer()
        
    def run(self):
        """
        The main body of the streaming thread
        ARGS:
          None
          
        Returns: None
        """
        
        # open file and begin streaming
        try:
            fp = open(self.filename, 'rb')
            data = fp.read(self.chunk_size)
            while data and self.RUNNING:
                self.put(data)
                data = fp.read(self.chunk_size)
        except Exception as e:
            #print "Exception during local file streaming %s" % str(e)
            pass
        
        # Send termination byte
        self.put(0)
        self.THREAD_EXIT = True


    def put(self, data, info=None):
        """
        Function to insert data into buffer
        ARGS:
          data = The audio element to insert
          
        Returns: None
        """
        
        return self.buffer.put(data)
      
    def read(self):
        """
        Function to read one element from buffer
        ARGS:
          None
          
        Returns: Data element in fifo order
        """
        
        return self.buffer.read()

    
    def close(self):
        """
        Function to close stream
        ARGS:
          None
          
        Returns: True when done
        """
        
        self.RUNNING = False
        # Wait on thread to terminate
        while not self.THREAD_EXIT:
            time.sleep(.02)
        # Clear buffer
        self.buffer.empty_buffer()
        return True
        
        
class file_streaming:
    """
    Class to make streaming mp3 from lokal file look the same 
    as streaming over http or over TCP/IP 
    """
    
    def __init__(self):
        """
        Class constructor
          ARGS:
          
        None
        """

        self.fp = None

                
    def read(self):
        """
        Function to read from stream
        ARGS:
          None
          
        Returns audio element
        """
        
        return self.fp.read()
        

    def close(self):
        """
        Function to close stream
        ARGS:
          None
          
        Returns: The value of the called function. 
                 (Currently only True is returned when done)
        """
        
        ret = self.fp.close()
        # Deinitialize fp
        self.fp = None
        return ret
        

    def open_stream(self, media):
        """
        Function to open stream regardless if it is an
        http, tcp/ip or local file stream
        ARGS:
          media = The audio URI

        Returns: True if the URI is recognized and an streaming instance
                 has been created. If the URI cannot be recognized False 
                 is returned
        """
        
        # test if it is a local file
        if media.lower().startswith('file://'):
            # Start streaming file
            self.fp = audio_localfile_client(media)
            self.fp.start()
            return True
        
        # test if it is an tcp/ip stream
        elif media.lower().startswith('tcp://'):
            # Start fetching file from server
            self.fp = audio_tcp_client(media)
            self.fp.start()
            return True

        # Handle ordinary http streaming or SHOUTcast
        elif media.lower().startswith('http://'):
            # Start streaming SHOUTcast
            self.fp = HttpStreamingClient(media)
            self.fp.start()
            return True
        
        # If not URI is recognized we end up here :(
        else:
            #print 'URI not supported'
            return False
