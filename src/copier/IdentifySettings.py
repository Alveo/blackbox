import wx
from FlowPanel import *
import globals
import os.path
from recorder.Const import *
import os
import urllib2

import config
config.configinit()


class IdentifySettings(FlowPanel):
    """Identify globals.source, globals.localTarget, globals.host"""
    def __init__(self, parent, stepNumber):
        FlowPanel.__init__(self, parent, stepNumber=stepNumber, label="Detect configuration")
        self.parent = parent
        self.resultSpot = wx.StaticText(self, wx.ID_ANY, self.messages)
        self.sizer.Add(self.resultSpot, flag=wx.RIGHT|wx.LEFT, border = 20)

    def do(self):
 
        globals.host = config.config("HOST_FINAL", "echidna.science.mq.edu.au")
        
        # global error list, initialise here
        globals.errors = []
        
        self.messages = ""

        proto = config.config("PROTO", "https") 
        
        # check if host is alive
        try: 
            u = urllib2.urlopen(proto+"://%s/forms/reports/upload/real/" % (globals.host,)) #@UndefinedVariable 
            globals.canUpload = True
        except:
            globals.canUpload = False
            self.resultSpot.SetLabel("Can't contact server at %s\nUpload will not be possible." % globals.host) #@UndefinedVariable
            self.resultSpot.SetForegroundColour((255,0,0))
        else:
            self.resultSpot.SetLabel("Host server: %s" % globals.host) #@UndefinedVariable


        # check that we can see the camera calibration files
        PATH_CALIBRATION_FILES = config.config("PATH_CALIBRATION_FILES")
        if not os.path.exists(PATH_CALIBRATION_FILES):
            wx.MessageDialog(
                      parent=None,
                      message='Camera Calibration files directory %s does not exist.\n Compression will not be possible.' % PATH_CALIBRATION_FILES,
                              caption='Software Problem',
                              style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
                          ).ShowModal()
            globals.canCompress = False
        else:
            globals.canCompress = True


        self.setStatus(STATUS_READY)

        #self.parent.Layout()
        self.parent.Fit()
        
        if len(self.messages) == 0:
            self.finished()
            return True
        else:
            return False
