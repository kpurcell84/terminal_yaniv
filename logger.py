#!/usr/bin/env python

import time

logging = True

def write(message):
	if logging:
		now = time.strftime("%a %m/%d/%Y %H:%M:%S") 
		log = open("yaniv.log", 'a')
		log.write("["+now+"] "+str(message)+"\n\n")
		log.flush()
		log.close()