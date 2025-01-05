import wx
from FlowPanel import *

class RemoveTarget(FlowPanel):
    def __init__(self, parent, stepNumber):
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Eject Target'), flag=wx.BOTTOM|wx.LEFT, border=5)
        self.extraText = wx.StaticText(self, wx.ID_ANY, 'You may now eject the remote target')
        self.sizer.Add(self.extraText, flag=wx.BOTTOM|wx.LEFT, border=5)
        self.bttn = wx.Button(self,id=wx.ID_ANY,label="Done")
        self.sizer.Add(self.bttn, flag=wx.LEFT|wx.BOTTOM, border=5)
        self.extraText.Hide()
        self.bttn.Hide()
        self.sizer.Fit(self)
        def bttnClick(evt):
            self.cframe.exit()
        self.bttn.Bind(wx.EVT_BUTTON, bttnClick)

    def do(self):
        self.extraText.Show(True)
        self.bttn.Show(True)
        return False
