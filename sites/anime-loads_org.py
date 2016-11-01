# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.util import cUtil
from resources.lib.config import cConfig
import json, time, re, xbmcgui

SITE_IDENTIFIER = 'anime-loads_org'
SITE_NAME = 'AnimeLoads'
SITE_ICON = 'anime-loads.png'

URL_MAIN = 'http://www.anime-loads.org/'
URL_SEARCH = URL_MAIN + 'search?q=%s'
URL_MOVIES = URL_MAIN + '%s-movies/'
URL_MOVIES_ASC = URL_MOVIES + '?sort=title&order=asc'
URL_SERIES = URL_MAIN + '%s-series/'
URL_SERIES_ASC = URL_SERIES + '?sort=title&order=asc'

# supported movie-types
SUPP_TYPES = [ "anime", "asia", "hentai" ]

def load():
    logger.info("Load %s" % SITE_NAME)

    oGui = cGui()
    params = ParameterHandler()

    params.setParam('sType', "anime")
    oGui.addFolder(cGuiElement('Anime', SITE_IDENTIFIER, 'showBasicMenu'), params)
    params.setParam('sType', "asia")
    oGui.addFolder(cGuiElement('Asia', SITE_IDENTIFIER, 'showBasicMenu'), params)
    if showAdult():
        params.setParam('sType', "hentai")
        oGui.addFolder(cGuiElement('Hentai', SITE_IDENTIFIER, 'showHentaiMenu'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showBasicMenu():
    oGui = cGui()
    params = ParameterHandler()

    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showMovieMenu'), params)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showSeriesMenu'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), params)
    oGui.setEndOfDirectory()

def showHentaiMenu():
    oGui = cGui()
    params = ParameterHandler()
    
    sType = params.getValue('sType')

    params.setParam('sUrl', URL_MAIN + sType)
    oGui.addFolder(cGuiElement('Neuste Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN + sType + '/?sort=title&order=asc')
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), params)
    oGui.setEndOfDirectory()

def showMovieMenu():
    oGui = cGui()
    params = ParameterHandler()
    
    sType = params.getValue('sType')

    params.setParam('sUrl', URL_MOVIES % sType)
    oGui.addFolder(cGuiElement('Neuste Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES_ASC % sType)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showSeriesMenu():
    oGui = cGui()
    params = ParameterHandler()

    sType = params.getValue('sType')

    params.setParam('sUrl', URL_SERIES  % sType)
    oGui.addFolder(cGuiElement('Neuste Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIES_ASC  % sType)
    oGui.addFolder(cGuiElement('Alle Serien', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()

    if not entryUrl: entryUrl = params.getValue('sUrl')

    # set 'safe_search' for adult results
    safeSearchUrl = entryUrl + ('&' if '?' in entryUrl else '?') + 'safe_search=' + str(int(showAdult()))

    sHtmlContent = _getRequestHandler(safeSearchUrl, True, (sGui is not False)).request()
    pattern = '<img[^>]*src="([^"]*)"[^>]*class="img-responsive[ ]img-rounded"[^>]*>.*?' # Thumbnail
    pattern += '<a[^>]*href="([^"]*)"[^>]*>(.*?)</a[>].*?' # link / title
    pattern += '<a[^>]*><i[^>]*></i>(.*?)</a[>].*?' # type
    pattern += '<a[^>]*><i[^>]*></i>(.*?)</a[>].*?' # year
    pattern += '<span[^>]*><i[^>]*></i>(.*?)</span[>].*?' # episode count
    pattern += '<div[^>]*class="mt10"[^>]*>([^<>]*)</div>.*?' # description
    pattern += '<a[^>]*class="label[ ]label-info"[^>]*>([^<>]*)</a>' # genre (atm. without use)
    aResult = cParser().parse(sHtmlContent, pattern)

    if not aResult[0]: 
        if not sGui: oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    sType = params.getValue('sType')
    isTvshow = True if (URL_SERIES % sType) in entryUrl else False

    total = len (aResult[1])
    for sThumbnail, sUrl, sName, sKind, sYear, sEpisodes, sDesc, sGenre in aResult[1]:
        sKind = sKind.strip().lower()
        sKindName = re.compile('\A(\w+)[ ]?').findall(sKind)[0]
        if sKindName not in SUPP_TYPES: # only process supportet types
            continue
        isMovie = True if sKind.endswith('film')  or ' ' not in sKind else False
        sDesc = cUtil().unescape(sDesc.decode('utf-8')).encode('utf-8').strip()
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showReleases')
        oGuiElement.setMediaType('movie' if isMovie else 'tvshow')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc.strip())
        oGuiElement.setYear(sYear)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, True, total)

    aResult = cParser().parse(sHtmlContent, "<a[^>]*href=['\"]#['\"][^>]*>\d+</a>.*?<a[^>]*href=['\"]([^'\"]*)['\"][^>]*>\d+</a>")
    if aResult[0] and aResult[1][0]:
        params.setParam('sUrl', aResult[1][0])
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

    if not sGui:
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()

def showReleases():
    oGui = cGui()
    params = ParameterHandler()

    sHtmlContent = _getRequestHandler(params.getValue('entryUrl'), True).request()
    pattern = "<a[^>]*href=['\"]#stream_(\d+)['\"][^>]*>.*?</i>(.*?)" # releaseId / Name (opt)
    pattern += "(?:<i[^>]*class=['\"].*?flag-(\w+)['\"][^>]*>.*?)?" # main-lang (opt)
    pattern += "(?:[|]\s<i[^>]*class=['\"].*?flag-(\w+)['\"][^>]*>.*?)?</li>" # suptitle-lang (opt)
    aResult = cParser().parse(sHtmlContent, pattern)

    if not aResult[0] or not aResult[1][0]: 
        oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    sThumbnail = params.getValue('sThumbnail')
    sName = params.getValue('sName')

    total = len(aResult[1])
    for sReleaseId, sReleaseName, sLang, sSubLang in aResult[1]:
        aStreams = cParser().parse(sHtmlContent, "id=['\"]streams_episodes_%s_\d['\"]" % sReleaseId)
        if not aStreams[0] or not aStreams[1][0]: # skip empty releases
            continue
        sReleaseName = sReleaseName.strip()
        if sLang and sSubLang:
            sReleaseName += " (%s | %s)" % (sLang.upper(),sSubLang.upper())
        elif sLang:
            sReleaseName += " (%s)" % (sLang.upper())
        oGuiElement = cGuiElement(sReleaseName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('iReleaseId', int(sReleaseId))
        if len(aStreams[1]) > 1:
            oGuiElement.setFunction("showEpisodes")
            oGui.addFolder(oGuiElement, params, True, total)
        else:
            params.setParam('iEpisodeId', 0)
            oGui.addFolder(oGuiElement, params, False, total)
    oGui.setEndOfDirectory()

def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()

    sHtmlContent = _getRequestHandler(params.getValue('entryUrl')).request()
    pattern = "<a[^>]*href=['\"]#streams_episodes_%d_(\d+)['\"][^>]*>.*?" % int(params.getValue('iReleaseId')) # EpisodeId
    pattern += "<strong>(\d+)</strong>(.*?)</span>" # Episode-Nr / Name
    aResult = cParser().parse(sHtmlContent, pattern)

    if not aResult[0] or not aResult[1][0]: 
        oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    sThumbnail = params.getValue('sThumbnail')
    sName = params.getValue('sName')

    total = len(aResult[1])
    for sEpisodeId, sNumber, sEpisodName in aResult[1]:
        oGuiElement = cGuiElement(str(int(sNumber)) + " - " + sEpisodName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setMediaType('episode')
        oGuiElement.setEpisode(int(sNumber))
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('iEpisodeId', int(sEpisodeId))
        oGui.addFolder(oGuiElement, params, False, total)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()

def showHosters():
    params = ParameterHandler()
    sHtmlContent = _getRequestHandler(params.getValue('entryUrl')).request()
    aUdResult = cParser().parse(sHtmlContent, "'&ud=(.*?)\">")
    pattern = 'id="streams_episodes_%d_%d"\sdata-enc="(.+?)"' % (int(params.getValue('iReleaseId')),int(params.getValue('iEpisodeId')))
    aResult = cParser().parse(sHtmlContent, pattern)
    hosters = []
    if aUdResult[0] and aResult[0]:
        hosters = _decryptLink(aResult[1][0], aUdResult[1][0])
    return hosters

def getHosterUrl(sUrl = False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')

    results = []
    result = {}
    result['streamUrl'] = _resolveLeaveLink(sUrl)
    result['resolved'] = False

    # fallback if links cant be resolved
    if result['streamUrl']:
        results.append(result)

    return results

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
  
    # add filter-typ for type base search
    sType = ParameterHandler().getValue('sType')
    if sType:
        sSearchText = sSearchText.strip() + "&type="+sType

    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)

def showAdult():
    oConfig = cConfig()
    if oConfig.getSetting('showAdult')=='true':    
        return True
    return False

def _decryptLink(enc, ud):
    # try to get links from captcha response
    response = _sendEnc(enc, ud)
    if 'code' in response and response['code'] == 'error':
        token = _uncaptcha()
        if token:
            response = _sendEnc(enc, ud, token)

    hosters = []
    if 'content' in response:
        for entry in response['content']:
            hostEntry = entry
            if type(entry) is not dict and 'links' in response['content'][entry]:
                hostEntry = response['content'][entry]

            if 'links' in hostEntry:
                for item in hostEntry['links']:
                    hoster ={}
                    hoster['link'] = item['link']
                    hoster['name'] = hostEntry['hoster_name']
                    if 'part' in item:
                        hoster['displayedName'] = '%s - Part %s' % (hostEntry['hoster_name'],item['part'])
                    hosters.append(hoster)

    if len(hosters) > 0:
        hosters.append('getHosterUrl')
    return hosters

def _resolveLeaveLink(link):
    sHtmlContent = _getRequestHandler(URL_MAIN + 'leave/' + link).request()
    aResult = cParser().parse(sHtmlContent, "link\s+=\s'(.*?)',")
    if aResult[0]:
        dialog = xbmcgui.DialogProgress()
        dialog.create('xStream',"Waiting for Redirect...")
        secToWait = 15 # this is needed for the leave-page
        for count in range(0, secToWait+1):
            if dialog.iscanceled():
                break
            dialog.update((count)*100/secToWait, 'waiting for redirect: '+ str(secToWait-count)+'sec remaining')
            time.sleep(1)
        dialog.close()
        oRequestHandler = _getRequestHandler(aResult[1][0])
        oRequestHandler.request()
        return oRequestHandler.getRealUrl()

def _sendEnc(enc, ud, response = None):
    _getRequestHandler('%sassets/pub/js/userdata?ud=%s' % (URL_MAIN, ud)).request()
    oRequestHandler = _getRequestHandler(URL_MAIN + 'ajax/captcha')
    oRequestHandler.addParameters('enc', enc)
    oRequestHandler.addParameters('response', (response if response else 'nocaptcha'))
    return json.loads(oRequestHandler.request())

def _uncaptcha():
    try:
        siteKey=_getSiteKey()
        if siteKey:
            from urlresolver.plugins.lib import recaptcha_v2
            token = recaptcha_v2.UnCaptchaReCaptcha().processCaptcha(siteKey, lang='de,en-US;q=0.7,en;q=0.3')
            if token:
                return token
    except ImportError:
        pass

def _getSiteKey():
    sHtmlContent = _getRequestHandler(URL_MAIN, True).request()
    pattern = '<script [^>]*src="([^"]*basic.(?:min.)?js[^"]*)"[^>]*></script[>].*?'
    aResult = cParser().parse(sHtmlContent, pattern)
    if aResult[0]:
        sHtmlContent = _getRequestHandler(aResult[1][0], True).request()
        aResult = cParser().parse(sHtmlContent, "'sitekey'\s?:\s?'(.*?)'")
        if aResult[0]:
            return aResult[1][0]
        else:
            logger.error("error while getting sitekey: sitekey not found in basic.min.js")
    else:
        logger.error("error while getting sitekey: basic.min.js not found")

def _getRequestHandler(sUrl, bCache = False, ignoreErrors = False):
    oRequest = cRequestHandler(sUrl, caching = bCache, ignoreErrors = ignoreErrors)
    oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0')
    return oRequest
