# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.util import cUtil

SITE_IDENTIFIER = 'streamkiste_tv'
SITE_NAME = 'StreamKisteTV'
SITE_ICON = 'streamkiste.png'

URL_MAIN = 'http://streamkiste.tv/'
URL_KINO = URL_MAIN + 'cat/kinofilme/'
URL_FILME = URL_MAIN + 'cat/filme/'
URL_SEARCH = URL_MAIN + '?s=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_KINO)
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    oGui.addFolder(cGuiElement('Filme nach...', SITE_IDENTIFIER, 'showMovieafter'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showMovieafter():
    oGui = cGui()
    params = ParameterHandler()
    oGui.addFolder(cGuiElement('Jahr', SITE_IDENTIFIER, 'showYear'))
    params.setParam('sUrl', URL_FILME + '?sortby=date')
    params.setParam('sParm', '?sortby=date')
    oGui.addFolder(cGuiElement('Most Recent', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_FILME + '?sortby=views')
    params.setParam('sParm', '?sortby=views')
    oGui.addFolder(cGuiElement('Most Views', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_FILME + '?sortby=imdb')
    params.setParam('sParm', '?sortby=imdb')
    oGui.addFolder(cGuiElement('According to IMDB Rate', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()    
    
def showYear():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_FILME).request()
    isMatch, aResult = cParser().parse(sHtmlContent, 'li class="year-item year.*?"><a href="([^"]+)">([^<]+)')
    if isMatch:
        total = len(aResult)
        for sUrl, sName in aResult:
            params.setParam('sUrl', URL_FILME + sUrl)
            params.setParam('sParm', sUrl)
            oGui.addFolder(cGuiElement((sName), SITE_IDENTIFIER, 'showEntries'), params, True, total)
    oGui.setEndOfDirectory()

def showGenre():
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = '>Genre[^>]Listen</a>.*?</ul>'
    isMatch, sContainer = cParser().parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        return

    pattern = '<a[^>]href="([^"]+).*?">([^<]+)'
    isMatch, aResult = cParser().parse(sContainer, pattern)

    if not isMatch:
        return

    oGui = cGui()
    params = ParameterHandler()
    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sName , SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()    

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    parser = cParser()
    pattern = 'src="([^"]+).*?<a[^>]href="([^"]+).*?">([^<]+).*?">([^<]+).*?class="story">([^<]+)'
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    if not isMatch: 
        if not sGui: oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    total = len (aResult)
    for sThumbnail, sUrl, sName, sYear, sDesc in aResult:
            oGuiElement = cGuiElement(cUtil().unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setDescription(sDesc)
            oGuiElement.setYear(sYear)
            params.setParam('entryUrl', sUrl)
            oGui.addFolder(oGuiElement, params, False, total)

    isMatchNextPage, sNextUrl = parser.parseSingleResult(sHtmlContent, '<link[^>]*rel="next"[^>]*href="([^"]+)"')
    if isMatchNextPage:
        sParm = params.getValue('sParm')
        if sParm:
            sNextUrl += sParm

        params.setParam('sUrl', sNextUrl)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

    if not sGui:
        oGui.setView('movies')
        oGui.setEndOfDirectory()

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<div[^>]id="stream-links"><a[^>]href="([^"]+).*?">([^<]+)'
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl, sName in aResult[1]:
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sName
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl=False):
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
