import os

import config
config.configinit()

# hack flag for whether we're in production release or not
production = True

""" EXECUTABLES """
# the directories containing these executables have to be added
# to the PATH environment variable such that the GUI does
# not have to know where these files are located.
AUDIO_MONITOR = "C:\\Windows\\SysWOW64\\M-AudioFastTrackUltra8RControlPanel.exe"

FFMPEG_PROGRAM = config.config("FFMPEG_PROGRAM", "../programs/ffmpeg.exe")
FFMPEG_OPTIONS = ["-vcodec", "mpeg4", "-b", "20000k", "-minrate", "20000k", "-maxrate", "20000k", "-bufsize", "1835k", "-r", "48.04", "-an"]
MENCODER_PROGRAM = config.config("MENCODER_PROGRAM", "../programs/mencoder.exe")

PATH_RECORDINGS = config.config("PATH_RECORDINGS")
PATH_FINAL = config.config("PATH_FINAL")

PATH_CALIBRATION_FILES = os.path.join(PATH_RECORDINGS, "calibration")

""" PATHS """
# Absolute ABSOLUTE path
PATH_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." + os.sep + 'extra')

PATH_PROMPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'protocol-prompts')
PATH_IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')




""" IMAGES """
IMG_CHECK = os.path.join(PATH_IMAGES, "check.gif")
IMG_WARNING = os.path.join(PATH_IMAGES, "warn.gif")
IMG_ERROR = os.path.join(PATH_IMAGES, "error.gif")
IMG_INFO = os.path.join(PATH_IMAGES, "info.gif")

""" TEMPLATES """
# templates for recording paths and filenames
# paths are relative to PATH_RECORDINGS
TPL_RECORDING_PATH = os.path.join("Spkr%(colourId)d_%(animalId)d_Session%(sessionId)d", "Session%(sessionId)d_%(componentId)d")
TPL_RECORDING_FILE = "%(colourId)d_%(animalId)d_%(sessionId)d_%(componentId)d_%(itemId)03d"
TPL_CALIBRATION_FILE = "calibration"
""" OTHERS """
DB_NAME = os.path.join(PATH_DB, 'austalk.db')
SQL_NAME = os.path.join(PATH_DB, "austalk.sql")
METADATA_DB_NAME = os.path.join(PATH_DB, "metadata.db")

"""DISPLAYS"""
RA_DISPLAY = 0
SPEAKER_DISPLAY = 1

""" EVENTS """
EVENT_CONFIRMED_SETUP_1 = 'ConfirmedSetup1'
EVENT_CONFIRMED_SETUP_2 = 'ConfirmedSetup2'
EVENT_CONFIRMED_SETUP_3 = 'ConfirmedSetup3'
EVENT_CONFIRMED_SETUP_4 = 'ConfirmedSetup4'
EVENT_RECORD_SILENCE = 'RecordSilence'
EVENT_CALIBRATE = 'Calibrate'
EVENT_SESSION_START = 'SessionStart'
EVENT_NEXT = 'Next'
EVENT_PREVIOUS = 'Previous'
EVENT_NEXT_COMPONENT = 'NextComponent'
EVENT_PREVIOUS_COMPONENT = 'PreviousComponent'
EVENT_NEXT_RECORDING_ACTION = "NextAction"
EVENT_START = 'Start'
EVENT_STOP = 'Stop'
EVENT_STOP_YES = 'StopYes'
EVENT_STOP_NO = 'StopNo'
EVENT_PAUSE = "Pause"
EVENT_RESET = 'Reset'
EVENT_EXIT = 'Exit'
EVENT_HEARTBEAT = 'StatusUpdateTimer'
EVENT_MAUDIO = 'MAudio'
EVENT_CHECK_VIDEO = "Check Video"
EVENT_SET_VIDEO1 = "Set Video 1"
EVENT_SET_VIDEO2 = "Set Video 2"
EVENT_FINALISE = 'Finalise'
EVENT_GOTO = 'GoTo'

# LAYOUTS
# layout names must match the names in the component table (austalk.sql)
# code should use these symbolic names
LAYOUT_FIRST = 'First'
LAYOUT_SECOND = 'Second'
LAYOUT_THIRD = 'Third'
LAYOUT_FOURTH = 'Fourth'
LAYOUT_INITIAL = 'Initial'
LAYOUT_FINAL = 'Final'
LAYOUT_YES_NO = 'YesNo'
LAYOUT_DEFAULT = 'Prompts'
LAYOUT_MAPTASK = "MapTask"

""" PROMPTS """
PROMPT_SETUPINFO_1 = 'Protocol-Setup/Slide2.JPG'
PROMPT_SETUPINFO_2 = 'Protocol-Setup/Slide3.JPG'
PROMPT_SETUPINFO_3 = 'Protocol-Setup/Slide4.JPG'
PROMPT_SETUPINFO_4 = 'Protocol-Setup/Slide5.JPG'
PROMPT_DEFAULT = 'Slide1.JPG'
PROMPT_BLANK = 'blank.jpg'
PROMPT_WELCOME = 'welcome.jpg'
PROMPT_GOODBYE = 'goodbye.jpg'

""" STAGES """
STAGE_FIRST = 0
STAGE_SECOND = 0
STAGE_THIRD = 0
STAGE_FOURTH = 0
STAGE_INITIAL = 0
STAGE_RECORDING = 1
STAGE_FINAL = 2

try:
    from Local_Const import *
except ImportError:
    pass
