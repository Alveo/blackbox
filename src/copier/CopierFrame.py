import wx
import string
import os
import os.path

import globals
import signal

from recorder.Const import *

# create a new event type to be triggered when a panel has done it's work
import wx.lib.newevent
PanelFinishedEvent, EVT_PANEL_FINISHED = wx.lib.newevent.NewEvent()

class CopierFrame(wx.Frame):
    currentPanel = 0
    panels = []
    exiting = False
    pools = []
    statusMsg = None
    progressBar = None
    finishBtn = None
    interruptBtn = None

    def __init__(self, parent, panels, title):
        wx.Frame.__init__(self, parent, title=title, size=(600,700))

        self.panels = []
        for step in range(len(panels)):
            self.panels.append(panels[step](self, stepNumber=step+1))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        for p in self.panels:
            sizer.Add(p, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
            sizer.AddSpacer(10)

        # progress bar
        self.progressBar = wx.Gauge(parent=self)
        sizer.Add(self.progressBar, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        sizer.AddSpacer(5)
        # status bar
        self.statusMsg = wx.StaticText(self, wx.ID_ANY, "Idle")
        sizer.Add(self.statusMsg, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=20)
        sizer.AddSpacer(5)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetBackgroundColour('WHITE')

        # bind ctrl-c event and other signals
        signal.signal(signal.SIGINT, self.__exitSignal)
        signal.signal(signal.SIGABRT, self.__exitSignal)
        signal.signal(signal.SIGTERM, self.__exitSignal)
        # bind window close event
        self.Bind(wx.EVT_CLOSE, self.__exit)

        self.Bind(EVT_PANEL_FINISHED, self.next_panel)
        
        
        self.Show(True)
        self.Centre()

        # start the first panel running
        self.next_panel()

    def setSessions(self, sessions):
        """Set the sessions list for this instance"""

        self.sessions = sessions

    def getSessions(self):
        """Return the sessions list for this instance"""

        return self.sessions

    def next_panel(self, evt=None):
        """Event handler for the EVT_PANEL_FINISHED event
        run the next panel"""

        for p in self.panels:
            if not p.done():
                p.do()
                return

    def toggleFinishInterrupt(self):
        if self.finishBtn != None and self.interruptBtn != None:
            if self.finishBtn.Enabled:
                self.finishBtn.Disable()
                self.interruptBtn.Enable()
            else:
                self.finishBtn.Enable()
                self.interruptBtn.Disable()

    def __exit(self, event):
        self.exit()

    def __exitSignal(self, signo, frame):
        self.exit(signo == signal.SIGABRT or signo == signal.SIGTERM or self.exiting)

    def exit(self, kill=False):
        # it somehow get blocked when trying to not terminate the subprocesses
        # possibly the subprocesses also receive Ctrl^C or something like that.
        # or possibly some wx weird thing, maybe calling wx.Yield() would help
        if len(self.pools) > 0:
            if True or kill or self.exiting:
                print "Killing all subprocesses and exiting ..."
                # block signals
                signal.signal(signal.SIGABRT, signal.SIG_IGN)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                # terminate pending subprocesses
                map(lambda x: x.terminate(), self.pools)
            else:
                # unused for now
                self.exiting = True
                print "Waiting for subprocesses to finish and exiting ..."
                # wait for all subprocesses to finish
                map(lambda x: x.close(), self.pools)
                map(lambda x: x.join(), self.pools)

        self.Destroy()
        quit(0)
