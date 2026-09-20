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

class SkinParser(xml.sax.handler.ContentHandler):
    
    def __init__(self, parser, dirName):
        """
        The class's constructor
        Args:
          parser = the sax parser object
        """
        # Init the sax handler
        xml.sax.handler.ContentHandler.__init__(self)
        # Init the config data
        self.data = {}
        self.menuName = False
        self.dirName = dirName

        
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

        Returns: None
        """
        if name == "menuItem":
            self.menuName = False
            

    def startElement(self, name, attr):
        """
        Methode called when the start of an tag is reached
        Args:
          name = The name of the tag
          attr = The tag's attributes
          
        Returns: None
        """
        
        if name == "button" or name == "toggleButton":
            if name not in self.data:
                self.data[str(name)] = []

            # Extract button config
            tmp = {}
            tmp["imgUp"] = os.path.join(self.dirName, str(attr["imgUp"]))
            tmp["imgDown"] = os.path.join(self.dirName, str(attr["imgDown"]))
            tmp["toolTip"] = str(attr["toolTip"])
            tmp["event"] = str(attr["event"])
            tmp["x"] = int(str(attr["x"]))
            tmp["y"] = int(str(attr["y"]))

            if "bg" in attr:
                tmp["bg"] = str(attr["bg"])

            if "fg" in attr:
                tmp["fg"] = str(attr["fg"])
                
            # Append button
            self.data[str(name)].append(tmp)

        if name == "playlistButton":
            if name not in self.data:
                self.data[str(name)] = []

            # Extract button config
            tmp = {}
            tmp["imgUp"] = os.path.join(self.dirName, str(attr["imgUp"]))
            tmp["imgDown"] = os.path.join(self.dirName, str(attr["imgDown"]))
            tmp["toolTip"] = str(attr["toolTip"])
            tmp["event"] = str(attr["event"])
            tmp["x"] = int(str(attr["x"]))
            tmp["y"] = int(str(attr["y"]))

            # Append button
            self.data[str(name)].append(tmp)
            
        elif name == "label":
            if name not in self.data:
                self.data[str(name)] = []

            # Extract label config
            tmp = {}
            tmp["length"] = int(str(attr["length"]))
            tmp["height"] = int(str(attr["height"]))
            tmp["type"] = str(attr["type"])
            tmp["scrolling"] = str(attr["scrolling"])
            tmp["x"] = int(str(attr["x"]))
            tmp["y"] = int(str(attr["y"]))
            tmp["bg"] = str(attr["bg"])
            tmp["fg"] = str(attr["fg"])

            # Append label
            self.data[str(name)].append(tmp)

        elif name == "menuItem":
            if name not in self.data:
                self.data[str(name)] = []

            if str(attr["event"]) == "parent":
                
                self.menuName = True
                tmp = {}
                tmp["name"] = str(attr["name"])
                tmp["parent"] = True
                tmp["children"] = []
                self.data[str(name)].append(tmp)
            else:
                tmp = {}
                tmp["name"] = str(attr["name"])
                tmp["parent"] = False
                tmp["event"] = str(attr["event"])
                self.data[str(name)].append(tmp)
                
        elif name == "subItem":
            if self.menuName == False:
                raise Exeption("subItem must be a sub-tag of menuItem!!")
            tmp = {}
            tmp["name"] = str(attr["name"])
            tmp["event"] = str(attr["event"])
            self.data["menuItem"][-1]["children"].append(tmp)
            
             
        elif name == "VolumeSlider":
            if name not in self.data:
                self.data[str(name)] = {}
                self.data[str(name)]["size"] = int(str(attr["size"]))
                self.data[str(name)]["x"] = int(str(attr["x"]))
                self.data[str(name)]["y"] = int(str(attr["y"]))
            else:
                raise Exception("VolumeSlider must be defined only once")
        elif name == "bgImage":
            if name not in self.data:
                self.data[str(name)] = {}

            self.data["bgImage"]["path"] = os.path.join(self.dirName, str(attr["path"]))

        elif name == "playlistBgImage":
            if name not in self.data:
                self.data[str(name)] = {}

            self.data["playlistBgImage"]["path"] = os.path.join(self.dirName,
                                                                str(attr["path"]))
        elif name == "scrollList":
            if name not in self.data:
                self.data[str(name)] = {}

            self.data[str(name)]["height"] = int(str(attr["height"]))
            self.data[str(name)]["width"] = int(str(attr["width"]))
            self.data[str(name)]["x"] = int(str(attr["x"]))
            self.data[str(name)]["y"] = int(str(attr["y"]))
            self.data[str(name)]["bgColour"] = str(attr["bg"])
            self.data[str(name)]["fgColour"] = str(attr["fg"])
            
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
        return self.data


class ParseSkin:
    """
    Class to parse a pyPlayer Skin
    """
    
    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        pass

    def parseSkin(self,filename):
        """
        Method to parse a skin config file
        Args:
          filename = The full path too the skin's xml config file
          
        Returns: A dictonary containing the skin's config
        """
        dirName = os.path.dirname(filename)
        parser = xml.sax.make_parser()
        myHandler = SkinParser(parser, dirName)
        parser.setContentHandler(myHandler)

        try:
            fp = open(filename, "r")
            parser.parse(fp)
            fp.close()
        except Exception as e:
            print('Exception occured traversing xml document!')
            print(e)
            # Failed parsing
            raise

        return myHandler.getData()

if __name__ == "__main__":
    p = ParseSkin()
    print(p.parseSkin("skin.xml"))
