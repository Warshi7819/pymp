###################################################
# Application : pyMP                              #
#  * Asynchronous event based music player        #
#  * utilizing the powers of pymedia and wxPython #
#                                                 #
# Author      : Rune Devik                        #
# Date        : 14:37 05.09.2004                  #
# License     : GNU General Public License (GPL)  #
###################################################

import copy
import os.path
import time

# Turn debug on/off
DEBUG = False
def printDebug(str):
    if DEBUG:
        print(str)

class PlaylistSearch:
    """
    Class implementing playlist search feature
    Suffix search?
    """

    def __init__(self):
        """
        Class constructor
        Args:
          None
        """
        pass
    

class Node:
    """
    Node of the suffix tree
    """

    def __init__(self):
        self.matches = [] # List of matches on current node
        self.children = {} # list of children
        self.root = False # root or not root, that is the question
        self.str = [] # List of characters (The nodes substring)
        self.id = 0


class Tree:

    def __init__(self, caseSensitive = False):
        """
        The class constructor
        Args:
          caseSensitive = If the search should be case sensitive or not
                          case sensitive search will require more memory
        """
        self.caseSensitive = caseSensitive # Wether or not the search should be case sensitive
        self.root = Node()
        self.root.str = list("root")
        self.id = 0
        self.searchResults = []


    def search(self, searchString):
        """
        Method to search the tree for a given string
        Args:
          searchString = The string to search for

        Returns: A list of matches found
        """
        self.searchResults = []
        self.foundNode = None

        # Convert string to a list of chars for
        # easy manipulation
        searchString = searchString.strip()

        if not self.caseSensitive:
            searchString = searchString.lower()

        if len(searchString) == 0:
            return []

        searchString = list(searchString)
        # perform the search itself
        if searchString[0] in self.root.children:
            self.performSearch(searchString,
                               self.root.children[searchString[0]])
                               
        else:
            return []
        
        # Gather results by performing a depth first
        # search from the node where the search string was
        # exhausted
        if self.foundNode != None:
            self.gatherResults(self.foundNode)
        else:
            return []

        # Remove any duplicates and return results
        return self.removeSearchDuplicates()


    def performSearch(self, subString, curNode):
        """
        Method to perform a search in the suffix tree
        Args:
          subString = The search string or what's left of it
                      after recursion
          curNode = The current node in the suffix tree

        Returns: None
        """
        curNodeLength = len(curNode.str)
        searchStringLength = len(subString)
        found = True
        for i in range(0, searchStringLength):
            if i == curNodeLength:
                # The current nodes string is exhausted. look for a
                # matching child where the search can continue
                if subString[i] in curNode.children:
                    printDebug("%d%s" % (2, subString))
                    self.performSearch(subString[i:],
                                       curNode.children[subString[i]])
                    found = False
                    break
                else:
                    # no matching child, search failed
                    found = False
                    break
            else:
                # test if strings differ
                if subString[i] != curNode.str[i]:
                    found = False
                    break
        
        if found:
            self.foundNode = curNode


    def gatherResults(self, node):
        """
        Method that performs depth first search from a
        given node and gathers all matches
        Args:
          node = The current node in the recursion
        """
        
        self.searchResults.extend(node.matches)
            
        for child in node.children:
            self.gatherResults(node.children[child])
            

    def removeSearchDuplicates(self):
        """
        Method to remove all search duplicates
        Args:
          None

        Returns: A list of search results
        """
        self.searchResults.sort()
        tmp = []
        numHits = len(self.searchResults)
        if numHits > 1:
            last = self.searchResults[0]
            tmp.append(last)
            for i in range(1, numHits):
                current = self.searchResults[i]
                if last != self.searchResults[i]:
                    tmp.append(current)
                last = current

            return tmp
        else:
            return self.searchResults[:]


    def addString(self, str, id):
        """
        Method to add a new string to the tree
        Args:
          str = The new string we want to add to the tree
          id = The id of the string
        """
        str = str.strip("\n").strip("\r").strip()
        if not self.caseSensitive:
            str = str.lower()
            
        if not str == "":
            strArray = list(str)
            # Mark end of string
            strArray.append("END")
            
            for i in range(0, len(strArray)-1):
                curChar = strArray[i]
                if curChar != "END":
                    if curChar not in self.root.children:
                        self.addNode(strArray[i:], id, self.root)
                    else:
                        self.searchAndInsert(strArray[i:], id,
                                             self.root.children[curChar])
                
        else:
            printDebug("String contains no valid data and was disregarded")


    def searchAndInsert(self, subString, id, curNode):
        """
        Method to search for the node where this substring should be inserted
        Args:
          subString = The substring we are on
          id = The new strings id
          curNode = the node we are currently searching

        Returns: None
        """
        printDebug("search")

        for i in range(0, len(subString)):
            printDebug("current search: %s" % subString[i:])
            printDebug("current node: %s" % curNode.str[i:])
            if i == len(curNode.str):
                # The current nodes string is exhausted. look for a
                # matching child where the search can continue
                if subString[i] in curNode.children:
                    printDebug("%d%s" % (2, subString))
                    self.searchAndInsert(subString[i:], id,
                                         curNode.children[subString[i]])
                    break
                else:
                    # no matching child, create new one
                    printDebug(3)
                    self.addNode(subString[i:], id, curNode)
                    break
                
            else:
                # Test if the new substring is exhausted
                if subString[i] == "END":
                    if not curNode.str[i] == "END":
                        printDebug(4)
                        self.splitNode(curNode, i, subString[i:], id)
                        break
                    else:
                        printDebug(5)
                        if not id in curNode.matches:
                            curNode.matches.append(id)
                        break

                # test if strings differ
                elif subString[i] != curNode.str[i]:
                    printDebug(6)
                    self.splitNode(curNode, i, subString[i:], id)
                    break
                    
        
    def splitNode(self, node, index, subString, id):
        """
        Method to split node. Create two new nodes, one containing
        the children and matches of the original node. The other only
        contains the remainder of the new string inserted and it's id
        Args:
          node = The node to split
          index = The index on which we should preform the split
          subString = The remainder of the new sub string
          id = The id of the string we are inserting

        Returns: None
        """
        printDebug("splitting")
        newNodeOne = Node()

        self.id += 1
        newNodeOne.id = self.id
        
        # Copy original nodes matches
        newNodeOne.matches = node.matches[:]
        # Copy original nodes children
        newNodeOne.children = copy.deepcopy(node.children)
        # Set correct substring
        newNodeOne.str = node.str[index:]

        newNodeTwo = Node()

        self.id += 1
        newNodeTwo.id = self.id
        
        # Appen new strings id
        newNodeTwo.matches.append(id)
        # append new nodes remaining substring
        newNodeTwo.str = subString
        
        # update original node
        node.children = {}
        node.matches = []
        node.children[newNodeOne.str[0]] = newNodeOne
        node.children[newNodeTwo.str[0]] = newNodeTwo
        node.str = node.str[0:index]


    def addNode(self, subString, id, parent):
        """
        Method to add substring under the root node
        Args:
          subString = The subString to add
          id = The id of the new string

        Returns: None
        """
        printDebug("adding node")
        # Append new node to root
        node = Node()

        self.id += 1
        node.id = self.id
        node.matches.append(id)
        node.str = subString
        parent.children[subString[0]] = node
        

    def dotGraph(self):
        """
        Debug method to dot a graph.
        Args:
          None
          
        Returns: None
        """

        fp = open("graph.dot", "w")
        fp.write("digraph{\n")

        # Create dot graph file
        self.traverseAndDot(fp, self.root, "")

        fp.write("}")
        fp.close()


    def traverseAndDot(self, fp, node, dotText):
        """
        Method to traverse the suffix tree and create a
        grap.dot file which will generate a graph using the
        dot program. 'dot -Tps graph.dot -o graph.ps'
        Args:
          fp = The file where we should write the graph
          node = The current node we are traversing
          dotText = The current text that we will use
                    determening what to write to the file

        Returns: None
        """

        nodeName = "%s%sNODE%d" % ("".join(node.str),
                               "".join(node.matches), node.id)

        if node.id != 0:
            dotText += " -> %s" % (nodeName)
            fp.write("%s;\n" % dotText)
        
        for child in node.children:
            self.traverseAndDot(fp, node.children[child], nodeName)


    def debugLoadPlaylistData(self):
        """
        Method to load playlist data used for testing
        the suffix tree implementation
        Args:
          None
        """
        testSet = []
        if os.path.isfile("playlist.pypl"):
            fp = open("playlist.pypl", "r", encoding='utf-8')
            data = fp.readlines()
            fp.close()

            for line in data:
                line = line.strip("\n")
                items = line.split("<")
                testSet.append("%s - %s" % (items[2], items[1]))
        else:
            print("Playlist not found in current directory")
            return []

        return testSet
    
if __name__ == "__main__":
    tree = Tree()
    testSet = tree.debugLoadPlaylistData()
    print("Starting indexing %d items" % len(testSet))

    start = time.time()
    for i in range(0, len(testSet)):
        tree.addString(testSet[i], "%d" % i)

    end = time.time()
    print("  time: %d" % (end - start))

    while(1):
        print("> ", end="")
        searchTerm = input()
        if searchTerm.lower() != "exit":
            results = tree.search(searchTerm)

            print("Matches (%d):" % len(results))
            for id in results:
                print(" - %s" % testSet[int(id)])
        else:
            break

    # Dot graph
    #tree.dotGraph()
