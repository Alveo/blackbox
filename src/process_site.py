#!/usr/bin/python

"""Process site related metadata"""

import sys, os
import urllib2

from datetime import datetime

from datahandling.RecordedItem import post_multipart
from datahandling import find_existing_sessions
import random
import config
import shutil
import re

config.configinit()


def determSite(directory, filepath, host):
    """Determine recording location of data in ``directory''
    ``host'' is a server to obtain recording location of a participant
    ``filepath'' is where to write the result"""
    sel = "/forms/reports/participant/to/site/%(colour)d/%(animal)d"
    proto = config.config("PROTO", "https")

    sessions, errors = find_existing_sessions(directory)
    if errors:
        print "Errors found: ", errors

    # reasonably limit the number of attempts
    max_attempts = 7 < len(sessions) and 7 or len(sessions)
    sitedata = None
    for i in range(0, max_attempts):
        session = sessions[random.randrange(0, len(sessions))]
        try:
            sitedata = urllib2.urlopen(proto+"://"+host+sel % { 'colour' : session.colourId, 'animal' : session.animalId })
        except urllib2.HTTPError:
            sitedata = None
        else:
            break

    if sitedata != None:
        f = open(filepath, "w")
        f.write(sitedata.read())
        f.close()
        return True
    else:
        return False


def upload_silence(dirname, host):
    """Upload silence files along with their `created' timestamps"""
    sel = "/forms/reports/upload/silence/"
    bigascsitef = "bigascsite.py"

    datadir = os.path.join(dirname, "silence")
    proto = config.config("PROTO", "https")

    if os.path.isdir(datadir):
        if not os.path.isfile(os.path.join(datadir, bigascsitef)):
            if not determSite(dirname, os.path.join(datadir, bigascsitef), host):
                print "Error: unable to determine Recording location of ``silence'' recordings"
                print "Warning: ``silence'' recordings not uploaded"
                return

        fname_patt = re.compile('silence-(\d{2})-(\d{2})-(\d{4}).*')
        redir_selector = "/forms/reports/data/[0-9]+/"

        sys.path.append(datadir)
        from bigascsite import RECORDING_SITE_ID

        fields = [ ('location', str(RECORDING_SITE_ID)), ('form-TOTAL_FORMS', '1'),
           ('form-INITIAL_FORMS', "0"), ('form-MAX_NUM_FORMS', ''),
        ]

        i = 0
        errors = 0
        for f in os.listdir(datadir):
            if os.path.isfile(os.path.join(datadir, f)) and re.match(fname_patt, f) != None:
                fp = os.path.join(datadir, f)
                day, month, year = re.match(fname_patt, f).groups()
                errcode, headers, fr = post_multipart(proto, host, sel, \
                                fields + [('createddate', '%s-%s-%s' % (year, month, day))],
                                [('form-0-data', f, fp)])
                if errcode == 302 and re.search(redir_selector, str(headers)) != None:
                    i += 1
                else:
                    errors += 1

        # TODO: get rid of the processed silence files so that we don't upload them
        #+over and over again

        print "Notice: %d silence files uploaded successfully." % i
        if errors > 0:
            print "Error: upload of %d silence files failed." % errors
    else:
        print "Warning: silence directory `%s' is missing." % datadir

def _convert_file(src, f, dst):
    # TODO: fairly duplicate code with RecordedItem.video_convert
    full_f = os.path.join(src, f)
    errors = ""
    if ( os.path.splitext(f)[1] == '.raw16' ):
        import videoconvert
        try:
            if f.find("camera-0") >= 0:
                cameraSN = int(videoconvert.cameraSerial(0))
            else:
                cameraSN = int(videoconvert.cameraSerial(1))

            left, right = videoconvert.convert(full_f, dst, cameraSN)
        except IOError, err:
            errors = 'video copy of ' + f + ' failed '+str(err)

    elif (os.path.splitext(f)[1] == '.wav' ):
        try:
            shutil.copyfile(full_f, os.path.join(dst,f))
        except IOError, err:
            errors = 'audio copy of ' + f + ' failed '+str(err)
    else:
        # ignore other files
        errors = "Warning: File `%s' ignored" % f

    return errors


def copy_silence(source, dest):
    if source == dest:
        return

    label = "silence"

    srcdatadir = os.path.join(source, label)
    dstdatadir = os.path.join(dest, label)

    if os.path.isdir(srcdatadir):
        # make sure we're clean
        if os.path.isdir(dstdatadir):
            shutil.rmtree(dstdatadir)
        os.makedirs(dstdatadir)

        i = 0
        # omit subdirs
        for f in os.listdir(srcdatadir):
            if os.path.isfile(os.path.join(srcdatadir, f)):
                errs = _convert_file(srcdatadir, f, dstdatadir)
                if len(errs) == 0:
                    i += 1
                else:
                    print "Error: %s" % errs

        print "Notice: %d %s data files successfully converted and copied to %s" % (i, label, dstdatadir)
    else:
        print "Warning: %s directory `%s' is missing." % (label, srcdatadir)


def copy_calibration(source, dest):
    if source == dest:
        return

    label = "calibration"

    srcdatadir = os.path.join(source, label)
    dstdatadir = os.path.join(dest, label)

    if os.path.isdir(srcdatadir):
        if os.path.isdir(dstdatadir):
            shutil.rmtree(dstdatadir)

        shutil.copytree(srcdatadir, dstdatadir)
        print "Notice: %s data files successfully copied to %s" % (label, dstdatadir)
    else:
        print "Warning: %s directory `%s' is missing." % (label, srcdatadir)

def upload_calibration(dirname, host):
    """Upload calibration files"""
    sel = "/forms/reports/upload/calibration/"
    bigascsitef = "bigascsite.py"

    datadir = os.path.join(dirname, "calibration")
    proto = config.config("PROTO", "https")

    if os.path.isdir(datadir):
        if not os.path.isfile(os.path.join(datadir, bigascsitef)):
            if not determSite(dirname, os.path.join(datadir, bigascsitef), host):
                print "Error: unable to determine Recording location of ``calibration'' files"
                print "Warning: ``calibration'' files not uploaded"
                return

        sys.path.append(datadir)
        from bigascsite import RECORDING_SITE_ID

        forUpload = []
        for f in os.listdir(datadir):
            # do not upload bigascsitef (.py or .pyc)
            if os.path.isfile(os.path.join(datadir, f)) and not f.startswith(bigascsitef):
                num = len(forUpload)
                forUpload.append(('form-%d-data' % num, f, os.path.join(datadir, f)))

        fields = [ ('location', str(RECORDING_SITE_ID)), ('form-TOTAL_FORMS', str(len(forUpload))),
           ('form-INITIAL_FORMS', "0"), ('form-MAX_NUM_FORMS', ''),
        ]

        redir_selector = "/forms/reports/data/[0-9]+/"

        errcode, headers, fr = post_multipart(proto, host, sel, fields, forUpload)
        if errcode == 302 and re.search(redir_selector, str(headers)) != None:
            print "Notice: %d calibration files uploaded" % len(forUpload)
        else:
            print "Error: upload of %d calibration files failed." % len(forUpload)
    else:
        print "Warning: calibration directory `%s' is missing." % datadir

upl_calibration = upload_calibration


def clean(*args):
    #TODO: combine with "new" clean in copier.py (GUI) ???
    msg, forDelete = _status(*args)

    print msg, "\n"

    answer = raw_input("%s\nDo you really want to permanently delete these %d sessions? [Y/n] " % ("\n".join(forDelete), len(forDelete))).strip()
    while answer.lower() != 'y' and answer.lower() != 'n':
        answer = raw_input("Please, enter either 'Y' for yes, or 'n' for no: ").strip()

    if answer.lower() == 'y':
        map(shutil.rmtree, forDelete)
        print "Notice: %d sessions deleted" % len(forDelete)
    else:
        print "Notice: nothing done."

def status(*args):
    msg, forDelete = _status(*args)
    print msg

def _status(rawDir, comprDir, host):
    #TODO: combine with "new" clean in copier.py (GUI) ???
    # compressed sessions
    forDelete = []

    comprText = "-------\n"
    comprText += "Compressed data directory: %s\n\n" % comprDir
    comprSessions, errors = find_existing_sessions(comprDir)
    if errors:
        comprText += "Errors found: " + errors + "\n"

    uplNum = 0
    uplSize = 0
    comprSessionsVerb = []
    for session in comprSessions:
        errors = session.validate_files()
        if len(errors) > 0:
            comprText += "!%s \t contains errors!\n" % session
            comprText += "\t" + "\n\t".join(errors) + "\n"
        else:
            comprSessionsVerb.append(str(session))
            uploaded, errors = session.uploaded(host)
            if uploaded:
                comprText += "%s \t uploaded\n" % session
                uplNum += 1
                uplSize += session.getsize()
                forDelete.append(session.full_path())
            else:
                comprText += "%s \t pending upload or errors in uploaded data\n" % session
                comprText += "\t%s\n" % errors
    comprText += "\n%d out of %d sessions were successfully uploaded, %.1f MB could be freed\n\n" % (uplNum, len(comprSessions), uplSize)

    # raw sessions
    rawText = "Raw data directory: %s\n\n" % rawDir
    rawSessions, errors = find_existing_sessions(rawDir)
    if errors:
        rawText += "!!!Errors found: " + errors + "\n"

    comprNum = 0
    comprSize = 0
    for session in rawSessions:
        errors = session.validate_files()
        if len(errors) > 0:
            rawText += "!%s \t contains errors!\n" % session
            rawText += "\t" + "\n\t".join(errors) + "\n"
        elif str(session) in comprSessionsVerb:
            rawText += "%s \t compressed\n" % session
            comprNum += 1
            comprSize += session.getsize()
            forDelete.append(session.full_path())
        else:
            rawText += "%s \t pending compression or errors in compressed data\n" % session
    rawText += "\n%d out of %d sessions were successfully compressed, %.1f MB of space could be freed\n\n" % (comprNum, len(rawSessions), comprSize)

    # total
    total = "-------\n"
    total += "In total: %d out of %d sessions were processed, %.1f MB could be freed\n" % \
                    (comprNum + uplNum, len(rawSessions) + len(comprSessions), comprSize+uplSize)

    return (rawText + comprText + total, forDelete)


def print_usage():
    print "Usage process_site.py  <operation> <rawDir> <comprDir> <host>"
    print "A valid <operation> is one of:"
    print ""
    print "\tupl_silence"
    print "\tupl_calibration"
    print "\tstatus"
    print "\tclean - delete all sessions that have been processed "
    print "\t\t (ask for confirmation first)"
    print ""


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print_usage()
        quit(1)

    operation = sys.argv[1]

    try:
        op = globals()[operation]
    except KeyError:
        print_usage()
        quit(2)

    op(*sys.argv[2:])
