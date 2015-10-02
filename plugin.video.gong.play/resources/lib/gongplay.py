import xbmc, xbmcaddon, urllib, urllib2, cookielib, urlparse, os.path, sys, re
from redirecthandler import GPHTTPRedirectHandler

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
	addon = xbmcaddon.Addon(id='plugin.video.gong.play')
	addon_name = addon.getAddonInfo('name')
	cj = cookielib.LWPCookieJar()
	profile = xbmc.translatePath( addon.getAddonInfo('profile') )
	cookie_file = os.path.join(profile, '.cookies')
	username = addon.getSetting('username')
	password = addon.getSetting('password')
	language = addon.getLocalizedString
	icon = xbmc.translatePath(os.path.join(addon.getAddonInfo('path'), "icon.png"))
	#urls
	url_main = 'http://play.gong.bg/'
	url_fixtures = 'http://play.gong.bg/fixture'
	#User agents
	ua_mobile = 'Mozilla/5.0 (Linux; Android 5.0.2; bg-bg; SAMSUNG GT-I9195 Build/JDQ39) AppleWebKit/535.19 (KHTML, like Gecko) Version/1.0 Chrome/18.0.1025.308 Mobile Safari/535.19' 
	ua_pc = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'
	last_response = ''

	def __init__(self):
		cookieprocessor = urllib2.HTTPCookieProcessor(self.cj)
		opener = urllib2.build_opener(GPHTTPRedirectHandler, cookieprocessor)
		urllib2.install_opener(opener)

	def request(self, url):
		if os.path.isfile(self.cookie_file):
			self.cj.load(self.cookie_file)

		req = urllib2.Request(url)
		req.add_header('User-Agent', self.ua_mobile)
		req.add_header('Referer', self.url_main)
		res = urllib2.urlopen(req)
		self.last_response = res.read()
		res.close()
		self.set_user_info()

	def login(self):
		post_data = urllib.urlencode({'email' : self.username, 'password' : self.password})
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

	def get_games(self):
		self.request(self.url_fixtures)
		dates = self.find_regex('date-info[\s\"]*.*>(.*?)</')
		hours = self.find_regex('time-info[\s\"]*.*>(.*?)</')
		details = self.find_regex('href[\s=]*\"(.*)\".*title[\s=]*\"(.*)\".*class[\s=\"]*.*btn-table.*(regular|live).*\".*>')
		if len(dates) != len(hours) or len(hours) != len(details) :
			return

		games = []
		
		for i in range(0, len(dates) - 1):
			title = "| [COLOR white]" + details[i][1] + "[/COLOR]"
			if details[i][2] == "live":
				live = "[COLOR green][B]" + self.language(30210) + "[/B][/COLOR]" 
				title = "[COLOR white]" + live.encode('utf-8') + " " + details[i][1] + "[/COLOR]"
			game = {}
			game['url'] = urlparse.urljoin(self.url_main, urllib.quote(details[i][0]))
			game['text'] = '[CAPITALIZE][B]' + dates[i][:9] + " " + hours[i] + "[/B][/CAPITALIZE] " + title
		
			games.append(game)
		return games

	def get_game_stream(self, url_game):
		if self.is_loggedin == False:
			self.login()

		self.request(url_game)
		#game_streams = ["http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8"]
		game_streams = []
		
		matches = self.find_regex('title>(.*?)</title')
		if len(matches) > 0:
			self.game_title = matches[0]

		matches = self.find_regex('iframe.*width=\"[0-9]*\" +height=\"[0-9]*\" +src=\"(.*?)\" +frameborder')
		if len(matches) > 0:
			url_iframe = matches[0]
			self.request(matches[0])
			video = self.find_regex('video.*src=(.*?) +controls')
			xbmc.log("Number of matches found for video: " + str(len(video)))
			if len(video) > 0:
				game_streams.append(video[0])
				game_streams.append(re.sub('_(1)\.st', "_2.st", video[0]))
		return game_streams

	def find_regex(self, exp, flags=re.IGNORECASE):
		return re.compile(exp, flags).findall(self.last_response)