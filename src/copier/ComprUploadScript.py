import re
import globals
import os
import os.path
import datetime
import shutil
from FlowPanel import *
from datahandling import RecordedItem, RecordedSession
from videoconvert import clear_temp_files
from time import time

import random

import config

import multiprocessing
from copier.UploadScript import poolUpload, poolCalibration, poolSilence, poolManifest
from copier.CompressionScript import poolCompr, poolComprUpload, poolGenManifest

config.configinit()
max_retries = int(config.config("MAX_RETRIES", 3))

yellow = (255,165,0)
red = (255,0,0)

logfile = os.path.join(globals.localTarget, globals.logLocation)


class ComprUploadScript(FlowPanel):
    def __init__(self, parent):
        FlowPanel.__init__(self, parent)
        self.setStatusMessage('Compressing and uploading to the data server ...')

    def handleUploadedItems(self, items, forUploadRetry):
        num = 0
        for success, failed, item, size, retries in items:
            items.remove((success, failed, item, size, retries))
            if not success:

                failmessage = ""
                for msg in failed:
                    # include the failure message from the server
                    if len(msg) == 2:
                        failmessage += msg[1][:77] + "\n"
                    else:
                        failmessage += str(msg)

                if retries < max_retries:
                    forUploadRetry.append((item, globals.host, logfile, size, retries+1),) #@UndefinedVariable
                    self.parent.addErrorMsg("Warning: Failed to upload item %s (trying %d more times)" \
                            % (item.basename, max_retries - retries), yellow)
                else:
                    message = "Error: Failed to upload item %s\nReason: %s" % (item.basename, failmessage)
                    self.parent.addErrorMsg(message, red)
                    globals.errors.append(message)
            else:
                self.u += 1

            self.processedSize += size        # TODO: different sizes
            self.updateEstimatedDuration()
            self.parent.progress.SetValue(self.processedSize*1000)

            # ensure the for cycle does not take too much time (block enqueueing compressed items for upload)
            if num == 5:
                break
            num += 1

    def do(self):
        # determines a number of workers allocated for compression and upload
        # compr. workers >= ratio * upload workers
        # allocating separate pools for compression and upload encourages paralelization as otherwise
        # majority of the compression tasks are likely to be at the beginning of the task queue

        # clear up any old temporary files
        clear_temp_files()

        ratio = float(config.config("MP_RATIO", 1.61803399))        # golden ratio
        mp_processes = int(config.config("MP_PROCESSES", 3))
        timeout = float(config.config("MP_TIMEOUT", 0.01))  # for periodical checking whether a subprocess has finished

        uploadWorkers = int(round(mp_processes / (1 + ratio)))
        comprWorkers = mp_processes - uploadWorkers > 0 and mp_processes - uploadWorkers or 1       # at least one

        print "Initializing %d compression worker(s) and %d upload worker(s)" % (comprWorkers, uploadWorkers)

        self.parent.setStatus(STATUS_READY)
        # set range of progress bar based on estimated total size of items
        self.totalSize = globals.totalSize #@UndefinedVariable
        self.parent.progress.SetRange(self.totalSize*1000)

        print "logging to ", logfile

        self.c = 0
        self.u = 0
        i = 0

        self.initSpeed = int(config.config("COMPRESSION_SPEED", 4)) + \
                            int(config.config("UPLOAD_SPEED", 17))/2
                            # let us assume that 1 MB of raw data is 0.5 MB of compr data

        comprPool = multiprocessing.Pool(processes=comprWorkers)
        uploadPool = multiprocessing.Pool(processes=uploadWorkers)
        self.parent.parent.pools.append(comprPool)
        self.parent.parent.pools.append(uploadPool)

        # upload manifest files (use rawSessions to check whether compression copied all files)
        # the manifest files are uploaded from raw and compressed sessions (note that the ``new'' compressed sessions
        #+(from raw sessions) should have the same manifest file as their raw sessions
        # do this twice just in case something went wrong with the first one
        otherItems = map(lambda session: uploadPool.apply_async(poolManifest, ((session, globals.source, globals.host),)), globals.comprSessions + globals.rawSessions + globals.comprSessions + globals.rawSessions) #@UndefinedVariable
        finUpload = []
        forComprRetry = []
        forUploadRetry = []

        self.start = time()
        self.updateEstimatedDuration()

        # initial task lists
        # Our compression also now performs a pre-liminary upload, what it does is upload the meta data and the audio files
        comprItems = comprPool.imap_unordered(poolComprUpload, [ (item, globals.localTarget, globals.host, logfile, 1) for item in globals.rawItems ]) #@UndefinedVariable
        uplItems = map(lambda x: uploadPool.apply_async(poolUpload, \
                        ((x, globals.host, logfile, x.getsize(), 1),), callback=finUpload.append), globals.comprItems) #@UndefinedVariable

        #for newFiles, item in comprItems:
        while True:
            if i*timeout > 1:      # do this only about once a second
                self.setStatusMessage("Compressed %d/%d items, uploaded %d/%d items, " % \
                                (self.c, globals.rawItemCount, self.u, globals.rawItemCount+globals.comprItemCount) + "%s remaining") #@UndefinedVariable
                i = 0

            #wx.Yield()     # so that the GUI is not unresponsive
            i += 1

            # note that finUpload is modified in this call
            self.handleUploadedItems(finUpload, forUploadRetry)

            try:
                success, newFiles, errors, item, retries = comprItems.next(timeout)
            except multiprocessing.TimeoutError:
                continue
            except StopIteration:
                # if there are items for retry, process them
                if len(forComprRetry) > 0:
                    comprItems = comprPool.imap_unordered(poolCompr, forComprRetry)
                    forComprRetry = []
                else:
                    break

            if not success:
                # don't upload items that failed compression
                if retries < max_retries:
                    forComprRetry.append((item, globals.localTarget, logfile, retries+1))
                    self.parent.addErrorMsg("Warning: Failed to compress item `%s' (trying %d more times)" \
                                        % (item.get_base_name(), max_retries - retries), yellow)
                else:
                    message = "Error: Failed to compress item `%s' - tried %d times. \nReason: %s" \
                                        % (item.get_base_name(), max_retries, errors)
                    self.parent.addErrorMsg(message, red)
                    globals.errors.append(message)
            else:
                self.c += 1
                uplItems.append(uploadPool.apply_async(poolUpload, \
                       ((RecordedItem(item.path.replace(globals.source, globals.localTarget), \
                       item.get_base_name()), globals.host, logfile, item.getsize(), 1),), callback=finUpload.append) #@UndefinedVariable
                )

            #self.processedSize and self.estDuration handled in handleUploadedItems
            #+(size is added after the item is fully processed)

        # just to make sure (not really necessary)
        #comprPool.close()
        #comprPool.join()

        self.parent.text.SetLabel("Waiting for the upload workers to finish ...")
        print "Waiting for the upload workers to finish ..."
        #wx.Yield()


        # let's use the compression pool, it's idle anyway (the compression has finished)
        # upload silence files
        otherItems += [ comprPool.apply_async(poolSilence, ((globals.source, globals.localTarget, globals.host),)) ] #@UndefinedVariable
        # upload calibration files
        otherItems.append(comprPool.apply_async(poolCalibration, ((globals.source, globals.localTarget, globals.host),))) #@UndefinedVariable
        # copy manifests for the compressed sessions (just for validation purposes, not really necessary)
        otherItems += map(lambda session: comprPool.apply_async(poolGenManifest, \
                            ((session, globals.source, globals.localTarget),)), \
                        globals.rawSessions ) #@UndefinedVariable

        # wait for the upload workers to finish
        while True:
            if i*timeout > 1:   # do this only about once a second
                self.setStatusMessage("Compressed %d/%d items, uploaded %d/%d items, " % \
                                (self.c, globals.rawItemCount, self.u, globals.rawItemCount + globals.comprItemCount) + "%s remaining") #@UndefinedVariable
                i = 0

            #wx.Yield()          # so that the GUI is not unresponsive
            i += 1

            if len(uplItems) == 0:
                if len(forUploadRetry) > 0:
                    uplItems = map(lambda x: uploadPool.apply_async(poolUpload, \
                                            (x,), callback=finUpload.append), forUploadRetry)
                    forUploadRetry = []
                else:
                    # finished uploading (and compressing) including retries
                    break

            u = uplItems.pop()
            try:
                uf = u.get(timeout)
            except multiprocessing.TimeoutError:
                uplItems.insert(random.randrange(0, len(uplItems)+1), u)
            else:
                #self.handleUploadedItems([ uf ])
                # all finished (uploaded) items are put into finUpload
                self.handleUploadedItems(finUpload, forUploadRetry)


        # just to make sure that the calibration, silence and manifest files were uploaded
        self.parent.text.SetLabel("Waiting for the silence, manifest and calibration uploads to finish ...")
        while len(otherItems) > 0:
            #wx.Yield()
            u = otherItems.pop()
            try:
                u.get(timeout)
            except multiprocessing.TimeoutError:
                otherItems.insert(random.randrange(0, len(otherItems)+1), u)

        print "Notice: finished compressing and uploading in %d seconds." % (time()-self.start,)

        self.finished()

        if (len(self.parent.errorsmsg.GetLabel()) != 0):
            self.parent.setStatus(STATUS_PROBLEM)
        else:
            self.parent.setStatus(STATUS_FINISHED)

        return (self.c,self.u)
