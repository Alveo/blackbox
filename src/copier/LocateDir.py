import wx
from FlowPanel import *
import globals
import os.path
import os

class LocateDir(FlowPanel):
    def __init__(self, parent, stepNumber, dirType="Source"):
        import wx
        self.dirType = dirType
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Locate ' + dirType), flag=wx.BOTTOM|wx.LEFT, border=5)

        lowerSizer = wx.BoxSizer(wx.HORIZONTAL)
        dirDialog = wx.DirDialog(self, "Choose "+ dirType +" Directory", "/Users/mattr/elsewhere/atc", style=wx.DD_DIR_MUST_EXIST)
        self.textCtrl = wx.TextCtrl(self)
        bttn = wx.Button(self,id=wx.ID_ANY,label="Choose Dir")

        # event for selecting a directory
        def showDialog(evt):
            res = dirDialog.ShowModal()
            if (res == dirDialog.GetAffirmativeId()):
                self.textCtrl.SetValue(dirDialog.GetPath())
                # don't need to try and jump from here because the change tot he value of textCtrl will trigger an attempt to jump
                #print 'trying to jump from show dialog'
                #self.tryToJump(None)

        bttn.Bind(wx.EVT_BUTTON, showDialog)

        lowerSizer.Add(self.textCtrl, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT, border=5, proportion=1)
        lowerSizer.AddSpacer(10)
        lowerSizer.Add(bttn, flag=wx.RIGHT, border=50)
        self.sizer.Add(lowerSizer)

        # capturing other events
        def textChanged(evt):
            if (self.dirType == "Source"):
                globals.source = self.textCtrl.GetValue()
            elif (self.dirType == "Local Target"):
                globals.localTarget = self.textCtrl.GetValue()
            else:
                globals.remoteTarget = self.textCtrl.GetValue()
            self.cframe.redo(evt)

        self.textCtrl.Bind(wx.EVT_TEXT, textChanged)
        self.textCtrl.SetValue("/Users/mattr/elsewhere/atc/sample_data/correct/")
        self.cframe.redo(None)

    def do(self):
        self.setStatus(STATUS_READY)
        val = self.textCtrl.GetValue()
        if (os.path.isdir(val)):
            messages = ""
            if (self.dirType=="Target"):
                #directory must be empty
                lst = []
                try:
                    lst = os.listdir(val)
                except:
                    self.messages = "permission error"
                    self.setStatus(STATUS_PROBLEM)
                    return False
                print lst
                if (len(lst) == 0):
                    return True
                else:
                    self.messages = "Target directory is not empty"
                    self.setStatus(STATUS_PROBLEM)
                    return False
            elif (self.dirType == "Local Target"):
                lst = []
                lst2 = []
                try:
                    lst = os.listdir(val)
                    lst2 = os.listdir(os.path.join(val, "finalised"))
                except:
                    self.messages = "permission error or there is no finalised directory"
                    self.setStatus(STATUS_PROBLEM)
                    return False
                print lst
                if (((lst == ['finalised']) | (lst == ['finalised', 'log.txt'])) & (lst2 == ['audio', 'video'])):
                    return True
                else:
                    self.messages = "Target directory is does not have right structure"
                    self.setStatus(STATUS_PROBLEM)
                    return False

            return True
        else:
            self.messages = "not a directory"
            self.setStatus(STATUS_PROBLEM)
            return False
