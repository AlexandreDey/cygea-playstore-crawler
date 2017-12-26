#!/bin/python

import CygeaPlayStoreCrawler as cpc	

DOWNLOAD=10
SEARCH_ONLY=11

# Spawn a crawler that will download application
crawler = cpc.PlaystoreCrawler("conf", SEARCH_ONLY)

# The same thing but the crawler will only search for app without downloading
# crawler = cpc.PlaystoreCrawler("conf", SEARCH_ONLY)

# Start the crawling process
crawler.startCrawler()
