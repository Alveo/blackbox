#!/usr/bin/python

"""Compress and upload one or more sessions

A command line version of the compressor tool
"""

import sys, os
from datahandling import RecordedSession, find_existing_sessions 
import config
config.configinit()

dest = config.config("PATH_FINAL")
host = config.config("HOST_FINAL")
logfile = os.path.join(dest, "log.txt")

def usage():
	print """Usage:  compress_upload.py <sessiondir>"""

if len(sys.argv) != 2:
    usage()
    exit()

dirname = sys.argv[1]

# make sure to remove a trailing /
if dirname.endswith(os.sep):
    dirname = os.path.dirname(dirname)

(sessions, errors) = find_existing_sessions(dirname)

for session in sessions:
	 
	print "Session: ", session

	for item in session.item_generator():
		try:
			print "Processing item:", item.basename
			item.copy_upload_audio(dest, logfile, host, True)
			(success, files, message) = item.convert_video_and_upload(dest, host, logfile)
			if success:
				# now remove the copied files
				for f in files:
					os.remove(f)
			else:
				print "Error: ", message
		except:
			print "Problem processing item: ", item.basename
			with open(os.path.join(dest, "errorlog.txt"), "a") as h:
				h.write("Problem with " + item.basename + '\n')
			
			