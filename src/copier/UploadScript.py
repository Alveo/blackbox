import re
import globals
import os
import os.path
import datetime
import shutil
from FlowPanel import *
import config
from time import time
import traceback
import sys

import multiprocessing

from process_site import *
from datahandling.RecordedSession import RecordedSession

config.configinit()

debug = config.config("DEBUG", "No") != "No"


def poolSafe(func, args):
        # gets a function + arguments
        # apply function on arguments, if debug and there is an exception, print full (real) stacktrace 
        #+(even if it's inside of multiprocessing)
        if not debug:
                return func(*args)
        else:
                try:
                        return func(*args)
                except:
                        traceback.print_exc(10)
                        raise


def poolUpload(args):
    # args = (item, host, logfile, retries), optionally args = (item, host, logfile, size of raw data, retries)
    success, failed = poolSafe(args[0].upload_files, (args[1], args[2]))

    if len(args) == 4:
        return (success, failed, args[0], args[3])
    else:
        return (success, failed, args[0], args[3], args[4])

def poolManifest(args):
    # args = (session, raw items dir, host)
    # if the manifest doesn't exist, regenerate it
    if not os.path.exists(args[0].manifest_path()):
        # it will not get copied during the video conversion because we're using
        #+items, not sessions
        poolSafe(args[0].gen_manifest, (False, args[1]))
        #args[0].gen_manifest(isRawDir=False, rawDir=args[1])

    poolSafe(args[0].upload_manifest, (args[2],))
    return args[0].basename

def poolSilence(args):
    # args = (raw items dir, compressed items dir, host)
    # copy the file if it's not there yet
    poolSafe(copy_silence, (args[0], args[1]))
    return poolSafe(upload_silence, (args[1], args[2]))


def poolCalibration(args):
    # args = (raw items dir, compressed items dir, host)
    # copy the file if it's not there yet
    poolSafe(copy_calibration, (args[0], args[1]))
    return poolSafe(upload_calibration, (args[1], args[2]))


class UploadScript(FlowPanel):
    def __init__(self, parent):

        FlowPanel.__init__(self, parent) 
        self.setStatusMessage('Uploading to the data server ...')

    def do(self): 

        max_retries = int(config.config("MAX_RETRIES", 3))
        mp_timeout = float(config.config("MP_TIMEOUT", 0.01))       # for periodical checking whether a subprocess has finished
        mp_processes = int(config.config("MP_PROCESSES", 3))
        uploadWorkers = mp_processes

        pool = multiprocessing.Pool(processes=uploadWorkers)
        self.parent.parent.pools.append(pool)

        print "Initializing %d upload worker(s)" % uploadWorkers

        yellow = (255,165,0)
        red = (255,0,0)

        self.parent.setStatus(STATUS_READY)

        # we will be processing the compressed data only
        self.totalSize = globals.comprSize

        self.parent.progress.SetRange(self.totalSize*1000)

        logfile = os.path.join(globals.localTarget, globals.logLocation)
        print "logging to ", logfile

        n = 0
        i = 1

        # time estimate initialization
        self.initSpeed = int(config.config("UPLOAD_SPEED", 713))    # in seconds

        # upload silence files
        otherItems = [ pool.apply_async(poolSilence, ((globals.source, globals.localTarget, globals.host),)) ]
        # upload calibration files
        otherItems.append(pool.apply_async(poolCalibration, ((globals.source, globals.localTarget, globals.host),)))
        # upload manifest files (use rawSessions to check whether compression copied all files)
        # upload twice in case something went wrong with the first upload
        #TODO:
        otherItems += map(lambda session: pool.apply_async(poolManifest, ((session, globals.source, globals.host),)), \
                                    globals.comprSessions + globals.comprSessions)

        # upload data items
        procItems = pool.imap_unordered(poolUpload, [ (item, globals.host, logfile, 1) for item in globals.comprItems ] )

        self.start = time()
        self.updateEstimatedDuration()
        forRetry = []

        while True:
            if i*mp_timeout > 1:        # do this only about once a second
                self.setStatusMessage("Uploaded %d/%d items, " % (n, globals.comprItemCount) + "%s remaining")
                i = 0

            self.parent.progress.SetValue(self.processedSize*1000)
            #wx.Yield()
            i += 1

            try:
                success, failed, item, retries = procItems.next(mp_timeout)
            except multiprocessing.TimeoutError:
                continue
            except StopIteration:
                # if there are items for retry, process them
                if len(forRetry) > 0:
                    procItems = pool.imap_unordered(poolUpload, forRetry)
                    forRetry = []
                else:
                    break

            if not success:
                if retries < max_retries:
                    failmessage = ""
                    for msg in failed:
                        # include the failure message from the server
                        if len(msg) == 2:
                            failmessage += msg[1][:77] + "\n"
                        else:
                            failmessage += str(msg)

                    forRetry.append((item, globals.host, logfile, retries+1))
                    self.parent.addErrorMsg("Warning: Failed to upload item %s! (trying %d more times)" \
                                    % (item.basename, max_retries - retries), yellow)
                else:
                    message = "Error: Failed to upload item %s\nReason: %s" % (item.basename, failmessage)
                    self.parent.addErrorMsg(message, red)
                    
                    globals.errors.append(message)
                    print message
            else:
                n += 1

            self.processedSize += item.getsize()
            self.updateEstimatedDuration()

        # possibly wait for all the manifest, calibration and silence files
        self.parent.text.SetLabel("Waiting for the silence, manifest and calibration uploads to finish ...")
        while len(otherItems) > 0:
            #wx.Yield()
            u = otherItems.pop()
            try:
                u.get(mp_timeout)
            except multiprocessing.TimeoutError:
                otherItems.insert(random.randrange(0, len(otherItems)+1), u)

        self.parent.text.SetLabel("Upload finished in %d seconds" % (time()-self.start,))

        print "Notice: finished uploading in %d seconds." % (time()-self.start,)

        if (len(self.parent.errorsmsg.GetLabel()) != 0):
            self.parent.setStatus(STATUS_PROBLEM)
        else:
            self.finished()

        return n
