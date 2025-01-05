"""Config interface for the BB.
Reads the same configuration as used by paster for the
server and provides a convenient interface for the
dada code to the config variables.

Usage:
    call config.configinit(file) at least once
    to read the config file

    call config.config(name) to get the value of
    the configuration for name

The config file is a standard INI format file as supported
by ConfigParser. We use the DEFAULT block for all
settings

"""

import os, ConfigParser
import sys


# the configuration key used in the INI file
CONFIG_KEY = "DEFAULT"

__all__ = ['configinit', 'config', 'print_config', 'set_config']

import inspect

# locate the home dir of the package
homedir = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))

DEFAULT_CONFIG_FILE = os.path.join(homedir, "config.ini")
LOCAL_CONFIGFILE = os.path.join(homedir, "local_config.ini")

_default_config = {
    'home': homedir,
}
_config_loaded = False
_config = None


def configinit(configfile=DEFAULT_CONFIG_FILE):
    """Load the configuration file """

    global _config_loaded, _config, _default_config

    if _config_loaded:
        return _config
    else:
        _config = ConfigParser.ConfigParser(_default_config)
        _config.read(configfile)
        # load local config file, if it exists (silently ignore if it doesn't)
        _config.read(LOCAL_CONFIGFILE)
        _config_loaded = True

        _config_derived()
    #print_config()


def _config_derived():
    """Derive some values from those given in the config."""

    set_config("PATH_CALIBRATION_FILES", os.path.join(config("PATH_RECORDINGS"), "calibration"))


def set_config(key, value):
    """Set the value for some key in the configuration"""
    global _config

    _config.set(CONFIG_KEY, key, value)


def config(key, default=''):
    """Get the value for the given key in the configuration
    returning default if there is no such key"""
    global _config

    if _config.has_option(CONFIG_KEY, key):
        return _config.get(CONFIG_KEY, key)
    else:
        return default

def print_config():
    """Print out the current configuration"""
    global _config

    _config.write(sys.stdout)



if __name__=='__main__':
    configinit()
    print_config()
    print "HOME IS", config("home")
