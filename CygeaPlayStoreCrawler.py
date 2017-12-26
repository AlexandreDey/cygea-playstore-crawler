#!/bin/python
import multiprocessing
import threading
import queue
import time

import config
from gpapi.googleplay import GooglePlayAPI
from helpers import sizeof_fmt

# Constant to ease usage
EMAIL=0
PASSWORD=1
AUTH_TOKEN=2
ANDROID_ID=3
PROXY=4

DOWNLOAD=10
SEARCH_ONLY=11

class AccountBanned(Exception):
	pass

class UnknownApp(Exception):
	pass

class ConnectionImpossible(Exception):
	pass


class PlaystoreInterface():
	def __init__(self, resources, download_folder, min_stock=3):
		self.AVAILABLE_RESOURCES = resources
		# Threshold under which the interface will wait before opening a new playstore connection
		self.MIN_STOCK = min_stock
		self.DOWNLOAD_FOLDER = download_folder
		print("Interface created with access to %s account" %(resources.qsize()))
		print("Minimal stock is %s" %(min_stock))
		print("Download path is %s" %(download_folder))

	# Get an available account
	def requestRessource(self):				
		# Add a "wait" entry if not enough resssource
		if(self.AVAILABLE_RESOURCES.qsize() <= self.MIN_STOCK):
			self.AVAILABLE_RESOURCES.put([None, None, None, None, None])
			return [None, None, None, None, None]

		res = self.AVAILABLE_RESOURCES.get()

		return res

	# Release account
	def releaseRessource(self, ressource):		
		self.AVAILABLE_RESOURCES.put(ressource)

	# Initiate a connection to the playstore
	def loginToAccount(self, maxAttempt=4): 
		connected = 0
		attempt = 0

		while True:
			user = self.requestRessource()
			if not user[EMAIL] == None:
				break
			time.sleep(2)

		# Connection to a google account
		while connected == 0:
			attempt += 1
			if attempt > maxAttempt:
				raise ConnectionImpossible()
			# create api connection
			api = GooglePlayAPI(proxies_config=user[PROXY])
			print (user[EMAIL])
			# connect it
			try:
				if user[AUTH_TOKEN]:
					print(user[AUTH_TOKEN])
					api.login(None, None, user[ANDROID_ID], user[AUTH_TOKEN])
				else:
					api.login(user[EMAIL], user[PASSWORD], None, None)
					user[ANDROID_ID] = api.gsfId
				connected = 1           
			except:
				print("Connection failed, switching account")
				user[AUTH_TOKEN] = None
				self.releaseRessource(user)
				while True:
					user = self.requestRessource()
					if not user[EMAIL] == None:
						break
					time.sleep(2)

				

		#save auth token
		user[AUTH_TOKEN] = api.authSubToken
		print (api.authSubToken)
		return (api, user)

	# params
	#	api = logged google api object
	#	packagename : package to download
	#	filename : where to download the file
	def downloadApp(self, api,package,filename):
				                   
		try:
			stream = api.download(package, None, progress_bar=False)
			data = stream['data']
			with open(filename, "wb") as f:
				f.write(data)
			print("Done")
		except RequestError as e:
			print(e)
			raise UnknownApp


	# params
	#	packagename : package to download
	def download(self, packagename):
		attempt = 0
		try:
			api, connected_user = self.loginToAccount()
		except ConnectionImpossible:
			# TODO: notify administrator that connection error occured
			print ("Unable to connect")
			return -1

		while attempt < 4:
			try:
				attempt += 1
				self.downloadApp(api, packagename, self.DOWNLOAD_FOLDER + packagename + ".apk")	
				self.releaseRessource(connected_user)		
				return self.DOWNLOAD_FOLDER + packagename + ".apk"
			except AccountBanned:
				connected_user[AUTH_TOKEN] = None
				self.releaseRessource(connected_user)
				try:
					api, connected_user = self.loginToAccount()
					continue
				except ConnectionImpossible:
					# TODO: notify administrator that connection error occured
					return -1
			except UnknownApp:
				self.releaseRessource(connected_user)			
				return -1
			except:
				self.releaseRessource(connected_user)
				return -1

	def search(self, word):
		# Connection to a google account
		try:
			api, user = self.loginToAccount()
		except ConnectionImpossible:
			# TODO: notify administrator that connection error occured
			print ("Unable to connect")
			return -1 
		
		try:
			message = api.search(word, 250, None) # Search the playstore with the word
		except:
			print ("Error: HTTP 500 - one of the provided parameters is invalid")
			self.releaseRessource(user)
			api, user = self.loginToAccount()
			return 0

		try:
			return message
		except IndexError: # if we were blocked
			# Auth token is no longer valid
			user[AUTH_TOKEN] = None
			print ("Account blocked, switching ...")
			self.releaseRessource(user)
			api, user = self.loginToAccount()           
			return 0



class DownloadThread(threading.Thread):
	def __init__(self, work, resources, download_folder):
		super(DownloadThread, self).__init__()
		self.AVAILABLE_RESOURCES = resources
		self.WORK_QUEUE = work
		self.INTERFACE = PlaystoreInterface(self.AVAILABLE_RESOURCES, download_folder, min_stock=resources.qsize()-1)
		# Used to interrupt the thread after completting his
		self.KILL_FLAG = 0

	# Used to perform action before downloading the app (ex: statistics on apps info)
	def pre_download_action(self, app_info):
		return

	# Used to perform action after downloading the app (ex: store apk in db, perform analysis on it, ...)
	def post_download_action(self, app_info, apk_file):
		return

	def kill(self):
		self.KILL_FLAG = 1

	def run(self):
		# The thread will stop when the parent process tells it to
		while not self.KILL_FLAG:
			# Wait until there is work in the queue
			pkg = self.WORK_QUEUE.get()
			# Perform pre-download actions
			self.pre_download_action(pkg)
			# Download
			dl_dst = self.INTERFACE.download(pkg["docId"])
			if not dl_dst == -1:
				# If all went well, perform post-download action
				self.post_download_action(pkg, dl_dst)
			self.WORK_QUEUE.task_done()


class CrawlerProcess(multiprocessing.Process):
	def __init__(self, proc_num, download_folder, proc_resources, found_app, dictionary, max_thread=4, proc_type=DOWNLOAD):
		super(CrawlerProcess, self).__init__()
		self.MAX_THREAD = max_thread
		self.CURRENT_NB_THREAD = 0
		self.ID = proc_num
		self.PROC_TYPE = proc_type
		self.dl_threads = []
		self.unfinished_job = None
		self.proc_progress = 0
		self.DOWNLOAD_FOLDER = download_folder
		self.KILL_FLAG = 0

		print("[proc%s]: Initializing process ..." %(self.ID))


		self.FOUND_APP = found_app

		# Resources that the child threads will use
		self.AVAILABLE_RESOURCES = proc_resources

		# Interface that will be used to communicate with the playstore
		self.INTERFACE = PlaystoreInterface(self.AVAILABLE_RESOURCES, None)

		print("[proc%s]: Got %s Accounts ..." %(self.ID, self.AVAILABLE_RESOURCES.qsize()))
		self.DICT = dictionary
	
	
	def search_and_download(self):
		manager = multiprocessing.Manager()
		to_download_list = manager.Queue()
		ThreadStarted = False

		i = 0
		total_found_by_proc = 0
		for word in self.DICT:
			if self.KILL_FLAG == 1:
				break

			newly_found_app = 0
			search_result = self.INTERFACE.search(word)
			for result in search_result:
				# If we are not able to insert in FOUND_APP, the app was already found
				if not result['docId'] in self.FOUND_APP:
					self.FOUND_APP.append(result['docId'])
					to_download_list.put(result)
					newly_found_app += 1
			i += 1
			total_found_by_proc += newly_found_app
			print("[proc%s]: Number of search: %s\nNumber of found app by process: %s (%s in this loop)\nTotal of found app: %s" %(self.ID, i, total_found_by_proc, newly_found_app, len(self.FOUND_APP)))
			
			if ThreadStarted == False:
				ThreadStarted = True
				# Spawn download threads
				for i in range(self.MAX_THREAD):					
					self.dl_threads.append(DownloadThread(to_download_list, self.AVAILABLE_RESOURCES, self.DOWNLOAD_FOLDER))
					print("[proc%s]: Spawned thread %s ..." %(self.ID, i))
					self.dl_threads[i].start()

		# Return the list of app that have been found but not downloaded and the number of words searched
		self.unfinished_job = to_download_list
		self.proc_progress = i

		# Wait until killing process is done
		while KILL_FLAG == 1:
			continue

	def search_only(self):
		i = 0
		total_found_by_proc = 0
		for word in self.DICT:
			if self.KILL_FLAG == 1:
				break

			newly_found_app = 0
			search_result = self.INTERFACE.search(word)
			for result in search_result:
				# If we are not able to insert in FOUND_APP, the app was already found
				if not result['docId'] in self.FOUND_APP:
					self.FOUND_APP.append(result['docId'])
					newly_found_app += 1
			i += 1
			total_found_by_proc += newly_found_app
			print("[proc%s]: Number of search: %s\nNumber of found app by process: %s (%s in this loop)\nTotal of found app: %s" %(self.ID, i, total_found_by_proc, newly_found_app, len(self.FOUND_APP)))
		
		# Return the number of words searched
		self.proc_progress = i
		
		# Wait until killing process is done
		while KILL_FLAG == 1:
			continue

	def kill(self):
		self.KILL_FLAG = 1
		# Send the kill signal to everyone
		for i in range(self.MAX_THREAD):
			self.dl_threads[i].kill()
		# Then wait for them to be done
		for i in range(self.MAX_THREAD):
			self.dl_threads[i].join()

		# Wait until killing process is done
		self.KILL_FLAG = 0
		# Return the progress of the processus if it is to be resumed later
		return (self.unfinished_job, self.proc_progress)

	

	def run(self):
		if self.PROC_TYPE == SEARCH_ONLY:
			self.search_only()
		else:
			self.PROC_TYPE = DOWNLOAD
			self.search_and_download()




class PlaystoreCrawler():
	def __init__(self, config_folder="crawler_conf", crawler_type=DOWNLOAD):
		self.config = config.CrawlerConfig(config_folder)
		
		self.PROC_LIST = []
		self.manager = multiprocessing.Manager()
		# TODO load from backup
		self.FOUND_APP = self.manager.list()

		proc_res = self.manager.Queue()
		#Enqueue all available account
		for acc in self.config.RESOURCES:			
			proc_res.put(acc)

		for i in range(self.config.MAX_PROC):
			proc = CrawlerProcess(i, self.config.DOWNLOAD_FOLDER, proc_res, self.FOUND_APP, self.config.DICTIONARY[i], max_thread=self.config.MAX_THREAD_PER_PROC, proc_type=crawler_type)
			self.PROC_LIST.append(proc)

		print("Playstore crawler ready to run")
		

	def startCrawler(self):
		for i in range(self.config.MAX_PROC):
			self.PROC_LIST[i].start()
		print("Process started")
		for i in range(self.config.MAX_PROC):
			self.PROC_LIST[i].join()


