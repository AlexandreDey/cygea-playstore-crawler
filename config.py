# separator used by search.py, categories.py, ...
#SEPARATOR = ";"

#LANG            = "fr_FR" # can be en_US, fr_FR, ...

#ANDROID_ID = ["3eded73a231f2845", "3c43890dbbe9f0b6", "317d8f22ba17fc04", "3092f78a95131d3c", "3fe977c60a14acea", "325846523c90edb9", "3642fa682aee1cf1", "3b4dfe0b1aa44443", "384731fe419126dc"]#, "34ad1a027d41326a", "3b128fac037b54ea", "325846523c90edb9"]
#GOOGLE_LOGIN = ["mariegruegrue@gmail.com", "mariamsable22@gmail.com", "thomenxxx@gmail.com", "comptepourdede53000@gmail.com", "cptprdey5300@gmail.com", "cptprdeydey5301@gmail.com", "comptefactice2@gmail.com","ad.dupond.123@gmail.com", "alexdup.53@gmail.com"] #, "titi07975@gmail.com", "guillaume.maxar.53@gmail.com", "jesuisgentiljeparticipe@gmail.com"]

#GOOGLE_PASSWORD = ["gruegrue","bakasable", "coucoucmoa", "tiptop00", "tititoto00", "tititoto00","factice1234", "motdepasse123", "motdepasse123"]#, "tititoto00", "fredvcuiop", "motdepassefacile"]

#PROXY_LIST = [{"http" : "41.187.15.198"}, {"http" : "203.129.195.178"}, {"http" : "113.255.49.49"}, {"http" : "152.160.35.171"}, {"http" : "60.194.100.51"}, {"http" : "161.202.30.245"}, {"http" : "49.159.86.227"},{"http" : "94.177.254.225"}, {"http" : "144.217.40.115"}, {"http" : "182.253.197.62"}]#, {"http" : "61.220.46.19"}, {"http" : "218.191.247.51"}]

#AUTH_TOKEN = ["QAT5ZCGamDRxyTnAjL2k-m1pqkSDhi70Aa9Y28Bg6q2xmS1bvHZrToYqJai9mWUsTwbdpA.", "QARIeUQmp1FGDZVWyh1G1AH2s58fCar5rDTJU6o-4quzPBIFP_DEda5Ff6tdtg4Q9fBmHg.", None, None, None, None, None, None, None]#, None, None, None]




class CrawlerConfig():
	def __init__(self, config_folder):
		self.CONF_FOLDER = config_folder
		self.MAX_PROC = 0
		self.MAX_THREAD_PER_PROC = 0
		self.DOWNLOAD_FOLDER = None
		self.BACKUP_FOLDER = None
		self.DICTIONARY = []
		self.RESOURCES = []
		self.ParseGeneralConfig()
		self.LoadDictionary()
		self.ParseResources()

	def ParseGeneralConfig(self):
		with open("%s/crawler.conf"%(self.CONF_FOLDER), "r") as f:
			lines = f.readlines()
			for line in lines:
				splitted_line = line.split(" = ")
				if "MAX_PROC" in splitted_line[0]:
					self.MAX_PROC = int(splitted_line[1])
				if "MAX_THREAD_PER_PROC" in splitted_line[0]:
					self.MAX_THREAD_PER_PROC = int(splitted_line[1])
				if "DOWNLOAD_FOLDER" in splitted_line[0]:
					self.DOWNLOAD_FOLDER = splitted_line[1]
				if "BACKUP_FOLDER" in splitted_line[0]:
					self.BACKUP_FOLDER = splitted_line[1]
	
	def LoadDictionary(self):
		nb_proc = self.MAX_PROC

		# Create an empty array for each process
		for i in range(nb_proc):
			self.DICTIONARY.append([])


		with open("%s/dict"%(self.CONF_FOLDER), "r") as f:
			dictionary = f.readlines()
			
			# Separate dictionary between process
			for i in range(len(dictionary)):
				self.DICTIONARY[i%nb_proc].append(dictionary[i])

	# Parse all the availables accounts (format: email,password,auth_token,android_id,proxy)
	def ParseResources(self):
		local_res = []
		with open("%s/accounts"%(self.CONF_FOLDER), "r") as f:
			accounts = f.readlines()
			for a in accounts:
				# CSV based file
				raw = a.split(",")
				
				parsed = [None]*5

				# Set email address (required)
				if not raw[0]:
					print("no email, next")
					continue
				parsed[0] = raw[0]

				# Set password (required)
				if not raw[1]:
					print("no password, next")
					continue
				parsed[1] = raw[1]

				# Set auth token (optional)
				if raw[2]:
					parsed[2] = raw[2]

				# Set android id (required)
				if not raw[3]:
					print("no android id, next")
					continue
				parsed[3] = raw[3]

				# Set proxy (optional)
				if raw[4]:
					parsed[4] = {"https" : "%s"%(raw[4])}

				self.RESOURCES.append(parsed)
			

	def ShowGeneralConfig(self):
		print("MAX_PROC = %d"%(self.MAX_PROC))
		print("MAX_THREAD_PER_PROC = %d"%(self.MAX_THREAD_PER_PROC))
		print("DOWNLOAD_FOLDER = %s"%(self.DOWNLOAD_FOLDER))
		print("BACKUP_FOLDER = %s"%(self.BACKUP_FOLDER))

	def ShowResources(self):
		for account in self.RESOURCES:
			print("")
			print("email = %s"%(account[0]))
			print("password = %s"%(account[1]))
			print("auth token = %s"%(account[2]))
			print("android id = %s"%(account[3]))
			print("proxy = %s"%(account[4]))



