import wx
import globals
from FlowPanel import *

class TargetCheckSums(FlowPanel):
    def __init__(self, parent, stepNumber):
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Check validity of files on Target'), flag=wx.BOTTOM|wx.LEFT, border=5)

    def do(self):
        return True
