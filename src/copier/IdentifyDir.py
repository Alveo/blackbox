import wx
from FlowPanel import *
import globals
import os.path
import os
import config; config.configinit()

class IdentifyDir(FlowPanel):
    def __init__(self, parent, stepNumber, dirLoc=".", name="Directory", validate=None):

        self.dirLoc = dirLoc
        self.confirmed = False
        self.validate = validate

        FlowPanel.__init__(self, parent, stepNumber=stepNumber, label="Identify "+name)

        self.dirLabel = wx.StaticText(self, wx.ID_ANY, self.dirLoc)
        self.modifyBtn = wx.Button(self, 10, "Choose Directory")
        self.confirmBtn = wx.Button(self, 11, "Confirm")

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.dirLabel, 1)
        sizer.Add(self.modifyBtn, 0)
        sizer.Add(self.confirmBtn, 0)

        self.sizer.Add(sizer, flag=wx.EXPAND|wx.RIGHT|wx.LEFT, border=20)

        def chooseDir(event):
            dd = wx.DirDialog(self, "Choose "+name, dirLoc)
            dd.ShowModal()
            self.dirLoc = dd.GetPath()
            self.dirLabel.SetLabel(self.dirLoc)


        self.Bind(wx.EVT_BUTTON, chooseDir, id=10)
        self.Bind(wx.EVT_BUTTON, self.confirm, id=11)
        
        self.disable_buttons()

    def enable_buttons(self):
        
        self.modifyBtn.Enable()
        self.confirmBtn.Enable()
            
    def disable_buttons(self):
        
        self.modifyBtn.Disable()
        self.confirmBtn.Disable()
        
        
    def confirm(self, evt):
        self.finished()

    def do(self):

        self.setStatus(STATUS_READY)
        self.enable_buttons()
        return True


class IdentifySourceDir(IdentifyDir):
    def __init__(self, parent, stepNumber):
            # default source is in config
        source = config.config("PATH_RECORDINGS")
        IdentifyDir.__init__(self, parent, stepNumber, source, name="Original Data Directory")

    def confirm(self, evt): 
        if not os.path.exists(self.dirLoc):
            wx.MessageDialog(
                      parent=None,
                      message='Source directory does not exist',
                              caption='Software Problem',
                              style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
                          ).ShowModal()

        else:
            globals.source = self.dirLoc 
            self.finished()

class IdentifyLocalTargetDir(IdentifyDir):
    def __init__(self, parent, stepNumber):
            # default target is in config
        target = config.config("PATH_FINAL")
        # make sure at least the default exists if we can
        if not os.path.exists(target):
            try:
                os.makedirs(target)
            except:
                pass

        IdentifyDir.__init__(self, parent, stepNumber, target, name="Compressed Data Directory")

    def confirm(self, evt): 
        if os.path.normcase(os.path.realpath(self.dirLoc)) == os.path.normcase(os.path.realpath(globals.source)):
            wx.MessageDialog(
                      parent=None,
                      message='Target directory must be different to source',
                              caption='Software Problem',
                              style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
                          ).ShowModal()
        else:
            globals.localTarget = self.dirLoc 
            self.finished()

