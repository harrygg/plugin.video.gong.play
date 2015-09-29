# -*- coding: utf-8 -*-
import re, sys, os.path
import urllib, urllib2, cookielib, urlparse
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

reload(sys)  
sys.setdefaultencoding('utf8')

__addon_id__= 'plugin.video.gong.play'
__Addon = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __Addon.getAddonInfo('name')
__language__ = __Addon.getLocalizedString
__path = xbmc.translatePath(__Addon.getAddonInfo('path') + "/resources/")
url_main = "http://play.gong.bg/"
url_fixtures = "http://play.gong.bg/fixture"
url_login = "http://play.gong.bg/signin"
#Get the debug mode from settings
debug = __Addon.getSetting("debug")
COOKIEFILE = __path + 'cookies'
GAME_TITLE = ""

### Functions definition
def Log(msg, error=False):
	if (error == True):
		xbmc.log("[" + __addon_id__ + '] | ' + msg.encode('utf-8'), xbmc.LOGERROR)
	else:
		if (debug == "true"):
			xbmc.log("[" + __addon_id__ + '] | ' + msg.encode('utf-8'))

msg = "Debug mode is " + debug
Log(msg)
		
MUA = 'Mozilla/5.0 (Linux; Android 5.0.2; bg-bg; SAMSUNG GT-I9195 Build/JDQ39) AppleWebKit/535.19 (KHTML, like Gecko) Version/1.0 Chrome/18.0.1025.308 Mobile Safari/535.19' 
UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'

## Intercept the redirect and invoke the cookies processor
class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_302(self, req, fp, code, msg, headers):
		return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
	http_error_301 = http_error_303 = http_error_307 = http_error_302

cj = cookielib.LWPCookieJar()
cookieprocessor = urllib2.HTTPCookieProcessor(cj)
opener = urllib2.build_opener(MyHTTPRedirectHandler, cookieprocessor)
urllib2.install_opener(opener)
LoggedIn = False
subscription_expired_msg = ""
response = ""

def CATEGORIES():
	Log ("CATEGORIES | Requesting url: " + url_fixtures)
	response = REQUEST(url_fixtures)
	SET_LOGGEDIN(response)
	
	#To make thinks simpler, get the content of the <UL> element which holds all games first.
	ul_content = re.compile('<ul.*program-nav.*tablist[\s\"]*>(.*?)</ul>', re.DOTALL).findall(response)
	if len(ul_content) != 0:
		#Find out category links and titles. 
		hrefs = re.compile('href[\s="]*(.*?)"').findall(ul_content[0])
		Log ("CATEGORIES | Found: " + str(len(hrefs)) + " href matches")
		categories = re.compile('p.*?>(.*?)</p').findall(ul_content[0])
		Log ("CATEGORIES | Found: " + str(len(categories)) + " p matches")
		# The hrefs are always one more than the category names
		if len(categories) == len(hrefs) - 1:
			addDir('Програма - Всички категории', url_fixtures, 1, '')
			for i in range(0, len(categories)):
				#Filter category and capitalize it
				title = categories[i][0].upper() + categories[i][1:]
				title = title.replace('<br>', '')
				url = urlparse.urljoin(url_main, hrefs[i+1])
				addDir(title, url, 1, 'DefaultFolder.png')
				Log ("CATEGORIES | Category: " + categories[i])
				Log ("CATEGORIES | Url: " + hrefs[i+1])
	else:
		#If we didn't find any categories for some reason - maybe the source has changed, try using the hardcoded list
		#TODO Maybe hardcoded links are not a good idea...
		addDir('Програма - Всички категории', urlparse.urljoin(url_main, 'fixture'),1,'DefaultFolder.png')
		addDir('България - А група', urlparse.urljoin(url_main, 'fixture/index/1'),1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/grupa-a.png'))
		addDir('България - Купа на България', urlparse.urljoin(url_main, 'fixture/index/2'),1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/kupa-bg.png'))
		addDir('Англия - Premier Lague', urlparse.urljoin(url_main, 'fixture/index/0'),1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/visha-liga.png'))
		addDir('Англия - FA Cup', urlparse.urljoin(url_main, 'fixture/index/3'),1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/fa-cup.png'))
		addDir('Англия - Capital One Cup', urlparse.urljoin(url_main, 'fixture/index/4'), 1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/capital-one-cup.png'))
		addDir('Англия - Sky Bet Championship', urlparse.urljoin(url_main, 'fixture/index/5') ,1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/sky-bet.png'))
		addDir('Франция - Ligue 1', urlparse.urljoin(url_main, 'fixture/index/14'), 1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/visha-liga.png'))
		addDir('Евро 2016', urlparse.urljoin(url_main, 'fixture/index/13'), 1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/evro-kcalificacii-2016.png'))
		addDir('Формула 1', urlparse.urljoin(url_main, 'fixture/index/7'),1 , urlparse.urljoin(url_main,  'img/championships-logos-sprites-only/formula-1.png'))
		addDir('NBA', urlparse.urljoin(url_main, 'fixture/index/6'), 1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/nba.png'))
		addDir('Бокс', urlparse.urljoin(url_main, 'fixture/index/12'), 1, urlparse.urljoin(url_main, 'img/championships-logos-sprites-only/box.png'))
		

def INDEX(url_fixtures):
	Log ( "INDEX | Requesting url: " + url_fixtures )
	response = REQUEST(url_fixtures)

	#1. Find dates <p class=\"date-info\">(.*)</p>
	Log ( "INDEX | Using regular expression 'date-info[\s\"]*.*>(.*?)</' to find out the game dates" )
	dates = re.compile('date-info[\s\"]*.*>(.*?)</').findall(response)
	#2. Find hours
	Log ( "INDEX | Using regular expression 'time-info[\s\"]*.*>(.*?)</' to find out the game start hours" )
	hours = re.compile('time-info[\s\"]*.*>(.*?)</').findall(response)
	#. Find match link and text
	Log ("INDEX | Using regular expression 'href[\s=]*\"(.*)\".*title[\s=]*\"(.*)\".*class[\s=\"]*.*btn-table.*(regular|live).*\".*>' to find out the game url and text")
	details = re.compile('href[\s=]*\"(.*)\".*title[\s=]*\"(.*)\".*class[\s=\"]*.*btn-table.*(regular|live).*\".*>').findall(response)
	Log ("INDEX | Found: " + str(len(dates)) + " dates")
	Log ("INDEX | Found: " + str(len(hours)) + " hours")
	Log ("INDEX | Found: " + str(len(details)) + " links and titles")

	if len(dates) != len(hours) or len(hours) != len(details) :
		Log ("INDEX | The number of found RE didn't match. Please contact the support!")
		Log ("INDEX | Page response:")
		#print  response
		return

	end = len(dates) - 1

	for i in range(0, end):
		title = "| [COLOR white]" + details[i][1] + "[/COLOR]"
		if details[i][2] == "live":
			live = "[COLOR green][B]" + __language__(30210) + "[/B][/COLOR]" 
			title = "[COLOR white]" + live.encode('utf-8') + " " + details[i][1] + "[/COLOR]"
		match_url = urlparse.urljoin(url_main, urllib.quote(details[i][0]))
		Log ("INDEX | Generated match_url: " + match_url )
		Log ("INDEX | dates["+str(i)+"]: " + dates[i] )
		#Log ("INDEX | dates[i].rstrip()[:-9]: " + dates[i][:6] )
		match_text = '[CAPITALIZE][B]' + dates[i][:9] + " " + hours[i] + "[/B][/CAPITALIZE] " + title
		#Create a directory link for the given game
		addDir(match_text, match_url, 2, "")
		
def GETGAMESTREAMS(match_url):
	Log ( "GETGAMESTREAMS | Requesting url: " + match_url )
	
	# 1. Find the iframe that contains the stream url
	iframe_url = GETIFRAME(match_url)
	if (iframe_url == "" and LoggedIn == False): # We are either not logged in
		LOGIN()
		iframe_url = GETIFRAME(match_url)

	if iframe_url == "" :	# Again no iframe ... Check if payment has expired
		Log ( "GETGAMESTREAMS | <iframe> Not found" )
		#1.1 If Iframe was not found, check whether subscription has expired
		payment_expired = IS_PAYMENT_EXPIRED()
		if payment_expired == True :
			Log ("GETGAMESTREAMS | Payment expired on: " + subscription_expired_msg, True)
			xbmcgui.Dialog().ok( __language__(30203), __language__(30204), subscription_expired_msg)

	else : #IFrame is found so request it and get the stream url
		Log ("GETGAMESTREAMS | <iframe> src search: Found " + iframe_url )
		# 2. Load the iframe url
		Log ("GETGAMESTREAMS | Requesting url: " + iframe_url )
		response = REQUEST ( iframe_url )

		# 3. Find the <video> tag containing the HTML5 playlist
		Log ( "GETGAMESTREAMS | Using regular expression '<video +src=(.*) +controls' to find out the game playlist url" )
		video = re.compile('<video.*src=(.*?) +controls').findall(response)
		Log ( "GETGAMESTREAMS | Found: " + str(len(video)) + " video matches" )
		if ( len(video) > 0 ) :
			Log ( "GETGAMESTREAMS | <video> tag src: " + video[0] )
			hd_link = re.sub('_(1)\.st', "_2.st", video[0])
			Log ( "GETGAMESTREAMS | generated HD stream: " + hd_link )
			addLink(GAME_TITLE + " SD", video[0], 3, "")
			addLink(GAME_TITLE + " HD", hd_link, 3, "")

def GETIFRAME(match_url)	:
	Log ( "GETIFRAME() | Requesting url: " + match_url )
	response = REQUEST(match_url)	
	
	# 1. Find title
	game_title_matches = re.compile('title>(.*?)</title').findall(response);
	if len(game_title_matches) > 0:
		global GAME_TITLE
		GAME_TITLE = game_title_matches[0]
		Log ("GETIFRAME() | Found game title: " + GAME_TITLE )

	# 2. Find the iframe that contains the player
	iframe_url = re.compile('<iframe.*width=\"[0-9]*\" +height=\"[0-9]*\" +src=\"(.*?)\" +frameborder').findall(response)
	if len(iframe_url) > 0:
		Log ( "GETIFRAME() | Found iframe url: " + iframe_url[0] )
		return iframe_url[0]
	else :
		Log ( "GETIFRAME() | <iframe> Not found" )
		return ""
		
# Login
def LOGIN() :
	Log ("Login() | Trying to login with credentials:")
	username = __Addon.getSetting("username")
	password = __Addon.getSetting("password")
	Log ("Login() | Username: " + username + " Password: " + password)
	post_data = {'email' : username, 'password' : password}
	post_data = urllib.urlencode(post_data)
	Log ("Login() | URL encoded data: " + post_data)

	req = urllib2.Request(url_login, post_data)
	req.add_header('User-Agent', UA)
	req.add_header('Content-Type', "application/x-www-form-urlencoded")

	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	cj.save(COOKIEFILE, ignore_discard=True)
	
	SET_LOGGEDIN(data)
	if LoggedIn == False:
		xbmcgui.Dialog().ok(__addonname__, __language__(30205))

def SET_LOGGEDIN(response) :
	Log ( "SET_LOGGEDIN | response: " +  response )
	matches = re.compile('(/signout\")').findall(response)
	global LoggedIn
	if len(matches) > 0:
		Log ("SET_LOGGEDIN | Loggedin")
		LoggedIn = True
	else:
		Log ("SET_LOGGEDIN | Not logged in. 'signout' -> " + str(len(matches)) + " maches")
		LoggedIn = False

def IS_PAYMENT_EXPIRED() :
	Log ( "IS_PAYMENT_EXPIRED | <iframe> Not found" )
	#2.1 If Iframe was not found, check whether subscription has expired
	payment_expired = re.compile('alert-abonament.*[\"\s]*<span.*>(.*)</span').findall(response)
	Log ("IS_PAYMENT_EXPIRED | Search for expired payment: Found " + str(len(payment_expired)) + " results" )
	if len(payment_expired) > 0:
		Log ("IS_PAYMENT_EXPIRED | Payment expired on: " + payment_expired[0], True)
		payment_expired_on = re.compile('([0-9]{1,2}.*[0-9]{4}.*[0-9:]{5})').findall(payment_expired[0])
		if len(payment_expired_on) > 0:
			Log ("IS_PAYMENT_EXPIRED | payment_expired_on " + payment_expired_on[0], True )
			global subscription_expired_msg
			subscription_expired_msg = payment_expired_on[0]
			Log ("IS_PAYMENT_EXPIRED | subscription_expired_msg: " + subscription_expired_msg )
			return True
	else :
		return False

def REQUEST(url) :
	Log ("request() | Requesting url: " + url)
	if os.path.isfile(COOKIEFILE):
		cj.load(COOKIEFILE)
	req = urllib2.Request(url)
	req.add_header('User-Agent', MUA)
	req.add_header('Referer', url_main)
	res = urllib2.urlopen(req)
	global response
	response = res.read()
	res.close()
	return response
	
def PLAY(url):
	Log ( "PLAY | Playing stream: " + url )
	li = xbmcgui.ListItem(iconImage="", thumbnailImage="", path=url)
	li.setInfo('video', { 'title': "" })
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))

def addLink(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty("IsPlayable" , "true")
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok

def addDir(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
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
	url=urllib.unquote_plus(params["url"])
except:
	pass
try:
	name=urllib.unquote_plus(params["name"])
except:
	pass
try:
	name=urllib.unquote_plus(params["iconimage"])
except:
	pass
try:
	mode=int(params["mode"])
except:
	pass

if mode==None or url==None or len(url)<1:
	print ""
	CATEGORIES()
    
elif mode==1:
	print ""+url
	INDEX(url)

elif mode==2:
	print ""+url
	GETGAMESTREAMS(url)

elif mode==3:
	print ""+url
	PLAY(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
