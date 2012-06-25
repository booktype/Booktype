# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.


from booki.utils.json_wrapper import simplejson
from django.conf import settings
import threading

writeLock = threading.RLock()

class ConfigurationError(Exception):
    def __init__(self, description = ''):
        self.description = description

    def __str__(self):
        return self.description


def readConfiguration():
    """
    Reads configuration file and returns content as a dictionary.

    @rtype: C{dict}
    @return: Returns dictionary with all the values
    """
    
    configPath = '%s/configuration.json' % settings.BOOKI_ROOT

    try:
        f = open(configPath, 'r')
        data = f.read()
        f.close()
    except IOError:
        raise ConfigurationError("Can't read file %s." % configPath)
    except:
        raise ConfigurationError("Unknown error.")

    try:
        confData = simplejson.loads(data)
    except:
        return None

    return confData


def loadConfiguration():
    """
    Loads configuration. This function is supposed to be called from the settings.py file.

    try:
        BOOKTYPE_CONFIG = config.loadConfiguration()
    except config.ConfigurationError:
        BOOKTYPE_CONFIG = None

    @rtype: C{dict}
    @return: Returns dictionary with all the values
    """

    data = readConfiguration()

    return data

def saveConfiguration():
    """
    Saves the configuration to file. Configuration data is taken from settings.BOOKTYPE_CONFIG variable.
    """
    
    import tempfile
    import os
    import os.path

    if not hasattr(settings, 'BOOKTYPE_CONFIG'):
        return False

    writeLock.acquire()

    data = settings.BOOKTYPE_CONFIG

    configPath = '%s/configuration.json' % settings.BOOKI_ROOT
    # check for errors
    jsonData = simplejson.dumps(data)

    try:
        fh, fname = tempfile.mkstemp(suffix='', prefix='configuration', dir=settings.BOOKI_ROOT)
        f = open(fname, 'w+')
        f.write(jsonData.encode('utf8'))
        f.close()

        if os.path.exists(configPath):
            os.unlink(configPath)

        os.rename(fname, configPath)
    except IOError:
        raise ConfigurationError("Can't write to file %s." % configPath)
    except:
        raise ConfigurationError("Unknown error.")
    finally:
        writeLock.release()


def getConfiguration(name, value = None):
    """
    Returns content of a configuration variable. It will first search in user defined configuration. 
    If it can't find it it will go into settings file and finaly constant variables provided with
    Booktype source.

    @type name: C{string}
    @param: Name of the variable

    @type value: C{object}
    @param: Default value if it can't find defined variable.

    @type: C{object}
    @return: Returns the content of the variable
    """

    from booki import constants

    # Check if we have it in the configuration file
    if hasattr(settings, 'BOOKTYPE_CONFIG'):
        if settings.BOOKTYPE_CONFIG != None and settings.BOOKTYPE_CONFIG.has_key(name):
            return settings.BOOKTYPE_CONFIG[name]
        
    # Check if we have it in the settings file
    if hasattr(settings, name):
        return getattr(settings, name)
    
    if hasattr(constants, name):
        return getattr(constants, name)

    return value


def setConfiguration(name, value):
    """
    Sets value for configuration variable. 

    @type name: C{string}
    @param: Name of the variable

    @type value: C{object}
    @param: Value for the variable
    """

    writeLock.acquire()

    try:
        if hasattr(settings, 'BOOKTYPE_CONFIG'):
            if not settings.BOOKTYPE_CONFIG:
                settings.BOOKTYPE_CONFIG = {}

            settings.BOOKTYPE_CONFIG[name] = value

        setattr(settings, name, value)
    finally:
        writeLock.release()


def delConfiguration(name):
    """
    Deletes configuration variable.

    @type name: C{string}
    @param: Name of the variable
    """

    if hasattr(settings, 'BOOKTYPE_CONFIG'):
        writeLock.acquire()

        try:
            del settings.BOOKTYPE_CONFIG[name]
        finally:
            writeLock.release()
