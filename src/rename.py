import os
import re
import sys
import shutil
import time

from abc import ABCMeta, abstractmethod
from datahandling.RecordedSession import RecordedSession
from datahandling.RecordedItem import RecordedItem
from datahandling.RecordedComponent import RecordedComponent
from logger import Logger


class RenameStrategy:
    """ The renaming of component, speaker and item have been refactored into classes. Each
    rename is an algorithm which made is straightforward to refactor into a class and hence
    the stragegy pattern. """
    __metaclass__ = ABCMeta

    now = time.localtime(time.time())
    logger = Logger('/var/tmp/', 'Rename-%s' % time.strftime("%Y-%m-%d_%H:%M:%S", now))


    def __init__ (self, root_folder):
        """ When a rename strategy is initialised the session and manifest details are
        prepared for use. """
        self.root_folder = root_folder
        self.recorded_session = initialise_session(root_folder)
        self.manifest = self.recorded_session.read_raw_manifest()


    @abstractmethod
    def rename(self, colour, animal):
        pass


    def check_for_leftovers(self, path):
        """ This function simply checks to see if any files were left over in a particular folder and it's subfolders. It does
        not discriminate between file types. """
        result = []
        for root, dirs, files in os.walk(path, topdown = False):
            for f in files:
                if not (f.startswith('.') or f in ('manifest.txt', 'validation.txt')):
                    result.append(f)
                
        return result


    def cleanse_leftovers(self, path):
        """ This function Deletes the folder if there are no leftovers in it. It works purely at the component level. """
        problem = False
        for root, dirs, files in os.walk(path, topdown = False):
            for folder in dirs:
                if len(self.check_for_leftovers(os.path.join(root, folder))) == 0:
                    shutil.rmtree(os.path.join(root, folder))
                else:
                    problem = True
            
        # If there are no problems now delete the root
        if not problem:
            shutil.rmtree(path)



class ComponentRename(RenameStrategy):
    """ This class represents a component rename strategy. """

    def __init__ (self, root_folder):
        RenameStrategy.__init__ (self, root_folder)


    def rename(self, component_param, new_component_param):
        self.logger.log('Rename of components started')
        print 'Renaming of component in progress'
        
        for component in self.recorded_session.components():
            if component_param == str(component.get_id()):
                colour, animal, session = self.recorded_session.get_speaker_and_session()
                component.rename_items(colour, animal, new_component_param, self.logger)
        
        # After renaming the component regenerate the manifest
        # Delete the manifest first though
        os.remove(os.path.join(self.root_folder, 'manifest.txt'))
        self.recorded_session.gen_manifest(True, self.root_folder, True, self.manifest[0], self.manifest[1])
        
        # Final cleanup
        path = os.path.join(self.root_folder, 'Session%s_%s' % (session, component_param))
        if len(self.check_for_leftovers(path)) == 0:
            self.logger.log('Removing folder %s' % (path))
            shutil.rmtree(path)



class SpeakerRename(RenameStrategy):

    def __init__ (self, root_folder):
        RenameStrategy.__init__ (self, root_folder)


    def rename(self, colour_param, animal_param):
        self.logger.log('Rename of speaker started')
        print 'Renaming of speaker in progress'
        
        # After renaming the component regenerate the manifest at the new location
        self.recorded_session.rename_speaker(colour_param, animal_param, self.logger)
        colour, animal, session = self.recorded_session.get_speaker_and_session()
        root, basename = os.path.split(self.root_folder)
        new_session = RecordedSession(root, 'Spkr%s_%s_Session%s' % (colour, animal, session))
        new_session.gen_manifest(True, os.path.join(root, 'Spkr%s_%s_Session%s' % (colour, animal, session)), True, self.manifest[0], self.manifest[1])
        
        # Final cleanup
        self.cleanse_leftovers(self.root_folder)

        self.logger.log('Rename of speaker completed')



def get_row_id(line):
    """ This function returns the identifier of a row from a log file. The row identifier appears just after the timestamp for the log entry """
    line_items = line.split('|')
    row_id = line_items[1]
    return int(row_id)


def get_filename_withoutext(full_path):
    """ This function returns the name of a file without it's extension """
    name = os.path.split(full_path)
    return os.path.splitext(name[1])[0]
    

def ingest_txt(path):
    """ This function uses a mapping file which specifies an item number map """
    txt_handle = open(path, 'r')
    mappings = {}
    for line in txt_handle:
        line_split = line.split('|')
        mappings[int(line_split[0])] = int(line_split[1])
                      
    return mappings


def initialise_session(root_folder):
    root, basename = os.path.split(root_folder)
    return RecordedSession(root, basename)


def valid_manifest(recorded_session):
    # Before starting we should validate the manifest and only proceed if it is valid
    errors, warnings = recorded_session.validate_files(nocache = True) # We do not care about warnings, only errors
    
    if len(errors) > 0:
        print "Cannot proceed, there are errors in the manifest."
        for error in errors:
            print error
        
        return False
    
    return True


def rename(rename_component, root_folder, param1, param2, ignore_errors = False):
    # Example command: python rename.py component/item colour animal component
    recorded_session = initialise_session(root_folder)
    if valid_manifest(recorded_session) or ignore_errors:
        if rename_component == 'component':
            strategy = ComponentRename(root_folder)
        elif rename_component == 'speaker':
            strategy = SpeakerRename(root_folder)
        else:
            raise NotImplementedError()

        strategy.rename(param1, param2)


def get_audio_fn(log, sample_no, output_loc):
    log_handle = open(log, 'r')
    for line in log_handle:
        line_items = line.split(';')
        row_id = get_row_id(line)
        if int(sample_no) == row_id:
            return '%s-ch6-speaker.wav' % (line_items[3].split(':')[1])
     
    return None


def backup(source_file, destination):
    """ This function backs up a document to the destination folder. The folder is created if it does not exist. """
    if not os.path.exists(destination):
        os.mkdir(destination)

    shutil.copy2(source_file, destination)
    return os.path.exists(os.path.join(destination, source_file))
    

def is_processed(log, item_name):
    """ This function checks to see if an item has already been processed """
    log_handle = open(log, 'r')
    for line in log_handle:
        line_item_name = line.split(' ')[2]
        if line_item_name == item_name:
            return True
            
    return False


def process_sentences(log, mappings, backup_location, new_comp_no, start_sample, end_sample):
    """ This function process the log file produced by the command python query.py -s... command. 
    This log file contains information about items which qualify for sentence or prompt renaming. """
    log_handle = open(os.path.join('/var/tmp/', log), 'r')
    logger = Logger('/var/tmp/', '%sProcessed' % get_filename_withoutext(log))
    ri_logger = Logger('/var/tmp/', 'Rename-%s' % time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time())))
    
    for line in log_handle:
        
        line_items = line.split('|')
        location = line_items[3].split(':')[1]
        line_sample_no = get_row_id(line)
        
        # Only proceed with the correction if the sample number matched and the item
        # has not been processed a prior
        if line_sample_no >= start_sample and line_sample_no <= end_sample and \
            os.path.exists(location):
            
            # Initialise the Record component and then rename all it's items
            path, basename = os.path.split(location)
            rc = RecordedComponent(path, basename)
            
            items = rc.item_generator()
            
            for ri in items:
            
                if not is_processed(logger.get_log_file_name(), ri.full_path()):
                    # ri = RecordedItem(path, basename)
                    comp_no = int(ri['component'])
                    item_no = int(ri['item'])
            
                    print 'Renaming %s_%s_%s_%s to %s_%s_%s_%s' % \
                        (ri['colour'], ri['animal'], comp_no, item_no, \
                        ri['colour'], ri['animal'], new_comp_no, mappings[int(ri['item'])])
            
                    # Backup Meta-data only
                    success = backup('%s.xml' % ri.full_path(), backup_location)
            
                    if success:
                        ri.rename_item(ri['colour'], ri['animal'], new_comp_no, mappings[int(ri['item'])], ri_logger)
                        logger.log('%s component %s -> %s item %s -> %s' % \
                            (ri.full_path(), comp_no, new_comp_no, item_no, mappings[item_no]))
                    else:
                        print 'Backup of %s.xml failed.' % (location)
                        
            
            rebuild_manifest(path)
            
            
            # Final cleanup
            if len(check_for_leftovers(location)) == 0:
                ri_logger.log('Removing folder %s' % (location))
                shutil.rmtree(location)
                

def rebuild_manifest(path):
    """ This function will re-build the manifest for a particular session """
    abs_path = os.path.join(path, 'manifest.txt')
    rs = initialise_session(path)
    manifest = rs.read_raw_manifest()
    
    if (os.path.exists(abs_path)):
        os.remove(abs_path)
    
    if manifest is None:
        rs.gen_manifest(True, path)
    else:    
        rs.gen_manifest(True, path, True, manifest[0], manifest[1])
    
            
def main():
  
    if (len(sys.argv) < 5 or sys.argv[1] == '-h') and sys.argv[1] != '-m':
        print 'Example: python rename.py speaker colour animal root_folder'
        print 'Example: python rename.py component old_component new_component root_folder ?ignore_errors?'
        print 'Example: python rename.py -s excel_location log backup_loc new_component_no start_sample_no end_sample_no'
        print 'Example: python rename.py -m path'
        return
  
    param0 = sys.argv[1].strip()
    param1 = sys.argv[2].strip()
    
    if param0 == '-m':
        # Re-build the manifest for a particular session 
        rebuild_manifest(param1)
        return
    
    param2 = sys.argv[3].strip()
    param3 = sys.argv[4].strip()
    
    if param0 == '-s':
        mappings = ingest_txt(param1)

        new_comp_no = int(sys.argv[5].strip())
        start_sample = int(sys.argv[6].strip())
        end_sample = int(sys.argv[7].strip())
        process_sentences(param2, mappings, param3, new_comp_no, start_sample, end_sample)

    else:
        if (len(sys.argv) == 6):
            rename (param0, param3, param1, param2, sys.argv[5].strip() == 'ignore')
        else:
            # param0 is either speaker or component
            # param1 is the speakers colour
            # param2 is the speakers animal
            # param3 is the root folder
            rename(param0, param3, param1, param2)
    
    print 'Complete'
            
    
if __name__ == "__main__":
    main()
