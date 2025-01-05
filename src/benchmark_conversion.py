#!/usr/bin/python

## Benchmark various settings for video conversion on some test data

from videoconvert import *
import  time
import sys


sourcedir = sys.argv[1]
targetdir = sys.argv[2]

times = dict()
algnames = {CP_NONE: 'CP_NONE',
            CP_NEAREST_NEIGHBOUR: 'CP_NEAREST_NEIGHBOUR',
            CP_EDGE_SENSING: 'CP_EDGE_SENSING',
            CP_HQ_LINEAR: 'CP_HQ_LINEAR',
            CP_RIGOROUS: 'CP_RIGOROUS'
            }
algorithms = [CP_NEAREST_NEIGHBOUR, CP_EDGE_SENSING, CP_HQ_LINEAR]

for file in os.listdir(sourcedir):
    if file.endswith("raw16"):
        print "FILE: ", file

        for alg in algorithms:
            print "\t", algnames[alg]
            start = time.time()
            # put output from each algorithm in a new dir
            algdir = os.path.join(targetdir, algnames[alg])
            if not os.path.exists(algdir):
                os.makedirs(algdir)
            files = convert(os.path.join(sourcedir, file), algdir, algorithm=alg)
            times[file+":"+algnames[alg]] = time.time()-start


for key in sorted(times.keys()):
    print key, ":", times[key]
