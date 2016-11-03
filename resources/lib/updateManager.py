# -*- coding: utf-8 -*-
import urllib
import os
import json
import zipfile
import logger
from resources.lib.common import addonPath, profilePath
from resources.lib.download import cDownload

## Installation path.
ROOT_DIR = addonPath
ADDON_DIR = os.path.abspath(os.path.join(ROOT_DIR, '..'))
XSTREAM_DIRNAME = os.path.basename(ROOT_DIR)


## URLRESOLVER
REMOTE_URLRESOLVER_COMMITS = "https://api.github.com/repos/tknorris/script.module.urlresolver/commits/master"
REMOTE_URLRESOLVER_DOWNLOADS = "https://github.com/tknorris/script.module.urlresolver/archive/master.zip"

## XSTREAM
REMOTE_XSTREAM_COMMITS = "https://api.github.com/repos/xStream-Kodi/plugin.video.xstream/commits/nightly"
REMOTE_XSTREAM_NIGHTLY = "https://github.com/xStream-Kodi/plugin.video.xstream/archive/nightly.zip"

## Filename of the update File.
LOCAL_FILE_NAME = "xStream_update.zip"
LOCAL_NIGHTLY_VERSION = os.path.join(profilePath, "nightly_commit_sha")
LOCAL_RESOLVER_VERSION = os.path.join(profilePath, "resolver_commit_sha")


def xStreamUpdate():
    logger.info("xStream xStreamUpdate")
    nightlycommitsXML = urllib.urlopen(REMOTE_XSTREAM_COMMITS).read()
    commitUpdate(nightlycommitsXML, LOCAL_NIGHTLY_VERSION, REMOTE_XSTREAM_NIGHTLY, ROOT_DIR, "Updating xStream")

def urlResolverUpdate():
    logger.info("xStream urlResolverUpdate")

    urlResolverPaths = []
    for child in os.listdir(ADDON_DIR):
        if not child.startswith('script.module.urlresolver'): continue
        resolver_path = os.path.join(ADDON_DIR, child)
        if os.path.isdir(resolver_path):
            urlResolverPaths.append(resolver_path)

    if len(urlResolverPaths) > 1:
        from resources.lib.gui.gui import cGui
        cGui().showError('xStream', 'Es ist mehr als ein URLResolver installiert. Bitte löschen!', 5)
        logger.info("Its more the one URLResolver installed!")
        return

    commitXML = urllib.urlopen(REMOTE_URLRESOLVER_COMMITS).read()
    commitUpdate(commitXML, LOCAL_RESOLVER_VERSION, REMOTE_URLRESOLVER_DOWNLOADS, urlResolverPaths[0], "Updating URLResolver")

def commitUpdate(onlineFile, offlineFile, downloadLink, LocalDir, Title):
    try:
        if not os.path.exists(offlineFile) or open(offlineFile).read() != \
                json.loads(onlineFile)['sha']:
            update(LocalDir, downloadLink, Title)
            open(offlineFile, 'w').write(json.loads(onlineFile)['sha'])
    except Exception as e:
        logger.info("Ratelimit reached")
        logger.info(e)

def update(LocalDir, REMOTE_PATH, Title):
    logger.info(Title + " from: " + REMOTE_PATH)
    cDownload().download(REMOTE_PATH, LOCAL_FILE_NAME, False, Title)

    updateFile = zipfile.ZipFile(os.path.join(profilePath, LOCAL_FILE_NAME))

    removeFilesNotInRepo(updateFile, LocalDir)

    for index, n in enumerate(updateFile.namelist()):
        if n[-1] != "/":
            dest = os.path.join(LocalDir, "/".join(n.split("/")[1:]))
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            data = updateFile.read(n)
            if os.path.exists(dest):
                os.remove(dest)
            f = open(dest, 'wb')
            f.write(data)
            f.close()
    updateFile.close()

    logger.info("Update Successful")

def removeFilesNotInRepo(updateFile, LocalDir):
    updateFileNameList = [i.split("/")[-1] for i in updateFile.namelist()]

    for root, dirs, files in os.walk(LocalDir):
        if ".git" in root or "pydev" in root or ".idea" in root:
            continue
        else:
            for file in files:
                if file not in updateFileNameList:
                    os.remove(os.path.join(root, file))
