import os
import time
import re
import recorder

class RecordedComponent():
    
    def __init__(self, path, basename, no_guess_meta=False):
        
        self.path = path
        self.basename = basename
        self.no_guess_meta = no_guess_meta
        self._items = []
        self.parse_basename_into_properties()


    def add_item_and_chain(self, item):
        self._items.append(item)
        return item

    def full_path(self):
        return os.path.join(self.path, self.basename)


    def get_id(self):
        """ Returns the components identifier """
        return self.componentId


    def verbose_name(self):
        """Return the full component name"""

        return recorder.Persistence.ComponentName(self.componentId)

    def parse_basename_into_properties(self):
        """Get the session, component numbers from the basename and store them"""

        parse_it = re.compile(r'^Session(\d*)_(\d*)$')
        match = parse_it.search(self.basename)
        if match:
            groups = match.groups()
            self.sessionId    = int(groups[0])
            self.componentId    = int(groups[1])
        else:
            print os.path.join(self.path, self.basename), "doesn't match the filename pattern"

    def getSession(self, no_guess_meta=False):
        """Return a RecordedSession instance corresponding to
        the session that this component is part of"""

        from RecordedSession import RecordedSession
        # remove any trailing slash
        if self.path.endswith(os.path.sep):
            p = self.path[:-1]
        else:
            p = self.path
        (cpath, cbasename) = os.path.split(self.path)
        rs = RecordedSession(cpath, cbasename, no_guess_meta = no_guess_meta)

        return rs

    def _find_item_names(self):
        """Return a list of file basenames of files that
        might be our items"""

        itemname_set = []
        fullItemList = os.listdir(self.full_path())
        for filename in fullItemList:
            basename = os.path.splitext(filename)[0]
            m = re.match('\d+_\d+_\d+_\d+_\d+', basename)
            if m:
                itemname = m.group()
                if not itemname in itemname_set:
                    itemname_set.append(itemname)
        return itemname_set
    
    
    def getItems(self):
        """Return a list of RecordedItem instances for all
        of our items"""
        
        if self._items == []:
            self._items = list(self.item_generator())

        return self._items


    def rename_items(self, colour, animal, component, logger, test_mode = False):
        """ This function renames x number of items as part of a component """
        items = self.item_generator()
        for ri in items:
            ri.rename_item(colour, animal, component, ri['item'], logger, test_mode)
        
        
    def item_generator(self):
        """return a generator over the items in this component"""
        from RecordedItem import RecordedItem 
        from itertools import imap
        itemnames = self._find_item_names()
        return imap(lambda i: RecordedItem(self.full_path(), i, no_guess_meta=self.no_guess_meta), itemnames)


    def count_items(self):
        """Return a count of our items, much faster than
        find_all_items since we don't instantiate RecordedItems for
        each item"""
        
        return len(self._find_item_names())


    def to_html(self):
        """Generate an HTML description of this Component that links
        to all of the items"""

        if self.count_items() == 0:
            return "<h2>Empty Component</h2>"

        items = self.getItems()
        participant = items[0].verbose_participant()
        component = self.verbose_name()
        html = "<h2>Participant: %s</h2>\n<h2>Component: %s</h2>\n" % (participant, component)
        for item in items:
            html += item.to_html()

        return html

    def write_html(self):
        """Write out an HTML description of ourselves in the component directory"""

        filename = os.path.join(self.full_path(), "index.html")

        fh = open(filename, "w")
        fh.write(self.to_html())
        fh.close()

        return os.path.join(self.basename, "index.html")



    def validate_files(self):
        """Validate a component, return a tuple of (errors, warnings)
        listing any errors or warnings that are found.
        Errors should mean that the session is invalid
        Warnings are just for information, session is still valid."""

        errors = []
        warnings = []
        for item in self.item_generator():
            (e, w) = item.validate_files()
            errors += e
            warnings += w 
        return (errors, warnings)


    def add_camera_metadata(self, camera0, camera1):
        """Add the camera serial number metadata to all items
        if it's missing"""

        for item in self.item_generator():
            item['cameraSN0'] = camera0
            item['cameraSN1'] = camera1
            item.write_metadata()


    def convert_video(self, dest, log):
        """Convert video files of all items to compressed versions and
        copy to a destination. Update meta-data to reflect
        the compressed status and the location of the
        compressed files. Write meta-data to original and
        new (compressed) locations."""

        logh = open(log, 'a')
        logh.write("\n")
        logh.write(str(time.time()) + " : processing component : " + str(self.basename)+"\n")
        logh.close()

        for item in self.item_generator():
            success, newFiles, errors = item.convert_video(dest, log)
            if not success:
                print errors


    def upload_files(self, host, log):
        """Upload files of all items to the host server.
        Update meta-data to reflect the uploaded files"""

        logh = open(log, 'a')
        logh.write("\n")
        logh.write(str(time.time()) + " : uploading component : " + str(self.basename)+"\n")
        logh.close()

        for item in self.item_generator():
            success, failed = item.upload_files(host, log)
            if not success:
                print "\n".join( "Error: Failed to upload `%s'!\nReason: %s\n\n" % (fail[0], fail[1]) for fail in failed)

    def unupload_files(self, filename=""):
        """Marks files as unuploaded in the corresponding xml"""
        for item in self.item_generator():
            item.unupload_files(filename)
