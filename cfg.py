# System imports
from time import time
# Third-party imports
import praw
# Project imports
import file_manager

r = None
config_path = 'config/'  # Root of all configuration files
last_updated = 0
cached_returns = {}  # Used to, well, cache function returns. Not wildly


# used in the configuration files, but a handy
# option nonetheless.
# TODO: Look into streamlining the caching process

# Aliases of the file_manager functions to control the relative path
def read(relative_path):
    global config_path
    return file_manager.read(config_path + relative_path)


def readJson(relative_path):
    global config_path
    return file_manager.readJson(config_path + relative_path)


def save(relative_path, data):
    global config_path
    return file_manager.save(config_path + relative_path, data)


def saveJson(relative_path, data):
    global config_path
    return file_manager.saveJson(config_path + relative_path, data)


# Bot settings
def getSettings():
    import authentication
    global cached_returns
    global last_updated
    global config_path
    global r
    global profile

    # Only allow updating the settings once every couple minutes
    if 'settings' in cached_returns and time() - cached_returns['settings']['updated'] < 60 * 2:
        return cached_returns['settings']['return']

    settings = readJson('settings.json')

    # Get the OAuth information
    settings['bot'] = getAccounts()

    if 'settings' not in cached_returns:
        cached_returns['settings'] = {}
    cached_returns['settings']['updated'] = time()
    cached_returns['settings']['return'] = settings

    return settings


# Bot account OAuth information // These don't follow the profile,
# keep all bots in the same accounts.json file
def getAccounts():
    global config_path
    return file_manager.readJson(config_path + 'accounts.json')


def setAccounts(newAccounts):
    global config_path
    file_manager.saveJson(config_path + 'accounts.json', newAccounts)


# The Reddit app OAuth info necessary for registering ourselves as legit
def getOAuthInfo():
    return readJson('oauth.json')
