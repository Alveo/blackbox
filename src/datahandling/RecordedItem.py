"""Various utility functions for file copying and handling"""

# obsolete
#from xml.dom import minidom

from xml.etree import ElementTree
import UserDict
import hashlib
import urllib2

import os
import re
import sys
import time
import shutil
from recorder.Const import *
import recorder.Persistence  # for participant info

import socket
import ssl
import mmap

import mimetools
import httplib, mimetypes
from cStringIO import StringIO

import config


config.configinit()
chunk_size = int(config.config("CHUNK_SIZE", 1024*1024*10))     # in bytes

proto = config.config("PROTO", "https")

class RecordedItem(UserDict.DictMixin):
    """Class representing a set of files on disk that are the result of
    recording a single item

    """
    # meta-data keys required for validity
    required_keys = ["participant", "cameraSN1", "cameraSN0", "componentName", "colour",
                     "component", "item", "session", "animal", "timestamp", "basename",
                     "prompt", "files", "path", "uploaded" ]
    size = None


    def __init__(self, path, basename, no_guess_meta=False):
        """Initialise a recorded item given a directory path and
        a file basename. The item acts to collect all files in that
        directory with the common prefix 'basename'
        If no_guess_meta is True we won't try to guess metadata if it's missing."""

        self.path = path
        self.basename = basename
        self.no_guess_meta = no_guess_meta
        self._files = None
        self._compressed_files = None
        self._properties = dict()

        # should validate these two against each other
        self.parse_basename_into_properties()
        self['uploaded'] = []

        # record the software version in the file metadata
        if not self.has_key('version'):
            self['version'] = config.config("VERSION", "testing")

        # this can have the side effect of writing the metadata file if it's
        # missing, so we do it after defaulting all properties
        self.read_metadata()

    ## dictionary methods work on the _properties dict
    def __getitem__(self, key):
        return self._properties[key]

    def keys(self):
        return self._properties.keys()

    def __setitem__(self, key, value):
        self._properties.__setitem__(key, value)

    def __delitem__(self, key):
        self._properties.__delitem__(key)

    # other nice methods
    def __str__(self):
        return self.path + ":" + self.basename +"=>" + str(self.fileList())

    def full_path(self):
        return os.path.join(self.path, self.basename)

    def getsize(self):
        """Return size (MB) that this sessions occupies on the hard drive"""
        if self.size == None:
            self.size = float(self.byte_size()) / (1024*1024)   # to make it MB

        return self.size

    def lookup_prompt(self):
        """Get the correct prompt for this item from
        the lookup table"""

        return recorder.Persistence.ItemPrompt(self["component"], self["item"])


    def get_dir_name(self):
        """ Get the directory name for this item """

        return TPL_RECORDING_PATH % {
            'colourId': int(self['colour']),
            'animalId': int(self['animal']),
            'sessionId': int(self['session']),
            'componentId': int(self['component']),
            'itemId': int(self['item'])
        }

    def get_base_name(self):
        """ Get the recording basename based on the various properties of this item """

        return TPL_RECORDING_FILE % {
            'colourId': int(self['colour']),
            'animalId': int(self['animal']),
            'sessionId': int(self['session']),
            'componentId': int(self['component']),
            'itemId': int(self['item'])
        }


    def getComponent(self):
        """Return a RecordedComponent instance corresponding to
        the component that this item is part of"""

        from RecordedComponent import RecordedComponent
        # remove any trailing slash
        if self.path.endswith(os.path.sep):
            p = self.path[:-1]
        else:
            p = self.path
        (cpath, cbasename) = os.path.split(self.path)
        rc = RecordedComponent(cpath, cbasename)

        return rc


    def verbose_participant(self):
        """Return the full colour-animal name for this participant"""

        participant = recorder.Domain.Participant(int(self['colour']), int(self['animal']))
        return participant.GetColourName() + "-" + participant.GetAnimalName()

    def verbose_component(self):
        """Return the full component name"""

        return recorder.Persistence.ComponentName(self['component'])

    def parse_basename_into_properties(self):
        """Get the session, component, speaker (animal and colour) and item ids
        from the file basename, set these as properties on
        this item."""

        parse_it = re.compile(r'^(\d*)_(\d*)_(\d*)_(\d*)_(\d*)$')
        match = parse_it.search(self.basename)
        if match:
            groups = match.groups()
            self['colour']    = groups[0]
            self['animal']    = groups[1]
            self['session']   = groups[2]
            self['component'] = groups[3]
            self['item']      = str(int(groups[4]))  # do this to trim leading zeros

            # generate two derived properties
            self['participant'] = self.verbose_participant()
            self['componentName'] = self.verbose_component()

        else:
            print os.path.join(self.path, self.basename), "doesn't match the filename pattern"

    def to_html(self):
        """Generate an HTML fragment to link to the recordings in this item
        using readable names"""

        template = """<div class='item'><span>Item %s, Prompt <em>"%s"</em></span>
<ul>
""" % (self['item'], 'prompt' in self.keys() and self['prompt'] or "Unknown")
        for file in self.fileList():
            template += "<li><a href='%s'>%s</a></li>\n" % (file, file)
        template += "</ul>\n"

        return template


    def fileList(self):
        """Return a list of files corresponding to this recording
        that are actually stored on disk"""

        if self._files == None:
            # look for the files on the file system starting with basename
            self._files = []
            if os.path.exists(self.path):
                for f in os.listdir(self.path):
                    # we don't include the XML metadata file in here
                    if os.path.isfile(os.path.join(self.path, f)) and f.startswith(self.basename) and not f.endswith(".xml"):
                        self._files.append(unicode(f))

        return sorted(self._files)

    def byte_size(self):
        """Returns the size of the combined files for this item in bytes"""

        size = 0
        for f in self.fileList():
            fname = os.path.join(self.path, f)
            size += os.path.getsize(fname)
        return size

    def checksums(self, files):
        """Return a dictionary of file checksums for the given list of
        absolute file names, keys are the file basenames, values are the checksums"""

        result = dict()
        for f in files:
            result[os.path.basename(f)] = self.md5hexdigest(f)
        return result

    def md5hexdigest(self, filename):
        """Compute an md5 signature for the given file,
        return the signature as a Hex digest string.
        filename is an absolute filename."""

        # if there is no file here, return a dummy checksum
        if not os.path.exists(filename):
            return "missing file"

        md5 = hashlib.md5()
        with open(filename,'rb') as f:
            for chunk in iter(lambda: f.read(1024*md5.block_size), ''):
                md5.update(chunk)
        return md5.hexdigest()


    def validate_checksum(self, filename, checksum):
        """check that the claimed checksum for this file is correct,
        Return True if it is, False otherwise"""

        realcs = self.md5hexdigest(os.path.join(self.path, filename))
        return realcs.strip() == checksum.strip()


    def validate_files(self):
        """Validate all file checksums against those recorded in the item metadata XML file.
        Return a tuple of (errors, warnings) listing any errors or warnings that are found.
        Errors should mean that the session is invalid Warnings are just for information, session is still valid."""

        warnings = []
        errors = []

        # get the files from the file system
        foundfiles = self.fileList()

        # check that we have all the files
        for filename in self['files']:
            if not filename in foundfiles:
                errors.append("File %s is in metadata but not on disk" % (filename,))

        # don't check for the checksum if a file is not on the disk
        for filename in filter(lambda x : x in foundfiles, self['checksums'].keys()):
            if not self.validate_checksum(filename, self['checksums'][filename]):
                errors.append("File %s has incorrect checksum" % (filename,))

        if len(self['files']) == 0:
            # this means there are no data files for this item, we can check to see whether that's true
            # by looking on the file system
            files = self.fileList()
            if files == []:
                # we have an empty item,it should be reported but deleted
                warnings.append('%s - Item %s (%s) has no data.' % (self.verbose_component(), str(self['item']),  self.basename))
            else:
                # there isn't any metadata, the file was missing or empty or corrupted
                # try to regenerate the metadata
                # should never happen now since we re-generate in read_metadata
                self._guess_metadata()
                warnings.append('%s - Item %s (%s) metadata was missing and has been re-generated' %  (self.verbose_component(), str(self['item']),  self.basename))

        else:
            # note any files on disk that aren't in the metadata
            for filename in foundfiles:
                if not filename in self['files']:
                    errors.append("File %s is on disk but not in metadata" % (filename,))

        return (errors, warnings)


    def _guess_metadata(self):
        """IN the situation when we have a missing metadata file we can try to
        reconstruct it from the item basename and other context.
        Write a new metadata file, return self"""


        if self.no_guess_meta:
            return self

        files = self.fileList()

        if len(files) == 0:
                # no files, no metadata, we got nothing...
            return self

        # work out the timestamp from the creation time of one of the files
        self['timestamp'] = time.ctime(os.stat(os.path.join(self.path, files[0])).st_ctime)

        # get the prompt from the lookup table
        self['prompt'] = self.lookup_prompt()

        # include a flag to say that we regenerated this
        self['regenerated'] = "REGENERATED METADATA"

        self._grab_cameras_sn()

        self.write_metadata()

        return self

    def read_metadata(self):
        """Read item metadata from the given filename
        Populates our dictionary of properties and values
        All elements become dictionary keys with their text
        content as a value except 'files' and 'checksums' which
        become a list (of filenames) and a dictionary with
        file name keys and hash values"""
        """Also, there is a list of files which have been uploaded self['uploaded']"""

        filename = os.path.join(self.path, self.basename + ".xml")

        # ensure self has these always defined
        self["checksums"] = dict()
        self['files'] = []
        self['uploaded'] = []


        # two error conditions where we fail silently, there should be a
        # way to report these back to somewhere
        if not os.path.exists(filename):
            return self._guess_metadata()

        try:
            dom = ElementTree.parse(filename)
        except ElementTree.ParseError:
            return self._guess_metadata()

        if dom.getroot() is None:
            # no root element found  => corrupted xml
            return self._guess_metadata()

        for node in dom.getroot():
            name = node.tag
            if name == "files":
                    # we make a list of the filenames
                for ch in node.findall(".//file"):
                    filename = ch.text
                    # early versions were writing .xml files into the metadata, we don't
                    # want to know about that
                    if not filename.endswith(".xml"):
                        self["files"].append(filename)
                        if ch.get('uploaded') == 'true':
                            self['uploaded'].append(filename)
                        # TODO: might be new style with md5 as an attribute
                        if ch.get('md5hash') is not None:
                            self["checksums"][filename] = ch.get('md5hash')

            elif name == "checksums":
                # handle old style checksums in a separate element
                for ch in node.findall(".//md5hash"):
                    filename = ch.get('file')
                    self["checksums"][filename] = ch.text
            elif name == "uploaded":
                    #TODO: ignore for now
                pass
            else:
                self[name] = node.text
        return self


    def rename_item(self, colour, animal, component, item, logger, test_mode = False):
        """ This function renames an item. The action of renaming changes the items meta data.
        The speaker id is represented by a colour and animal.
        """
        meta_data = self.read_metadata() # This actually passes back a reference to self
        meta_data['colour'] = colour
        meta_data['animal'] = animal
        meta_data['component'] = component
        meta_data['item'] = item

        # refresh the verbose names for participant and component
        meta_data['participant'] = self.verbose_participant()
        meta_data['componentName'] = self.verbose_component()

        # Write the meta data back to disk but before doing doing so check to see if a file exists
        base_name = '%s_%s_%s_%s_%s' % (str(colour), str(animal), meta_data['session'], str(component), self.get_canonical_item_name(item))
        meta_data['basename'] = base_name
        file_name = base_name + '.xml'

        # Obtain the new output location and update the meta data to reflect this
        destination_folder = self.get_destination_folder(self.path, colour, animal, meta_data['session'], component)
        meta_data['path'] = destination_folder

        if os.path.exists(os.path.join(destination_folder, file_name)):
            raise IOError('Cannot rename %s_%s_%s_%s_%s, a duplicate exists' % (colour, animal, meta_data['session'], component, self.get_canonical_item_name(item)))


        if not test_mode:
            # If the destination folder does not exist then create it
            if not os.path.exists(destination_folder):
                logger.log('Making directory %s' % (destination_folder))
                os.makedirs(destination_folder)

        # Now rename the documents as listed in the  meta data
        associated_files = self.fileList()
        new_file_list = []
        for associated_file in associated_files:
            # Rename each file as well
            new_associated_file = re.sub('\d+_\d+_\d+_\d+_\d+', base_name, associated_file)

            # Make sure that the upload status is tracked
            if associated_file in meta_data['uploaded']:
                self['uploaded'].append(new_associated_file)

            new_file_list.append(new_associated_file)
            if not test_mode:
                # The rename implicitly performs the move of the file across to the new folder
                logger.log('Renaming \n\t%s to \n\t%s' % (os.path.join(self.path, associated_file), os.path.join(destination_folder, new_associated_file)))
                os.rename(os.path.join(self.path, associated_file), os.path.join(destination_folder, new_associated_file))


        # Update the uploaded list to match the new list of file names
        meta_data['uploaded'] = [item for item in meta_data['uploaded'] if item in new_file_list]


        # If no exception has been raised then write the new meta data and delete the old file
        if not test_mode:
            logger.log('Writing meta data to file %s' % (os.path.join(destination_folder, file_name)))
            self.write_metadata(path = destination_folder, copiedFiles = new_file_list, filename = os.path.join(destination_folder, file_name))
            os.remove(os.path.join(self.path, self.basename + '.xml'))


        # Return the name of new item
        return base_name


    def get_destination_folder(self, path, colour, animal, session, component):
        """ The destination folder is determined by the session and component identifier
        the following piece of code determines this (This is here though the session cannot change)
        """
        grand_parent_folder = os.path.split(path)[0]
        great_grand_parent = os.path.split(grand_parent_folder)[0]
        new_grand_parent  = os.path.join(great_grand_parent, self.get_canonical_gpfolder_name(colour, animal, session))

        new_parent_folder = self.get_canonical_folder_name(session, component)
        return os.path.join(new_grand_parent, new_parent_folder)


    def get_canonical_gpfolder_name(self, colour, animal, session):
        """ This function returns the name of the speaker/session folder name which follows the naming
        convention Spkr{colour}_{animal}_Session{sessionid} """
        return 'Spkr%s_%s_Session%s' % (colour, animal, session)


    def get_canonical_folder_name(self, session, component):
        """ This function converts a session and component to the correct folder name """
        return 'Session%s_%s' % (session, component)


    def get_canonical_item_name(self, item):
        """ This function returns the canonical name of an item. Item names are 3 digit numbers always """
        item_str = str(item)
        for index in range(len(item_str), 3):
            item_str = '0' + item_str

        return item_str


    def _grab_cameras_sn(self):
        # check whether we have the camera serial numbers and grab them from the
        # hardware if not

        if config.config("GRAB_CAMERAS_IF_MISSING", "no") == "yes":
            if not self.has_key("cameraSN0"):
                # use the videoconvert library to get the info since if we're
                # recording, we'll have it (ie. this is just for old data
                import videoconvert
                self["cameraSN0"] = videoconvert.cameraSerial(0)
                self["cameraSN1"] = videoconvert.cameraSerial(1)
        else:
            # we're not allowed to look at the hardware,
            # so we look in the config file
            # default them to '0' if not found
            cameraSN0 = config.config("CAMERASN0", 0)
            cameraSN1 = config.config("CAMERASN1", 0)

            self['cameraSN0'] = cameraSN0
            self['cameraSN1'] = cameraSN1

        return self


    def write_metadata(self, path=None, copiedFiles=[], filename = None):
        """Convert our properties dict into XML with a few special cases
        for lists of files and md5 hashes.
        Gives special version if you ask for copied version

        In the normal version, the object is quized for metadata and all
        but its files and checksums are
        populated this way.  Files are populated by the list calculated by
        listFiles and a fresh checksum
        is calculated on each of these

        The path argument is used to set the base path for the copied
        files since we don't write absolute paths to metadata. If path=None
        (the default) then the path of the RecordedItem is used, otherwise
        it should be the absolute path to the root of the file names that
        are to be written out

        """


        # if path is None then we are writing metadata for the files that belong
        # to this item
        if path is None:
            path = self.path
            files = self.fileList()
            checksums = self["checksums"]
        else:
            # we are writing metadata for a new copied set of files
            files = copiedFiles
            checksums = None

        fullpaths = [os.path.join(path, f) for f in files]

        # work out the destination
        if filename is None:
            filename = os.path.join(path, self.basename + ".xml")

        # if we already have checksums, then we can write the file
        # directly, if not, we write once without them, then
        # calculate and write again to ensure we don't lose
        # data if we're interrupted during a long checksum
        # calculation
        if checksums:
            xml = self.generate_metadata_xml(path, files, checksums)

            fh = open(filename, "w")
            fh.write(xml)
            fh.close()

        else:
            xml = self.generate_metadata_xml(path, files, None)

            fh = open(filename, "w")
            fh.write(xml)
            fh.close()

            checksums = self.checksums(fullpaths)
            xml = self.generate_metadata_xml(path, files, checksums)

            fh = open(filename, "w")
            fh.write(xml)
            fh.close()


    def generate_metadata_xml(self, path, files, checksums=None):
        """Generate the XML to write out to the metadata file
        files is a list of files that we reference
        checksums is a dictionary of file checksums"""

        from xml.etree.ElementTree import Element, tostring


        root = Element("item")
        for k in filter(lambda x: not (x in ("files", "checksums", "path")), self.keys()):
            el = Element(k)
            el.text=str(self[k])
            root.append(el)


        el = Element("files")

        for item in files:
            i = Element("file")
            # take care just to write the basename to the metadata file
            i.text = str(os.path.basename(item))

            # record the uploaded status
            i.attrib['uploaded'] = i.text in self['uploaded'] and "true" or "false"

            # write file checksum if present
            if checksums and checksums.has_key(item):
                i.attrib['md5hash'] = checksums[item]

            el.append(i)
        root.append(el)

        # add the path from the local variable, not the property so
        # we get the proper version
        el = Element("path")
        el.text = path
        root.append(el)

        return tostring(root)


    def missing_metadata(self):
        """Check that all the required meta-data fields are present.
        Return a list of missing fields, [] if all is valid"""

        missing_fields = []
        for field in self.required_keys:
            if not self.has_key(field):
                missing_fields.append(field)

        return missing_fields


    def _convert_video_file(self, source, destdir):
        """Convert a single video file (source, a name relative to
        self.path), write the new version
        in the directory destdir. Return the full path to the new
        video files (left and right channels)"""

        # load videoconvert here - loading it earlier causes a conflict
        # with the hardware (SSCPBackend) module
        import videoconvert

        # which camera is this file from
        if source.find("camera-0") >= 0:
            if self.has_key("cameraSN0"):
                cameraSN = int(self["cameraSN0"])
            else:
                raise Exception("Can't find camera serial number for camera 0")
        else:
            if self.has_key("cameraSN1"):
                cameraSN = int(self["cameraSN1"])
            else:
                raise Exception("Can't find camera serial number for camera 1")

        val =  videoconvert.convert(os.path.join(self.path, source), destdir, cameraSN)

        return val


    def convert_video_and_upload(self, dest, host, log):
        """ This function performs compression, but also uploads as a priority. This is because
        we do not want compression failures to get in the way of data uploads. """

        return self._convert_video_internal(dest, log, host, True)


    def convert_video(self, dest, logfile):
        """ This function has been kept for backwards compatibility """
        return self._convert_video_internal(dest, logfile)


    def copy_upload_audio(self, dest, logfile, host=None, upload_data=False):
        """Copy all audio data to dest and attempt to upload it if
        upload_data is True.
        Write updated metadata to dest for the item containing dummy
        entries for any video files expected

        Return (Success?, newFiles, errorDetails)
        """


        # make a path for the data relative to dest
        targetdir = os.path.join(dest,  self.get_dir_name())
        # ensure the directory exists
        try:
            os.makedirs(targetdir)
        except OSError:
            # the directory may have already been created
            # or another subprocess may have created it (race condition)
            pass

        # grab just the audio files
        audio_files = [f for f in self.fileList() if f.endswith(".wav")]

        # copy audio files over to dest
        errors = []
        for f in audio_files:
            try:
                targetfile = os.path.join(targetdir,f)
                shutil.copyfile(os.path.join(self.path, f), targetfile)

            except IOError, err:
                errors = errors + ['copy failed'+str(err)]

        # write metadata to destination

        # we add video files here on the expectation that they will
        # be uploaded later. Here we generate the expected output
        # names for each of the video files we have
        video_files = []
        for f in self.fileList():
            if f.endswith(".raw16"):
                rootname = os.path.splitext(f)[0]
                video_files.append(rootname+"-left.mp4")
                video_files.append(rootname+"-right.mp4")


        self.write_metadata(targetdir, audio_files+video_files)

        if upload_data:
            # now try to upload the audio from the targetdir
            self._upload_files_internal(audio_files, host, logfile, path=targetdir)

            # rewrite the metadata to record the uploaded status of these files
            self.write_metadata(targetdir, audio_files+video_files)

        if len(errors) > 0:
            return (False, audio_files, "Error: copy of audio for item `" + self.basename + "'" + ", ".join(errors))
        else:
            return (True, audio_files, "")



    def _convert_video_internal(self, dest, logfile, host = None, upload_data = False):
        """ Convert all video files to compressed versions and copy to a destination. Update meta-data to reflect
        the compressed status and the location of the compressed files. Write meta-data to original and
        new (compressed) locations.

        Return (Success?, newFiles, errorDetails)"""

        #time.sleep(self.getsize()*float(config.config("COMPRESSION_SPEED", 4)))
        start_time = time.time()
        log = open(logfile, 'a')

        # make a path for the data relative to dest
        targetdir = os.path.join(dest,  self.get_dir_name())

        # ensure the directory exists
        try:
            os.makedirs(targetdir)
        except OSError:
            # the directory may have already been created
            # or another subprocess may have created it (race condition)
            pass

        # first deal with audio
        audio_status, audio_files, errors = self.copy_upload_audio(dest, logfile, host, upload_data)

        # if audio copy failed, there is a major problem with writing to the
        # destination and we don't bother trying to compress video
        if audio_status==False:
            return (False, audio_files, errors)

        video_files = [f for f in self.fileList() if f.endswith('.raw16')]

        # copy the files (raw16 is video, wav is audio)
        new_video_files = []
        errors = []
        for f in video_files:
            # special case, if the video file is empty, we just ignore it
            if os.path.getsize(os.path.join(self.path, f)) == 0:
                errors.append("Skipped empty video file " + os.path.basename(f))
                # just skip, this file won't be added to the file list
                # for the new item
                continue

            try:
                (left, right) = self._convert_video_file(f, targetdir)
                # left or right not exist if compression failed
                # but we add the to the result list all the same
                # so that they end up in the metadata
                new_video_files.append(os.path.basename(right))
                new_video_files.append(os.path.basename(left))
                # we show an error if they don't exist
                if not os.path.exists(left):
                    errors.append("Failed to compress left channel video for " + self.basename)
                if not os.path.exists(right):
                    errors.append("Failed to compress right channel video for " + self.basename)

            except IOError, err:
                errors = "Copy Failed: " + str(err)
                return (False, new_video_files, "Error: compression of item `" + self.basename + "'. " + errors)

        copied_files = audio_files + new_video_files

		# write metadata in destination
        self.write_metadata(targetdir, copied_files)

        log.write("Compressed item : %s : %d : %d\n" % (str(self.basename), self.byte_size(), time.time()-start_time))

        #print "Item: `%s' compressed successfully" % (self.get_base_name(),)

        if upload_data:
            # now try to upload the audio from the targetdir
            self._upload_files_internal(new_video_files, host, logfile, path=targetdir)

        # make paths absolutes
        copied_files = [os.path.join(targetdir,f) for f in copied_files]

        if len(errors) > 0:
            return (False, copied_files, "\n ".join(errors))
        else:
            return (True, copied_files, "")


    def upload_files(self, host, log):
        """ This method has been added for backwards compatibility """
        return self._upload_files_internal(self.fileList(), host, log)


    def _upload_files_internal(self, file_list, host, logfile, path=None):
        """Upload all files to the host server. Update meta-data to reflect the uploaded files and
        upload the modified meta-data to the host server.

        If path is not None, it gives the location of the files to upload, the path is added
        to the file name to get the absolute name of the file to upload.

        Returns a tuple (success, failures) where 'success' is True if all files were successfully uploaded, and
        False otherwise and 'failures' is a list of failure messages (empty if success is True) which consist
        of tuples of two elements, a string with the names of failed files and the server failure response,
        eg. (True, [])
           (False, [(u'1_1123_3_8_001.xml, 1_1123_3_8_001-camera-0-left.mp4', '<html....')])
        """

        # a discussion on paralelizing daemonig processes (multiprocessing)
        # http://www.gossamer-threads.com/lists/python/python/905166
        #<file uploaded="true">2_2_1_11_001right.wav</file>
        start_time = time.time()
        log = open(logfile, 'a')
        skipped = False
        failed = []

        # if path is not provided we upload from our own location
        if path is None:
            path = self.path

        web_prefix = config.config("WEBAPP_PREFIX", "/forms")

        upload_selector = web_prefix + "/reports/upload/real/"   # This is for development only
        redir_selector = web_prefix + "/reports/participants/[0-9]+/"
        alt_redir_selector = web_prefix + "/data/[0-9]+/"    # if participant not known on the site

        fields = [ ('colour', self['colour']), ("animal", self['animal']),
                   ('component', self['component']), ('item', self['item']),
                   ('session', self['session']),
                   ('form-INITIAL_FORMS', "0"), ('form-MAX_NUM_FORMS', ''),
                ]

        xmlfilename = os.path.join(path, self.basename + ".xml")
        if not os.path.exists(xmlfilename):
            return (False, (", ".join([ self.basename+".xml" ] + self.fileList()), "Metadata file `%s' has not been uploaded to the server." % xmlfilename))

        # upload the xml file and all not already uploaded files and note it in the xml file
        forUpload = [ ('form-0-data', self.basename + ".xml", xmlfilename ) ]
        for f in file_list:
            if not f in self['uploaded']:
                num = len(forUpload)    # just to be on the safe side
                forUpload.append(('form-%d-data' % num, f, os.path.join(path, f)))
            else:
                #print "Warning: Skipping file `%s' - has already been uploaded" % (f,)
                skipped = True

        # authentication - ignore?
        # checksum validation is handled on the server, e.g. 500 if incorrect
        errcode, headers, fr = post_multipart(proto, host, upload_selector, fields+[('form-TOTAL_FORMS', str(len(forUpload)))], forUpload)

        if errcode == 302 and \
                      ( re.search(redir_selector, str(headers)) != None or
                        re.search(alt_redir_selector, str(headers)) != None ):
            #print "Files: `%s' uploaded successfully" % (", ".join([ f for fn, f, fp in forUpload ]),)         # debug

            for fn, f, fp in forUpload:
                _mark_uploaded(self.path, self.basename, f, 'true')
                self['uploaded'].append(f)

        else:
            failed.append((", ".join([ f for fn, f, fp in forUpload ]), fr.read()))

        # upload the possibly "new" xml (containing information about uploaded files)
        errcode, headers, fr = post_multipart(proto, host, upload_selector,
                        fields+[('form-TOTAL_FORMS', '1' )], [ ('form-0-data', self.basename+".xml", xmlfilename) ])
        if errcode == 302 and \
                      ( re.search(redir_selector, str(headers)) != None or
                        re.search(alt_redir_selector, str(headers)) != None ):
            # print "Updated metadata: `%s' uploaded successfully" % (self.basename+".xml",)         # debug
            pass
        else:
            failed.append((self.basename+".xml", fr.read()))

        if skipped:
            #print "Item: `%s' already uploaded" % (str(self.basename),)
			pass
        elif len(failed) > 0:
            print "Item: `%s' UPLOAD FAILED" % (str(self.basename),)
            #  just for debugging let's see full failure messages
            if config.config("DEBUG", "No") == "Yes":
                print "FAILURE Messages: "
                for m in failed:
                    print m
        else:
            #print "Item: `%s' uploaded successfully" % (str(self.basename),)
			pass

        log.write("Uploaded item : %s : %d : %d : %s\n" % (str(self.basename), self.byte_size(), time.time()-start_time, str(skipped)))

        return (len(failed) == 0 and True or False, failed)


    def unupload_files(self, filename=""):
        """Mark files as not uploaded in the xml (for testing)"""
        for f in self.fileList():
            if len(filename) == 0 or f == filename:
                _mark_uploaded(self.path, self.basename, f, 'false')
                if f in self['uploaded']:
                    self['uploaded'].remove(f)




def _mark_uploaded(path, basename, filename, value):
    xmlfilename = os.path.join(path, basename + ".xml")
    # if the file's not there, we can't do anything
    if not os.path.exists(xmlfilename):
        return

    # assume the xml file is valid (must have been fixed during read_metadata)
    try:
        dom = ElementTree.parse(xmlfilename)
    except ElementTree.ParseError:
        # parse error, we can't really recover
        raise Exception("XML parse error in mark uploaded for file %s" % basename)

    for el in dom.getroot().findall('.//file'):
        if el.text == filename:
            el.set('uploaded', value)
            dom.write(xmlfilename)
            break


def post_multipart(proto, host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body, length = encode_multipart_formdata(fields, files)

    h = (proto == "https" and httplib.HTTPSConnection(host) or httplib.HTTPConnection(host))
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', length)
    try:
        h.endheaders()

        # send the form data
        for chunk_text, chunk_mfile in body:
            h.send(chunk_text)
            while True:
                file_chunk = chunk_mfile.read(chunk_size)
                if len(file_chunk) == 0:
                            # the end of the file
                    break
                h.send(file_chunk)
            chunk_mfile.close()

        resp = h.getresponse()      # (hopefully) receive a response from the server
    # the exception must be specific, otherwise it also catches exceptions from the multiprocessing module
    #+the subprocesses cannot be terminated
    except (socket.gaierror, socket.error, httplib.HTTPException, ssl.SSLError):
        # if anything goes wrong on the client side
        return 600, '', StringIO('Unspecified client error')

    # read on resp returns a body of the response, getheader is case insensitive
    return resp.status, resp.getheader('Location'), resp


def encode_multipart_formdata(vars, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body, length of body), body is composed of a list of (text, datafile as mmap.mmap object)
    """
    boundary = mimetools.choose_boundary()
    body = []
    text = ''
    length = 0
    # assume that form data are never too long, only files are potentially long
    for(key, value) in vars:
        text += '--%s\r\n' % boundary
        text += 'Content-Disposition: form-data; name="%s"' % key
        text += '\r\n\r\n' + str(value) + '\r\n'

    for(key, filename, filepath) in files:
        openfile = open(filepath, "rb")
        contenttype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
        text += '--%s\r\n' % boundary
        text += 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename)
        text += 'Content-Type: %s\r\n' % contenttype
        text += '\r\n'
        fsize = os.path.getsize(filepath)
        #data = mmap.mmap(openfile.fileno(), fsize > chunk_size and chunk_size or fsize, access=mmap.ACCESS_READ)
        #data = mmap.mmap(openfile.fileno(), 0, access=mmap.ACCESS_READ)
        data = openfile
        body.append((text, data))
        length += len(text) + fsize
        text = '\r\n'   # start with new text data

    text += '--' + boundary + '--\r\n\r\n'

    body.append((text, StringIO('')))   # we're done here (StringIO is a file-like interface as well as mmap.mmap)
    length += len(text) + len('')

    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body, length
#END borrowed code


# this is the main callable for metadata from the Protocol module

import threading

def Metadata(participant, session, component, item, path, filename, prompt, cameras, maptask=False):
    """ Logs the information related to the state of sessions """

    # write item metadata to filename.xml in simple XML format
    # append a line to path/metadata.csv with the same information (DEFERRED)

    if not os.path.exists(path):
        # we can't do anything, fail silently
        print "PATH DOESN'T EXIST: ", path
        return

    # colour, animal, session, component and item are derived from the filename
    recitem = RecordedItem(path, filename, no_guess_meta=True)
    recitem['timestamp'] = time.ctime()
    recitem['path'] = path
    recitem['prompt'] = prompt
    recitem['basename'] = filename
    recitem['cameraSN0'] = cameras[0]
    recitem['cameraSN1'] = cameras[1]

    if maptask:
        recitem['otherColour'] = maptask['colourId']
        recitem['otherAnimal'] = maptask['animalId']
        recitem['otherParticipant'] = maptask['participant']
        recitem['map'] = maptask['map']
        recitem['role'] = maptask['role']

    # call write_metadata in another thread so that we don't hold up
    # the session
    thread = threading.Thread(target=recitem.write_metadata, args=[])
    thread.start()
    #recitem.write_metadata()
