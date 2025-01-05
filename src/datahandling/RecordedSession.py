import os
from datahandling import *
import string
import re
from datetime import date
from datahandling.RecordedItem import post_multipart
import urllib2

import config
import shutil

config.configinit()
proto = config.config("PROTO", "https")

def session_list_item_generator(sessions):
    
    from itertools import chain
    
    return chain.from_iterable([s.item_generator() for s in sessions])


def find_existing_sessions(dirname):
    """
    Returns a tuple of a list of sessions and a list of errors
    Ignores files starting with .
    """

    try:
        fullList = os.listdir(dirname)
    except:
        return ([], ["directory listing failed for " + dirname])

    sesspattern = re.compile("Spkr([01234ab]+)_([0-9]+)_Session([0-9]+)")
    sesslist = filter(lambda x: sesspattern.match(x), fullList)

    sessions = []
    errors = []
    # sessions are all the directories in source
    for x in sesslist:
        try:
            sessions.append(RecordedSession(dirname, x))
        except Exception as err:
            errors.append("RecordedSession(%s, %s): %s" % (dirname, x, str(err)))

    # sort the sessions from the biggest in size (first) to the smallest
    #sessions.sort(cmp=lambda x, y: cmp(x.getsize(), y.getsize()), reverse=True)

    return (sessions, errors)


def parse_validation_report(report):
    """Parse a standard validation report and return a
    triple (ok, errors, warnings) where ok is True or False
    based on whether the report has errors, errors is a 
    list of error messages and warnings is a list of 
    warnings"""
    
    errors = []
    warnings = []
    readwarns = False
    for line in report.split('\n'):
        if line == "Errors:" or line == "":
            continue
        elif line == "Warnings:":
            readwarns = True
        else:
            if readwarns:
                warnings.append(line.rstrip("\n"))
            else:
                errors.append(line.rstrip("\n"))
                
    return (len(errors)==0, errors, warnings)
    

def generate_validation_report(errors, warnings):
    """Generate the standard validation report format, return
    it a a string"""
    
    report = "Errors:\n"
    report += "\n".join(errors)
    report += "\n\n"
    report += "Warnings:\n"
    report += "\n".join(warnings) 
    
    return report

class RecordedSession():

    dirpattern = re.compile("Session([1234ab]+)_([0-9]+)")
    size = None

    def __init__(self, path, basename, no_guess_meta=False):
        self.path = path
        self.basename = basename
        self.no_guess_meta = no_guess_meta
        self.manifest = "manifest.txt"
        self.validation = "validation.txt"
        self._components = []
        self.find_all_components()
        self.parse_basename_into_properties()

    def __str__(self):
        return 'Spkr%d_%d_Session%s' % (self.colourId, self.animalId, str(self.sessionNumber))

    def full_path(self):
        return os.path.join(self.path, self.basename)

    def manifest_path(self):
        return os.path.join(self.full_path(), self.manifest)

    def parse_basename_into_properties(self):
        """Get the session and speaker ids from the basename and store them"""

        parse_it = re.compile(r'Spkr(\d*)_(\d*)_Session([1234ab]+)')
        match = parse_it.search(self.basename)
        if match:
            groups = match.groups()
            self.colourId    = int(groups[0])
            self.animalId    = int(groups[1])
            self.sessionNumber = int(groups[2])
        else:
            print self.basename, "doesn't match the filename pattern for a session"

    def verbose_participant(self):
        """Return the full colour-animal name for this participant"""

        participant = recorder.Domain.Participant(self.colourId, self.animalId)
        return participant.GetColourName() + "-" + participant.GetAnimalName()


    def find_all_components(self):
        """Find all components directories in our path.
        Populate our _components list"""

        self._components = []
        dirlist = os.listdir(self.full_path())
        for dirname in dirlist:
            if self.dirpattern.match(dirname):
                comp = RecordedComponent(self.full_path(), dirname, no_guess_meta=self.no_guess_meta)
                self._components.append(comp)


    def get_speaker_and_session(self):
        return self.colourId, self.animalId, self.sessionNumber

        
    def rename_speaker(self, colour, animal, logger):
        """ This method allows a speaker to be renamed as defined by colour and animal """
        if colour != self.colourId or animal != self.animalId:
            # Only do work if there is a change in the speaker identifier
            self.colourId = colour
            self.animalId = animal
            for component in self.components():
                component.rename_items(colour, animal, component.get_id(), logger)
        
        
    def get_component_folders(self):
        """ This function returns a list containing the names of the sub-folders of this particular session """
        result = []
        for root, dirs, files in os.walk(self.full_path(), topdown = False):
            for item in dirs:
                result.append(item)
                
        return result
             

    def components(self):
        """Return the set of components"""
        return self._components

    def count_items(self):
        count = 0
        for c in self._components:
            count += c.count_items()
        return count
    
    def item_generator(self):
        
        from itertools import chain
        
        return chain.from_iterable([c.item_generator() for c in self._components])


    def add_component_and_chain(self, comp):
        self._components.append(comp)
        return comp


    def getCameras(self, forComponent):
        """Get the camera serial numbers from one of our components.
        If forComponent is not None, then that's the component we don't know camera info
        for, so don't look there.Used in trying to reconstruct lost metadata for an item"""

        components = self.components()
        if len(components) > 1:
                # we might be able to guess from an item
            for c in components:
                if c.basename == forComponent.basename:
                    continue
                else:
                    return c.getCameras()
        
        # and if that didn't work, we don't know
        print "Unable to find camera serial numbers from the session"
        return (0, 0)




    def validate_files(self, nocache=False):
        """Validate a session, return a tuple of (errors, warnings) listing any errors or warnings that are found.
        Errors should mean that the session is invalid Warnings are just for information, session is still valid."""
        
        pvalidation = os.path.join(self.full_path(), self.validation)
        errors = []
        warnings = []
        
        if not nocache and os.path.isfile(pvalidation):
            
            # take validation results from cache
            report = open(pvalidation, "r").read()
            (ok, errors, warnings) = parse_validation_report(report)

            return (errors, warnings)

        
        for comp in self.components():
            try:
                (e, w) = comp.validate_files()
                errors += e
                warnings += w 
            except Exception as err:
                errors.append("Component %d: %s" % (comp.componentId, str(err)))

        errors += self.validate_manifest()
 
        
        # cache validation results
        fvalidation = open(pvalidation, "w")
        fvalidation.write(generate_validation_report(errors, warnings))
        fvalidation.close()

        return (errors, warnings)


    def add_camera_metadata(self, camera0, camera1):
        """Add the camera serial number metadata to all items
        if it's missing"""

        for comp in self.components():
            comp.add_camera_metadata(camera0, camera1)


    def uploaded(self, host):
        sel = "/forms/reports/status/%d/%d/%s" % (self.colourId, self.animalId, self.sessionNumber)
        ok = False
        errors = []
        warnings = []
        try:
            f = urllib2.urlopen(proto + "://" + host + sel)
            resp = f.read()
            # resp is either 'OK' or it's a full validation report
            if resp == "OK":
                return (True, [], [])
            else:
                return parse_validation_report(resp)  
        
        except urllib2.HTTPError:
            # note that HTTPError is a subclass of URLError
            errors = ["Error: error response from server for colour `%d' and animal `%d', please re-try validation" % (self.colourId, self.animalId)]
        except urllib2.URLError:
            errors = ["Error: cannot connect to the server `%s'" % host]
        except httplib.BadStatusLine:
            errors = ["Error: bad response from server for colour `%d' and animal `%d', please re-try validation" % (self.colourId, self.animalId)]

        return (ok, errors, warnings)

    def getsize(self):
        """Return size (MB) that this sessions occupies on the hard drive"""
        if self.size == None:
            size = 0
            for path, dirs, files in os.walk(self.full_path()):
                for f in files:
                    size += os.path.getsize( os.path.join(path, f) )

            self.size = float(size) / (1024*1024)       # to make it MB

        return self.size

    def write_html(self):
        """Write an HTML description of this Session that links
        to all of the components"""

        participant = self.verbose_participant()
        session = self.sessionNumber

        html = "<h2>%s Session %s</h2>" % (participant, session)
        for component in self.components():
            link = component.write_html()
            html += "<li><a href='%s'>%s</a></li>\n" % (link, component.verbose_name())

        fh = open(os.path.join(self.full_path(), "index.html"), "w")
        fh.write(html)
        fh.close()
        return (os.path.join(self.basename, "index.html"), participant + ": Session " + str(session))


    def convert_video(self, dest):
        """Convert video files of all components to compressed versions and copy to a destination. Update meta-data to reflect the compressed status and the location of the compressed files. Write meta-data to original and
        new (compressed) locations. Write a log file (log.txt) in the destination directory listing all operations and timing"""

        log = os.path.join(dest, "log.txt")

        logh = open(log, 'a')
        logh.write("\n")
        logh.write(str(time.time()) + " : processing session : " + str(self.basename)+"\n")
        logh.close()

        for comp in self.components():
            comp.convert_video(dest, log)

        # copy the manifest file
        comprRS = RecordedSession(dest, self.basename)
        comprRS.gen_manifest(isRawDir=False, rawDir=self.path)


    def upload_files(self, host):
        """Upload files of all components to the host server.
        Update meta-data to reflect the uploaded files and upload the modified meta-data
        to the host server.
        Write a log file (log.txt) in the destination directory listing all operations and timing
        Also, upload manifest file."""

        log = os.path.join(self.full_path(), "log.txt")

        logh = open(log, 'a')
        logh.write("\n")
        logh.write(str(time.time()) + " : uploading session : " + str(self.basename)+"\n")
        logh.close()

        self.upload_manifest(host)
        for comp in self.components():
            comp.upload_files(host, log)


    def unupload_files(self, filename=""):
        """Mark files as unuploaded in xml. Just for testing"""
        for comp in self.components():
            comp.unupload_files(filename)


    def gen_manifest(self, isRawDir, rawDir=None, writeManifest = True, version = None, manifest_date = None):
        """Generate a manifest file for this session into self.full_path()/self.manifest
        and copy it to dest (if given); if a file already exists, only copy it to a new dest
        (never regenerate)"""
        
        # make sure rawDir is here when we're not rawDir
        if not isRawDir and not os.path.exists(rawDir):
            print "Error: in generating manifest for `%s' (no rawDir specified)" % self.basename
            return

        manifest = ''

        if isRawDir:
            # If writeManifest is true then check to see if a manifest file
            # already exists at the location already
            if not (writeManifest and os.path.exists(self.manifest_path())):
                __version__ = '1.0'

                manifest  = version == None and '@version: '+__version__+'\n' or version + '\n'
                manifest += manifest_date == None and '@date: '+date.today().strftime("%Y-%m-%d")+"\n" or manifest_date + "\n"
                manifest += '\n'

                # get all files from the subdir. tree of dest, reduce filenames to session identifiers,
                #+unify
                manifest += "\n".join(
                                        _unify(
                                        map(lambda x: re.match('\d+_\d+_\d+_\d+_\d+', x).group(),
                                        filter(lambda x: re.match('\d+_\d+_\d+_\d+_\d+', x) != None,
                                                _findfiles(self.full_path())))))
                                                
                # possibly truncate an existing file
                if writeManifest:
                    f = open(self.manifest_path(), 'w')
                    f.write(manifest)
                    f.close()
                    print "Notice: manifest file for raw session `%s' successfully generated" % self.basename
                    
            else:
                print "Warning: manifest file for raw session `%s' already exists (nothing done)" % self.basename
        else:
            # we need to generate the manifest in the rawDirectory first and then copy it here
            rawRS = RecordedSession(rawDir, self.basename)
            rawRS.gen_manifest(isRawDir=True)
            if rawRS.full_path() != self.full_path():
                shutil.copy(rawRS.manifest_path(), self.manifest_path())
                print "Notice: manifest file for compressed session `%s' copied from raw session" % (self.basename,)
            # else: I've just generated the manifest for myself

        return manifest


    def read_manifest(self):
        """Read the manifest file and return a list of items"""

        if os.path.exists(self.manifest_path()):
            result = []
            f = open(self.manifest_path(), 'r')
            for line in f:
                if not line.startswith("@") and not len(line.strip()) == 0:
                    result.append(line.strip())
            f.close()
            return result
        else:
            return None


    def read_raw_manifest(self):
        """Read the raw manifest file and return a list of items"""

        if os.path.exists(self.manifest_path()):
            result = []
            f = open(self.manifest_path(), 'r')
            for line in f:
                result.append(line.strip())
            f.close()
            return result
        else:
            return None
        
        
    def upload_manifest(self, host):
        if os.path.isfile(self.manifest_path()):
            proto = config.config("PROTO", "https")
            redir_selector = "/forms/reports/participants/[0-9]+/"
            alt_redir_selector = "/forms/data/[0-9]+/"      # if participant not known on the site

            fields = [ ('colour', str(self.colourId)), ("animal", str(self.animalId)),
               ('session', str(self.sessionNumber)), ('form-TOTAL_FORMS', '3'),
               ('form-INITIAL_FORMS', "0"), ('form-MAX_NUM_FORMS', ''),
            ]

            errcode, headers, fr = post_multipart(proto, host, "/forms/reports/upload/manifest/",
                                            fields, [('form-0-data', self.manifest, self.manifest_path())])
            if errcode == 302 and \
                          ( re.search(redir_selector, str(headers)) != None or
                            re.search(alt_redir_selector, str(headers)) != None ):
                print "Notice: manifest file for session `%s' uploaded successfully." % self.basename
            else:
                print "Error: upload of manifest file for session `%s' failed." % self.basename
        else:
            print "Warning: manifest file for session `%s' does not exist (nothing done)." % self.basename


    def validate_manifest(self):
        """Validate this session against its manifest file (if present)
        Return a list of validation errors, [] if there are none."""

        if os.path.isfile(self.manifest_path()):
            manifest_items = self.read_manifest()

            allitems = [ i.get_base_name() for i in self.item_generator() ]
 
            # items not in allitems have some data but no metadata
            # we'll try to regenerate the metadata
            missing = filter(lambda x: x not in allitems, manifest_items)

            # manifest_items - allitems (set minus)
            return map(lambda x: "Item %s not found" % x, missing)

        else:
            # we have no manifest, we could try to make one
            return ["Error: manifest file for session `%s' does not exist!" % self.basename]


def _findfiles(directory):
    """list all files in a subdirectory (recursive)"""
    files = []
    if os.path.exists(directory):
        for f in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, f)):
                files += _findfiles(os.path.join(directory, f))
            else:
                files.append(f)

    return files

def _unify(l):
    """Unify a list (remove duplicates)"""
    d = {}
    for i in l:
        d[i] = 1
    return d.keys()
