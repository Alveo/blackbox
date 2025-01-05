import os
import re
import shutil
import sys
import time

from time import mktime
from datetime import datetime, timedelta
from datahandling.RecordedComponent import RecordedComponent
from logger import Logger


def findItems(path, sessionId, componentId):
    components = findComponents(path, sessionId, componentId)
    
    result = []
    for component in components:
        for item in component.getItems():
            result.append(item)
            
    return result
    
    
def findComponents(path, sessionId, componentId):
    """ This method finds all the sessions with a specific session id and component id """
    results = []
    for path, dirs, files in os.walk(path, topdown = True, onerror = None, followlinks = True):
        for folder in dirs:
            if folder == 'Session%s_%s' % (sessionId, componentId):
                results.append(RecordedComponent(path, folder))
                
    return results


def listRecordingDates(components): 
    """ This function shows the recording dates for a session/component. This is evaluated by
    looking up the timestamp of the first item in the component. 
    """
    result = {}
    
    for component in components:
        items = component.getItems()
        if items != None and len(items) > 0:
            first_item = items[0]
            result[component] = datetime.fromtimestamp(mktime(time.strptime(first_item['timestamp'], "%a %b %d %H:%M:%S %Y")))

    return result


def listComponentsRecordedBefore(components, recordedDate, noDays):
    """ This function lists all items for sessionId and componentId recorded x Days before the recordedDate """
    results = []
   
    for component in components:
        items = component.getItems()
        for item in items:
            recorded_date = datetime.fromtimestamp(mktime(time.strptime(item['timestamp'], "%a %b %d %H:%M:%S %Y")))
            if (recordedDate - recorded_date) > timedelta(days = noDays):
                if not component in results:
                    results.append(component)

    return results


def copyCh6Wav(components, destination):
    """ This function copies the ch6 media file to a location specified by path. If the path
    does not exist, it is created. Note that only the item 1 media file is copied over and
    not the rest """
    if not os.path.exists(destination):
        os.mkdir(destination)
        
    for component in components:
        for item in component.getItems():
            # For the first item (i.e. 001) copy it's ch6-speaker.wav file to the specified location
            if item['item'] == '1':
                files = item.fileList()
                for media_file in files:
                    if 'ch6-speaker' in media_file:
                        shutil.copy2(os.path.join(item.path, media_file), destination)


def findRecordingDates(path, sessionId, componentId):
    components = findComponents(path, sessionId, componentId)
    recordingDates = listRecordingDates(components)
    return recordingDates


def findCorrespondingFromSession2Component16(path, recordingDates):
    # Get maximum recording date
    record_max = None
    for item in recordingDates.values():
        if record_max is None or (item - record_max) > timedelta(days=0):
            record_max = item
    
    components2 = findComponents(path, '2', '16')
    return listComponentsRecordedBefore(components2, record_max, 31)


def listOrderedRecordings(path, sessionId, componentId, mappings = None, cut_over_date = None):
    """ Lists the recordings in chronological order for a specifc component """
    # The logger is used to write the results, this is easier than openning and manipulating a file handle
    now = time.localtime(time.time())
    logger = Logger('/var/tmp/', 'Query-%s' % time.strftime("%Y_%m_%d_%H_%M_%S", now))
    
    processed = {}
    result = findItems(path, sessionId, componentId)
    count = 1
    
    if len(result) > 0:
        # A dictionary cannot be sorted on a value so instead we flip the result set around 
        # and sort on the value which becomes the key
        for w in sorted(result, key=lambda item: \
            datetime.fromtimestamp(mktime(time.strptime(item['timestamp'], "%a %b %d %H:%M:%S %Y")))):
            
            if w.has_key('timestamp'):
                formatted_date = datetime.fromtimestamp(mktime(time.strptime(w['timestamp'], "%a %b %d %H:%M:%S %Y")))
                if mappings is None or mappings.has_key(w['prompt'].capitalize()):
                    
                    if formatted_date <= datetime.strptime(cut_over_date, '%Y-%m-%d') \
                        and not processed.has_key(w.getComponent().full_path()):
                        
                        logger.log('|%s|Timestamp:%s|Location:%s' % \
                            (count, formatted_date, w.getComponent().full_path()))
                        processed[w.getComponent().full_path()] = ''
                        count += 1


def minAndMaxVersionsForCollection(path, sessionId, componentId):
    """ This method returns the min and max version for a particular collection based on 
    session and component id as filters."""
    result = getComponentsAsDict(path, sessionId, componentId)
    minVersion = maxVersion = None
    
    if len(result.keys()) > 0:
        # A dictionary cannot be sorted on a value so instead we flip the result 
        # set around and sort on the value which becomes the key
        for w in sorted(result, key=result.get, reverse=False):    
            try:
                # We ignore the last digit of the version number which is usually 
                # something like 1.3.1, the last .1 does not make sense for the moment
                version = float(result[w]['version'][0:3])
            except:
                version = 0
                
            if maxVersion is None or version > maxVersion: maxVersion = version
            if minVersion is None or version < minVersion: minVersion = version
    
    return (minVersion, maxVersion)


def minAndMaxDatesForCollection(path, sessionId, componentId):
    """ This method returns the min and max dat for a particular collection based on 
    session and component id as filters."""
    result = getComponentsAsDict(path, sessionId, componentId)
    minDate = maxDate = None
    
    if len(result.keys()) > 0:
        # A dictionary cannot be sorted on a value so instead we flip the result set around and sort on the value which becomes the key
        for w in sorted(result, key=result.get, reverse=False):
            if result[w].has_key('timestamp'): 
                formatted_date = datetime.fromtimestamp(mktime(time.strptime(result[w]['timestamp'], \
                                                        "%a %b %d %H:%M:%S %Y")))
            
                if maxDate is None or formatted_date > maxDate: maxDate = formatted_date
                if minDate is None or formatted_date < minDate: minDate = formatted_date   
    
    return (minDate, maxDate)
                       
    
def main():
    ''' Example commands:
            List components subject to a potential rename; python query.py -l /path 1 12
            List estimated recording dates for session components; python query.py -d /path 1 12
            List in chronological order the recording information for all items belonging to a session and component: python query.py -s /path 1 12 cut_over_date /xl_spreadsheet_path
    '''
    
    # Grab the primary arguments
    arg = sys.argv[1].strip()
    path = sys.argv[2].strip()
    sessionId = sys.argv[3].strip()
    componentId = sys.argv[4].strip()
    
    if arg == '-l':
        
        # This will list the components that meet the search criteria
        components = findComponents(path, sessionId, componentId)
        for component in components:
            print 'Session ', sessionId, ' located at ', component.full_path(), ' has component(s) ', component.get_id()
            
    elif arg == '-d':
        
        # This parameter lists the recording date for a session and component
        recordingDates = findRecordingDates(path, sessionId, componentId)
        for key, value in recordingDates.iteritems():
            print 'Session ', sessionId, ' has component(s) ', key.get_id(), ' recorded on ', value, 'located @ {', key.full_path(), '}'
            
    elif arg == '-o':
        
        # This parameter lists the recording data
        # recordingDates = findRecordingDates(path, sessionId, componentId)
        # session2Components = findCorrespondingFromSession2Component16(path, recordingDates)
        session2Components = findComponents(path, sessionId, componentId)
        session2Component16RecordingDates = listRecordingDates(session2Components)
        
        for key, value in session2Component16RecordingDates.iteritems():
            print 'Session ', sessionId, ' has component(s) ', key.get_id(), ' recorded on ', value, 'located @ {', key.full_path(), '}' 
            
    elif arg == '-c':
        
        # This parameter lists the recording data
        recordingDates = findRecordingDates(path, sessionId, componentId)
        session2Components = findCorrespondingFromSession2Component16(path, recordingDates)
        copyCh6Wav(session2Components, sys.argv[5].strip())
    
    elif arg == '-s':
        
        mappings = None
        cut_over_date = sys.argv[5].strip()
        
        # This command list the sessions that meets a specific criteria
        listOrderedRecordings(path, sessionId, componentId, mappings, cut_over_date)
    
    elif arg == '-v':
        
        minVersion, maxVersion = minAndMaxVersionsForCollection(path, sessionId, componentId)
        print 'Min Version: %s' % (minVersion)
        print 'Max Version: %s' % (maxVersion)
    
    elif arg == '-w':
        
        minDate, maxDate = minAndMaxDatesForCollection(path, sessionId, componentId)
        print 'Min Date: %s' % (minDate)
        print 'Max Date: %s' % (maxDate)
        
    else:
        print 'Unknown command.'


if __name__ == "__main__":
    main()
