import wx
from FlowPanel import *
import globals
import os.path
import os

class Signal(FlowPanel):
    def __init__(self, parent, stepNumber, msg="Ready to Go?"):
        self.go = False
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.bttn = wx.Button(self,id=wx.ID_ANY,label=msg)

        # event for moving forward
        def go(evt):
            self.go = True
            self.cframe.redo(None)
            # disable the button once pressed
            self.bttn.Disable()


        self.bttn.Bind(wx.EVT_BUTTON, go)
        self.sizer.Add(self.bttn, flag=wx.BOTTOM|wx.LEFT, border=50)
        self.bttn.Disable()

    def do(self):
        if not self.go:
            self.bttn.Enable()
        return self.go
