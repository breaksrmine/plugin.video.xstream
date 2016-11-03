#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from os import getcwd
from os.path import join
from sys import path
import xbmc
import platform
from xbmc import log
from resources.lib import common

__settings__ = common.addon
__cwd__ = common.addonPath

# Add different library path
path.append(join(__cwd__, "resources", "lib"))
path.append(join(__cwd__, "resources", "lib", "gui"))
path.append(join(__cwd__, "resources", "lib", "handler"))
path.append(join(__cwd__, "resources", "art", "sites"))
path.append(join(__cwd__, "sites"))

log("The new sys.path list: %s" % path, level = xbmc.LOGDEBUG)

# Run xstream
from xstream import run
log('*---- Running xStream, version %s ----*' % __settings__.getAddonInfo('version'))
print "\t[xStream] Python-Version: %s" % platform.python_version()

#import cProfile
#cProfile.run('run()',join(__cwd__,'xstream.pstats'))
try:
    run()
except Exception, err:
    if str(err) == 'UserAborted':
        print "\t[xStream] User aborted list creation"
    else:
        import traceback
        import xbmcgui
        print traceback.format_exc()
        dialog = xbmcgui.Dialog().ok('Error',str(err.__class__.__name__)+" : "+str(err),str(traceback.format_exc().splitlines()[-3].split('addons')[-1]))
    