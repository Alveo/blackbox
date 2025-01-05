import collections
import csv
import os
import sys
import re
import urllib, urllib2
import xml.dom.minidom

from xml.dom.minidom import Node
from urlparse import urljoin
from HTMLParser import HTMLParser

class ConfigurationParser(object):
  ''' This class parsers the configuration file and provides getter methods for use
  by the main routine '''

  def parse(self, configuration_file):
    ''' Method parses the configuration file and loads the data into Named Tuples
    which reflect the structure of the configuration file '''
    doc = xml.dom.minidom.parse(configuration_file)
    
    Configuration = collections.namedtuple('Configuration', 'sites')
    Site = collections.namedtuple('Site', ['id', 'speakers'])
    Speaker = collections.namedtuple('Speaker', ['id', 'sessions'])
    Session = collections.namedtuple('Session', ['id', 'components'])
    Component = collections.namedtuple('component', 'id')

    config = Configuration(sites=[])
    
    for node in doc.getElementsByTagName("site"):
      # Process sites
      site_id = node.getAttribute("id")
      site = Site(id = site_id, speakers = [])
      config.sites.append(site)
      
      for speaker_node in node.getElementsByTagName("speaker"):
        # Process speakers
        speaker_id = speaker_node.getAttribute("id")
        speaker = Speaker(id = speaker_id, sessions = [])
        site.speakers.append(speaker)
        
        for session_node in speaker_node.getElementsByTagName("session"):
          # Process sessions
          session_id = session_node.getAttribute("id")
          session = Session(id = session_id, components = [])
          speaker.sessions.append(session)
          
          for component_node in session_node.getElementsByTagName("component"):
            # Now process the components
            component_id = component_node.getAttribute("id")
            component = Component(id = component_id)
            session.components.append(component)


    return config


class SitesHTMLParser(HTMLParser):
  '''
  This class is parses the HTML pages which are generated from the webdav store. These pages following
  a convention, so the parser is used to parse the sites, sessions, components and files list.
  '''

  def __init__(self):
    ''' Definition required to chain constructors '''
    HTMLParser.__init__(self) 

    self.is_site = False
    self.row_count = 0
    self.raw_site_list = []
    

  def handle_starttag(self, tag, attrs):  
    ''' Event fires and handles the opening <a> tag. All other tags are ignored '''
    if tag == 'a':
      self.is_site = True
    elif tag == 'tr':
      self.row_count += 1

        
  def handle_endtag(self, tag):
    ''' Sets the global flag to say there is no anchor to process '''
    if tag == 'a':
      self.is_site = False

      
  def handle_data(self, data):
    ''' Primary event which fires when data is present between HTML tags '''
    # The first two rows of the table contains a table header and a back link the directory above
    if self.is_site and self.row_count > 3:
      self.raw_site_list.append(data)
      
      
  def get_list(self):
    return self.raw_site_list



class RecordingSites(object):
  '''
  This class provides different methods to retrieve lists at each level of the directory heirarchy. i.e. It is used
  to retrieve the site names, session identifiers, component identifiers and the recordings including the meta data.
  '''
  
  def __init__(self):
    # Base url is hard coded for this application, anything else is not required.
    self.root = 'https://austalk.edu.au/dav/bigasc/data/real/'
  
  
  def get_site_names(self):
    ''' This function goes through the names of the folders in the web dav store and cleanses them '''
    raw_site_names = self.__parse_and_return(self.root)
    
    cleansed_names = {}
    for name in raw_site_names:
      ''' Loop removes underscores and all words after the first comma '''
      mod_name = re.sub('_', ' ', name)
      mod_name = re.sub(',[\s\w/]+', '', mod_name)
      cleansed_names[mod_name] = name
      
    return cleansed_names
    
  
  def get_speaker_ids(self, site_mappings, site_id):
    ''' This function returns the speaker ids for a particular site '''
    speaker_url = self.translate_to_siteurl(site_mappings, site_id)
    speakers = self.__parse_and_return(speaker_url)
  
    cleansed = {}
    for spkr in speakers:
     ''' Loop removes underscores and all words after the first comma '''
     if re.match('Spkr', spkr):
       mod = re.sub('Spkr', '', spkr)
       cleansed[mod.replace('/', '')] = spkr

    return cleansed
   
   
  def get_session_names(self, site_mappings, site_id, speaker_id):
    ''' This function returns the session names for a particular site and speaker id '''
    sessions_url = self.translate_to_speakerurl(site_mappings, site_id, speaker_id)
    sessions = self.__parse_and_return(sessions_url)
    
    cleansed_names = {}
    for name in sessions:
     ''' Loop removes underscores and all words after the first comma '''
     mod_name = re.sub(self.__translate_speaker_id(speaker_id) + '_', '', name)
     cleansed_names[mod_name.replace('/', '')] = name

    return cleansed_names
  

  def get_component_names(self, site_mappings, session_mappings, site_id, speaker_id, session_name):
    ''' This function returns component names for a particular site, speaker id and session name '''
    components_url = self.translate_to_sessionurl(site_mappings, session_mappings, site_id, speaker_id, session_name)
    components = self.__parse_and_return(components_url)

    cleansed_names = {}
    for name in components:
      ''' Loop removes the word Session from the component name '''      
      if re.search('/', name):
        mod_name = re.sub('Session', '', name)
        cleansed_names[mod_name.replace('/', '')] = name

    return cleansed_names
  
  
  
  def get_sample_names(self, site_mappings, session_mappings, component_mappings, site_id, speaker_id, session_name, component_name):
    ''' This function returns component names for a particular site, speaker id and session name '''
    item_url = self.translate_to_componenturl(site_mappings, session_mappings, component_mappings, site_id, speaker_id, session_name, component_name)
    items = self.__parse_and_return(item_url)
  
    sample_names = {}  
    for item in items:
      if re.search('(.xml|-ch6-)', item):
        sample_names[item] = self.translate_to_itemurl(site_mappings, session_mappings, component_mappings, site_id, speaker_id, session_name, component_name, item)
    
    return sample_names
    
  
  def translate_to_siteurl(self, site_mappings, site_id):
    ''' Function constructs an absolute url for the for a site from a site name '''
    return urljoin(self.root, site_mappings[site_id])
  
    
  def translate_to_speakerurl(self, site_mappings, site_id, speaker_id):
    ''' Function constructs an absolute url for the location of sessions based on a speaker id and site id '''
    relative_url = urljoin(self.root, site_mappings[site_id])
    return urljoin(relative_url, self.__translate_speaker_id(speaker_id))


  def translate_to_sessionurl(self, site_mappings, session_mappings, site_id, speaker_id, session_name):
    ''' Function constructs an absolute url for the location of sessions based on a speaker id and site id '''
    speaker_url = self.translate_to_speakerurl(site_mappings, site_id, speaker_id)
    return urljoin(speaker_url + '/', session_mappings[session_name])


  def translate_to_componenturl(self, site_mappings, session_mappings, component_mappings, site_id, speaker_id, session_name, component_name):
    ''' Function constructs an absolute url for the location of sessions based on a speaker id and site id '''
    session_url = self.translate_to_sessionurl(site_mappings, session_mappings, site_id, speaker_id, session_name) 
    return urljoin(session_url, component_mappings[component_name])
      
      
  def translate_to_itemurl(self, site_mappings, session_mappings, component_mappings, site_id, speaker_id, session_name, component_name, item_url):
    ''' Function constructs an absolute url for the location of sessions based on a speaker id and site id '''
    component_url = self.translate_to_componenturl(site_mappings, session_mappings, component_mappings, site_id, speaker_id, session_name, component_name) 
    return urljoin(component_url, item_url)
     
    
  def __translate_speaker_id(self, speaker_id):
    return 'Spkr' + speaker_id
    
    
  def __parse_and_return(self, url):
    ''' Helper function which opens a url and returns a list of values '''
    resource = urllib.urlopen(url)
    raw_html = resource.read()

    parser = SitesHTMLParser()
    parser.feed(raw_html)
    return parser.get_list()
    
    
class Downloader(object):
  ''' This class performs the download as  it used by the main routine to perform this step. '''
  
  def download_samples_to(self, site_name, speaker_id, session_name, component_name, path):
    ''' This function downloads all the samples for the speaker, session and component to the provided path. If the path
    does not exist it creates it '''
    
    if not os.path.exists(path):
      print 'Please provide a folder which exists'
      return
    else:
      print "Commencing download for site %s, speaker %s, session %s, component %s" % (site_name, speaker_id, session_name, component_name)
      
    # The following sequence builds up the names of the samples by reading the online directory
    # The contents of the online directory are pattern matched agains the provided keys (i.e. speaker_id, session_name etc)
    rs = RecordingSites()
    site_mappings = rs.get_site_names()
    session_names = rs.get_session_names(site_mappings, site_name, speaker_id)
    component_names = rs.get_component_names(site_mappings, session_names, site_name, speaker_id, session_name)
    samples = rs.get_sample_names(site_mappings, session_names, component_names, site_name, speaker_id, session_name, component_name)
    
    # Now download the files to the specified location
    sofar = 0
    total = len(samples.keys())
    
    for key, value in samples.iteritems():
      sofar += 1
      self.message = "%s of %s" % (sofar, total)

      # If the file exists at the output location and is of the same size as the file to download (i.e. the download was not interrupted)
      # then perform the download
      output_path = os.path.join(self.build_out(path, site_name, speaker_id, session_name, component_name), key)
      if self.should_download (value, output_path):
        try:
          urllib.urlretrieve(value, output_path, self.__report_progress)
        except Exception as ex:
          # Absorb exception and continue with a report of the error
          print "An error occured downloading %s" % (value,)


    print "\033[2K   ", "Download complete", "\033[A"


  def should_download (self, value, output_path):
    """ This function determines if a download should take place. If the file was successfully downloaded earlier then
    this function returns false else true. """
    if os.path.exists (output_path):
     
      response = urllib2.urlopen (HeadRequest (value))
      content_length = response.info ()['Content-Length']
      downloaded_file_size = os.stat(output_path).st_size
     
      if int (content_length) == int (downloaded_file_size):
        print "\033[2K   ",  value, " already downloaded.", "\033[A"
        return False
      else:
        return True
    else:
      return True


  def __report_progress(self, count, block_size, total_size):
    """ Function reports progress of download """
    total_blocks = float(total_size) / float(block_size)
    percentage = int(count / total_blocks * 100) if int(count / total_blocks * 100) < 100 else 100
    print "\033[2K   ", self.message, " : progress ", percentage, "%", "\033[A"
    

  def build_out(self, path, site_name, speaker_id, session_name, component_name):
    ''' This function creates the directory structure required for the downloader to
    write the output files, it builds the following directory structure if it does not
    exist {path}/site_name/speaker_id/session_name/component_name/ '''
    dir = os.path.join(path, site_name, speaker_id, session_name, component_name)
    
    # If path does not exist create it
    if not os.path.exists(dir):
      os.makedirs(dir)
          
    return dir
    

class HeadRequest (urllib2.Request):

  def get_method (self):
    return "HEAD"


# Start of procedure variable declarations
recording_sites = RecordingSites()

def get_site_names():
  ''' Shows the names of the sites on the console '''
  sites = recording_sites.get_site_names()
  var = print_list(sites, 'Select site')
  return (sites, sites.keys()[var-1])
  

def get_speaker_ids(site_mappings, site_name):
  ''' Shows the list of speaker ids for the site '''
  speakers = recording_sites.get_speaker_ids(site_mappings, site_name)

  item_no = 0
  for name, url in speakers.iteritems():
    item_no += 1
    print item_no, '. ', name

  ids = raw_input('\n' + "Select speakers as a single value or comma separated list (e.g:10 or 2,5,8,23):")
  speaker_ids = []
  for row in csv.reader([ids]):
    for item in row:
      speaker_ids.append (speakers.keys ()[ int (item) - 1]) 

  return (speakers, speaker_ids)


def get_session_numbers(site_mappings, site_name, speaker_ids):
  ''' Shows the list of sessions numbers for a site and speaker '''

  sessions = {}
  master_sessions = {}

  for speaker_id in speaker_ids:
    speaker_sessions = recording_sites.get_session_names(site_mappings, site_name, speaker_id)
    master_sessions[speaker_id] = speaker_sessions
    for key, value in speaker_sessions.iteritems ():
      if key in sessions:
        sessions[key].append (value)
      else:
        sessions[key] = [value]

  var = print_list(sessions, 'Select session')
  return (master_sessions, sessions.keys()[var-1])


def get_component_ids(site_mappings, site_name, speaker_ids, session_mappings, session_id):
  ''' Shows the list of sessions numbers for a site and speaker '''
  # Now go through each speaker, and for that speaker find the corresponding session we are interested in
  # and pass this to get_component names
  alldict = []
  for speaker_id in speaker_ids:
    speaker_components = recording_sites.get_component_names(site_mappings, session_mappings[speaker_id], site_name, speaker_id, session_id)
    alldict.append (speaker_components)

  allkeys = reduce(set.intersection, map(set, map(dict.keys, alldict)))
  components = {}
  for key in allkeys:
    components[key] = 'Session' + key

  var = print_list(components, 'Select component')
  return (components, components.keys()[var-1])


def print_list_proper (list, message):
  item_no = 0
  for name in list:
    item_no += 1
    print item_no, '. ', name

  return int(raw_input('\n' + message + " [1-" + str(item_no) + "]: "))


def print_list (dictionary, message):
  ''' Helper function which dumps a list of options to the console '''
  item_no = 0
  for name, url in dictionary.iteritems():
    item_no += 1
    print item_no, '. ', name

  return int(raw_input('\n' + message + " [1-" + str(item_no) + "]: "))


def main():
  ''' Primary application entry point for downloading the samples ''' 
  
  # First check to see if the user has specified a configuration file
  if len(sys.argv) > 1:
    if sys.argv[1] == '-c':
      config_file_name = sys.argv[2]
  
      cp = ConfigurationParser()
      components = cp.parse(config_file_name)
  
      output_path = raw_input("Provide a path to download to (e.g /var/tmp): ")

      downloader = Downloader()
      for site in components.sites:
        for speaker in site.speakers:
          for session in speaker.sessions:
            for component in session.components:
              try:
                downloader.download_samples_to(site.id, speaker.id, session.id, component.id, output_path)
              except KeyError:
                print 'Problem with these values'
                print '  Site: ', site.id
                print '  Speaker: ', speaker.id
                print '  Session: ', session.id
                print '  Component: ', component.id, ' \n'


    if sys.argv[1] == "-s":
      config_file_name = sys.argv[2]

      sites = recording_sites.get_site_names()
      sessions = ['Session1', 'Session2', 'Session3', 'Session4']
      components = ['2', '3', '5', '6', '13', '14', '16', '17', '22', '32']
      session_id = print_list_proper (sessions, 'Select session')
      component_id = print_list_proper (components, 'Select component')

      file_handle = open (config_file_name, 'r').read ().splitlines ()
      output_path = raw_input("Provide a path to download to (e.g /var/tmp): ")
      downloader = Downloader()

      for line in file_handle:
        try:
            (site_name, speaker_id) = line.split (',')
        except:
            print "Malformed line:", line
            continue
        # print "%s %s %s %s" % (site_name, speaker_id, sessions[session_id - 1], str (session_id) + '_' + components [component_id -1])
        try:
          downloader.download_samples_to(site_name, speaker_id, sessions[session_id - 1], str (session_id) + '_' + components [component_id -1], output_path)
        except KeyError:
          pass

  else:
  
    (sites, site_name) = get_site_names()
    (speakers, speaker_ids) = get_speaker_ids(sites, site_name)
    (sessions, session_id) = get_session_numbers(sites, site_name, speaker_ids)
    (components, component_id) = get_component_ids(sites, site_name, speaker_ids, sessions, session_id)
  
    output_path = raw_input("Provide a path to download to (e.g /var/tmp): ")
    downloader = Downloader()

    for speaker_id in speaker_ids:
      # print "%s %s %s %s" % (site_name, speaker_id, session_id, component_id)
      downloader.download_samples_to(site_name, speaker_id, session_id, component_id, output_path)


if __name__ == "__main__":
  main()