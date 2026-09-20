###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Import own modules
from OwnConstants import *

class Buffer:
    """
    Class to handle audio buffer
    """

    def __init__(self, bufferElements = 1):
        """
        The class constructor
        Args:
          (opt)bufferElements = Number of elements to initially buffer up
                                before starting to play
        """
        self.audio_buffer = []
        self.BUFFERING = True
        # Buffer size in chunk_size elements 
        self.BUFFER_ELEMENTS = bufferElements
        self.MAX_BUFFER_ELEMENTS = 256
        printDebug("Initial Buffer size: %d" % bufferElements) 


    def put(self, data, info=None):
        """
        Method to insert data into buffer
        Args:
          (byte string) data = The audio element to insert
          (opt)info =   info about data element, if any. Default is None

        Returns: None
        """
        self.audio_buffer.insert(0, [data, info])
    

    def read(self):
        """
        Method to read one element from buffer
        Args:
          None
          
        Returns: (byte string) Data element in fifo order
        """

        length = len(self.audio_buffer)
        # Buffering
        if self.BUFFERING:
            #print "BUFFER SIZE = %d" % self.BUFFER_ELEMENTS
            if length > self.BUFFER_ELEMENTS:
                # Buffer size reached!
                self.BUFFERING = False

            elif length > 0:
                if self.audio_buffer[0][0] == 0:
                    # End of song reached!
                    self.BUFFERING = False

        # If we are still buffering
        if self.BUFFERING:
            return [None, {"type": TYPE_BUFFERING, "buffer_status": "%d/%d" % (length, self.BUFFER_ELEMENTS)}]
                
        # pop from list
        if len(self.audio_buffer):
            data = self.audio_buffer.pop()
            return data
        else:
            # List empty. Enter buffering modus
            self.BUFFERING = True
            # Adjust buffer size
            if self.BUFFER_ELEMENTS * 2 < self.MAX_BUFFER_ELEMENTS:
                self.BUFFER_ELEMENTS = self.BUFFER_ELEMENTS * 2
            else:
                self.BUFFER_ELEMENTS = self.MAX_BUFFER_ELEMENTS
            
            # No data in buffer, return None
            return [None, {"type": TYPE_BUFFERING, "buffer_status": "%d/%d" % (length ,self.BUFFER_ELEMENTS)}]


    def emptyBuffer(self):
        """
        Method to empty buffer
        Args:
          None
          
        Returns: None
        """
        self.audio_buffer = []
