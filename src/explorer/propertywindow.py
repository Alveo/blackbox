import os
import wx

from datahandling.RecordedItem import RecordedItem

class PropertyWindow(wx.TextCtrl):

    def __init__(self, publisher, parent, style):
        wx.TextCtrl.__init__(self, parent, style = style)
        self.Enable(0)
        
        # Setup the event handlers for this control
        self.publisher = publisher
        self.publisher.Bind(wx.EVT_TREE_SEL_CHANGED, self._onShowProperty, publisher)
        
    def _onShowProperty(self, evt):
        """ This event fires when the selected node on the publisher changes. The publisher in this
        case is the SessionNavigation class """
        itemData = self.publisher.GetItemData(evt.GetItem())
        treeNode = itemData.GetData()
        
        if treeNode and os.path.isfile(treeNode.path):
            self.Clear()
            self.Enable(False)
            self._parseXmlDocument(treeNode.path)
            self.SetInsertionPoint(0)
            self.SetFocus()
        else:
            self.Clear()
            self.Enable(False)
            
    def _parseXmlDocument(self, document):
        """ This method converts the properties in the XML document into a dictionary of
        key value pairs """
        path, basename = os.path.split(document)
        head, tail = os.path.splitext(basename)
        ri = RecordedItem(path, head)
        
        self.AppendText('Item Properties\n\n')
        for key, value in ri.iteritems():
            if isinstance(value, basestring):
                self.AppendText('  ' + key + ':\n\t' + value + '\n')
            elif isinstance(value, list):
                self.AppendText('  ' + key + ':\n')
                for item in value:
                    self.AppendText('\t' + item + '\n')
            elif isinstance(value, dict):
                self.AppendText('  ' + key + ':\n')
                for subkey, subvalue in value.iteritems():
                    self.AppendText('\t' + subkey + ': ' + subvalue + '\n')
                
    