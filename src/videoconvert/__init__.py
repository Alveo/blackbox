# driver file for raw2avi conversion binary
import shutil
from ffmpeg import ffmpeg, join_mp4
# get constant settings
from recorder.Const import *

import re

try:
    from RawToAvi import RawConverter
    DUMMY_RAWCONVERTER = False
except:
    DUMMY_RAWCONVERTER = True

    class RawConverter:
        """Dummy RawConverter class if we can't load the C++ extension"""


        def RawToAvi(self, fps, pixelFormat, colourAlgorithm, rawFilename, outputDir, calibrationFile):
            """Convert rawFilename to AVI format and write the output into outputDir.
            Output will be two files for left and right cameras.
            fps - frames per second
            pixelFormat - one of the PX constants
            colourAlgorithm - one of the CP constants
            calibrationFile - the camera calibration file"""

            print "RawToAvi", rawFilename, outputDir


        def GetCalFile(self, cameraId):
            """Get the calibration filename for the given camera (0 or 1)
            Returns the full path to the calibration file"""

            print "GetCalFile called"

            return "test/sample_data/realdata/cal/sn10251399.cal"


        def GetCameraSN(self, cameraId):
            """Get the camera serial number for the given camera (0 or 1)
            Returns an integer value"""

            #print "GetCameraSN called"
            return 10502031

## Stipple Format names
STIPPLEDFORMAT_BGGR = 0
STIPPLEDFORMAT_GBRG = 1
STIPPLEDFORMAT_GRBG = 2
STIPPLEDFORMAT_RGGB = 3
STIPPLEDFORMAT_DEFAULT = 4


## Colour Processing Algorithm Names
CP_DEFAULT = 5
CP_NONE = 0
CP_EDGE_SENSING = 1
CP_NEAREST_NEIGHBOUR = 2
CP_NEAREST_NEIGHBOUR_FAST = 3
CP_RIGOROUS = 4
CP_HQ_LINEAR = 5

# Do we remove any temporary files - must be True in production
CLEAN_UP_TEMP_FILES = True

import tempfile
import os


def calibrationFileName(cameraSN):
    """Return the path to the calibration file name for the camera
    with this serial number."""

    filename = os.path.join(PATH_CALIBRATION_FILES, "sn%d.cal" % cameraSN)
    if os.path.exists(filename):
        return filename
    else:
        # try to generate it

        storeCalibrationFiles()
        if os.path.exists(filename):
            return filename

        # otherwise we're stuck
        raise Exception("Can't locate calibration file for camera %s, got %s" % (str(cameraSN), filename))

def storeCalibrationFiles():
    """Retrieve the camera calibration files for this machine and store
    them in the standard location using the camera serial numbers as
    file names"""

    if not os.path.exists(PATH_CALIBRATION_FILES):
        os.mkdir(PATH_CALIBRATION_FILES)

    converter = RawConverter()

    for camId in (0, 1):
        sn = cameraSerial(camId)
        calFile = converter.GetCalFile(camId)
        if os.path.exists(calFile):
            dest = os.path.join(PATH_CALIBRATION_FILES, "sn%d.cal" % sn)
            shutil.copy(calFile, dest)
        else:
            # didn't get a cal file, so we can't do anything
            pass

def cameraSerial(cameraId):
    """Return the camera serial number for cameraId 0 or 1"""

    if cameraId in (0, 1):
        converter = RawConverter()
        return converter.GetCameraSN(cameraId)
    else:
        return 0


def clear_temp_files():
    """Clean up any old temporary directories that might have been left
    behind by earlier runs"""

    TEMP_DIR = config.config("TEMP_DIR", tempfile.gettempdir())
    # look for directories in TEMP_DIR that might be ours
    # that is they begin with tmp (old) or austalk (newer)
    # this might be too aggressive (eg. other apps might use tmp dirs) but
    # should be ok on the BB
    for d in os.listdir(TEMP_DIR):
        path = os.path.join(TEMP_DIR, d)
        if os.path.isdir(path) and (d.startswith("tmp") or d.startswith("austalk")):
            shutil.rmtree(path, ignore_errors=True)



# we have two possible implementations of compression
# pipelining tries to use less space by watching for new AVI files
# and converting them as they appear, otherwise we just let
# the avi conversion run to completion and then start
# compressing
if config.config("PIPELINE_VIDEO_COMPRESSION", "No") == "Yes":

    import time
    import multiprocessing

    def runconverter(fps, pfmt, alg, src, directory, cal):
        """multiprocessing needs a python callable to run
        in another thread -- run the RawToAvi call"""

        converter = RawConverter()
        converter.RawToAvi(fps, pfmt, alg, src, directory, cal)

    def raw_to_avi(source, cameraSN, fps=48, pixelFormat=STIPPLEDFORMAT_DEFAULT, algorithm=CP_HQ_LINEAR):
        """Convert a source raw video file to AVI format, yields
        a sequence of AVI file names, size is limited to 2G so
        for a large file there will be a sequence of these. They are named left-NNNN.avi and right-NNNN.avi
        for left and right cameras, the caller is responsible for managing the sequence"""

        # first convert from raw16 to AVI
        TEMP_DIR = config.config("TEMP_DIR", None)
        tempdir = os.path.realpath(tempfile.mkdtemp(prefix="austalk", dir=TEMP_DIR))

        calFile = calibrationFileName(cameraSN)

        # run the converter in a thread
        rcProcess = multiprocessing.Process(target=runconverter, args=(fps, pixelFormat, algorithm, str(source), str(tempdir + os.sep), calFile))
        rcProcess.start()

        # monitor the thread and the directory for new files, yield a new file
        # when it seems to be complete

        CONVERTER_SLEEP_TIME = 10
        AVI_SEGMENT_SIZE = 2148305776  # size of the 2G AVI file chunks

        reported = []  # list of files that we've already returned
        queue = []  # queue of files to be reported
        while rcProcess.is_alive():
            time.sleep(CONVERTER_SLEEP_TIME)
            filesnow = [f for f in os.listdir(tempdir) if f.endswith('.avi')]

            # queue up all files that are of the required size
            for file in filesnow:
                size = os.path.getsize(os.path.join(tempdir, file))
                if size == AVI_SEGMENT_SIZE and file not in reported and file not in queue:
                    queue.append(file)

            if len(queue) > 0:
                # take the first item
                file = queue.pop(0)
                if file not in reported:
                    reported.append(file)
                    yield os.path.join(tempdir, file)

        # now the thread is done, we yield any left over files
        for file in [f for f in os.listdir(tempdir) if f.endswith('.avi')]:
            if file not in reported:
                reported.append(file)
                yield os.path.join(tempdir, file)



    def convert(source, targetdir, cameraSN, fps=48, pixelFormat=0, algorithm=CP_HQ_LINEAR):
        """Convert a raw16 video to compressed mpeg4 using the configured settings
        source is a raw16 video file, targetdir is a directory name where the result
        will be written, the filename will be the same with the extension .mp4
        Returns a tuple giving the names of the left and right video files"""

        import time

        (rootname, ext) = os.path.splitext(os.path.basename(source))

        # first check that we haven't already done this
        if os.path.exists(os.path.join(targetdir, rootname + "-left.mp4")) and os.path.exists(os.path.join(targetdir, rootname + "-right.mp4")):
            # if so, just return the two file names
            #print "found compressed video: %s/%s" % (targetdir, rootname)
            return [os.path.join(targetdir, rootname + "-left.mp4"), os.path.join(targetdir, rootname + "-right.mp4")]

        #print "starting compression of %s/%s" % (targetdir, rootname)
        start = time.time()

        mp4files = {'left': [], 'right': []}

        for avifile in raw_to_avi(source, cameraSN, fps=fps, pixelFormat=pixelFormat, algorithm=algorithm):

            avidir = os.path.dirname(avifile)

            m = re.search("(left|right)-\d\d\d\d\.avi", avifile)
            if m:
                which = m.groups()[0]
                mp4files[which].append(ffmpeg_single_file(avifile))
            else:
                print "unknown filename returned from compression: ", avifile

        # after we're done, finalise the conversion
        result = []
        for which in ('left', 'right'):
            target = os.path.join(targetdir, rootname + "-" + which + ".mp4")
            result.append(finalise_compress(mp4files[which], target))

        #print "done compression, cleaning up %s" % (avidir,)
        # clean up temp directory
        if CLEAN_UP_TEMP_FILES:
            shutil.rmtree(avidir, ignore_errors=True)

        return result


else:
    # the older, non-pilelined implementation

    def raw_to_avi(source, cameraSN, fps=48, pixelFormat=STIPPLEDFORMAT_DEFAULT, algorithm=CP_HQ_LINEAR):
        """Convert a source raw video file to AVI format, return a list
        of file names (max 2G) which are the new AVI formatted data"""

        # first convert from raw16 to AVI
        TEMP_DIR = config.config("TEMP_DIR", None)
        tempdir = os.path.realpath(tempfile.mkdtemp(prefix="austalk", dir=TEMP_DIR))

        calFile = calibrationFileName(cameraSN)

        converter = RawConverter()
        converter.RawToAvi(fps, pixelFormat, algorithm, str(source), str(tempdir+os.sep), calFile)

        ## now find what intermediate files we have
        avifiles = {'left': [], 'right': []}
        for file in os.listdir(tempdir):
            if file.find("left") >= 0:
                avifiles['left'].append(os.path.join(tempdir,file))
            else:
                avifiles['right'].append(os.path.join(tempdir, file))

        return avifiles


    def convert(source, targetdir, cameraSN, fps=48, pixelFormat=0, algorithm=CP_HQ_LINEAR):
        """Convert a raw16 video to compressed mpeg4 using the configured settings
        source is a raw16 video file, targetdir is a directory name where the result
        will be written, the filename will be the same with the extension .mp4
        Returns a tuple giving the names of the left and right video files"""

        import time

        (rootname, ext) = os.path.splitext(os.path.basename(source))

        # first check that we haven't already done this
        if os.path.exists(os.path.join(targetdir, rootname+"-left.mp4")) and os.path.exists(os.path.join(targetdir, rootname+"-right.mp4")):
            # if so, just return the two file names
            #print "found compressed video: %s/%s" % (targetdir, rootname)
            return [os.path.join(targetdir, rootname+"-left.mp4"), os.path.join(targetdir, rootname+"-right.mp4")]

        #print "starting compression of %s/%s" % (targetdir, rootname)
        start = time.time()

        avifiles = raw_to_avi(source, cameraSN, fps=fps, pixelFormat=pixelFormat, algorithm=algorithm)

        avidir = os.path.dirname(avifiles['left'][0])

        result = []
        for which in ('left', 'right'):
            target = os.path.join(targetdir, rootname+"-"+which+".mp4")
            output = compress_avi_files(avifiles[which], target)
            result.append(output)

        #print "done compression, cleaning up %s" % (avidir,)
        # clean up temp directory
        if CLEAN_UP_TEMP_FILES:
            shutil.rmtree(avidir, ignore_errors=True)

        return result

# support code used in both implementations

def compress_avi_files(avifiles, resultname):
    """Given one or more avi files we compress them and then
    possibly join them together (if more than one) to give a
    single mp4 file result in the file 'resultname'

    Returns resultname"""

    result = []
    for afile in avifiles:
        outfile = ffmpeg_single_file(afile)
        if os.path.exists(outfile):
            result.append(outfile)

    return finalise_compress(result, resultname)


def ffmpeg_single_file(avifile):
    """Apply ffmpeg to a single avi file, keep the basename
    but add a .mp4 extension. Removes the original avifile.

    Returns the name of the converted file"""

    (root, ext) = os.path.splitext(avifile)
    outfile = root + ".mp4"
    ffmpeg(avifile, outfile)
    if CLEAN_UP_TEMP_FILES:
        os.unlink(avifile)
    return outfile


def finalise_compress(files, resultname):
    """Given a list of mp4 files, join them together
    if there's more than one or just copy to the
    resultname if not, return the resultname"""

    if len(files) == 0:
        return resultname
    if len(files) == 1:
        shutil.move(files[0], resultname)
    else:
        # first check that we have the files in order
        # and there are none missing in the sequence
        files.sort()

        prev = -1
        for f in files:
            m = re.search("(left|right)-(\d\d\d\d).avi", f)
            if m:
                n = string.atoi(m.groups()[1])
                if not n == prev+1:
                    raise Exception("Missing file in AVI file sequence")
                prev = n

        # join to a temp file, then rename
        # to ensure we don't end up with a partial result
        TEMP_DIR = config.config("TEMP_DIR", None)
        tmpfile = tempfile.mktemp(prefix="austalk", dir=TEMP_DIR)
        join_mp4(files, tmpfile)
        shutil.move(tmpfile, resultname)

    return resultname





if DUMMY_RAWCONVERTER:
    import time

    def convert(source, targetdir, cameraSN, fps=48, pixelFormat=0, algorithm=CP_HQ_LINEAR):

        (basename, ext) = os.path.splitext(os.path.basename(source))

        print "Convert", basename

        left = os.path.join(targetdir, basename + "-left.mp4")
        right = os.path.join(targetdir, basename + "-right.mp4")

        for file in (left, right):
            h = open(file, "w")
            h.write("test")
            h.close()
        # artifical delay
        time.sleep(0.05)

        return (left, right)
