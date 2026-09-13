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
import select
from errno import EISCONN
from socket import *
from urllib.parse import quote
import base64

# Import own modules
from OwnConstants import *


def getLocalIp():
    """
    Function to get local ip
    """
    return gethostbyname(gethostname())


class Network:
    """
    Network class to handle asynchron access to socket object
    """
    
    def __init__(self):
        """
        Class constructor
        ARGS:
          None
        """
        pass

    def unblocking_receive(self, conn, buffer, timeout = RECEIVE_TIMEOUT):
        """
        Function to handle unblocking receive from socket
        ARGS:
          (OBJ)      conn = The socket object 
          (INT)      buffer = The size of the buffer to fetch 
          opt(INT)   timeout = Max number of seconds to block on socket
          
        Returns: (byte string) Data fetched or empty list
        """
        
        # test to see if socket is readable
        (rd,wr,ex) = select.select([conn], [], [], timeout)
        
        if len(rd) != 0:
            # socket is readable
            try:
                msg = conn.recv(buffer)
                return msg
            except Exception as why:
                #print "Error receiving : " % why
                # Throw exception
                raise
        else:
            # No data available. Return empty string instead of blocking!
            return ""
        
    def unblocking_connect(self, conn, address, timeout = CONNECT_TIMEOUT):
        """
        Function to perform unblocking connect
        ARGS:
          (OBJ)           conn = The socket object
          ((STRING)(INT)) address = The address where we want to connect to. (IP, PORT)
          opt(INT)        timeout = The max number of seconds to block.
          
        Returns: (BOOLEAN) True if connection is established, False otherwise
        """
        
        # Go in noblocking mode when connecting
        conn.setblocking(0)
        # Connect with connect_ex. This call blocks on windows, therefore
        # setblocking work around above and below
        ret = conn.connect_ex(address)
        # Go back to blocking mode
        conn.setblocking(1)
        if not ret in [0, EISCONN]:
            # Wait on select max timout seconds
            (rd,wr,ex) = select.select([conn], [conn], [], timeout)
            # Test if the socket is writeable or readable
            if len(rd+wr)!= 0:
                # We are connected
                return True
            else:
                # Timed out on connect, socket is not readable nor writeable
                return False
                        
        else:
            # We are connected right away, not likely to happen though
            return True


class HttpUtils:
    """
    Class to handle http authentication if it occurs
    """

    def __init__(self):
        """
        Class constructor
        """
        self.net = Network()

    def parseHeaders(self, data):
        """
        Method to parse header
        ARGS:
          data = The header as plain text

        Returns: (list) status header [protocol, status code, ..],
                 (dict) the remaining headers {key, value}
                 data The data after the header if any
        """
        headers = {}
        first = True
        dataSplit = data.split("\r\n")
        for line in dataSplit:
            tmp = line.strip("\r\n")
            if first:
                # The first line contains protocol name and status code
                statusHeader = tmp.split()
                first = False
                continue

            # Extract key, value from line
            pos = tmp.find(":")
            headers[line[:pos]] = tmp[pos+2:]

            if line == "":
                # end of headers
                break

        data = data[data.find("\r\n\r\n")+4:]
        

        return statusHeader, headers, data
    
    def queryUser(self):
        """
        Open a gui windows so that we can query the user for username and
        password
        ARGS:
          None

        Returns: (string)username,
                 (string)password
        """

        print("FAKING USER INPUT ON USERNAME PASSWORD")
        return "FAKE", "FAKE"
        

    def sendGet(self, url):
        """
        Method to get a page from the great internet.
        Also handles Basic authentication
        ARGS:
          url = The url as a list [hostname, port, url]

        Returns: if http status 200:
                   (list)statusHeaders, (dict)headers, the socket obj
                 else:
                   raise Exception
        """

        # Build get request
        request = "GET /%s HTTP/1.1\r\n" % quote(url[2])
        request += "Host: %s\r\nAccept: */*\r\n" % getLocalIp()
        request += "User-Agent: %s/%s\r\n" % (APPLICATION_NAME, APPLICATION_VERSION)
        request += "Connection: Keep-Alive\r\nIcy-MetaData: 1\r\n"

                            
        # Connect and send request
        address = (url[0], url[1])
        c_soc = socket(AF_INET, SOCK_STREAM)

        # Try to connect!
        if not self.net.unblocking_connect(c_soc, address):
            raise Exception("Cannot connect to server")
        
        # Sending request
        c_soc.send("%s\r\n" % request)

        # Receive data
        data = self.net.unblocking_receive(c_soc, 2048, 100)
        
        if data:
            statusHeader, headers, data = self.parseHeaders(data)
        else:
            raise Exception("Failed requesting page")
        
        if statusHeader[1] == "401":
            # The page we are communicating with requests authentication
            # We only supports the Basic authentication scheem
            if not "WWW-Authenticate" in headers:
                raise Exception("Authentication requested but the 'WWW-Authenticate' is missing in the http header. Aborting.")
            else:
                if not headers["WWW-Authenticate"].startswith("Basic"):
                    raise Exception("%s only supports the Basic authentication scheem. Aborting authentication." % APPLICATION_NAME)

                else:
                    # We have to query the user for username and password
                    username, password = self.queryUser()
                    # Build new request with authentication
                    base64string = base64.encodebytes(('%s:%s' % (username, password)).encode()).decode().strip()
                    authheader =  "Authorization: Basic %s\r\n" % base64string
                    c_soc.close()

                    c_soc = socket(AF_INET, SOCK_STREAM)
                    # Try to connect!
                    if not self.net.unblocking_connect(c_soc, address):
                        raise Exception("Cannot connect to server")
                    # Sending request
                    c_soc.send("%s%s\r\n" % (request, authheader))
                    # Receive data
                    data = self.net.unblocking_receive(c_soc, 2048, 100)
                    
                    if data:
                        statusHeader, headers, data = self.parseHeaders(data)
                    else:
                        raise Exception("Failed requesting page with authentication")
                    
        if statusHeader[1]  == "200":
            print("TJOHO")
            return statusHeader, headers, c_soc, data
        else:
            raise Exception("Failed requesting page")
    

    def parseUrl(self, url):
        """
        Method that parses an url and breaks it up into (server, port, filename)
        ARGS:
          url = The url we want to parse

        Returns: urlTuple [server-ip, port, filename]
        """

        # Create url tuple needed
        url = url[7:]
        address = url[:url.find('/')]
        filename = url[url.find('/') + 1:]

        urlTuple = address.split(':')
        if len(urlTuple) == 1:
            urlTuple.append(80)
        elif len(urlTuple) > 2:
            raise Exception("Wrong format: %s" % url)
    
        else:
            urlTuple[1] = int(urlTuple[1])

        # Convert to ip
        urlTuple[0] = gethostbyname(urlTuple[0])

            
        urlTuple.append(filename)

        return urlTuple
