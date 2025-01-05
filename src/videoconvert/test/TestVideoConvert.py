"""Tests of file copying and meta-data handling"""

import unittest
import tempfile
import os
import sys
import shutil
# add the directory two above this one to the path
sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

from videoconvert import *

# get constant settings
from recorder.Const import *

class VideoConversionTests(unittest.TestCase):
    """Tests for the video conversion module"""



    def setUp(self):
        """Setup prompts user to copy a large file into the
        required slot"""

        self.testDataDir = os.path.join("test", "sample_data", "realdata")
        self.rawTestFile = os.path.join(self.testDataDir, "Spkr1_1121_Session1", "Session1_12", "1_1121_1_12_001-camera-0.raw16")

        self.largeRawTestFile = os.path.join(self.testDataDir, "largefile.raw16")

        self.camSerial = "sn12345"

    def test_getCameraSN(self):

        sn = cameraSerial(0)

        # should be 8 digit number
        self.failUnless(sn>10000000, "Serial number should be 8 digit number, got %d" % sn)

        sn = cameraSerial(1)

        # should be 8 digit number
        self.failUnless(sn>10000000, "Serial number should be 8 digit number, got %d" % sn)

    def test_storeCalibrationFiles(self):
        """Can we retrieve the cal files and store them in the
        right place?"""

        storeCalibrationFiles()
        # go looking for the files
        for name in os.listdir(PATH_CALIBRATION_FILES):
            print name

    def test_getCalibrationFilename(self):
        """Get the calibration filename for a given camera SN"""

        sn = cameraSerial(0)
        fn = calibrationFileName(sn)

        self.failUnless(os.path.exists(fn))


    def xtest_raw2avi(self):
        """Test conversion of raw16 files to AVI format"""

        # convert the rawTestFile to AVI

        avifiles = raw_to_avi(self.rawTestFile, self.camSerial)

        self.failUnless(len(avifiles['left'])==1, "raw_to_avi should return one file for the left camera")
        self.failUnless(len(avifiles['right'])==1, "raw_to_avi should return one file for the right camera")

        print "Please validate AVI files from conversion of", self.rawTestFile
        for k in avifiles.keys():
            print k, ":", avifiles[k]


    def xtest_raw2avi_largefile(self):
        """Test conversion of raw16 file to AVI for large files that will
        be split into 1G chunks"""

        if not os.path.exists(self.largeRawTestFile):
            message =  "Please copy a large (> 2G) raw16 format file to " + self.largeRawTestFile
            self.fail(message)

        print "Starting AVI conversion of large Raw file..."
        avifiles = raw_to_avi(self.largeRawTestFile, self.camSerial)

        self.failUnless(len(avifiles['left'])>1, "raw_to_avi for large file should return more than one file for the left camera")
        self.failUnless(len(avifiles['right'])>1, "raw_to_avi for large file should return more than one file for the left camera")

        print "Please validate AVI files from conversion of", self.rawTestFile
        for k in avifiles.keys():
            print k, ":", avifiles[k]


    def xtest_convert(self):
        """Test conversion pathway to AVI and then MP4"""

        tempdir = os.path.realpath(tempfile.mkdtemp(dir="."))

        mp4files = convert(self.rawTestFile, tempdir, self.camSerial)

        print "Please validate MP4 files from conversion of ", self.rawTestFile
        for file in mp4files:
            print "\t", file



    def xtest_convert_large_file(self):
        """Test convert on a large file that will split into two AVI files and
        so require re-joining via mencoder"""

        if not os.path.exists(self.largeRawTestFile):
            message =  "Please copy a large (> 2G) raw16 format file to " + self.largeRawTestFile
            self.fail(message)

        tempdir = os.path.realpath(tempfile.mkdtemp(dir="."))

        mp4files = convert(self.largeRawTestFile, tempdir, self.camSerial)

        print "Please validate MP4 files from conversion of ", self.largeRawTestFile
        for file in mp4files:
            print "\t", file


if __name__=='__main__':
    unittest.main()
