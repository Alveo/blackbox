import wx
from FlowPanel import *
import globals
import os.path
import os
from copier import *

# weird - why is it not in copier.*
from copier.StatusCleanScript import StatusCleanScript


class CleanerProcess(FlowPanel):
    def __init__(self, parent, stepNumber):

        FlowPanel.__init__(self, parent, stepNumber=stepNumber, label="Clean data")

        self.btn_clean = wx.Button(self, 21, 'Free processed data')
        self.disableButtons()

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.btn_clean, 1 )

        actions.setStatus = lambda x: x     # dummy

        self.sizer.Add(actions, flag=wx.EXPAND|wx.RIGHT|wx.LEFT, border=10)

        self.Bind(wx.EVT_BUTTON, self.onClean, id=21)

        self.stepNumber = stepNumber
        self.parent = parent


    def disableButtons(self):
        self.btn_clean.Disable()
        wx.Yield()

    def enableButtons(self):
        self.btn_clean.Enable()
        #wx.Yield()

    def do(self):
        self.setStatus(STATUS_READY)

        if len(globals.rawSessions) + len(globals.comprSessions) > 0:
            self.btn_clean.Enable()

        return True

    def onStatus(self, even):
        self.disableButtons()
        self.parent.toggleFinishInterrupt()
        ss = StatusCleanScript(self, action="status")
        n = ss.do()
        self.parent.toggleFinishInterrupt()
        self.enableButtons()
        self.finished()

    def onClean(self, even):
        self.disableButtons()
        self.parent.toggleFinishInterrupt()
        cs = StatusCleanScript(self, action="statusClean")
        n = cs.do()
        self.parent.toggleFinishInterrupt()
        self.enableButtons()
        self.finished()
