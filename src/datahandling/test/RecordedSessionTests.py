"""Tests of file copying and meta-data handling"""

import unittest
import tempfile
import shutil
import os
import sys
sys.path.append(".")

from datahandling import *

def unittests():
  return unittest.makeSuite(RecordedSessionTests)
  
  
class RecordedSessionTests(unittest.TestCase):
    """Tests about collections of Components in a session"""
    
    baddir = "test/sample_data/incorrect/"
    gooddir = "test/sample_data/correct/"
    host = "localhost:8000"
    hostdatadir = "/home/jumbo/work/macquarie/bigasc/bigasc/data/"


    def setUp(self):
        """ Prepare some temporary test data """
        sess = RecordedSession(self.gooddir, "Spkr2_2_Session1")
        base_path = os.path.dirname(sess.manifest_path())
        
        shutil.copy(os.path.join(base_path, 'validation.txt.bak'), os.path.join(base_path, 'validation.txt'))


    def test_validate(self):
        """Should be able to find all components within a given dir and validate them"""

        sess = RecordedSession(self.gooddir, "Spkr2_2_Session1")

        # just to make sure a correct manifest is present
        if os.path.isfile(sess.manifest_path()):
            os.remove(sess.manifest_path())
            
        sess.gen_manifest(isRawDir=True)
        
        (errors, warnings) = sess.validate_files()
        self.assertEqual(errors, [])

        # check that the validation fails when there is a missing item
        shutil.copy(sess.manifest_path(), sess.manifest_path()+'bak')
        f = open(sess.manifest_path(), 'a')
        f.write("1111_2222_3333_4444_007")
        f.close()
            
        (errors, warnings) = sess.validate_files(nocache = True)
        self.assertEqual(errors, ['Item 2_2_1_5_0081111_2222_3333_4444_007 not found'])
        shutil.move(sess.manifest_path()+'bak', sess.manifest_path())


        sess = RecordedSession(self.baddir, "Spkr2_2_Session1")

        # also, check that the validation fails when there is no manifest file
        if os.path.exists(sess.manifest_path()):
            os.remove(sess.manifest_path())

        (errors, warnings) = sess.validate_files()
        
        self.assertEqual(errors, ['File 2_2_1_11_001left.wav has incorrect checksum', 
                                'File 2_2_1_11_001right.wav has incorrect checksum', 
                                'File this_file_is_missing.wav is in metadata but not on disk', 
                                'File 2_2_1_11_002camera-1.raw16 is on disk but not in metadata', 
                                "Error: manifest file for session `Spkr2_2_Session1' does not exist!"])


    #@unittest.skip("upload needs server configured")
    def test_convert_video(self):
        """Should be able to convert video files in a session"""

        datadir = os.path.join("test", "sample_data", "realdata")

        sess = RecordedSession(datadir, "Spkr1_1121_Session1")

        tempdir = tempfile.mkdtemp()
        
        #print 'tempdir: ', tempdir
        sess.convert_video(tempdir)
        #print "Copied to ", tempdir


    @unittest.skip("upload needs server configured")
    def test_gen_manifest(self):
        sess = RecordedSession(self.gooddir, "Spkr2_2_Session1")

        if os.path.isfile(sess.manifest_path()):
            os.remove(sess.manifest_path())
        sess.gen_manifest(isRawDir=True)

        self.assertEqual(sess.read_manifest(),
                              [ '2_2_1_11_007',
                                '2_2_1_11_006',
                                '2_2_1_11_005',
                                '2_2_1_11_004',
                                '2_2_1_11_003',
                                '2_2_1_11_002',
                                '2_2_1_11_001',
                                '2_2_1_11_009',
                                '2_2_1_11_008',
                                '2_2_1_12_002',
                                '2_2_1_12_013',
                                '2_2_1_12_012',
                                '2_2_1_12_009',
                                '2_2_1_12_011',
                                '2_2_1_5_010',
                                '2_2_1_5_011',
                                '2_2_1_5_012',
                                '2_2_1_12_010',
                                '2_2_1_12_017',
                                '2_2_1_12_016',
                                '2_2_1_12_015',
                                '2_2_1_12_014',
                                '2_2_1_12_004',
                                '2_2_1_12_005',
                                '2_2_1_11_014',
                                '2_2_1_11_015',
                                '2_2_1_11_016',
                                '2_2_1_4_001',
                                '2_2_1_11_010',
                                '2_2_1_11_011',
                                '2_2_1_11_012',
                                '2_2_1_11_013',
                                '2_2_1_12_007',
                                '2_2_1_3_001',
                                '2_2_1_3_003',
                                '2_2_1_3_002',
                                '2_2_1_3_005',
                                '2_2_1_3_004',
                                '2_2_1_3_007',
                                '2_2_1_3_006',
                                '2_2_1_3_008',
                                '2_2_1_12_001',
                                '2_2_1_5_003',
                                '2_2_1_5_002',
                                '2_2_1_5_001',
                                '2_2_1_12_003',
                                '2_2_1_5_007',
                                '2_2_1_5_006',
                                '2_2_1_5_005',
                                '2_2_1_5_004',
                                '2_2_1_12_008',
                                '2_2_1_12_006',
                                '2_2_1_5_009',
                                '2_2_1_5_008',]
                        )

    
    @unittest.skip("upload needs server configured")
    def test_upload_files(self):
        if os.path.exists(self.hostdatadir):
            shutil.rmtree(self.hostdatadir)

        sess = RecordedSession(self.gooddir, "Spkr2_2_Session1")
        self.assertEqual(False, sess.uploaded(self.host)[0])

        sess.unupload_files()
        sess.upload_files(self.host)
        self.assertEqual(True, sess.uploaded(self.host)[0])


if __name__=='__main__':
    unittest.main()
