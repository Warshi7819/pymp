###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

# Standard modules
import xml.sax, xml.sax.handler, sys
from xml.dom import minidom
import os

from OwnConstants import *

class ConfigParser(xml.sax.handler.ContentHandler):

    def __init__(self, parser):
        """
        The class's constructor
        Args:
          parser = the sax parser object
        """
        # Init the sax handler
        xml.sax.handler.ContentHandler.__init__(self)
        # Init the config data
        self.config = {}

        
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
        Methode called when the end of an tag is reached
        Args:
          name = The name of the tag
          attr = The tag's attributes
          
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
        if name == "position":
            self.config["position"] = (int(attr["x"]), int(attr["y"]))
        elif name == "playlistPosition":
            self.config["playlistPosition"] = (int(attr["x"]), int(attr["y"]))

        elif name == "configPosition":
            self.config["configPosition"] = (int(attr["x"]), int(attr["y"]))

        elif name == "aboutPosition":
            self.config["aboutPosition"] = (int(attr["x"]), int(attr["y"]))
        
        elif name == "skin":
            self.config["skin"] = str(attr["path"])

        elif name == "current-track":
            self.config["current-track"] = int(attr["value"])

        elif name == "random":
            if str(attr["value"]).lower() == "true":
                self.config["random"] = True
            else:
                self.config["random"] = False

        elif name == "repeat":
            if str(attr["value"]).lower() == "true":
                self.config["repeat"] = True
            else:
                self.config["repeat"] = False
            
        elif name == "debug-skin":
            if str(attr["value"]).lower() == "true":
                self.config["debug-skin"] = True
            else:
                self.config["debug-skin"] = False
        elif name == "task-bar":
            if str(attr["value"]).lower() == "true":
                self.config["task-bar"] = True
            else:
                self.config["task-bar"] = False
        elif name == "stay-on-top":
            if str(attr["value"]).lower() == "true":
                self.config["stay-on-top"] = True
            else:
                self.config["stay-on-top"] = False

        elif name == "hotkeys":
            if str(attr["value"]).lower() == "true":
                self.config["hotkeys"] = True
            else:
                self.config["hotkeys"] = False
                
        elif name == "last-directory":
            path = str(attr["path"])
            if not path or not os.path.isdir(path):
                path = os.getcwd()
            self.config["last-directory"] = path

        else:
            pass
                
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
        return self.config

class ParseConfig:
    """
    Class to parse the config
    """
    
    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        pass

    def parseConfig(self,filename):
        """
        Method to parse the config file
        Args:
          filename = The full path too the xml config file
        
        Returns: A dictonary containing the players config
        """
        parser = xml.sax.make_parser()
        myHandler = ConfigParser(parser)
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
    p = ParseConfig()
    print(p.parseConfig("config.xml"))
