import re

from recorder.animals import animalIdMap
from recorder.Domain import colourIdMap
import recorder.Persistence

class Translator(object):
    """ This class is used to translate the numerical speaker identifier to the colour identifier
    recognisable by the end users """   
    def translate(self, name):
        """ This function translates either a session folder pattern into a nice name which includes
        the full colour and animal name """
        if self.isSessionFolder(name):
            p = re.compile('\d+')
            elements = p.findall(name)
            colourid = int(elements[0])
            animalid = int(elements[1])
            colour = colourIdMap[colourid]
            animal = animalIdMap[animalid]
            session = int(elements[2])
            
            # we display session 4 as 3
            if session == 4:
                session = "3b"
            elif session == 3:
                session = "3a"
            
            return 'Session %s, %s - %s (%s_%s)' % (session, colour, animal, colourid, animalid)
            
        
        if self.isComponentFolder(name):
            match = re.match('Session(\d+)_(\d+)', name) 
            if match:
                (session, component) = match.groups()
                componentName = recorder.Persistence.ComponentName(component)
                return "Component: %s (%s)" % (componentName, component)
                
        if self.isItem(name):
            p = re.compile('\d+')
            elements = p.findall(name)
            item = int(elements[4])
            return "Item %s" % (item, )
        
        return name
    
    def isComponentFolder(self, name):
        """ Function checks to see if folder represents a component folder"""
        
        match = re.match('Session(\d+)_(\d+)', name) 
        if match:
            return True
        else:
            return False
        
              
    def isSessionFolder(self, name):
        """ Function checks to see if a folder represents a session folder """
        match = re.match("^Spkr[\d]+_[\d]+_Session[\d]+$", name)
        if match:
            return True
        else:
            return False
        
    def isItem(self, name):
        """ Function checks to see if a folder or file represents an item """
        match = re.match("^[\d]+_[\d]+_[\d]+_[\d]+_[\d]+\.xml$", name)
        if match:
            return True
        else:
            return False
        
        