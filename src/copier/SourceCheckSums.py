import wx
import globals
from xml.dom import minidom
import os
import os.path
from FlowPanel import *

class SourceCheckSums(FlowPanel):
    def __init__(self, parent, stepNumber):
        FlowPanel.__init__(self, parent, stepNumber=stepNumber)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Check validity of session files'), flag=wx.BOTTOM|wx.LEFT, border=5)

    def do(self):
        self.setStatus(STATUS_READY)
        problem = False
        for s in globals.rawItems:
            problems = s.validate_files()
            if len(problems) > 0:
                self.messages = problems[0]
                problem = True

#      xmlfile = s + '.xml'
#      print "--- xmlfile ---"
#      print xmlfile
#      dom = minidom.parse(xmlfile)
#      files  = map(lambda n: n.childNodes[0].nodeValue, dom.getElementsByTagName("file"))
#
#      hashNodes = dom.getElementsByTagName("md5hash")
#      hashesFound = {}
#      for n in hashNodes:
#        hashesFound[n.attributes.values()[0].value] = n.childNodes[0].nodeValue
#
#      # add the sessions to this so we have the actual file name.
#      nfwithSession = (map(lambda x: os.path.join(os.path.dirname(s),x), files))
#
#      # now validate what we have found
#
#      # each file in the hash has an associated file in the file list
#      if (not (hashesFound.keys().sort() == nfwithSession.sort())):
#        self.messages = "for session " + os.path.basename(s)+ "the following md5hashes were found "+ hashesFound+ " when the following are necessary "+ nfwithSession
#        problem = True
#
#      # each file in the file list has the hash stored for it in the hash list
#      for f in nfwithSession:
#        h = globals.digest(f)
#        print "is " + h + " equal to " + hashesFound[os.path.basename(f)] + " ?"
#        if (not (h == hashesFound[os.path.basename(f)])):
#          self.messages = "hashes don't match for " + f
#          problem = True
#
        return (not problem)
