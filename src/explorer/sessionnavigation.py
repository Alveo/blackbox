import os
import wx

from translator import Translator
from treenode import TreeNode

class SessionNavigation(wx.TreeCtrl):
    """
    This class is used to represent the actual tree
    """
    def __init__(self, parent, startingPoint):
        """ Class constructor """
        wx.TreeCtrl.__init__(self, parent, wx.ID_ANY)
        self.translator = Translator()       
        self.render(startingPoint)
        
    def render(self, rootDir):
        """ This method walks the tree and adds the directories and files to the tree """
        self.DeleteAllItems()

        if rootDir == "":
            self.AddRoot("Please choose a directory from the File menu")
            return
        
        root = self.AddRoot(rootDir)
            
        self._renderChildren(root, rootDir)
   
    def _renderChildren(self, parent, child):
        """ Recursive function which builds the directory structure """
        try:
            dirlisting = os.listdir(child)
        except:
            # if we don't have permission etc.
            dirlisting = []
            
        for listing in dirlisting:
            pathinquestion = os.path.join(child, listing)
            # Only xml documents (i.e. metadata is added to the tree as a leaf
            # node
            if os.path.isfile(pathinquestion):
                extension = os.path.splitext(pathinquestion)
                extension = extension[1]
                if extension == ".xml":
                    self._appendItem(parent, pathinquestion, listing)
            # If we encounter a directory then we need to recursively
            # call this function to build the tree
            elif os.path.isdir(pathinquestion):
                newparent = self._appendItem(parent, pathinquestion, listing)               
                newdir = os.path.join(child, listing)
                self._renderChildren(newparent, newdir)
                  
    def _appendItem(self, parent, path, value):
        """ This function appends a node to a tree, the node could also be
        a leaf item. """
        translatedValue = self.translator.translate(value)
        if translatedValue:
            treeNode = TreeNode(path, translatedValue)
            return self.AppendItem(parent, translatedValue, data = wx.TreeItemData(treeNode) )
        else:
            treeNode = TreeNode(path, value)   
            return self.AppendItem(parent, value, data = wx.TreeItemData(treeNode))