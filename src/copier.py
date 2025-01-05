import wx
import signal

from copier import *
from recorder.Const import *
import config

import multiprocessing

app = wx.App(redirect=False)

panels = [ IdentifySettings,
           IdentifySourceDir,
           IdentifyLocalTargetDir,
           IdentifySessions,
           Process,
           #CleanerProcess,
           Finish,
         ]

multiprocessing.freeze_support()

frame = CopierFrame(None, panels, "BigASC data processing version %s" % config.config("VERSION", "Unknown"))

app.MainLoop()
