"""Tests of file copying and meta-data handling"""
import config
import unittest
import tempfile
import os
import sys
import shutil
import urllib2

from datahandling import *
from datahandling.RecordedItem import *

from logging import Logger
testlogger =  Logger("testlog")
  
class RecordedItemTests(unittest.TestCase):
    """Tests for the copying module"""

    host = "localhost:8000"
    
    @classmethod
    def setUpClass(cls):
        # sys.path += ".."
        config.configinit()
        proto = config.config("PROTO", "http")

 
    def test_file_checksums(self):
        """The checksums method correctly calculates checksums for a set of files"""

        tempdir = tempfile.mkdtemp()

        open(os.path.join(tempdir, '2_2_1_11_001-1.txt'),'wb').write('Hello world')
        open(os.path.join(tempdir, '2_2_1_11_001-2.txt'),'wb').write('Hello world again')
        open(os.path.join(tempdir, '2_2_1_11_001-3.txt'),'wb').write('Hello world')
        r = RecordedItem(tempdir, '2_2_1_11_001', no_guess_meta=True)
        self.assertEqual(sorted(r.fileList()), ['2_2_1_11_001-1.txt', '2_2_1_11_001-2.txt', '2_2_1_11_001-3.txt'])

        fullpaths = [os.path.join(tempdir, f) for f in r.fileList()]
        cc = r.checksums(fullpaths)
        self.assertEqual(sorted(cc.keys()), ['2_2_1_11_001-1.txt', '2_2_1_11_001-2.txt', '2_2_1_11_001-3.txt'])
        self.assertEqual(cc['2_2_1_11_001-2.txt'], '47f35eccdd32cf212d51bb40a637cc10')
        self.assertEqual(cc['2_2_1_11_001-3.txt'], '3e25960a79dbc69b674cd4ec67a72c62')
        self.assertEqual(cc['2_2_1_11_001-1.txt'], cc['2_2_1_11_001-3.txt'])

        # clean up
        shutil.rmtree(tempdir)

 
    def test_to_html(self):
        """Test the generation of HTML for an item"""

        tempdir = tempfile.mkdtemp()

        open(os.path.join(tempdir, '2_2_1_11_001-1.txt'),'wb').write('Hello world')
        open(os.path.join(tempdir, '2_2_1_11_001-2.txt'),'wb').write('Hello world again')
        open(os.path.join(tempdir, '2_2_1_11_001-3.txt'),'wb').write('Hello world')
        r = RecordedItem(tempdir, '2_2_1_11_001', no_guess_meta=True)

        expected = """<div class='item'><span>Item 1, Prompt <em>"Unknown"</em></span>
<ul>
<li><a href='2_2_1_11_001-1.txt'>2_2_1_11_001-1.txt</a></li>
<li><a href='2_2_1_11_001-2.txt'>2_2_1_11_001-2.txt</a></li>
<li><a href='2_2_1_11_001-3.txt'>2_2_1_11_001-3.txt</a></li>
</ul>
"""

        text = r.to_html()
        self.assertEqual(expected, text)

        
    def test_canonical_item_name(self):
        ri = RecordedItem("test/sample_data/correct/Spkr2_2_Session1/Session1_11", "2_2_1_11_001")
        self.assertEqual('001', ri.get_canonical_item_name('1'))
        self.assertEqual('011', ri.get_canonical_item_name('11'))
        self.assertEqual('011', ri.get_canonical_item_name('011'))
        self.assertEqual('0011', ri.get_canonical_item_name('0011'))
        
        
    def test_get_canonical_gpfolder_name(self):
        ri = RecordedItem("test/sample_data/correct/Spkr2_2_Session1/Session1_11", "2_2_1_11_001")
        self.assertEqual('Spkr2_3_Session1', ri.get_canonical_gpfolder_name(2, 3, 1))


    def test_rename_of_preexisting_item(self):
        ri = RecordedItem("test/sample_data/correct/Spkr2_2_Session1/Session1_11", "2_2_1_11_001")
        ri.read_metadata()
        
        self.assertRaises(IOError, ri.rename_item, 2, 2, 11, 2, testlogger)


    def test_rename_of_component_and_item(self):
        ri = RecordedItem("test/sample_data/correct/Spkr2_2_Session1/Session1_11", "2_2_1_11_001")
        ri.read_metadata()

        filename = ri.rename_item(2, 2, 12, 18, testlogger, test_mode = True)
        self.assertEqual('2_2_1_12_018', filename)


    def test_rename_of_item(self):
        ri = RecordedItem("test/sample_data/correct/Spkr2_2_Session1/Session1_11", "2_2_1_11_001")
        ri.read_metadata()

        filename = ri.rename_item(2, 2, 11, 17, testlogger, test_mode = True)
        self.assertEqual('2_2_1_11_017', filename)
    
    
    def test_rename_to_new_folder(self):
        ri = RecordedItem("test/sample_data/correct/Spkr2_2_Session1/Session1_4", "2_2_1_4_001")
        ri.read_metadata()

        filename = ri.rename_item(2, 2, 6, 1, testlogger, test_mode = True)
        self.assertEqual('2_2_1_6_001', filename)
           

    def test_rename_for_new_speaker_id(self):
        ri = RecordedItem("test/sample_data/correct/Spkr2_2_Session1/Session1_4", "2_2_1_4_001")
        ri.read_metadata()

        filename = ri.rename_item(2, 3, 4, 1, testlogger, test_mode = True)
        self.assertEqual('2_3_1_4_001', filename)


    def test_get_component_items(self):
        rc = RecordedComponent("test/sample_data/correct/Spkr2_2_Session1", "Session1_4")
        rc.rename_items(2, 2, 6, testlogger, test_mode = True)

    def test_create_recordedItem(self):
        """We create a recorded item and check that all the required
        properties are present"""
        
        tempdir = tempfile.mkdtemp()
        
        open(os.path.join(tempdir, '2_2_1_11_001-1.txt'),'wb').write('Hello world')
        open(os.path.join(tempdir, '2_2_1_11_001-2.txt'),'wb').write('Hello world again')
        open(os.path.join(tempdir, '2_2_1_11_001-3.txt'),'wb').write('Hello world')
        # make a recorded item
        r = RecordedItem(tempdir, '2_2_1_11_001')
        self.assertEqual(sorted(r.fileList()), ['2_2_1_11_001-1.txt', '2_2_1_11_001-2.txt', '2_2_1_11_001-3.txt'])      
        
        self.assertEqual(r['participant'], 'Green-Arnhem Sheath-tailed Bat')
        self.assertEqual(r['colour'], '2')
        self.assertEqual(r['animal'], '2')
        self.assertEqual(r['session'], '1')
        self.assertEqual(r['component'], '11')
        self.assertEqual(r['item'], '1')
        self.assertEqual(r['prompt'], 'Turn right 90  (face right wall)  2')
        
        # remove the xml file created above
        os.unlink(os.path.join(tempdir, '2_2_1_11_001.xml'))
        
        # make a recorded item, this time don't guess metadata
        r = RecordedItem(tempdir, '2_2_1_11_001', no_guess_meta=True)
        self.assertEqual(sorted(r.fileList()), ['2_2_1_11_001-1.txt', '2_2_1_11_001-2.txt', '2_2_1_11_001-3.txt'])      
        self.assertEqual(r['participant'], 'Green-Arnhem Sheath-tailed Bat')
        self.assertEqual(r['colour'], '2')
        self.assertEqual(r['animal'], '2')
        self.assertEqual(r['session'], '1')
        self.assertEqual(r['component'], '11')
        self.assertEqual(r['item'], '1')

        shutil.rmtree(tempdir)


    def test_write_metadata_own_files(self):
        """Test output of metadata for the case where we're 
        writing it out for our own list of files"""
        
        # set up camera numbers in config
        cameraSN0 = "00000001"
        cameraSN1 = "00000002"
        config.set_config("CAMERASN0", cameraSN0)
        config.set_config("CAMERASN1", cameraSN1)
        
        # xml template may be susceptible to variations in output of generated xml
        # should really read it into the DOM and compare
        xmltext_template = '<item><uploaded>[]</uploaded><participant>Green-Arnhem Sheath-tailed Bat</participant><version>testing</version><cameraSN1>%(camera1)s</cameraSN1><cameraSN0>%(camera0)s</cameraSN0><componentName>Calibration</componentName><colour>2</colour><component>11</component><regenerated>REGENERATED METADATA</regenerated><item>1</item><session>1</session><animal>2</animal><timestamp>%(timestamp)s</timestamp><prompt>Turn right 90  (face right wall)  2</prompt><files><file md5hash="3e25960a79dbc69b674cd4ec67a72c62" uploaded="false">2_2_1_11_001-1.txt</file><file md5hash="47f35eccdd32cf212d51bb40a637cc10" uploaded="false">2_2_1_11_001-2.txt</file><file md5hash="3e25960a79dbc69b674cd4ec67a72c62" uploaded="false">2_2_1_11_001-3.txt</file></files><path>%(path)s</path></item>'
        tempdir = tempfile.mkdtemp()
        
        expected_xmltext = xmltext_template % {'timestamp': time.ctime(), 'path': tempdir, 'camera0': cameraSN0, 'camera1': cameraSN1}
        
        open(os.path.join(tempdir, '2_2_1_11_001-1.txt'),'wb').write('Hello world')
        open(os.path.join(tempdir, '2_2_1_11_001-2.txt'),'wb').write('Hello world again')
        open(os.path.join(tempdir, '2_2_1_11_001-3.txt'),'wb').write('Hello world')
        # make a recorded item and have it guess the metadata, as a side effect this 
        # will call write_metadata which is what we're testing
        r = RecordedItem(tempdir, '2_2_1_11_001', no_guess_meta=False)
        self.assertEqual(sorted(r.fileList()), ['2_2_1_11_001-1.txt', '2_2_1_11_001-2.txt', '2_2_1_11_001-3.txt'])      
        
        # should now have an xml file
        metafile = os.path.join(tempdir, '2_2_1_11_001.xml')
        self.assertTrue(os.path.exists(metafile), "Metadata file is missing after write_metadata")
        
        # check the contents
        fh = open(metafile, 'r')
        xmltext = fh.read()
        fh.close()
         
        self.assertEqual(xmltext, expected_xmltext)

        shutil.rmtree(tempdir)
        
        
    def test_write_metadata_other_files(self):
        """Test output of metadata for the case where we're 
        writing it out for a copied set of files"""
        
        # xml template may be susceptible to variations in output of generated xml
        # should really read it into the DOM and compare
        xmltext_template = '<item><uploaded>[]</uploaded><participant>Green-Arnhem Sheath-tailed Bat</participant><version>testing</version><componentName>Calibration</componentName><colour>2</colour><component>11</component><item>1</item><session>1</session><animal>2</animal><files><file md5hash="3e25960a79dbc69b674cd4ec67a72c62" uploaded="false">2_2_1_11_001-1.txt</file><file md5hash="47f35eccdd32cf212d51bb40a637cc10" uploaded="false">2_2_1_11_001-2.txt</file><file md5hash="3e25960a79dbc69b674cd4ec67a72c62" uploaded="false">2_2_1_11_001-3.txt</file></files><path>%(path)s</path></item>'

        tempdir1 = tempfile.mkdtemp()
        tempdir2 = tempfile.mkdtemp()
        
        expected_xmltext = xmltext_template % {'timestamp': time.ctime(), 'path': tempdir2}
        
        # make files in the other directory
        open(os.path.join(tempdir2, '2_2_1_11_001-1.txt'),'wb').write('Hello world')
        open(os.path.join(tempdir2, '2_2_1_11_001-2.txt'),'wb').write('Hello world again')
        open(os.path.join(tempdir2, '2_2_1_11_001-3.txt'),'wb').write('Hello world')
        
        # make a recorded item for the first directory
        r = RecordedItem(tempdir1, '2_2_1_11_001', no_guess_meta=True)
       
        files = ['2_2_1_11_001-1.txt', '2_2_1_11_001-2.txt', '2_2_1_11_001-3.txt']
       
        # write the metadata for the other files
        r.write_metadata(path=tempdir2, copiedFiles=files)
        
        # should now have an xml file
        metafile = os.path.join(tempdir2, '2_2_1_11_001.xml')
        self.assertTrue(os.path.exists(metafile), "Metadata file is missing after write_metadata")
        
        # check the contents
        fh = open(metafile, 'r')
        xmltext = fh.read()
        fh.close()
         
        self.assertEqual(xmltext, expected_xmltext)

        
 
    def test_read_metadata(self):
        """The read_metadata method correctly reads a metadata file
        and returns a properly structured dictionary"""


        source ="""<item>
        <files>
          <file>2_2_1_11_001camera-1.raw16</file>
          <file>2_2_1_11_001left.wav</file>
          <file>2_2_1_11_001right.wav</file>
        </files>
        <prompt>Turn right 90 (face right wall)</prompt>
        <timestamp>Wed Jul  6 12:35:41 2011</timestamp>
        <basename>2_2_1_11_001</basename>
        <component>11</component>
        <session>1</session>
        <cameraSN0>1233456</cameraSN0>
        <cameraSN1>1234523</cameraSN1>
        <checksums>
          <md5hash file="2_2_1_11_001left.wav">5cd13fbee3e1eb55e08e5cca29beb25f</md5hash>
          <md5hash file="2_2_1_11_001right.wav">a1332ec17e8a29e1e983c31da304da61</md5hash>
          <md5hash file="2_2_1_11_001camera-1.raw16">b4af51084602e33b61ee5f2e0ebd4cf0</md5hash>
        </checksums>
        <path>recordings/Spkr2_2_Session1/Session1_11/</path>
        <colour>2</colour>
        <item>1</item>
        <animal>2</animal>
    </item>"""

        tempdir = tempfile.mkdtemp()

        filename = os.path.join(tempdir, "2_2_1_11_001.xml")

        fd = open(filename, "w")
        fd.write(source)
        fd.close()

        ri = RecordedItem(tempdir, "2_2_1_11_001")

        data = ri.read_metadata()

        self.assertEqual(data['prompt'], "Turn right 90 (face right wall)")

        # files is a dictionary of the file names as keys and md5hashes as value
        files = data['checksums']
        self.assertEqual(len(files.keys()), 3)
        self.assertTrue(files.has_key("2_2_1_11_001left.wav"))
        self.assertEqual(files["2_2_1_11_001left.wav"], "5cd13fbee3e1eb55e08e5cca29beb25f")

        # clean up
        shutil.rmtree(tempdir)

 
    def test_validate_files(self):
        """The validate_files method correctly checks the
        metadata against the files on the file system"""

        gooddir = "test/sample_data/correct/Spkr2_2_Session1/Session1_11"
        ri = RecordedItem(gooddir, "2_2_1_11_001")
        self.assertEqual(ri.validate_files(), ([], []))

        baddir = "test/sample_data/incorrect/Spkr2_2_Session1/Session1_11"
        ri = RecordedItem(baddir, "2_2_1_11_001")
        self.assertEqual(ri.validate_files(), ([u'File 2_2_1_11_001left.wav has incorrect checksum', u'File 2_2_1_11_001right.wav has incorrect checksum'], []))

        ri = RecordedItem(baddir, "2_2_1_11_002")
        self.assertEqual(ri.validate_files(), ([u'File this_file_is_missing.wav is in metadata but not on disk', u'File 2_2_1_11_002camera-1.raw16 is on disk but not in metadata'], []))

        # make an empty xml file for this item which will force re-generation of the metadata
        xmlfile = os.path.join(baddir, "2_2_1_11_020.xml")
        self.addCleanup(lambda: os.unlink(xmlfile))
        h = open(xmlfile, 'w')
        h.write('')
        h.close()
        ri = RecordedItem(baddir, "2_2_1_11_020")
        self.assertEqual(ri.validate_files(), ([], ['Calibration - Item 20 (2_2_1_11_020) metadata was missing and has been re-generated']))



    def test_lookup_prompt(self):
        """Can we look up the prompt for an item"""
        
        dir = "test/sample_data/correct/Spkr2_2_Session1/Session1_11"
        ri = RecordedItem(dir, "2_2_1_11_001")
        
        self.assertEqual(ri.lookup_prompt(), "Turn right 90  (face right wall)  2")
        
        
 
    def test_reconstruct_metadata(self):
        """When a metadata file is missing for an item, we try to
        reconstruct it"""

        # need to force metadata reconstruction
        config.set_config("GRAB_CAMERAS_IF_MISSING", "no")
        # set up camera numbers in config
        cameraSN0 = "00000001"
        cameraSN1 = "00000002"
        config.set_config("CAMERASN0", cameraSN0)
        config.set_config("CAMERASN1", cameraSN1)

        baddir = "test/sample_data/incorrect/Spkr2_2_Session1/Session1_11"
        ri = RecordedItem(baddir, "2_2_1_11_003")

        # xml file that should be made
        xmlname = os.path.join(ri.path, ri.basename + ".xml")

        # remove the generated xml file
        self.addCleanup(lambda: os.unlink(xmlname))

        # try to validate, should show up the lack of metadata
        self.assertEqual(ri.validate_files(), ([], ['Calibration - Item 3 (2_2_1_11_003) metadata was missing and has been re-generated']))

        self.assertTrue(os.path.exists(xmlname), "XML metadata file has not been generated")

        # check the camera numbers
        self.assertTrue(ri.has_key('cameraSN0'), "Missing cameraSN0 after metadata regeneration")
        self.assertEquals(ri['cameraSN0'], cameraSN0)


    @unittest.skip("calibration can't be found")
    def test_convert_video(self):
        """We can convert the video files for an item"""

        datadir = os.path.join("../../test", "sample_data", "realdata", "Spkr1_1121_Session1", "Session1_12")
        basename = "1_1121_1_12_001"

        # this doesn't work since videoconvert doesn't use config for this info, it still uses Const
        # so we don't have a way of telling it where the calibration files are
        config.set_config("PATH_CALIBRATION_FILES", os.path.join("..", "..", "test", "sample_data", "realdata", "cal"))

        ri = RecordedItem(datadir, basename)
        tempdir = tempfile.mkdtemp()
        logfile = "log.txt"

        success, newfiles, errors = ri.convert_video(tempdir, logfile)

        expected = [u'Spkr1_1121_Session1/Session1_12/1_1121_1_12_001-ch1-maptask.wav',
                    u'Spkr1_1121_Session1/Session1_12/1_1121_1_12_001-ch6-speaker.wav',
                    u'Spkr1_1121_Session1/Session1_12/1_1121_1_12_001-ch4-c2Left.wav',
                    u'Spkr1_1121_Session1/Session1_12/1_1121_1_12_001-ch5-c2Right.wav',
                    u'Spkr1_1121_Session1/Session1_12/1_1121_1_12_001-camera-0-left.mp4',
                    u'Spkr1_1121_Session1/Session1_12/1_1121_1_12_001-camera-0-right.mp4']

        self.assertEqual(sorted(newfiles), sorted(expected))

        # check the layout of files in the target dir
        """
        finalised = os.path.join(tempdir, "finalised")
        expected = [ (finalised, ['metadata', 'video', 'audio'], []),
                     (os.path.join(finalised, 'metadata'), ['Spkr1_1121_Session1'], []),
                     (os.path.join(finalised, 'metadata/Spkr1_1121_Session1'), ['Session1_12'], []),
                     (os.path.join(finalised, 'metadata/Spkr1_1121_Session1/Session1_12'), [], ['1_1121_1_12_001.xml']),
                     (os.path.join(finalised, 'video'), ['Spkr1_1121_Session1'], []),
                     (os.path.join(finalised, 'video/Spkr1_1121_Session1'), ['Session1_12'], []),
                     (os.path.join(finalised, 'video/Spkr1_1121_Session1/Session1_12'), [], ['1_1121_1_12_001-camera-0-right.mp4', '1_1121_1_12_001-camera-0-left.mp4']),
                     (os.path.join(finalised, 'audio'), ['Spkr1_1121_Session1'], []),
                     (os.path.join(finalised, 'audio/Spkr1_1121_Session1'), ['Session1_12'], []),
                     (os.path.join(finalised, 'audio/Spkr1_1121_Session1/Session1_12'), [], ['1_1121_1_12_001-ch1-maptask.wav', '1_1121_1_12_001-ch6-speaker.wav', '1_1121_1_12_001-ch4-c2Left.wav', '1_1121_1_12_001-ch5-c2Right.wav'])
                     ]
        dirtree = [f for f in os.walk(finalised)]
        self.assertEqual(dirtree, expected)
        """
        
        # print tempdir        
        shutil.rmtree(tempdir)


    @unittest.skip("upload needs server configured")
    def test_upload_files(self):
        """tests file_upload
             1) upload a correct session
             2) upload session with incorrect checksum (error)
             3) upload session without xml file (error)"""
        # run with python datahandling/test/RecordedItemTests.py -vvv RecordedItemTests.test_upload_files

        tempdir = tempfile.mkdtemp()
        logfile = "log.txt"

        # upload a correct file
        cordir = "../../test/sample_data/correct/Spkr2_2_Session1/Session1_11"
        ri = RecordedItem(cordir, "2_2_1_11_001")
        ri.unupload_files()
        success, failed = ri.upload_files(self.host, logfile)

        self.assertEqual(success, True)
        self.assertEqual(failed, [])
        # check that the file is indeed on the server
        data_selector = "/forms/reports/data/%(colour)s/%(animal)s/%(session)s/%(component)s/%(item)s/" % ri
        for f in ri.fileList():
            fu = urllib2.urlopen( "%s://%s%s%s" % (proto, self.host, data_selector, f,) ).read() # uploaded
            fl = open(os.path.join(ri.path, f)).read()
            self.assertEqual(hashlib.sha224(fl).hexdigest(), hashlib.sha224(fu).hexdigest())

        # upload a file which does not have an xml file on the website (incorrect)
        incordir = "../../test/sample_data/incorrect/Spkr2_2_Session1/Session1_11"
        ri = RecordedItem(incordir, "2_2_1_11_020")
        ri.unupload_files()
        success, failed = ri.upload_files(self.host, logfile)

        self.assertEqual(success, False)
        self.assertEqual(len(failed), 4)     # missing xml file + 3 regular (existing) files

        # upload a file with an incorrect content (checksum) (incorrect)
        ri = RecordedItem(incordir, "2_2_1_11_001")
        ri.unupload_files()
        success, failed = ri.upload_files(self.host, logfile)

        self.assertEqual(success, False)
        # files with incorrect checksum in the xml
        self.assertEqual(failed, [
                     (u'2_2_1_11_001.xml, 2_2_1_11_001camera-1.raw16, 2_2_1_11_001left.wav, 2_2_1_11_001right.wav',
                     "Error: checksum for the original file and uploaded file `2_2_1_11_001left.wav' do not match\n")
                     ])

        shutil.rmtree(tempdir)


    @unittest.skip("Comment out before checkin")
    def test_compress_and_upload(self):
        tempdir = tempfile.mkdtemp()
        logfile = os.path.join(tempdir, "log.txt")
        cordir = "../../test/sample_data/correct/Spkr2_2_Session1/Session1_11"
        
        ri = RecordedItem(cordir, "2_2_1_11_001")        
        ri.convert_video_and_upload(tempdir, self.host, logfile)

        val = RecordedItem(cordir, "2_2_1_11_001")
        val.read_metadata()

        self.assertEqual(val['uploaded'], ['2_2_1_11_001left.wav', '2_2_1_11_001right.wav'])

        # Clean up any temporary data
        # print tempdir
        shutil.rmtree(tempdir)


if __name__=='__main__':
    unittest.main()
