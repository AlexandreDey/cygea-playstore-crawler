# cygea-playstore-crawler
This is a scalable Playstore Crawler used to massively download Android applications.
This was developed in order to study the malware present on the playstore


## Acknowledgment
Thanks to dflower (https://github.com/dflower/) for the first version of the backend API (unfortunately it had to be replaced because it was outdated)
Many thanks to NoMore201 for the actual backend API (https://github.com/NoMore201/googleplay-api)

## Setup

* You need Python 3 to run this code. It was only tested on Linux (manjaro and ubuntu)
* The needed modules are:
  * pycryptodome
  * clint
  * protobuf
  * requests

## Usage

* Create a config folder wherever you want
* In this folder create three files:
  * **accounts** where all the accounts will be put. Format:
    * email@gmail.com,password,authtoken(optional),android_device_id(optional),proxy_address(optional),
    * For optional values, just put nothing between the commas (ex: email@gmail.com,password,,,192.168.0.1, ) 
  * **dict** a dictionary of words (try to mix languages)
  * **crawler.conf** the general crawler config file:
    * MAX_PROC = N <- The number of process to run at the same time
    * MAX_THREAD_PER_PROC = N <- The number of thread per process
    * DOWNLOAD_FOLDER = ./tmp/ <- path to the download folder
    * BACKUP_FOLDER = ./backup/ <- path to the backup folder (still WIP)
* Create the download folder
* Test the Crawler:
```python

import CygeaPlayStoreCrawler as cpc	

DOWNLOAD=10
SEARCH_ONLY=11

"""Spawn a crawler that will download application"""
crawler = cpc.PlaystoreCrawler("conf", DOWNLOAD)

"""The same thing but the crawler will only search for app without downloading
crawler = cpc.PlaystoreCrawler("conf", SEARCH_ONLY)"""

"""Start the crawling process"""
crawler.startCrawler()
```

## TODO

* Write complete documentation
* Implement backup functionalities
* Clean the code (Backend API has been replaced, which created useless code)
* Implement synchronisation over network for multiple machine installation

