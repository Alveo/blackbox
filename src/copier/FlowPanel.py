import wx
import os
import random
import time
from math import ceil
import multiprocessing

import config
config.configinit()

from CopierFrame import PanelFinishedEvent


# needs better configuration
#IMAGE_DIR = "copier"
#NEW: this directory
IMAGE_DIR = os.path.dirname(os.path.abspath(__file__))


# status codes used for panel state
STATUS_READY = 0
STATUS_FINISHED = -1
STATUS_PAUSED = 1
STATUS_PROBLEM = 2

class FlowPanel(wx.Panel):

    pause_img = os.path.join(IMAGE_DIR, "pause.png")
    pause_icon = None
    rightarrow_img = os.path.join(IMAGE_DIR, "rightarrow.png")
    rightarrow_icon = None
    tick_img = os.path.join(IMAGE_DIR, "tick.png")
    tick_icon = None
    wrong_img = os.path.join(IMAGE_DIR, "wrong.png")
    wrong_icon = None

    status = STATUS_PAUSED
    cframe = None
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.Point(0,0), size=wx.Size(200,50), stepNumber=0, label=""):
        wx.Panel.__init__(self, parent, id=id, pos=pos, size=size, style=wx.TAB_TRAVERSAL|wx.NO_BORDER)
        self.rightarrow_icon = wx.Bitmap(self.rightarrow_img)
        self.tick_icon       = wx.Bitmap(self.tick_img)
        self.pause_icon      = wx.Bitmap(self.pause_img)
        self.wrong_icon      = wx.Bitmap(self.wrong_img)
        self.parent = parent
        self.SetBackgroundColour('WHITE')
        self.outerSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.statusBitmap = wx.StaticBitmap(self, bitmap=self.pause_icon)
        self.outerSizer.Add(self.statusBitmap)


        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Step ' + str(stepNumber) + (label and ": "+str(label) or "")), flag=wx.BOTTOM|wx.LEFT, border=5)
        self.outerSizer.Add(self.sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.NO_BORDER, border=10, proportion=1)
        self.SetSizer(self.outerSizer)
        self.messages = ""
        self.sizer.Fit(self)
        self.Show()
        
        # twp size counts used to keep track of progress, initialise to zero here
        self.totalSize = 0
        self.processedSize = 0
        self.initSpeed = 0
        self.start = 0
        self.updateEstimatedDuration()
        
        # flag to say whether we're done or not, set by finished()
        self._done = False

    def finished(self):
        """We've finished what we needed to do, let the next
        panel run"""

        self._done = True
        self.setStatus(STATUS_FINISHED)
        
        # post a PANEL_FINISHED event to the parent
        wx.PostEvent(self.parent, PanelFinishedEvent())
        
    def done(self):
        """Return True if this panel has done it's work"""
        
        return self._done

    def setStatus(self, status):
        """Update the status of this panel, show the
        relevant icon"""

        # only redraw if status changes
        if status == self.status:
            return
        
        self.status = status
        if status == STATUS_READY:
            statusImg = self.rightarrow_icon 
        elif status == STATUS_FINISHED:
            statusImg = self.tick_icon 
        elif status == STATUS_PAUSED:
            statusImg = self.pause_icon 
        elif status == STATUS_PROBLEM:
            statusImg = self.wrong_icon 
        self.statusBitmap.SetBitmap(statusImg)
        self.outerSizer.Layout()
        
    def setStatusMessage(self, label):
        """Update the status message to say that we're processing this file"""
        if self.start != 0:
            pendSeconds = self.estDuration - (time.time() - self.start)
            if pendSeconds < 0: pendSeconds = 0
            if random.random() > 0.5:
                label += " ..."
            self.parent.text.SetLabel(label % \
                            (pendSeconds > 60 and "%d minutes" % ceil(pendSeconds/60,) or "%d seconds" % ceil(pendSeconds)))
        else:
            self.parent.text.SetLabel(label)

    def updateEstimatedDuration(self):
        """Recalculate estimate of duration stored in self.estDuration
        based on how many items have been processed"""
        
        # size * speed (seconds per MB)
        if self.processedSize != 0:
            self.estDuration = self.totalSize * (time.time()-self.start)/self.processedSize
        else:
            self.estDuration = self.totalSize * self.initSpeed / \
                                    (multiprocessing.cpu_count() - int(config.config("MP_RESERVED", 1)))

        return self.estDuration

    def do(self):
        """The do method carries out the action for this step.
        It returns True if the action was successfully completed
        and False otherwise.
        It calls self.finished() when work is complete.
        """
        
        self.setStatus(STATUS_READY)
        return False

    def showMessages(self, evt):
        dial = wx.MessageDialog(self, self.messages, "Info", wx.OK)
        dial.ShowModal()
