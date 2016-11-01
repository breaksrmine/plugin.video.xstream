# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.util import cUtil

SITE_IDENTIFIER = 'mykino_to'
SITE_NAME = 'MyKino'
SITE_ICON = 'mykino.png'

URL_MAIN = 'http://mykino.to/'
URL_Kinofilme = URL_MAIN + 'aktuelle-kinofilme/'
URL_FILME = URL_MAIN + 'filme/'
URL_SEARCH = URL_MAIN + 'index.php?do=search&subaction=search&story=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_Kinofilme)
    oGui.addFolder(cGuiElement('Aktuelle Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    params.setParam('sGenreId', 1)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    #params.setParam('sUrl', URL_MAIN)
    #params.setParam('sGenreId', 2)
    #oGui.addFolder(cGuiElement('Genre Serien', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showAlphaNumeric'), params)    
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showAlphaNumeric():
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = '<div[^>]*class="catalog-nav"[^>]*>(.*?)</div>'
    isMatch, sContainer = cParser().parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
       return

    pattern = '<a[^>]*href="([^"]+)"[^>]*>(\w)</a>'
    isMatch, aResult = cParser().parse(sContainer, pattern)

    if not isMatch:
        return

    oGui = cGui()
    params = ParameterHandler()
    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sName , SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()   

def showGenre():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('sUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<div[^>]*id="tabln%s"[^>]*>(.*?)</ul>' % oParams.getValue('sGenreId')
    isMatch, sContainer = cParser().parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
       return

    pattern = '<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>'
    isMatch, aResult = cParser().parse(sContainer, pattern)

    if not isMatch:
        return

    oGui = cGui()
    for sUrl, sName in aResult:
        oParams.setParam('sUrl', URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sName , SITE_IDENTIFIER, 'showEntries'), oParams)
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    parser = cParser()
    pattern = 'caption2"><a[^<]href="([^"]+).*?src="([^"]+).*?">([^<]+).*?<br>Jahr:[^<]([^<]+)'
    
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    if not isMatch: 
        if not sGui: oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    total = len (aResult)

    for sUrl, sThumbnail,  sName, sYear in aResult:
        oGuiElement = cGuiElement(cUtil().unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    isMatchNextPage, sNextUrl = parser.parseSingleResult(sHtmlContent, '<a[^>]*href="([^"]+)"[^>]*>Weiter</a>')
    if isMatchNextPage:
        params.setParam('sUrl', sNextUrl)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

    if not sGui:
        oGui.setView('movies')
        oGui.setEndOfDirectory()

def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    
    isMatch, aResult = cParser().parse(sHtmlContent, '<a[^>]*data-href="([^"]+)"[^>]*>.*?<span>([^<]*)<\/span>')
    if not isMatch:
        return []

    hosters = []
    for sUrls, sName in aResult:
        urls = sUrls.split(',')
        for idx, sLink in enumerate(sUrls.split(',')):
            hoster = {}
            hoster['name'] = sName
            hoster['link'] = sLink
            hoster['displayedName'] = '%s - Mirror %s' % (sName, idx+1)
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