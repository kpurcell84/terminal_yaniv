#!/usr/bin/env python

import time

def write(message):
	now = time.strftime("%a %m/%d/%Y %H:%M:%S") 
	log = open("yaniv.log", 'a')
	log.write("["+now+"] "+str(message)+"\n")
	log.flush()
	log.close()