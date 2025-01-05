import wx
from FlowPanel import *
import globals
import os.path
import os

class IdentifyHost(FlowPanel):
    
    def __init__(self, parent, stepNumber, host="echidna.science.mq.edu.au"):
        self.host = host
        self.parent = parent
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Locate Directory ' + host), flag=wx.RIGHT|wx.LEFT, border=10)
        self.resultSpot = wx.StaticText(self, wx.ID_ANY, '')
        self.sizer.Add(self.resultSpot, flag=wx.RIGHT|wx.LEFT, border = 10)

    def do(self):

        self.finished()
        return True


