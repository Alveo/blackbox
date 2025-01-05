import re
import globals
import os
import os.path
from FlowPanel import *
import config
from process_site import _status
import wx.lib.dialogs
import shutil
import multiprocessing
import datahandling

# TODO: put poolSafe somewhere better (more logical)
from copier.UploadScript import poolSafe

config.configinit()


def poolValidateCompr(args):
    return poolSafe(_poolValidateCompr, (args,))

def _poolValidateCompr(args):
    # args = (session, host, nocache)
    session = args[0]
    host = args[1]
    nocache = args[2]

    print "Validating compressed session", session

    comprText = "<ul>"
    compressed = False
    uploaded = False

    (errors, warnings) = session.validate_files(nocache=nocache)

    if len(warnings) > 0:
        comprText += "<li><strong>%s has warnings</strong>:\n" % session
        comprText += "<ul>"
        for w in warnings:
            comprText += "<li>%s</li>" % w
        comprText += "</ul>\n"

    if len(errors) > 0:
        comprText += "<li><strong>%s contains errors in compression, please re-run compress</strong>:\n" % session
        comprText += "<ul>"
        for e in errors:
            comprText += "<li>%s</li>" % e
        comprText += "</ul>\n"
        print "Compressed session", session, "has compression errors"
    else:
        # ok. we compressed ok, we'll validate the uploaded version on the server
        # don't report warnings as they are already displayed above - should be the same
        compressed = True
        uploaded, errors, warnings = session.uploaded(host)
        if uploaded:
            comprText += "<li>%s \t uploaded successfully</li>\n" % session
            print "Compressed session", session, "compressed and uploaded ok"
        else:
            if errors:
                comprText += "<li><strong>%s: compressed ok but has errors in uploaded data, please re-upload this session:</strong>\n" % session
                comprText += "<ul>"
                for e in errors:
                    comprText += "<li>%s</li>" % e
                comprText += "</ul>\n"
                comprText += "</li>\n"
                print "Compressed session", session, "compressed ok but errors in upload"
            else:
                comprText += "<li>%s \t not yet uploaded</li>\n" % session
                print "Compressed session", session, "not yet uploaded"

    comprText += "</ul>\n"
    
    return (session, comprText, compressed, uploaded)


class StatusCleanScript(FlowPanel):


    # static variable to cache already validated sessions
    validatedCompr = []

    def __init__(self, parent, action):
        FlowPanel.__init__(self, parent) 
        self.action = action


    def do(self): 

        self.parent.setStatus(STATUS_READY)

        mp_processes = int(config.config("MP_PROCESSES", 3))
        mp_timeout = float(config.config("MP_TIMEOUT", 0.01))       # for periodical checking whether a subprocess has finished

        validationWorkers = mp_processes 

        pool = multiprocessing.Pool(processes=validationWorkers)
        self.parent.parent.pools.append(pool)
        print "Initializing %d validation worker(s)" % validationWorkers

        self.parent.parent.progressBar.SetRange(len(globals.rawSessions))
        i = 0

        # compressed sessions
        comprText = "<p>"
        comprText += "Compressed data directory: %s</p>\n\n" % globals.localTarget
        forBackup = []
        uplNum = 0

        
        # scan again for compressed sessions that we can validate    
        # don't rely on earlier scans since they will be out of date
        (comprSessions, errors) = datahandling.find_existing_sessions(globals.localTarget)
        
        validatedSessions = pool.imap_unordered(poolValidateCompr, \
                        [ (session, globals.host, self.parent.cb_nocache.GetValue()) for session in comprSessions ] )

        while True:
            self.parent.parent.progressBar.SetValue(i)
            #wx.Yield()
            
            try:
                session, comprTextPart, compressed, uploaded = validatedSessions.next(mp_timeout)
            except multiprocessing.TimeoutError:
                continue
            except StopIteration:
                break

            comprText += comprTextPart
            if uploaded:
                forBackup.append(session.full_path())
                uplNum += 1

            i += 1
            self.parent.parent.statusMsg.SetLabel("Finished validating compressed session `%s'" % session)


        if len(globals.errors) > 0:
            errorText = "<h2>Errors During Processing</h2><ul>"
            for error in globals.errors:
                errorText += "<li>" + error + "</li>"
            errorText = "</ul>"
        else:
            errorText = ""


        comprText += "\n<p>%d out of %d sessions have been successfully uploaded.</p>\n\n" % (uplNum, len(globals.comprSessions))
        
        if self.action != "statusClean":
            reportTpl = """<html>
            <body>
    <h1>Validation Report</h1>

    %(errors)s

    <h2>Compressed Sessions</h2>

    %(compr)s

    <hr>
    <p>If you don't understand any parts of the above report,
    copy the text and send it in an email with your query to
    Steve.Cassidy@mq.edu.au.</p>
    </body>
    </html>"""

            report = reportTpl % { 'compr': comprText, 'errors': errorText}

            # present the report in a scrollable text box
            # with options to copy the text and dismiss the window

            htmlMessageWindow(None, report)

        self.finished()
        return i


import  wx.html
from wx.lib.scrolledpanel import ScrolledPanel

def htmlMessageWindow(parent, page):
        #Display an HTML page in a scrolling window

    frame = wx.Frame(parent, size=(600,400))
    panel = ScrolledPanel(frame)

    sizer = wx.BoxSizer(wx.VERTICAL)
    buttonszr = wx.BoxSizer(wx.HORIZONTAL)

    okbtn = wx.Button(panel, 2, "Close Window")
    copybtn = wx.Button(panel, 3, "Copy Text")

    html1 = wx.html.HtmlWindow(panel, 1)
    html1.SetPage(page)

    def handle_ok(ev):
        frame.Destroy()

    def handle_copy(ev):
        html1.SelectAll()
        if not wx.TheClipboard.IsOpened():
            wx.TheClipboard.Open()
            clip = wx.TextDataObject()
            clip.SetText(html1.ToText())
            wx.TheClipboard.SetData(clip)
            wx.TheClipboard.Close()

    okbtn.Bind(wx.EVT_BUTTON, handle_ok)
    copybtn.Bind(wx.EVT_BUTTON, handle_copy)

    buttonszr.Add(okbtn, 0, wx.EXPAND, 0)
    buttonszr.Add(copybtn, 0, wx.EXPAND, 0)

    sizer.Add(html1, 1, wx.EXPAND, 5)
    sizer.Add(buttonszr, 0, wx.ALIGN_CENTRE, 15)

    panel.SetSizer(sizer)
    panel.SetAutoLayout(1)
    panel.SetupScrolling()

    frame.Show()
    html1.SetFocus()
