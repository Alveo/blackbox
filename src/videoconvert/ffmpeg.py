try:
    from recorder.Const import FFMPEG_PROGRAM, FFMPEG_OPTIONS, MENCODER_PROGRAM
except:
    FFMPEG_PROGRAM = "ffmpeg"
    #FFMPEG_OPTIONS = ["-vcodec", "libx264", "-an", "-vpre", "hq", "-crf", "22", "-threads", "0"]
    FFMPEG_OPTIONS = ["-vcodec", "mpeg4", "-b", "20000000", "-r", "48.04", "-an"]
    MENCODER_PROGRAM = "mencoder"

import sys, os, time, signal, shutil
import subprocess
import re

def ffmpeg(sourcefile, targetfile, options=FFMPEG_OPTIONS):
    """Run FFMPEG with some command options, returning the output"""

    errormsg = ""

    ffmpeg = [FFMPEG_PROGRAM, "-y", "-i", sourcefile]
    ffmpeg += options
    ffmpeg += [targetfile]

    #print " ".join(ffmpeg)
#    info = subprocess.STARTUPINFO()
#    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#    info.wShowWindow = subprocess.SW_HIDE

    # send err output to nowhere
    devnull = open(os.devnull, "w")
    process =  subprocess.Popen(ffmpeg, stdout=devnull, stderr=devnull)

    while process.poll() == None:
        pass

    status = process.poll()
    # should check status



def join_mp4(files, target):
    """Join a number of mp4 files together using mencoder,
    the output file will be target"""

    mencoder = [MENCODER_PROGRAM, '-quiet', '-ovc', 'copy', '-o', target]
    mencoder.extend(sorted(files))

    #print " ".join(mencoder)

#    info = subprocess.STARTUPINFO()
#    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#    info.wShowWindow = subprocess.SW_HIDE
    # send err output to nowhere
    devnull = open(os.devnull, "w")
    process = subprocess.Popen(mencoder, stdout=devnull, stderr=devnull)
    while process.poll() == None:
        pass

    status = process.poll()

    # should check status
