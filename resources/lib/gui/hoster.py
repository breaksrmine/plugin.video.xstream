# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.player import cPlayer
import xbmc, xbmcgui
import logger
#test
import xbmcplugin
#import sys

class cHosterGui:

    SITE_NAME = 'cHosterGui'

    def __init__(self):
        self.userAgent = "|User-Agent=Mozilla/5.0 (Windows; U; Windows NT 5.1; de-DE; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3"
        self.maxHoster = int(cConfig().getSetting('maxHoster'))
        self.dialog = False

    # TODO: unify parts of play, download etc.
    def _getInfoAndResolve(self, siteResult):
        import urlresolver
        oGui = cGui()
        params = ParameterHandler()
        # get data
        data = {}
        mediaUrl = params.getValue('sMediaUrl')
        fileName = params.getValue('MovieTitle')
        if not fileName:
            fileName = params.getValue('Title')
        if not fileName: #only temporary
            fileName = params.getValue('sMovieTitle')
        if not fileName:
            fileName = params.getValue('title')

        data['title'] = fileName
        data['season'] = params.getValue('season')
        data['episode'] = params.getValue('episode')
        data['showTitle'] = params.getValue('TVShowTitle')
        data['thumb'] = params.getValue('thumb')
        # resolve
        if siteResult:
            mediaUrl = siteResult.get('streamUrl',False)
            mediaId = siteResult.get('streamID',False)

            if mediaUrl:
                logger.info('resolve: ' + mediaUrl)
                if siteResult['resolved']:
                    link = mediaUrl
                else:
                    link = urlresolver.resolve(mediaUrl)
            elif mediaId:
                logger.info('resolve: hoster: %s - mediaID: %s' % (siteResult['host'], mediaId))
                link = urlresolver.HostedMediaFile(host=siteResult['host'].lower(), media_id=mediaId).resolve()
        elif mediaUrl:
            logger.info('resolve: ' + mediaUrl)
            link = urlresolver.resolve(mediaUrl)
        else:
            oGui.showError('xStream', 'kein Hosterlink übergeben', 5)
            return False
        #resolver response
        if hasattr(link, 'msg'):
            msg = link.msg
        else: msg = False
        if link != False and not msg:
            data['link'] = link
            return data
        # error during resolving
        if not msg:
            msg = 'Stream nicht mehr verfügbar oder Link fehlerhaft'
            oGui.showError('xStream',str(msg),7)
        if hasattr(link, 'code'):
            logger.info(str(msg) +' UnresolveableCode: '+ str(link.code))
        else:
            logger.info(str(msg) +' UnresolveableCode: - ')
        '''
            UnresolveableCode
            0: Unknown Error
            1: The url was resolved, but the file has been permanantly
                removed
            2: The file is temporarily unavailable for example due to
                planned site maintenance
            3. There was an error contacting the site for example a
                connection attempt timed out
        '''
        return False

    def _addUserAgent(self, link):
        if 'User-Agent' or 'youtube' in link:
            return link
        if '|' in link:
            return link + '&' + self.userAgent
        else:
            return link	+ '|' + self.userAgent

    def play(self, siteResult=False):
        oGui = cGui()
        logger.info('attempt to play file')
        data = self._getInfoAndResolve(siteResult)
        if not data: return False
        logger.info('play file link: ' + str(data['link']))
        listItem = xbmcgui.ListItem(path=self._addUserAgent(data['link']))
        info = {}
        info['Title'] = data['title']
        if data['thumb']:
            listItem.setThumbnailImage(data['thumb'])
        if data['showTitle']:
            info['Episode'] = data['episode']
            info['Season'] = data['season']
            info['TvShowTitle'] = data['showTitle']
        oPlayer = cPlayer()
        if self.dialog:
            try:
                self.dialog.close()
            except:
                pass
        listItem.setInfo(type="Video", infoLabels=info)
        listItem.setProperty('IsPlayable', 'true')

        pluginHandle = oGui.pluginHandle
        xbmcplugin.setResolvedUrl(pluginHandle, True, listItem)
        res = oPlayer.startPlayer() #Necessary for autoStream
        return res

    def addToPlaylist(self, siteResult = False):
        oGui = cGui()
        logger.info('attempt addToPlaylist')
        data = self._getInfoAndResolve(siteResult)
        if not data: return False

        logger.info('addToPlaylist file link: ' + str(data['link']))
        oGuiElement = cGuiElement()
        oGuiElement.setSiteName(self.SITE_NAME)
        oGuiElement.setMediaUrl(data['link'])
        oGuiElement.setTitle(data['title'])
        if data['thumb']:
            oGuiElement.setThumbnail(data['thumb'])
        if data['showTitle']:
            oGuiElement.setEpisode(data['episode'])
            oGuiElement.setSeason(data['season'])
            oGuiElement.setTVShowTitle(data['showTitle'])
        if self.dialog:
            self.dialog.close()
        oPlayer = cPlayer()
        oPlayer.addItemToPlaylist(oGuiElement)
        oGui.showInfo('Playlist', 'Stream wurde hinzugefügt', 5);
        return True

    def download(self, siteResult = False):
        from resources.lib.download import cDownload
        logger.info('attempt download')
        data = self._getInfoAndResolve(siteResult)
        if not data: return False

        logger.info('download file link: ' + data['link'])
        if self.dialog:
            self.dialog.close()
        oDownload = cDownload()
        oDownload.download(data['link'], data['title'])
        return True

    def sendToPyLoad(self, siteResult = False):
        from resources.lib.handler.pyLoadHandler import cPyLoadHandler
        logger.info('attempt download with pyLoad')
        data = self._getInfoAndResolve(siteResult)
        if not data: return False
        cPyLoadHandler().sendToPyLoad(data['title'],data['link'])
        return True

    def sendToJDownloader(self, sMediaUrl = False):
        from resources.lib.handler.jdownloaderHandler import cJDownloaderHandler
        params = ParameterHandler()
        if not sMediaUrl:
            sMediaUrl = params.getValue('sMediaUrl')
        sFileName = params.getValue('sFileName')
        if self.dialog:
            self.dialog.close()
        logger.info('call send to JDownloader: ' + sMediaUrl)
        cJDownloaderHandler().sendToJDownloader(sMediaUrl)

    def __getPriorities(self, hosterList, filter = True):
        '''
        Sort hosters based on their resolvers priority.
        '''
        import urlresolver
        #          
        ranking = []
        #handles multihosters but is about 10 times slower
        for hoster in hosterList:
            # accept hoster which is marked as resolveable by sitePlugin
            if hoster.get('resolveable',False):
                ranking.append([0,hoster])
                continue
            source = urlresolver.HostedMediaFile(url=hoster['link'])
            if not source:
                source = urlresolver.HostedMediaFile(host=hoster['name'].lower(), media_id='dummy')
            if source:
                priority = False
                for resolver in source._HostedMediaFile__resolvers:
                    #prefer individual priority
                    if resolver.domains[0] != '*':
                        if hasattr(resolver, 'priority'):
                            priority = resolver.priority
                        else:
                            priority = resolver._get_priority()
                        break
                    if not priority:
                        if hasattr(resolver, 'priority'):
                            priority = resolver.priority
                        else:
                            priority = resolver._get_priority()
                if priority:
                    ranking.append([priority,hoster])
            elif not filter:
                ranking.append([999,hoster])

        if any('quality' in hoster[1] for hoster in ranking):
            if cConfig().getSetting('preferedQuality') != '5' and \
                    any('quality' in hoster[1] and int(hoster[1]['quality']) == int(cConfig().getSetting('preferedQuality')) \
                     for hoster in ranking):
                ranking = sorted(ranking, key=lambda hoster: \
                    int('quality' in hoster[1] and hoster[1]['quality']) == int(cConfig().getSetting('preferedQuality')), reverse=True)

            else:
                ranking = sorted(ranking, key=lambda hoster: 'quality' in hoster[1] and int(hoster[1]['quality']), reverse=True)
        else:
            ranking.sort()

        hosterQueue = []
        for i,hoster in ranking:
            hosterQueue.append(hoster)
        return hosterQueue

    def stream(self, playMode, siteName, function, url):
        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create('xStream',"get stream/hoster")
        #load site as plugin and run the function
        self.dialog.update(5,'import plugin...')
        plugin = __import__(siteName, globals(), locals())
        function = getattr(plugin, function)
        self.dialog.update(10,'catch links...')
        if url:
            siteResult = function(url)
        else:
            siteResult = function()
        self.dialog.update(40)
        if not siteResult:
            self.dialog.close()
            cGui().showInfo('xStream','stream/hoster not available')
            return
        # if result is not a list, make in one
        if not type(siteResult) is list:
            temp = []
            temp.append(siteResult)
            siteResult = temp
        # field "name" marks hosters
        if 'name' in siteResult[0]:
            functionName = siteResult[-1]
            del siteResult[-1]
            if not siteResult:
                self.dialog.close()
                cGui().showInfo('xStream','no hoster available')
                return

            self.dialog.update(60,'prepare hosterlist..')
            if (playMode !='jd') and (playMode != 'pyload') and \
                            cConfig().getSetting('presortHoster')=='true':
                # filter and sort hosters
                siteResult = self.__getPriorities(siteResult)
            if not siteResult:
                self.dialog.close()
                cGui().showInfo('xStream','no supported hoster available')
                return False
            self.dialog.update(90)
            #self.dialog.close()
            if len(siteResult) > self.maxHoster:
                siteResult = siteResult[:self.maxHoster-1]
            if len(siteResult)>1:
                #choose hoster
                if cConfig().getSetting('hosterSelect')=='List':
                    self.showHosterFolder(siteResult, siteName, functionName)
                    return
                siteResult = self._chooseHoster(siteResult)
                if not siteResult:
                    return
            else:
                siteResult = siteResult[0]
            # get stream links
            logger.info(siteResult['link'])
            function = getattr(plugin, functionName)
            siteResult = function(siteResult['link'])

            # if result is not a list, make in one
            if not type(siteResult) is list:
                temp = []
                temp.append(siteResult)
                siteResult = temp

        # choose part
        if len(siteResult)>1:
            siteResult = self._choosePart(siteResult)
            if not siteResult:
                logger.info('no part selected')
                return
        else:
            siteResult = siteResult[0]

        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create('xStream',' ')
        self.dialog.update(95,'start opening stream..')

        if playMode == 'play':
            self.play(siteResult)
        elif playMode == 'download':
            self.download(siteResult)
        elif playMode == 'enqueue':
            self.addToPlaylist(siteResult)
        elif playMode == 'jd':
            self.sendToJDownloader(siteResult['streamUrl'])
        elif playMode == 'pyload':
            self.sendToPyLoad(siteResult)

    def _chooseHoster(self, siteResult):
        dialog = xbmcgui.Dialog()
        titles = []
        for result in siteResult:
            if 'displayedName' in result:
                titles.append(result['displayedName'])
            else:
                titles.append(result['name'])
        index = dialog.select('Hoster wählen', titles)
        if index > -1:
            siteResult = siteResult[index]
            return siteResult
        else:
            logger.info('no hoster selected')
            return False

    def showHosterFolder(self, siteResult, siteName, functionName):
        oGui = cGui()
        total = len(siteResult)
        params = ParameterHandler()
        for hoster in siteResult:
            if 'displayedName' in hoster:
                name = hoster['displayedName']
            else:
                name = hoster['name']
            oGuiElement = cGuiElement(name, siteName, functionName)
            params.setParam('url',hoster['link'])
            params.setParam('isHoster','true')
            oGui.addFolder(oGuiElement, params, iTotal = total, isHoster = True)
        oGui.setEndOfDirectory()

    def _choosePart(self, siteResult):
        self.dialog = xbmcgui.Dialog()
        titles = []
        for result in siteResult:
            titles.append(result['title'])
        index = self.dialog.select('Part wählen', titles)
        if index > -1:
            siteResult = siteResult[index]
            return siteResult
        else:
            return False


    def streamAuto(self, playMode, siteName, function):
        logger.info('auto stream initiated')
        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create('xStream',"get stream/hoster")
        #load site as plugin and run the function
        self.dialog.update(5,'import plugin...')
        plugin = __import__(siteName, globals(), locals())
        function = getattr(plugin, function)
        self.dialog.update(10,'catch links...')
        siteResult = function()
        if not siteResult:
            self.dialog.close()
            cGui().showInfo('xStream','stream/hoster not available')
            return False
        # if result is not a list, make in one
        if not type(siteResult) is list:
            temp = []
            temp.append(siteResult)
            siteResult = temp
        # field "name" marks hosters
        if 'name' in siteResult[0]:
            self.dialog.update(90,'prepare hosterlist..')
            functionName = siteResult[-1]
            del siteResult[-1]
            hosters = self.__getPriorities(siteResult)
            if not hosters:
                self.dialog.close()
                cGui().showInfo('xStream','no supported hoster available')
                return False
            if len(siteResult) > self.maxHoster:
                siteResult = siteResult[:self.maxHoster-1]
            check = False
            self.dialog.create('xStream','try hosters...')
            total = len(hosters)
            for count, hoster in enumerate(hosters):
                if self.dialog.iscanceled() or xbmc.abortRequested or check: return
                percent = (count+1)*100/total
                try:
                    logger.info('try hoster %s' % hoster['name'])
                    self.dialog.create('xStream','try hosters...')
                    self.dialog.update(percent,'try hoster %s' % hoster['name'])
                    # get stream links
                    function = getattr(plugin, functionName)
                    siteResult = function(hoster['link'])
                    check = self.__autoEnqueue(siteResult, playMode)
                    if check:
                        return True
                except:
                    self.dialog.update(percent,'hoster %s failed' % hoster['name'])
                    logger.info('playback with hoster %s failed' % hoster['name'])
        # field "resolved" marks streamlinks
        elif 'resolved' in siteResult[0]:
            for stream in siteResult:
                try:
                    if self.__autoEnqueue(siteResult, playMode):
                        self.dialog.close()
                        return True
                except:
                    pass


    def __autoEnqueue(self, partList, playMode):
        # choose part
        if not partList:
            return False
        for i in range(len(partList)-1,-1,-1):
            try:
                if playMode == 'play' and i==0:
                    if not self.play(partList[i]):
                        return False
                elif playMode == 'download':
                    self.download(partList[i])
                elif playMode == 'enqueue' or (playMode=='play' and i>0):
                    self.addToPlaylist(partList[i])
            except:
                return False
        logger.info('autoEnqueue successful')
        return True


class Hoster:

    def __init__(self, name, link):
        self.name = name
        self.link = link
