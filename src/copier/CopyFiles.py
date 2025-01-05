import datetime
import os
import os.path
import globals
from FlowPanel import *
import shutil

class CopyFiles(FlowPanel):
    def __init__(self, parent, stepNumber):
        import wx
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Copy from Source to Target'), flag=wx.BOTTOM|wx.LEFT, border=5)

    def do(self):
        self.setStatus(STATUS_READY)
        try:
            shutil.copytree(globals.localTarget, os.path.join(globals.remoteTarget, str(datetime.datetime.utcnow())))
        except shutil.Error as err:
            self.setStatus(STATUS_PROBLEM)
            self.messages = ("copying tree failed\n " + str(err))
            return False
        return True
