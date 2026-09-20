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

    def __init__(self, media, metadata_only=False, metadata_callback=None):
        """
        Class constructor initializes instance
        Args:
          (STRING) media = The media string
          (BOOL) metadata_only = If True, only extract ICY metadata and
                 discard audio data. Used as a companion for ffmpeg-based
                 StreamPlayer to provide artist/song info.
          (FUNC) metadata_callback = Called with {"artist": ..., "song": ...}
                 when stream metadata changes. Used in metadata_only mode.
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
        self.metadata_only = metadata_only
        self.metadata_callback = metadata_callback

        # Make buffer instance
        self.buffer = Buffer(4)

        # Parse url string
        self.url = self.httpUtils.parseUrl(media)

    def run(self):
        """
        Thread to buffer data
        Args:
          None
    
        Returns: None 
        """

        c_soc = None
        
        try:
            statusHeader, headers, c_soc, data = self.httpUtils.sendGet(self.url)
            if statusHeader[1] == "200" and "icy-metaint" in headers:
                
                # We have a good signal. Parse rest of header
                stream = True
                                    
                if not "icy-metaint" in headers:
                    raise Exception("Information missing in header")
                            
                # If "ICY 200 OK" we start streaming
                if stream:
                    # Accumulate data and find first metadata boundary
                    # by scanning for StreamTitle= (handles mid-stream join)
                    icy_metaint = int(headers['icy-metaint'])
                    audio_buffer = data if data else b''

                    # Phase 1: Find first sync point
                    while self.RUNNING:
                        marker_pos = audio_buffer.find(b"StreamTitle=")
                        if marker_pos != -1:
                            # Found StreamTitle= — work backwards to find length byte
                            found = False
                            for offset in range(16):
                                content_start = marker_pos - offset
                                if content_start < 1:
                                    continue
                                length_byte_pos = content_start - 1
                                if length_byte_pos < 0:
                                    continue
                                length_byte = audio_buffer[length_byte_pos]
                                if length_byte == 0:
                                    continue
                                meta_block_size = length_byte * 16
                                meta_end = length_byte_pos + 1 + meta_block_size
                                if meta_end > len(audio_buffer):
                                    break  # need more data
                                content = audio_buffer[length_byte_pos + 1:meta_end]
                                if b"StreamTitle=" in content:
                                    # Found first metadata boundary
                                    audio_after_first = audio_buffer[meta_end:]
                                    # Process first metadata
                                    self._process_metadata(content)
                                    # Put audio before metadata into buffer
                                    audio_before = audio_buffer[:length_byte_pos]
                                    if not self.metadata_only and len(audio_before) > 0:
                                        self.put(audio_before)
                                    audio_buffer = audio_after_first
                                    found = True
                                    break
                            if found:
                                break

                        # Need more data
                        chunk = self.net.unblockingReceive(c_soc, self.chunk_size)
                        if chunk:
                            audio_buffer += chunk

                    # Phase 2: Continuously deliver audio, strip metadata when found
                    while self.RUNNING:
                        # Scan for StreamTitle= to locate metadata blocks
                        marker_pos = audio_buffer.find(b"StreamTitle=")
                        if marker_pos != -1:
                            # Work backwards to find length byte and validate
                            extracted = False
                            for offset in range(16):
                                content_start = marker_pos - offset
                                if content_start < 1:
                                    continue
                                length_byte_pos = content_start - 1
                                if length_byte_pos < 0:
                                    continue
                                length_byte = audio_buffer[length_byte_pos]
                                if length_byte == 0:
                                    continue
                                meta_block_size = length_byte * 16
                                meta_end = length_byte_pos + 1 + meta_block_size
                                if meta_end > len(audio_buffer):
                                    break  # need more data to validate
                                content = audio_buffer[length_byte_pos + 1:meta_end]
                                if b"StreamTitle=" in content:
                                    # Valid metadata — deliver audio before it, skip it
                                    if not self.metadata_only and length_byte_pos > 0:
                                        self.put(audio_buffer[:length_byte_pos])
                                    self._process_metadata(content)
                                    audio_buffer = audio_buffer[meta_end:]
                                    extracted = True
                                    break

                            if not extracted:
                                # StreamTitle= found but can't validate yet — deliver safe audio
                                # Keep max 4081 bytes (1 len + 255*16) where metadata might be
                                safe_end = max(0, marker_pos - 4081)
                                if safe_end > 0 and not self.metadata_only:
                                    self.put(audio_buffer[:safe_end])
                                audio_buffer = audio_buffer[safe_end:]

                        else:
                            # No StreamTitle= — everything is audio, deliver it
                            if not self.metadata_only and len(audio_buffer) > 0:
                                self.put(audio_buffer)
                            # Always clear — don't accumulate audio in metadata_only mode
                            audio_buffer = b''

                        # Read more data from socket
                        chunk = self.net.unblockingReceive(c_soc, self.chunk_size)
                        if chunk:
                            audio_buffer += chunk
                        
        
            # Ordinary http streaming
            elif statusHeader[1] == "200":
                streamedBytes = 0
                printDebug("Streaming ordinary http")
                while self.RUNNING:
                    if streamedBytes < int(headers["Content-Length"]):
                        data = self.net.unblockingReceive(c_soc, self.chunk_size)
                        
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

    def _process_metadata(self, raw_meta):
        """
        Extract artist/song from raw ICY metadata bytes and notify callback.
        Args:
          raw_meta = Raw metadata bytes from the stream

        Returns: None
        """
        meta_data_clean = raw_meta.replace(b'\x00', b'')
        meta_data_str = meta_data_clean.decode('utf-8', errors='replace').strip()
        st_idx = meta_data_str.find("StreamTitle=")
        if st_idx != -1:
            title = meta_data_str[st_idx + 13:]
            end = title.find(";")
            if end != -1:
                title = title[:end]
            title = title.strip().strip("'\"")
            sep = title.find(" - ")
            if sep != -1:
                artist = title[:sep].strip()
                song = title[sep + 3:].strip()
            else:
                artist = ""
                song = title
        else:
            artist = ""
            song = meta_data_str

        if self.metadata_callback:
            self.metadata_callback({"artist": artist, "song": song})
        
    def put(self, data, info=None):
        """
        Method to insert data into buffer
        Args:
          data = The audio element to insert
          
        Returns: None
        """
        return self.buffer.put(data, info)
      
    def read(self):
        """
        Method to read one element from buffer
        Args:
          None
          
        Returns: Data element in fifo order
        """
        return self.buffer.read()

            
    def close(self):
        """
        Method to close stream
        Args:
          None
        
        Returns: True when done
        """
        #print "Closed called"
        self.RUNNING = False
        # Wait on thread to terminate
        while not self.THREAD_EXIT:
            time.sleep(.02)
        # Clear buffer
        self.buffer.emptyBuffer()
        return True
    


class AudioTcpClient(threading.Thread):
    """
    Class for streaming over tcp/ip from pymp server
    """
    
    def __init__(self, media):
        """
        Class constructor initializes instance
        Args:
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
        Args:
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


                if not self.net.unblockingConnect(c_soc, self.address):
                    raise Exception("Cannot connect to server")
                           
                # send filename
                c_soc.send(struct.pack('!I', FILE_REQUEST))
                c_soc.send(filename.encode())
                
                data = self.net.unblockingReceive(c_soc, 4)

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
                            data = self.net.unblockingReceive(c_soc, self.chunk_size)
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
        Method to read one element from buffer
        Args:
          None
          
        Returns: Data element in fifo order
        """
        
        return self.buffer.read()

    def put(self, data, info=None):
        """
        Method to insert data into buffer
        Args:
          data = The audio element to insert
          
        Returns: None
        """
        
        return self.buffer.put(data)


    def close(self):
        """
        Method to close stream
        Args:
          None
          
        Returns: True when done
        """
        
        self.RUNNING = False
        # Wait on thread to terminate
        while not self.THREAD_EXIT:
            time.sleep(.02)
        # Clear buffer
        self.buffer.emptyBuffer()
        return True


class AudioLocalfileClient(threading.Thread):
    """
    Class for streaming local files
    """
    
    def __init__(self, filename):
        """
        Class constructor
        Args:
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
        Args:
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
        Method to insert data into buffer
        Args:
          data = The audio element to insert
          
        Returns: None
        """
        
        return self.buffer.put(data)
      
    def read(self):
        """
        Method to read one element from buffer
        Args:
          None
          
        Returns: Data element in fifo order
        """
        
        return self.buffer.read()

    
    def close(self):
        """
        Method to close stream
        Args:
          None
          
        Returns: True when done
        """
        
        self.RUNNING = False
        # Wait on thread to terminate
        while not self.THREAD_EXIT:
            time.sleep(.02)
        # Clear buffer
        self.buffer.emptyBuffer()
        return True
        
        
class FileStreaming:
    """
    Class to make streaming mp3 from lokal file look the same 
    as streaming over http or over TCP/IP 
    """
    
    def __init__(self):
        """
        Class constructor
          Args:
          
        None
        """

        self.fp = None

                
    def read(self):
        """
        Method to read from stream
        Args:
          None
          
        Returns audio element
        """
        
        return self.fp.read()
        

    def close(self):
        """
        Method to close stream
        Args:
          None
          
        Returns: The value of the called function. 
                 (Currently only True is returned when done)
        """
        
        ret = self.fp.close()
        # Deinitialize fp
        self.fp = None
        return ret
        

    def openStream(self, media):
        """
        Method to open stream regardless if it is an
        http, tcp/ip or local file stream
        Args:
          media = The audio URI

        Returns: True if the URI is recognized and an streaming instance
                 has been created. If the URI cannot be recognized False 
                 is returned
        """
        
        # test if it is a local file
        if media.lower().startswith('file://'):
            # Start streaming file
            self.fp = AudioLocalfileClient(media)
            self.fp.start()
            return True
        
        # test if it is an tcp/ip stream
        elif media.lower().startswith('tcp://'):
            # Start fetching file from server
            self.fp = AudioTcpClient(media)
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
