import logging
import os

class Logger(object):
    ''' This class wraps the python logging block '''
    def __init__(self, location, logName):
    
        self.logger = logging.getLogger(logName)
        self.full_name = os.path.join(location, logName + '.log')
        hdlr = logging.FileHandler(self.full_name)
        formatter = logging.Formatter('%(asctime)s %(message)s:')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr) 
        self.logger.setLevel(logging.DEBUG)

        
    def get_log_file_name(self):
        return self.full_name
    

    def log(self, message):
        ''' Log the message passed in '''
        self.logger.warning(message)