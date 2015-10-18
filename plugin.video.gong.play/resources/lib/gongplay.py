import xbmc, xbmcaddon, urllib, urllib2, cookielib, urlparse, os.path, sys, re
from redirecthandler import GPHTTPRedirectHandler
from StringIO import StringIO
import gzip

reload(sys)  
sys.setdefaultencoding('utf8')

class GongPlay:

	display_name = ''
	debug = True
	is_loggedin = False
	is_payment_expired = True
	expiration_date = ''
	subscription_expired_msg = ''
	subscription_msg = ''
	game_title = ''
	addon_name = ''
	username = ''
	password = ''
	cj = cookielib.LWPCookieJar()
	cookie_file = ''
	cookie_file_vbox = ''
	icon = ''
	#urls
	url_main = 'http://play.gong.bg/'
	url_fixtures = 'http://play.gong.bg/fixture'
	url_video_clips = 'http://vbox7.com/user:gongbg?p=allvideos'
	url_vbox_resolver = 'http://vbox7.com/etc/ext.do?key='
	#User agents
	ua_mobile = 'Mozilla/5.0 (Linux; Android 5.0.2; bg-bg; SAMSUNG GT-I9195 Build/JDQ39) AppleWebKit/535.19 (KHTML, like Gecko) Version/1.0 Chrome/18.0.1025.308 Mobile Safari/535.19' 
	ua_pc = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
	last_response = ''

	def __init__(self, addon):
		self.addon_name = addon.getAddonInfo('name')
		self.icon = xbmc.translatePath(os.path.join(addon.getAddonInfo('path'), "icon.png"))
		self.username = addon.getSetting('username')
		self.password = addon.getSetting('password')
		profile = xbmc.translatePath( addon.getAddonInfo('profile'))
		self.cookie_file = os.path.join(profile, '.cookies')
		self.cookie_file_vbox = os.path.join(profile, '.vboxcookie')
		cookieprocessor = urllib2.HTTPCookieProcessor(self.cj)
		opener = urllib2.build_opener(GPHTTPRedirectHandler, cookieprocessor)
		urllib2.install_opener(opener)

	def request(self, url, ua = ua_mobile, rf = url_main):
		if os.path.isfile(self.cookie_file):
			self.cj.load(self.cookie_file)
		req = urllib2.Request(url)
		req.add_header('User-Agent', ua)
		req.add_header('Referer', rf)
		res = urllib2.urlopen(req)
		self.last_response = res.read()
		res.close()
		if not 'vbox7' in url:
			self.set_user_info()

	def login(self):
		post_data = urllib.urlencode({'email' : self.username, 'password' : self.password})
		xbmc.log(post_data)
		req = urllib2.Request('http://play.gong.bg/signin', post_data)
		req.add_header('User-Agent', self.ua_mobile)
		req.add_header('Content-Type', "application/x-www-form-urlencoded")
		res = urllib2.urlopen(req)
		self.last_response = res.read()
		res.close()
		self.cj.save(self.cookie_file, ignore_discard=True)
		self.set_user_info()
	
	def set_user_info(self):
		#Limit the scope of search by getting the user info dir
		user_div = re.compile('user-info\">(.*?)</div', re.DOTALL).findall(self.last_response)
		if (len(user_div)) > 0:
			self.get_loggedin(user_div[0])	
			self.get_display_name(user_div[0])
			self.get_payment_info(user_div[0])
			
	def get_loggedin(self, text):
		matches = re.compile('(/signout\")').findall(text)
		self.is_loggedin = True if len(matches) > 0 else False

	def get_display_name(self, text):
		matches = re.compile('user-name.*>(.*?)</a').findall(text)
		if len(matches) > 0:
			self.display_name = matches[0]
			
	def get_payment_info(self, text):
		navbar = re.compile('navbar-right.*"\s*>(.*?)<').findall(text)
		if (len(navbar)) > 0 :
			self.subscription_msg = navbar[0]
			date = re.compile('([0-9]{1,2}.*[0-9]{4}.*[0-9:]{5})').findall(navbar[0])
			if (len(date)) > 0:
				self.expiration_date = date[0]
		expired = re.compile('alert-abonament').findall(text)
		self.is_payment_expired = True if len(expired) > 0 else False
		
	def get_categories(self):
		self.request(self.url_fixtures)
		matches = self.find_regex('ul.*program-nav.*tablist[\s\"]*>(.*?)</ul', re.DOTALL)
		categories = []
		if len(matches) != 0:
			#Find out category links and titles. 
			hrefs = re.compile('href[\s="]*(.*?)"').findall(matches[0])
			names = re.compile('p.*?>(.*?)</p').findall(matches[0])
			# The hrefs are always one more than the category names
			if len(names) == len(hrefs) - 1:
				categories.append({'text' : 'Програма - Всички категории', 'url' : hrefs[0]})
				for i in range(0, len(names)):
					#Filter category and capitalize it
					title = names[i][0].upper() + names[i][1:]
					category = {}
					category['text'] = title.replace('<br>', '')
					category['url'] =  urlparse.urljoin(self.url_main, hrefs[i+1])
					categories.append(category)
		return categories

	def get_games(self, url):
		games = []
		
		self.request(urlparse.urljoin(self.url_main, url))
		dates = self.find_regex('date-info[\s\"]*.*>(.*?)</')
		hours = self.find_regex('time-info[\s\"]*.*>(.*?)</')
		details = self.find_regex('href[\s=]*\"(.*)\".*title[\s=]*\"(.*)\".*class[\s=\"]*.*btn-table.*(regular|live).*\".*>')
		if len(dates) == len(hours) and len(hours) == len(details):
			for i in range(0, len(dates) - 1):
				title = "| [COLOR white]" + details[i][1] + "[/COLOR]"
				if details[i][2] == "live":
					live = "[COLOR green][B]%s[/B][/COLOR]" 
					title = "[COLOR white]" + live + " " + details[i][1] + "[/COLOR]"
				game = {}
				game['url'] = urlparse.urljoin(self.url_main, urllib.quote(details[i][0]))
				game['text'] = '[CAPITALIZE][B]' + dates[i][:9] + " " + hours[i] + "[/B][/CAPITALIZE] " + title
				games.append(game)
		return games

	def get_game_stream(self, url_game):
		if self.is_loggedin == False:
			self.login()
		self.request(url_game)
		#streams = ["http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8"]
		streams = []
		matches = self.find_regex('title>(.*?)<')
		if len(matches) > 0:
			self.game_title = matches[0]
		matches = self.find_regex('iframe.+src[="\'\s]+(.*?)[\'"\s]+')
		if len(matches) > 0:
			url_iframe = matches[0]
			self.request(matches[0])
			video = self.find_regex('video.+src[="\']+(.*?)[\'"\s]+')
			if len(video) > 0:
				streams.append(video[0])
				streams.append(re.sub('_(1)\.s', "_2.s", video[0]))
		return streams

	def find_regex(self, exp, flags=re.IGNORECASE):
		return re.compile(exp, flags).findall(self.last_response)
	
	def get_video_clips(self, url):
		self.request(url)
		video_clips = []
		matches = self.find_regex('a.*href=\"/play:([0-9a-zA-Z]{10})\".*img.*src=\"(.*?)\".*alt=\"(.*?)\"')
		if len(matches) > 0:
			for i in range(0, len(matches)):
				video_clip = {}
				video_clip['id'] = matches[i][0]
				video_clip['icon'] = matches[i][1]
				video_clip['text'] = matches[i][2]
				video_clips.append(video_clip)
		return video_clips
	
	def get_clip_stream(self, id):
		self.request(self.url_vbox_resolver + id, self.ua_pc, self.url_video_clips)
		matches = self.find_regex('flv_addr=(.*?)&')	
		return matches[0] if len(matches) > 0 else ''