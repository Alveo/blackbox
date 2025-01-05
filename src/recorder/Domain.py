import threading, time, os
from Const import *
from collections import defaultdict

# these are in another file because they're big
from animals import animalIdMap, animalNameMap, animals


colourIdMap =  { 0: u'Dummy for Testing',
     1: u'Gold',
     2: u'Green',
     3: u'Red',
     4: u'Blue'}

# enter this explicitly since we want to retain this ordering
colours =  [u'Dummy for Testing', u'Gold', u'Green', u'Red', u'Blue']

colourNameMap = dict()
for key in colourIdMap.keys():
    colourNameMap[colourIdMap[key]] = key


def print_sessions():
    """Output a complete list of all sessions, components
    and items"""

    for s in Session.GetInstances():
        s.display()


# Keep a list of references to instances of a class:
# http://stackoverflow.com/questions/328851/python-printing-all-instances-of-a-class
class KeepRefs(object):
    __refs__ = defaultdict(list)
    def __init__(self):
        self.__refs__[self.__class__].append(self)

    @classmethod
    def GetInstances(cls):
        for inst in cls.__refs__[cls]:
            yield inst

    @classmethod
    def GetInstance(cls, id):
        """Return the instance with the given id field, or None if not found"""

        for inst in cls.GetInstances():
            if inst.GetId() == id:
                return inst
        return None



class Participant():
    """ Encapsulates participant information """


    def __init__(self, colourId, animalId):
        """ Initialises participant"""

        self.__colourId = colourId
        self.__colourName = colourIdMap[colourId]

        self.__animalId = animalId
        self.__animalName = animalIdMap[animalId]

    def GetColourId(self):
        """ Returns participant colour id """
        return self.__colourId

    def GetColourName(self):
        """ Returns participant colour name """
        return self.__colourName

    def GetAnimalId(self):
        """ Returns participant animal id """
        return self.__animalId

    def GetAnimalName(self):
        """ Returns participant animal name """
        return self.__animalName

    def GetRecordingPath(self):
        return os.path.join(
            PATH_RECORDINGS,
            TPL_RECORDING_PATH % {'colourId': self.__colourId, 'animalId': self.__animalId}
        )

    def __str__(self):
        """ Returns concatenation of colour and animal when converted to string """
        return self.__colourName + ' - ' + self.__animalName


class Session(KeepRefs):
    """ Encapsulates session information """

    def __init__(self, id, name, components = []):
        super(Session, self).__init__()
        self.__id = id
        self.__name = name
        self.SetComponents(components)


    def Reset(self):
        """Reset to initial state"""
        self.firstComponent()
        

    def GetId(self):
        return self.__id


    def GetName(self):
        return self.__name


    def SetComponents(self, components):
        """Given a list of component ids find the list of
        instances"""

        self.__components = [Component.GetInstance(id) for id in components]
        self.__currentComponent = 0

        self.__map = {'id': {}, 'name': {}}
        for component in self.__components:
            self.__map['id'][component.GetId()] = component
            self.__map['name'][component.GetName()] = component

    def IsCompleted(self):
        """ Returns whether the session is complete """
        for component in self:
            if not component.IsCompleted():
                return False
        return True

    def GetDuration(self):
        """ Returns the total duration of the session """
        if not hasattr(self, '__duration'):
            total = 0
            for component in self:
                total += component.GetDuration()
            self.__duration = total
        return self.__duration

    def ToTree(self):
        """ Generates the tree as expected by raFrame """
        return [component.ToTree() for component in self]


    def getComponents(self):
        """ Returns the list of components associated for this particular session """
        return self.__components


    def HasNextComponent(self):
        return self.__currentComponent < len(self.__components) - 1

    def HasPreviousComponent(self):
        return self.__currentComponent > 0

    def PreviousComponent(self):
        if self.HasPreviousComponent():
            self.__currentComponent -= 1
            return self.GetCurrentComponent()
        return False

    def NextComponent(self):
        if self.HasNextComponent():
            self.__currentComponent += 1
            self.GetCurrentComponent().Reset()
            return self.GetCurrentComponent()
        return False

    def firstComponent(self):
        self.__currentComponent = 0
        c = self.GetCurrentComponent()
        # need to reset to first item in this component
        c.Reset()
        return c

    def LastComponent(self):
        self.__currentComponent = len(self.__components) - 1
        return self.GetCurrentComponent()

    def Index(self):
        return self.__currentComponent

    def SetIndex(self, index):
        self.__currentComponent = index

    def GetCurrentComponent(self):
        return self.__components[self.__currentComponent]

    def GetPreviousComponent(self):
        if self.PreviousComponent():
            return self.GetCurrentComponent()
        return False

    def getNextComponent(self):
        """ Returns the next component in the current lit of components """
        if self.NextComponent() != False:
            return self.GetCurrentComponent()
        
        return False

    def __str__(self):
        return str(self.__name)

    def __iter__(self):
        return iter(self.__components)

    def __len__(self):
        return len(self.__components)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.__map['id'][item]
        elif isinstance(item, str):
            return self.__map['name'][item]


    def display(self):
        """Print out a textual representation of the session
        with all components and items"""

        print self.__name
        for c in self.__components:
            c.display()
        


class Component(KeepRefs):
    """ Encapsulates component information """

    def __init__(self, id, name, duration, layout, prompts, syncprompts, mapfile, shortname):
        super(Component, self).__init__()
        self.__id = id
        self.__name = name
        self.__duration = duration
        self.__layout = layout
        self.__prompts = prompts
        self.__syncprompts = syncprompts
        self.__mapfile = mapfile
        self.__shortname = shortname
        self.LoadItems()

    def Reset(self):
        """Reset to initial state"""

        self.__currentItem = -1


    def GetId(self):
        return self.__id

    def GetName(self):
        return self.__name

    def GetShortName(self):
        return self.__shortname

    def LoadItems(self):
        """Load items either from a map file (if it exists)
        or from all jpg images in a directory.
        Both path names are relative to PATH_PROMPTS setting"""

        #print "Looking for map file", os.path.join(PATH_PROMPTS, self.__mapfile)

        if os.path.exists(os.path.join(PATH_PROMPTS, self.__mapfile)):
            self.__items = self.LoadItemsFromFile()
        else:
            self.__items = self.LoadItemsFromDir()
            
        self.__currentItem = -1 # inital value means we've not started yet
        self.__map = {}
        for item in self.__items:
            self.__map[item.GetId()] = item

    def LoadItemsFromFile(self):
        """Load items from a map file. Each line
        contains three fields separated by '|':
        index | prompt text | image file"""

        mapFile = os.path.join(PATH_PROMPTS, self.__mapfile)
        items = []
        if os.path.isfile(mapFile):
            for item in open(mapFile).readlines():
                item = item.strip().split("|")
                item = Item(int(item[0]), item[1], item[2])
                items.append(item)
        return items

    def LoadItemsFromDir(self):
        """Load items from a directory of jpg files rather than a
        map file.  Prompt becomes the file name.
        Remove default.jpg if it exists."""

        import string, re

        dir = os.path.join(PATH_PROMPTS, self.__prompts)

        def cmpfn(a, b):
            """Sort based on the numerical part of the filename only since
            they don't generally have leading zeros"""
            ma = re.search('[0-9]+', a)
            mb = re.search('[0-9]+', b)
            if ma and mb:
                return cmp(string.atoi(ma.group()), string.atoi(mb.group()))
            elif ma:
                return 1
            elif mb:
                return -1
            else:
                return 0


        items = []
        index = 1
        if os.path.isdir(dir):
            for file in sorted(os.listdir(dir), cmp=cmpfn):
                # use lowercase to insure against mixed case file names
                lcname = file.lower()
                if not lcname in ("slide1.jpg", "default.jpg") and lcname.endswith(".jpg"):
                    item = Item(index, lcname, file)
                    items.append(item)
                    index += 1
        return items

    def getItems(self):
        """ Returns the items that belong to this particular component """
        return self.__items

    def GetDuration(self):
        return self.__duration

    def GetLayout(self):
        return self.__layout

    def SyncPrompts(self):
        return self.__syncprompts

    def GetPromptPath(self):
        return os.path.join(PATH_PROMPTS, self.__prompts)



    def IsCompleted(self):
        for item in self:
            if not item.IsCompleted():
                return False
        return True

    def SetCompleted(self, itemIds, flag = True):
        for itemId in itemIds:
            self.__map[itemId].SetCompleted(flag)

    def ToTree(self):
        return [self.GetName(), [(item.GetPrompt(), item.IsCompleted()) for item in self]]

    def HasPreviousItem(self):
        return self.__currentItem > 0

    def HasNextItem(self):
        return self.__currentItem < len(self.__items) - 1

    def PreviousItem(self):
        if self.HasPreviousItem():
            self.__currentItem -= 1
            return self.GetCurrentItem()
        return False

    def NextItem(self):
        if self.HasNextItem():
            self.__currentItem += 1
            return self.GetCurrentItem()
        return False

    def Index(self):
        return self.__currentItem

    def SetIndex(self, index):
        self.__currentItem = index

    def FirstItem(self):
        self.__currentItem = 0
        return self.GetCurrentItem()

    def LastItem(self):
        self.__currentItem = len(self.__items) - 1
        return self.GetCurrentItem()

    def GetCurrentItem(self):
        """Return the current item or None if we've not yet started traversing items"""
        if self.__currentItem >= 0:
            return self.__items[self.__currentItem]
        else:
            return None

    def GetPreviousItem(self):
        if self.PreviousItem():
            return self.GetCurrentItem()
        return False

    def GetNextItem(self):
        if self.PreviousItem():
            return self.GetCurrentItem()
        return False

    def __str__(self):
        return str(self.__name + " (" + str(self.__id) + ")")

    def __iter__(self):
        return iter(self.__items)

    def __len__(self):
        return len(self.__items)

    def __getitem__(self, item): 
        return self.__map[item]

    def display(self):
        """Print out a textual representation of the component
        with all items"""

        print "\tComponent: ", str(self)
        for i in self.__items:
            print "\t\tItem: %s_%03d - %s" % (self.GetId(), i.GetId(), i.GetPrompt())


class Item():
    """ Encapsulates item information """

    def __init__(self, id, prompt, image, completed = False):
        self.__id = id
        self.__image = image
        self.__prompt = prompt
        self.__completed = completed

    def GetId(self):
        return self.__id

    def GetPrompt(self):
        return self.__prompt

    def GetPromptImage(self):
        return self.__image

    def IsCompleted(self):
        return self.__completed

    def SetCompleted(self, flag = True):
        self.__completed = flag

    def __str__(self):
        return str(self.__prompt)


class Timer(threading.Thread):
    """ Simple timer """

    _timeElapsed = 0
    _callbacks = []
    _run = True

    def __init__(self, *callbacks):
        """ Initialises thread """
        threading.Thread.__init__(self)
        self._callbacks = callbacks

    def run(self):
        """ Increment every second forever """
        while self._run:
            self._timeElapsed += 1
            self.Notify()
            time.sleep(1.0)

    def Stop(self):
        """ Makes sure the run method stops """
        self._run = False

    def AddCallback(self, callback):
        """ Registers a new callback function """
        self._callbacks.append(callback)

    def GetTimeElapsed(self):
        """ Returns time elapsed in seconds """
        return self._timeElapsed

    def Notify(self):
        """ Notifies all callback functions """
        for callback in self._callbacks:
            callback(self)
