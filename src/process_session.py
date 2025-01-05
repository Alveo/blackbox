#!/usr/bin/python

"""Validate all files in a session directory and show some
statistics"""

from datahandling import RecordedSession, find_existing_sessions
import sys, os


def usage():
    print "Usage: process_session.py <operation> -all? <dir> <destination | host>?"
    print "A valid <operation> is one of:"
    print ""
    print "\tvalidate - validate sessions, print a summary about processed "
    print "\t\t and unprocessed sessions"
    print "\tconvert - convert video files and copy to a new destination"
    print "\thtml - generate HTML descriptions for session"
    print "\tupload - upload session data files onto the server"
    print "\tunupload - remove the uploaded flag from all items in the session"
    print "\tfixmeta - fix metadata from old to new style, requires camera"
    print "\t\t serial numbers"
    print "\tgenmanifest - generate a manifest file and copy it to a new "
    print "\t\t (compressed) destination"
    print "\tuplmanifest - upload a manifest file for a session to the host server"
    print ""
    print "if -all is given, process all sessions in the given directory"



if not len(sys.argv) >= 3:
    usage()
    exit()

if sys.argv[2] == "-all":
    GET_ALL_SESSIONS = True
    # move other args down
    i=2
    while i<len(sys.argv)-1:
        sys.argv[i] = sys.argv[i+1]
        i += 1
    del(sys.argv[i])
else:
    GET_ALL_SESSIONS = False

operation = sys.argv[1]
dirname = sys.argv[2]

# make sure to remove a trailing /
if dirname.endswith(os.sep):
    dirname = os.path.dirname(dirname)

def operate(operation, session):
    if operation=='validate':

        (errors, warnings) = session.validate_files(nocache=False)

        if len(warnings) > 0:
            print "Warnings:"
            for w in warnings:
                print "\t", w


        if errors == []:
            print "Validation OK"
        else:
            print "Errors found:"
            for error in errors:
                print "\t", error

    elif operation=="fixmeta":

        # need to get camera SNs from command line
        if not len(sys.argv) == 5:
            print "fixmeta requires both camera serial numbers"
            exit()
        camera0 = sys.argv[3]
        camera1 = sys.argv[4]
        print "Cameras: ", camera0, camera1
        session.add_camera_metadata(camera0, camera1)

    elif operation=='html':

        session.write_html()

    elif operation=='convert':

        if not len(sys.argv) == 4:
            print "convert requires a destination directory"
            exit()

        dest = sys.argv[3]

        session.convert_video(dest)
    elif operation == 'upload':
        if not len(sys.argv) == 4:
            print "upload requires a host server"
            exit()

        host = sys.argv[3]

        session.upload_files(host)

    elif operation == 'genmanifest':

        if not len(sys.argv) == 4:
            print "genmanifest requires a destination directory"
            exit()

        dest = sys.argv[3]

        if dest.endswith(os.sep):
            dest = dest[:-1]

        if dest == session.full_path():
            # raw directory
            session.gen_manifest(isRawDir=True)
        elif GET_ALL_SESSIONS:
            # generate manifest in the compressed directory (automatically creates it in the raw dir if not present)
            comprSession = RecordedSession(dest, session.basename)
            comprSession.gen_manifest(isRawDir=False, rawDir=session.path)
        else:
            # generate manifest in the compressed directory (automatically creates it in the raw dir if not present)
            comprSession = RecordedSession(*os.path.split(dest))
            comprSession.gen_manifest(isRawDir=False, rawDir=session.path)

    elif operation == 'uplmanifest':
        if not len(sys.argv) == 4:
            print "upload requires a host server"
            exit()

        host = sys.argv[3]

        session.upload_manifest(host)

    elif operation == 'unupload':
        # just for testing
        session.unupload_files(len(sys.argv) == 4 and sys.argv[3] or "")

    else:
        print "Unknown operation"
        usage()
        exit()



if GET_ALL_SESSIONS:

    (sessions, errors) = find_existing_sessions(dirname)
    if errors:
        print "Errors found: ", errors

    if operation=="html":
        fh = open(os.path.join(dirname, "index.html"), "w")
        fh.write("<body>")

    for session in sessions:
        print "Session", session.basename

        if operation=="html":
            (link, text) = session.write_html()
            fh.write("<p><a href='%s'>%s</a></p>" % (link, text))
        else:
            operate(operation, session)

    if operation=="html":
        fh.close()

else:
    (path, basename) = os.path.split(dirname)

    session = RecordedSession(path, basename)
    operate(operation, session)
