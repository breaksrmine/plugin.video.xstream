# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.util import cUtil
import re

SITE_IDENTIFIER = 'dokustreamer_de'
SITE_NAME = 'Dokustreamer'
SITE_ICON = 'dokustreamer.png'

URL_MAIN = 'https://dokustreamer.de/'
URL_HDDOKU = URL_MAIN + 'category/doku/dokus/hd-doku-stream'
URL_BELIEBTE = URL_MAIN + 'beliebte-dokumentationen'
URL_SEARCH = URL_MAIN + '?s='

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Dokus', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_HDDOKU)
    oGui.addFolder(cGuiElement('HD Dokus', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_BELIEBTE)
    oGui.addFolder(cGuiElement('Beliebte Dokumentationen', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Kategorien', SITE_IDENTIFIER, 'showKategorien'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showKategorien():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    aResult = cParser().parse(sHtmlContent, 'cat-item.*?"><ahref="([^"]+).*?">([^"]+)</a>([^<]+)')
    if aResult[0] and aResult[1][0]:
        total = len(aResult[1])
        for sUrl, sName, sNr in aResult[1]:
            params.setParam('sUrl', sUrl)
            oGui.addFolder(cGuiElement((sName + sNr), SITE_IDENTIFIER, 'showEntries'), params, True, total)
    oGui.setEndOfDirectory()

def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<a[^>].*?href="([^"]+)"[^>]title="([^"]+)">[^>]<img.*?src="([^"]+)'
    aResult = cParser().parse(sHtmlContent, pattern)
    if aResult[0] and aResult[1][0]:
        total = len(aResult[1])
        for sUrl, sName, sThumbnail in aResult[1]:
            sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
            sThumbnail = re.sub('-\d+x\d+\.', '.',sThumbnail)
            oGuiElement = cGuiElement(cUtil().unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setThumbnail(sThumbnail.decode('utf-8').encode('utf-8'))
            params.setParam('entryUrl', sUrl)
            oGui.addFolder(oGuiElement, params, False, total)
    pattern = 'class="nextpostslink"[^>]rel="next"[^>]href="([^"]+)'
    aResult = cParser().parse(sHtmlContent, pattern)
    if aResult[0] and aResult[1][0]:
        params.setParam('sUrl', aResult[1][0])
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
    if not sGui:
#        oGui.setView('movies') Weiß nicht was setzen wir hier????????
        oGui.setEndOfDirectory()

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '"[^>]src="([^"]+)"[^>]frameborder='
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl in aResult[1]:
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sUrl
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

def showSearchEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = 'title">[^>]<ahref="([^"]+)"[^>]title="([^"]+)'
    aResult = cParser().parse(sHtmlContent, pattern)
    total = len(aResult[1])
    for sUrl, sName in aResult[1]:
        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        oGuiElement = cGuiElement(cUtil().unescape(sName.decode('utf-8')).encode('utf-8'), SITE_IDENTIFIER, 'showHosters')
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showSearchEntries(URL_SEARCH + sSearchText.strip() , oGui)
