# -*- coding: utf-8 -*-
import re, sys, os.path, urllib, urllib2, cookielib, urlparse
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from resources.lib.gongplay import GongPlay

reload(sys)  
sys.setdefaultencoding('utf8')
gong = GongPlay()

def CATEGORIES():	
	categories = gong.get_categories()
	for i in range(0, len(categories)):
		addDir(categories[i]['text'], categories[i]['url'], 1)
	if gong.is_loggedin == False:
		gong.login()
	if gong.is_loggedin == True:
		msg = gong.language(30204) + gong.expiration_date
		xbmc.executebuiltin('Notification(%s,%s,15000,%s)'%(gong.display_name, msg, gong.icon))

def GAMES(url_fixtures):
	games = gong.get_games()
	for i in range(0, len(games)):
		addDir(games[i]['text'], games[i]['url'], 2)
		
def STREAMS(match_url):
	streams = gong.get_game_stream(match_url)
	if len(streams) == 0:
		if gong.is_loggedin == False:
			xbmcgui.Dialog().ok(gong.addon_name, gong.language(30205))
		else:
			if gong.is_payment_expired == True:
				xbmcgui.Dialog().ok(gong.addon_name, gong.language(30203) + gong.expiration_date)
			else:
				xbmc.executebuiltin('Notification(%s,%s,5000,%s)'%(gong.addon_name,gong.language(30206), gong.icon))
	else:
		addLink(gong.game_title + " SD", streams[0], 3)
		xbmc.log("gong.game_title: " + str(gong.game_title) + " SD" + streams[0])
		if (len(streams)) > 1:
			addLink(gong.game_title + " HD", streams[1], 3)
			xbmc.log("gong.game_title: " + str(gong.game_title) + " HD" + streams[1])

def PLAY(url):
	li = xbmcgui.ListItem(iconImage=gong.icon, thumbnailImage=gong.icon, path=url)
	li.setInfo('video', { 'title': name })
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))

def addLink(name,url,mode):
	return addItem(name,url,mode)

def addDir(name,url,mode):
	return addItem(name,url,mode, True)

def addItem(name, url, mode, isDir = False):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage=gong.icon, thumbnailImage=gong.icon)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty("IsPlayable" , "true")
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isDir)
	return ok
	
def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

params=get_params()
url=None
name=None
iconimage=None
mode=None

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:
	name = urllib.unquote_plus(params["name"])
except:
	pass
try:
	iconimage = urllib.unquote_plus(params["iconimage"])
except:
	pass
try:
	mode = int(params["mode"])
except:
	pass

if mode==None or url==None or len(url)<1:
	CATEGORIES()
    
elif mode==1:
	GAMES(url)

elif mode==2:
	STREAMS(url)

elif mode==3:
	PLAY(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
