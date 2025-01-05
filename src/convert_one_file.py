#!/usr/bin/python

## Convert a single video file for testing purposes

from videoconvert import *
import sys
import time

if len(sys.argv) != 4:
    print "Usage convert_one_file.py <sourcefile> <outputdir> <cameraSN>"
    exit()

source = sys.argv[1]
targetdir = sys.argv[2]
cameraSN = sys.argv[3]

start = time.time()

files = convert(source, targetdir, int(cameraSN))

print "Time taken: ", time.time()-start

for f in files:
    print "Output: ", f
