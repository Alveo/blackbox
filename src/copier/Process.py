import wx
from FlowPanel import *
import globals
import os.path
import os
from copier import *
from random import random

# weird - why is it not in copier.*
from copier.StatusCleanScript import StatusCleanScript

from datahandling.RecordedSession import session_list_item_generator

class Process(FlowPanel):
    def __init__(self, parent, stepNumber):

        FlowPanel.__init__(self, parent, stepNumber=stepNumber, label="Process data")

        self.btn_compress = wx.Button(self, 10, 'Compress')
        self.btn_upload = wx.Button(self, 11, 'Upload')
        self.btn_comprUpload = wx.Button(self, 12, 'Compress && Upload')
        self.btn_validate = wx.Button(self, 13, "Validate")
        self.cb_nocache = wx.CheckBox(self, -1, "Ignore stored validation results")
        self.disableButtons()

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.btn_compress, 1 )
        actions.Add(self.btn_upload, 1 )
        actions.Add(self.btn_comprUpload, 1 )
        actions.Add(self.btn_validate, 1)

        actions.setStatus = lambda x: x     # dummy

        self.sizer.Add(actions, flag=wx.EXPAND|wx.RIGHT|wx.LEFT, border=10)
        self.sizer.AddSpacer(5)

        self.errorsmsg = wx.TextCtrl(self, wx.ID_ANY, size=((0, 47)), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.errorsmsg.SetForegroundColour((255,0,0))

        self.sizer.Add(self.errorsmsg, flag=wx.EXPAND|wx.RIGHT|wx.LEFT, border=10)
        self.sizer.AddSpacer(5)

        self.sizer.Add(self.cb_nocache, flag=wx.EXPAND|wx.RIGHT|wx.LEFT, border=10)
        self.sizer.AddSpacer(5)

        self.Bind(wx.EVT_BUTTON, self.onCompress, id=10)
        self.Bind(wx.EVT_BUTTON, self.onUpload, id=11)
        self.Bind(wx.EVT_BUTTON, self.onCompressUpload, id=12)
        self.Bind(wx.EVT_BUTTON, self.onValidate, id=13)

        self.stepNumber = stepNumber
        self.parent = parent
 

    def addErrorMsg(self, errmsg, colour=None):
        if colour is not None:
            self.errorsmsg.SetForegroundColour(colour)
        if not self.errorsmsg.IsEmpty():
            self.errorsmsg.AppendText('\n')
        self.errorsmsg.AppendText(errmsg)
        #self.parent.Fit()


    def disableButtons(self):
        self.btn_compress.Disable()
        self.btn_upload.Disable()
        self.btn_comprUpload.Disable()
        self.btn_validate.Disable()
        self.cb_nocache.Disable()

    def enableButtons(self):
        """Enable the appropriate action buttons depending on
        the number of raw and compressed sessions we found"""

        
        if len(globals.comprSessions) > 0:
            self.btn_validate.Enable()
            self.cb_nocache.Enable()
        # compress if we have raw items
        if len(globals.rawSessions) != 0 and globals.canCompress:
            self.btn_compress.Enable()
        # upload if we can
        if len(globals.rawSessions) != 0 and globals.canUpload and globals.canCompress:
            self.btn_comprUpload.Enable()
        if len(globals.comprSessions) != 0 and globals.canUpload:
            self.btn_upload.Enable()

    def do(self):

        self.text = self.parent.statusMsg
        self.progress = self.parent.progressBar

        self.setStatus(STATUS_READY)

        self.enableButtons()
            
        return self.done()

    def scanFiles(self):
        """Scan for items, most of the work is left to a 
        generator but we still need to scan the file system so it
        may take some time if there are many sessions"""
    
        self.parent.statusMsg.SetLabel("Scanning files ...")

        globals.rawItems = session_list_item_generator(globals.rawSessions)
        globals.comprItems = session_list_item_generator(globals.comprSessions)

        globals.rawItemCount = sum([c.count_items() for c in globals.rawSessions])
        globals.comprItemCount = sum([c.count_items() for c in globals.comprSessions])

        # estimate the size of data we need to process
        avgRawSize = int(config.config("AVERAGE_RAW_ITEM_SIZE", 122))
        avgComprSize = int(config.config("AVERAGE_COMPR_ITEM_SIZE", 26))
        globals.rawSize = globals.rawItemCount * avgRawSize
        globals.comprSize = globals.comprItemCount * avgComprSize
        globals.totalSize = globals.rawSize + globals.comprSize

        self.parent.statusMsg.SetLabel("Scanning files ... Done")

        

    def onCompress(self, even):
        self.disableButtons()
        self.parent.toggleFinishInterrupt()
        self.scanFiles()
        cs = CompressionScript(self)
        n = cs.do()

        ss = StatusCleanScript(self, action="status")
        n = ss.do()

        self.parent.toggleFinishInterrupt()
        self.enableButtons()
        self.finished()


    def onValidate(self, even):
        
        # validate doesn't need the item list so we don't scanfiles here
        
        self.disableButtons()
        self.parent.toggleFinishInterrupt()

        ss = StatusCleanScript(self, action="status")
        n = ss.do()

        self.parent.toggleFinishInterrupt()
        self.enableButtons()
        self.finished()

    def onUpload(self, even):
        self.disableButtons()
        self.parent.toggleFinishInterrupt()
        self.scanFiles()
        us = UploadScript(self)
        n = us.do()

        """
        msg = "Finished uploading to the data server (%d/%d items)." % (n, len(globals.comprItems))
        self.text.SetLabel(msg)
        conf = wx.MessageDialog(self.parent, msg, "Upload finished", style=wx.OK|wx.ICON_INFORMATION)
        conf.ShowModal()
        conf.Destroy()
        """

        ss = StatusCleanScript(self, action="status")
        n = ss.do()

        self.parent.toggleFinishInterrupt()
        self.enableButtons()
        self.finished()

    def onCompressUpload(self, even):
        self.disableButtons()
        self.parent.toggleFinishInterrupt()
        self.scanFiles()
        cus = ComprUploadScript(self)
        c, u = cus.do()


        ss = StatusCleanScript(self, action="status")
        n = ss.do()

        self.parent.toggleFinishInterrupt()
        self.enableButtons()
        self.finished()
