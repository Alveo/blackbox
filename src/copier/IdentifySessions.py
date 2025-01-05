import wx
import string
import os
import os.path

import globals
from FlowPanel import *
import datahandling


class IdentifySessions(FlowPanel):
    def __init__(self, parent, stepNumber):
        FlowPanel.__init__(self, parent, stepNumber=stepNumber, label="Identify sessions")
        #self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Locate Sessions'), flag=wx.BOTTOM|wx.LEFT, border=5)
        self.parent = parent
        self.resultSpot1 = wx.StaticText(self, wx.ID_ANY, '')
        self.sizer.Add(self.resultSpot1, flag=wx.RIGHT|wx.LEFT, border = 20)
        self.sizer.AddSpacer(5)
        self.resultSpot2 = wx.StaticText(self, wx.ID_ANY, '')
        self.sizer.Add(self.resultSpot2, flag=wx.RIGHT|wx.LEFT, border = 20)
        self.sizer.AddSpacer(5)
        globals.rawSessions = []
        globals.comprSessions = []


    def do(self):
        self.parent.toggleFinishInterrupt()
        self.setStatus(STATUS_READY)

        # don't repeat this if we already scanned for sessions
        if globals.rawSessions == [] and globals.comprSessions == []: #@UndefinedVariable
            print "Finding sessions in ", globals.source, globals.localTarget
            (ss1, errors1) = datahandling.find_existing_sessions(globals.source)
            (ss2, errors2) = datahandling.find_existing_sessions(globals.localTarget)
    
            if errors1:
                print "Errors found: data for compression: ", errors1
                self.finished()
            if errors2:
                print "Errors found: data for upload: ", errors2
                self.finished()
    
            globals.rawSessions = ss1
            globals.comprSessions = ss2

            self.resultSpot1.SetLabel("Found " + str(len(globals.rawSessions)) + " raw session" + (len(globals.rawSessions) != 1 and "s" or "")) #@UndefinedVariable
            
            if len(globals.rawSessions) == 0:  #@UndefinedVariable
                self.resultSpot1.SetForegroundColour((255,0,0))
                
            self.resultSpot2.SetLabel("Found " + str(len(globals.comprSessions)) + " compressed session" + (len(globals.comprSessions) != 1 and "s" or "")) #@UndefinedVariable
    
            self.parent.toggleFinishInterrupt()
            if (len(errors1) > 0 or len(errors2) > 0):
                more = ""
                if (len(errors1) > 0 or len(errors2) > 0) : more = " ..."
                self.messages = len(errors1) > 0 and errors1[0] or "" + len(errors2) > 0 and errors2[0] or "" + more
                self.setStatus(STATUS_PROBLEM)
                return False
            else:
                self.messages = ""
                self.finished()
                return True
        else:
            self.finished()
            return True