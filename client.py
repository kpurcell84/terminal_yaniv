#!/usr/bin/env python 

from cards import RenderCards

import socket 
import sys
import json

host = 'localhost' 
port = 50000 
size = 1024 
s = None
try: 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((host,port)) 
except socket.error, (value,message): 
    if s: 
        s.close() 
    print "Could not open socket: " + message 
    sys.exit(1)
name = raw_input("Enter your name: ")
s.send(name)
data = s.recv(size)
if data == name:
	print "Successfully joined"

while 1:
	ui = RenderCards()
	pre_turn_data = json.loads(s.recv(size))
	# check if round/game ended
	if pre_turn_data['roundover']:
		# TODO display end of round stats
		if pre_turn_data['gameover']:
			break
	
	discards = ui.chooseCards(pre_turn_data['hand'])
	print "discards:"
	print discards

	post_turn_data = {}
	post_turn_data['discards'] = discards
	post_turn_data['deck_draw'] = True
	post_turn_data['yaniv'] = False
	s.send(json.dumps(post_turn_data))

