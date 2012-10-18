#!/usr/bin/env python2.7
import json
import webapp2
from bs4 import BeautifulSoup
from google.appengine.ext import db
from urllib import urlencode as encode
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template

client_id = '338132796157.apps.googleusercontent.com'
client_secret = '-NbOc_ZrFcT_2RsJoDgz0vQA'
calander_name = 'My Ucc Timetable'

#redirect_uri = 'http://localhost:8080/auth'
redirect_uri = 'http://ucc-timetabler.appspot.com/auth'

dayOffsets = {'Mo': 0, 'Tu': 1, 'We': 2, 'Th': 3, 'Fr': 4}
timeBlocks = {0:'080000', 1:'083000', 2:'090000', 3:'093000', 4:'100000', 5:'103000', 6:'110000', 7:'113000', 8:'120000', 9:'123000', 10:'130000', 11:'133000', 12:'140000', 13:'143000', 14:'150000', 15:'153000', 16:'160000', 17:'163000', 18:'170000', 19:'173000', 20:'180000', 21:'183000', 22:'190000', 23:'193000', 24:'200000', 25:'203000'} 
weeksTable = {"1":20120827, "2":20120903, "3":20120910, "4":20120917, "5":20120924, "6":20121001, "7":20121008, "8":20121015, "9":20121022, "13":20121119, "10":20121029, "14":20121126, "15":20121203, "11":20121105, "12":20121112, "16":20121210, "17":20121217, "18":20121224, "19":20121231, "20":20130107, "21":20130114, "22":20130121, "23":20130128, "24":20130204, "25":20130211, "26":20130218, "27":20130225, "28":20130304, "29":20130311, "30":20130318, "31":20130325, "32":20130401, "34":20130415, "33":20130408, "35":20130422, "36":20130429, "37":20130506, "38":20130513, "39":20130520, "40":20130527, "41":20130603, "42":20130610, "43":20130617, "44":20130624, "45":20130701, "46":20130708, "47":20130715, "48":20130722, "49":20130729, "50":20130805, "51":20130812, "52":20130819}

class Programme(db.Model):
	code = db.StringProperty(required=True)

class Module(db.Model):
	day = db.StringProperty()
	code = db.StringProperty()
	title = db.StringProperty()
	location = db.StringProperty()
	startTime = db.StringProperty()
	endTime = db.StringProperty()
	startDate = db.StringProperty()
	endDate = db.StringProperty()
	programme = db.ReferenceProperty(Programme, collection_name='modules', required=True)

def out(self, text):
	self.response.out.write(str(text) + '\n')

class MainHandler(webapp2.RequestHandler):
	def get(self):
		request = encode({
			'client_id' : client_id,
			'redirect_uri' : redirect_uri,
			'response_type' : 'code',
			'approval_prompt' : 'force',
			'scope' : 'https://www.googleapis.com/auth/calendar',
		})
		url = 'https://accounts.google.com/o/oauth2/auth?' + request
		self.response.out.write(template.render('templates/home.html', {'url': url}))

class AuthHandler(webapp2.RequestHandler):
	def get(self):
		code = self.request.get('code', False)
		error = self.request.get('error', False)
		if code:
			request = encode({
				'code' : code,
				'client_id' : client_id,
				'client_secret' : client_secret,
				'redirect_uri' : redirect_uri,
				'grant_type' : 'authorization_code'
			})
			result = urlfetch.fetch(
				url='https://accounts.google.com/o/oauth2/token',
				payload=request,
				method=urlfetch.POST)
			data = json.loads(result.content)
			request = encode({'access_token' : data['access_token']})
			self.redirect('/landing?' + request)

class ModuleHandler(webapp2.RequestHandler):
	def get_timetable(self):
		request = encode({ 
			'identifier': self.programme_code,
			'days':'1-5',
			'periods':'1-20',
			'weeks':'5-16;20-31',
			'objectclass':'programme+of+study',
			'style':'individual'
		})
		result = urlfetch.fetch(
					url='http://timetable.ucc.ie/showtimetable.asp',
					payload=request,
					method=urlfetch.POST)
		self.html = result.content
	
	def parse(self):
	  	soup = BeautifulSoup(self.html)
	  	rows = soup.find("table", {"class" : "grid-border-args"}).findAll("tr", recursive=False)[1:]
	  	day = ''
	  	modules = []
	  	for row in rows:
			timePosition = 0
			if 'row-label-one' in row.td['class']:
		  		day = row.td.text[:2]
		 		timePosition = -1
			dayOffset = dayOffsets[day]

			blocks = row.find_all('td', recursive=False)
			for block in blocks:
		  		if 'object-cell-border' in block['class']:
					#module found
		  			#ensure different object for each period
					weeks = block('td')[-1].text.split(', ')
					for period in weeks:
						module = Module(programme=self.programme)

						#set module code and title
						abbrs = block('abbr')
						module.code, module.title = abbrs[0]['title'][:6], abbrs[0]['title'][7:]

						#set module time
						module.day = day
						moduleLength = int(block['colspan'])
						module.startTime = timeBlocks[timePosition]
						module.endTime = timeBlocks[timePosition + moduleLength]

						#set module location if exists
						location = None
						if len(abbrs) == 2: 
						  	module.location = abbrs[1]['title']

					  	dates = [str(weeksTable[date] + dayOffset) for date in period.split('-')]
					  	if len(dates) == 2:
						  	module.startDate, module.endDate = dates[0], dates[1]
					  	else:
						  	module.startDate = module.endDate = dates[0]
					  	modules.append(module)
					timePosition += int(block['colspan'])
				else:
					timePosition += 1
		if len(modules) > 0:
			db.put(modules)
		else:
			self.programme.delete()
			raise Exception('No modules Available')
		
	def get(self):
		self.programme_code = self.request.get('programme_code', False)
		if self.programme_code:
			try:
				programmes = list(Programme.gql('WHERE code = :1', [self.programme_code]).run(batch_size=1000))
				if len(programmes) == 0:
					#parse new course
					self.programme = Programme(code=self.programme_code)
					self.programme.put()
					self.get_timetable()
					self.parse()
				else:
					self.programme = programmes[0]

				modules = sorted(set([(module.code, module.title) for module in self.programme.modules]), reverse=True)
				values = {
					'modules' : modules,
					'programme_code' : self.programme_code
				}
				self.response.out.write(template.render('templates/modules.html', values))
			except Exception as error:
				self.response.out.write(template.render('templates/error.html', {'error': error}))
		else:
			self.response.out.write(template.render('templates/error.html', {}))

class FinalizeHandler(webapp2.RequestHandler):
	def insert(self, base, string, p1, p2):
		return base[:p1] + string + base[p1:p2] + string + base[p2:]

	def formatDate(self, date):
		return self.insert(date, '-', 4, 6)

	def formatTime(self, time):
		return self.insert(time, ':', 2, 4) + '.000'

	def calanderExists(self):
		result = urlfetch.fetch(
			url='https://www.googleapis.com/calendar/v3/users/me/calendarList?access_token=' + self.access_token,
			method=urlfetch.GET)
		data = json.loads(result.content)
		exists = False
		for calander in data['items']:
			if calander['summary'] == calander_name:
				self.calander_id = calander['id']
				exists = True
				break
		return exists

	def deleteCalander(self):
		urlfetch.fetch(
			url='https://www.googleapis.com/calendar/v3/calendars/'+ self.calander_id +'?access_token=' + self.access_token,
			method=urlfetch.DELETE)

	def createCalander(self):
		calander = {
			'summary': calander_name,
			'location': 'University College Cork',
			'timeZone': 'Europe/Dublin',
		}
		calander = json.dumps(calander, indent=4)
		result = urlfetch.fetch(
			url='https://www.googleapis.com/calendar/v3/calendars?access_token=' + self.access_token,
			payload=calander,
			method=urlfetch.POST,
			headers={'Content-Type': 'application/json'})
		data = json.loads(result.content)
		self.calander_id = data['id']

	def putModule(self, module):
		event = {
			'summary': module.code,
			'description': module.title,
			'location': module.location,
			'start': {
				'dateTime': self.formatDate(module.startDate)+ 'T' + self.formatTime(module.startTime),
				'timeZone': 'Europe/Dublin'
			},
			'end': {
				'dateTime': self.formatDate(module.startDate)+ 'T' + self.formatTime(module.endTime),
				'timeZone': 'Europe/Dublin'
			},
			'recurrence': [
				'RRULE:FREQ=WEEKLY;UNTIL=' + module.endDate,
			],
		}
		event = json.dumps(event, indent=4)
		rpc = urlfetch.create_rpc()
		urlfetch.make_fetch_call(
			rpc=rpc,
			url='https://www.googleapis.com/calendar/v3/calendars/'+self.calander_id+'/events?access_token=' + self.access_token,
			payload=event,
			method=urlfetch.POST,
			headers={'Content-Type': 'application/json'})
		self.rpcs.append(rpc)

	def get(self):
		self.access_token = self.request.get('access_token', False)
		self.programme_code = self.request.get('programme_code', False)
		self.choices = self.request.get_all('module', False)

		if self.access_token and self.programme_code and self.choices:
			try:
				programme_key = Programme.gql('WHERE code = :1', [self.programme_code]).get().key()
				modules = list(Module.gql('WHERE programme = :1 AND code IN :2', programme_key, self.choices).run(batch_size=1000))

				if not self.calanderExists():
					self.createCalander()

				self.rpcs = []
				for module in modules:
					self.putModule(module)

				for rpc in self.rpcs:
					rpc.wait()

				self.response.out.write(template.render('templates/finish.html', {}))
			except Exception as error:
				self.response.out.write(template.render('templates/error.html', {'error': error}))
		else:
			self.response.out.write(template.render('templates/error.html', {}))

#only link this when debugging
class ClearHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write(db.delete(db.Query(keys_only=True)))

app = webapp2.WSGIApplication([('/', MainHandler),
							   ('/auth', AuthHandler),
							   ('/select_modules', ModuleHandler),
							   ('/finalize', FinalizeHandler)])
