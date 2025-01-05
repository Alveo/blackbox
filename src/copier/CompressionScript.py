import re
import globals
import os
import os.path
import datetime
import shutil
from FlowPanel import *
import config
from datahandling import RecordedSession
from videoconvert import clear_temp_files
from time import time
import random
import multiprocessing

# TODO: put poolSafe somewhere better (more logical)
from copier.UploadScript import poolSafe

config.configinit()


def poolComprUpload(args):
    success, newFiles, errors = poolSafe(args[0].convert_video_and_upload, (args[1], args[2], args[3]))
    return (success, newFiles, errors, args[0], args[4])


def poolCompr(args):
    # args = (item, localTarget, logfile, retries)
    success, newFiles, errors = poolSafe(args[0].convert_video, (args[1], args[2]))
    return (success, newFiles, errors, args[0], args[3])

def poolGenManifest(args):
    # args = (session, sourceDir, destDir)
    if os.path.exists(os.path.join(args[2], args[0].basename)):
        # ignore sessions that were not created properly
        rs = poolSafe(RecordedSession, (args[2], args[0].basename))
        poolSafe(rs.gen_manifest, (False, args[1]))
    return

class CompressionScript(FlowPanel):
    def __init__(self, parent):
        FlowPanel.__init__(self, parent)
        self.setStatusMessage('Compressing data ...')

    def do(self):

        max_retries = int(config.config("MAX_RETRIES", 3))
        mp_processes = int(config.config("MP_PROCESSES", 3))
        mp_timeout = float(config.config("MP_TIMEOUT", 0.01))       # for periodical checking whether a subprocess has finished


        # clear up any old temporary files
        clear_temp_files()

        comprWorkers = mp_processes

        pool = multiprocessing.Pool(processes=comprWorkers)
        self.parent.parent.pools.append(pool)

        print "Initializing %d compressions worker(s)" % comprWorkers

        yellow = (255,165,0)
        red = (255,0,0)

        self.parent.setStatus(STATUS_READY)

        # we'll process just the raw data
        self.totalSize = globals.rawSize #@UndefinedVariable
        self.parent.progress.SetRange(self.totalSize*1000)

        logfile = os.path.join(globals.localTarget, globals.logLocation)
        print "logging to ", logfile

        n = 0
        i = 0

        # time estimate initialization
        self.initSpeed = int(config.config("COMPRESSION_SPEED", 60))        # in seconds
        
        procItems = pool.imap_unordered(poolCompr, [ (item, globals.localTarget, logfile, 1) for item in globals.rawItems ] ) #@UndefinedVariable

        self.start = time()
        self.updateEstimatedDuration()
        forRetry = []

        while True:
            if i*mp_timeout > 1:        # do this only about once a second
                self.setStatusMessage("Compressed %d/%d items, " % (n, globals.rawItemCount) + "%s remaining") #@UndefinedVariable
                i = 0

            self.parent.progress.SetValue(self.processedSize*1000)
            #wx.Yield()
            i += 1

            try:
                success, newFiles, errors, item, retries = procItems.next(mp_timeout)
            except multiprocessing.TimeoutError:
                continue
            except StopIteration:
                # if there are items for retry, process them
                if len(forRetry) > 0:
                    procItems = pool.imap_unordered(poolCompr, forRetry)
                    forRetry = []
                else:
                    break

            if not success:
                if retries < max_retries:
                    forRetry.append((item, globals.localTarget, logfile, retries+1))
                    self.parent.addErrorMsg("Warning: Failed to compress item %s (trying %d more times)" \
                                        % (item.get_base_name(), max_retries - retries, errors), yellow)
                else:
                    message = "Error: Failed to compress item %s, tried %s times\nReason: %s" % (item.get_base_name(), max_retries, errors)
                    self.parent.addErrorMsg(message, red)
                    globals.errors.append(message)
            else:
                n += 1

            self.processedSize += item.getsize()
            self.updateEstimatedDuration()

        # generate/copy manifests
        otherItems = map(lambda session: pool.apply_async(poolGenManifest, ((session, globals.source, globals.localTarget),)), \
                                    globals.rawSessions ) #@UndefinedVariable
        self.parent.text.SetLabel("Waiting for the manifests to be generated ...")
        while len(otherItems) > 0:
            #wx.Yield()
            c = otherItems.pop()
            try:
                c.get(mp_timeout)
            except multiprocessing.TimeoutError:
                otherItems.insert(random.randrange(0, len(otherItems)+1), c)
 

        print "Notice: finished compressing in %d seconds." % (time()-self.start,)

        if (len(self.parent.errorsmsg.GetLabel()) != 0):
            self.parent.setStatus(STATUS_PROBLEM)
        else:
            self.finished()

        return n
