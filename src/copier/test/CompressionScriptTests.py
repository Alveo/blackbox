"""Tests of file copying and meta-data handling"""
import unittest

from datahandling.RecordedSession import session_list_item_generator, RecordedSession


class CompressionScriptTests(unittest.TestCase):
    """Tests for the compression script """
    
    gooddir = "../../test/sample_data/correct/"
    
    @classmethod
    def setUpClass(cls):
        pass
        
        
    def test_compress(self):
        sess = RecordedSession(self.gooddir, "Spkr2_2_Session1")
        session_list = []
        session_list.append(sess)
        
        for item in session_list_item_generator(session_list):
            print item


if __name__=='__main__':
    unittest.main()