import wx
from FlowPanel import *
import globals
import os.path
import os

class Finish(FlowPanel):
    def __init__(self, parent, stepNumber):
        self.go = False
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.parent = parent
        self.parent.finishBtn = wx.Button(self,id=wx.ID_ANY,label="Finish")
        self.parent.interruptBtn = wx.Button(self,id=wx.ID_ANY,label="Interrupt")
        self.parent.interruptBtn.Disable()

        actions = wx.BoxSizer(wx.HORIZONTAL)

        # event for moving forward
        def go(evt):
            self.finished()
            # disable the button once pressed
            self.parent.exit()


        self.parent.finishBtn.Bind(wx.EVT_BUTTON, go)
        actions.Add(self.parent.finishBtn, 1)

        self.parent.interruptBtn.Bind(wx.EVT_BUTTON, go)
        actions.Add(self.parent.interruptBtn, 1)

        self.sizer.Add(actions, flag=wx.EXPAND|wx.RIGHT|wx.LEFT, border=10)

    def do(self):
        self.setStatus(STATUS_READY)
        self.finished()
        return True
