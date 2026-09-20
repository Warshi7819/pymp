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
import xml.sax, xml.sax.handler, sys
from xml.dom import minidom
import os.path

# Import own modules
from OwnConstants import *

class AboutParser(xml.sax.handler.ContentHandler):
    """
    About file parser
    """
    
    def __init__(self, parser):
        """
        The class's constructor
        Args:
          parser = the sax parser object
        """
        # Init the sax handler
        xml.sax.handler.ContentHandler.__init__(self)
        # Init the config data
        self.data = {}
        self.data["lines"] = []
        self.data["scrollspeed"] = 1
        
    def startDocument(self):
        """
        Method called at the start of the document
        Args:
          None
          
        Returns: None
        """
        pass

    def endElement(self, name):
        """
        Method called when end of tag is reached
        Args:
          name = The name of the tag

        Returns: None
        """
        pass
            
    def startElement(self, name, attr):
        """
        Methode called when the start of an tag is reached
        Args:
          name = The name of the tag
          attr = The tag's attributes
          
        Returns: None
        """
        
        if name == "text":
            element = {}
            element["value"] = str(attr["value"])
            element["size"] = str(attr["size"])
            element["color"] = str(attr["colour"])
            element["indent"] = str(attr["indent"])
            element["font"] = str(attr["font"])
            element["y"] = 0
            element["running"] = False
            element["staticText"] = None

            self.data["lines"].append(element)

        elif name == "about":
            self.data["scrollspeed"] = str(attr["scrollspeed"])
                                        
    def endDocument(self):
        """
        Method called when end of document is reached
        Args:
          None
          
        Returns: None
        """
        # Clean up after parsing
        pass

    def characters(self, content):
        """
        Method to handle the parsing of data between two tags
        Args:
          content = The content between tags
          
        Returns: None
        """
        pass

    def getData(self):
        """
        Method to return the data parsed
        Args:
          None
          
        Returns: Dictionary containing the parsed data
        """
        return self.data

class ParseAbout:
    """
    Class to parse the about file
    """

    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        pass

    def parseAbout(self,filename):
        """
        Method to parse the about file
        Args:
          filename = The full path too the xml config file
          
        Returns: A dictonary containing the about info
        """
        parser = xml.sax.make_parser()
        myHandler = AboutParser(parser)
        parser.setContentHandler(myHandler)

        try:
            fp = open(filename, "r")
            parser.parse(fp)
            fp.close()
        except Exception as e:
            printDebug('Exception occured traversing xml document!')
            printDebug(e)
            # Failed parsing
            raise

        return myHandler.getData()

if __name__ == "__main__":
    p = ParseAbout()
    print(p.parseAbout("about.xml"))
