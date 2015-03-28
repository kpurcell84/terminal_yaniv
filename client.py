#!/usr/bin/env python 

from render import RenderUI

import socket 
import sys
import json

host = 'localhost' 
port = 50000 
size = 1024 
server = None
try: 
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.connect((host,port)) 
except socket.error, (value,message): 
    if server: 
        server.close() 
    print "Could not open socket: " + message 
    sys.exit(1)

name = raw_input("Enter your name: ")
server.send(name)
data = server.recv(size)
if data == name:
	print "Successfully joined"

ui = RenderUI()
while 1:
	pre_turn_data = json.loads(server.recv(size))
	# check if round/game ended
	if pre_turn_data['roundover']:
		# TODO display end of round stats
		if pre_turn_data['gameover']:
			break
	
	print "pre_turn_data['hand']:"
	print pre_turn_data['hand']
	print ""
	discards = ui.chooseCards(pre_turn_data['hand'])
	print "discards:"
	print discards
	print ""

	post_turn_data = {}
	post_turn_data['discards'] = discards
	post_turn_data['deck_draw'] = True
	post_turn_data['yaniv'] = False
	server.send(json.dumps(post_turn_data))

