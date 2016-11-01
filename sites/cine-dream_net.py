# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.pluginHandler import cPluginHandler
from resources.lib.util import cUtil
import re

SITE_IDENTIFIER = 'cine-dream_net'
SITE_NAME = 'CineDream'
SITE_ICON = 'cine-dream_net.png'

URL_MAIN = 'http://www.cine-dream.net/'
URL_KINO = 'http://www.cine-dream.net/category/aktuelle-kinofilme'
URL_SEARCH =  URL_MAIN + '?s=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_KINO)
    oGui.addFolder(cGuiElement('Aktuelle Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Kategorien', SITE_IDENTIFIER, 'showCategory'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showCategory():
    params = ParameterHandler()
    oGui = cGui()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = 'class="cat-item.*?a[^>]*href="([^"]+)" title="([^"]+)' # url / title
    aResult = cParser().parse(sHtmlContent, pattern)
    for sUrl, sTitle in aResult[1]:
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sTitle.strip(), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')

    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    parser = cParser()
    aResult = parser.parse(sHtmlContent, '<h2[^>]*class="maintitle">(.*?)<center') # filter main content if needed
    if aResult[0]:
        sHtmlContent = aResult[1][0]

    pattern = '<div[^>]*class="thumbnail">.*?' # container
    pattern += '<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>.*?' # linke / title
    pattern += '<img[^>]*src="([^"]*)"' # image
    aResult = parser.parse(sHtmlContent, pattern)

    if not aResult[0]:
        if not sGui: oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return
    util = cUtil()
    total = len (aResult[1])
    for sEntryUrl, sName, sThumbnail in aResult[1]:
        if "stream" not in sEntryUrl: continue
        oGuiElement = cGuiElement(util.unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', sEntryUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    pattern = '<a[^>]*class="nextpostslink"[^>]*href="([^"]+)"'
    aResult = parser.parse(sHtmlContent, pattern)
    if aResult[0] and aResult[1][0]:
        params.setParam('sUrl', aResult[1][0])
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

    if not sGui:
        oGui.setView('movies')
        oGui.setEndOfDirectory()
        return

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '>Stream:\s([^\s]+)\s.*?<center><a href="([^"]+)' # hostername / url
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sName, sUrl in aResult[1]:
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sName
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl = False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {}
    result['streamUrl'] = sUrl
    result['resolved'] = False
    results.append(result)
    return results

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)