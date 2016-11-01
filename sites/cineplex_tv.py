# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.util import cUtil
SITE_IDENTIFIER = 'cineplex_tv'
SITE_NAME = 'Cineplex'
SITE_ICON = 'cineplex.png'

URL_MAIN = 'http://cineplex.su/'
URL_CINEMA2015 = URL_MAIN + 'filme_2015/'
URL_CINEMA2014 = URL_MAIN + 'filme_2014/'
URL_CINEMA2013 = URL_MAIN + 'filme_2013/'
URL_SEARCH = URL_MAIN + 'index.php?story='
URL_GENRES_LIST = {'Abenteuer' : 'abenteuer/', 'Action' : 'action/', 'Animation' : 'animation/', 'Drama' : 'drama/', 'Fantasy' : 'fantasy/', 'Horror' : 'horror/', 'Krieg' : 'krieg/', 'Kriminal' : 'kriminal/', 'Komödie' : 'komoedie/', 'Romanze' : 'romanze/', 'Sci-Fi' : 'sci-fi/', 'Sport' : 'sport/', 'Thriller' : 'thriller/', 'Western' : 'western/'}
AZ_LIST = {'0-9' : '/catalog/0-9/', 'A' : '/catalog/A/', 'B' : '/catalog/B/', 'C' : '/catalog/C/', 'D' : '/catalog/D/', 'E' : '/catalog/E/', 'F' : '/catalog/F/', 'G' : '/catalog/G/', 'H' : '/catalog/H/', 'I' : '/catalog/I/', 'J' : '/catalog/J/', 'K' : '/catalog/K/', 'L' : '/catalog/L/', 'M' : '/catalog/M/', 'N' : '/catalog/N/', 'O' : '/catalog/O/', 'P' : '/catalog/P/', 'Q' : '/catalog/Q/', 'R' : '/catalog/R/', 'S' : '/catalog/S/', 'T' : '/catalog/T/', 'U' : '/catalog/U/', 'V' : '/catalog/V/', 'W' : '/catalog/W/', 'X' : '/catalog/X/', 'Y' : '/catalog/Y/', 'Z' : '/catalog/Z/'}

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genres', SITE_IDENTIFIER, 'showGenres'), params)
    oGui.addFolder(cGuiElement('Erscheinungsjahr', SITE_IDENTIFIER, 'MoviesByYear'))
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showAZ'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def MoviesByYear():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_CINEMA2015)
    oGui.addFolder(cGuiElement('Filme aus 2015', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_CINEMA2014)
    oGui.addFolder(cGuiElement('Filme aus 2014', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_CINEMA2013)
    oGui.addFolder(cGuiElement('Filme aus 2013', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showAZ():
    oGui = cGui()
    params = ParameterHandler()
    for key in sorted(AZ_LIST):
        params.setParam('sUrl', (URL_MAIN + AZ_LIST[key]))
        oGui.addFolder(cGuiElement(key, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showGenres():
    oGui = cGui()
    params = ParameterHandler()
    for key in sorted(URL_GENRES_LIST):    
        params.setParam('sUrl', (URL_MAIN + URL_GENRES_LIST[key]))
        oGui.addFolder(cGuiElement(key, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<li><a[^>]href="([^"]+).*?<img[^>]src="([^"]+).*?alt="([^(]+)[^>]([^)]+)'
    aResult = cParser().parse(sHtmlContent, pattern)

    if not aResult[0]:
        if not sGui: oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    total = len (aResult[1])
    util = cUtil()
    for sUrl, sThumbnail, sName, sYear in aResult[1]:
        oGuiElement = cGuiElement(util.unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    pattern = '<ul[^>]class="pagination">.*?</li>.*<li[^>]*><a[^>]*href="([^"]*)">Weiter<'
    aResult = cParser().parse(sHtmlContent, pattern)
    if aResult[0] and aResult[1][0]:
        params.setParam('sUrl', aResult[1][0])
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
    if not sGui:
        oGui.setView('movies')
        oGui.setEndOfDirectory()
        return

def showSearchEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = 'class="short">.*?href="([^"]+)"[^>]class="title">([^<(]+)[^>]([^")]+).*?<img[^>]src="([^"]+)".*?>([^<]+)</p>'
    aResult = cParser().parse(sHtmlContent, pattern)
    if not aResult[0]:
        if not sGui: oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return
    total = len (aResult[1])
    util = cUtil()
    for sEntryUrl, sName, sYear, sThumbnail, sDescription in aResult[1]:
        oGuiElement = cGuiElement(util.unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(util.unescape(sDescription.decode('utf-8')).encode('utf-8'))
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', sEntryUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    return

def showHosters():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<div[^>]+role="tabpanel"[^>]*id="([^"]+)"[^>]*>\s+(?:<span|<a)(.*?)</div>'
    parser = cParser()
    aResult = parser.parse(sHtmlContent, sPattern)
    hosters = []
    if not aResult[1]: return hosters
    for entry in aResult[1]:
        Pattern = 'href="([^"]+)"'
        lResult = parser.parse(entry[1], Pattern)
        if not lResult[1]: continue
        for i, link in enumerate(lResult[1],1):
            temphoster = {}
            temphoster['name'] = entry[0]
            temphoster['link'] = link
            temphoster['displayedName'] = '%s  Mirror %s' % (entry[0], i)
            hosters.append(temphoster)
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
    showSearchEntries(URL_SEARCH + sSearchText.strip() + '&do=search&subaction=search', oGui)
