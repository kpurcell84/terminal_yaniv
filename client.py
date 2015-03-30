#!/usr/bin/env python 

from render import RenderUI

import socket
import jsocket
import sys
import json

port = 50000 

client = jsocket.JsonClient(port=50000)
client.connect()

name = raw_input("Enter your name: ")
client.send_obj({'name':name})
name_data = client.read_obj()
if name_data['name'] == name:
	print "Successfully joined"

ui = RenderUI()
while 1:
	pre_turn_data = client.read_obj()
	# check if round/game ended
	if pre_turn_data['roundover']:
		# TODO display end of round stats
		if pre_turn_data['gameover']:
			break
	
	# print "pre_turn_data['hand']:"
	# print pre_turn_data['hand']
	# print ""
	ui.renderDiscards(pre_turn_data['last_discards'])
	discards = ui.chooseHand(pre_turn_data['hand'])
	# print "discards:"
	# print discards
	# print ""

	post_turn_data = {}
	post_turn_data['discards'] = discards
	post_turn_data['deck_draw'] = True
	post_turn_data['yaniv'] = False
	client.send_obj(post_turn_data)

	# receive updated data and display
	pre_turn_data = client.read_obj()
	ui.renderHand(pre_turn_data['hand'])
	ui.renderDiscards(pre_turn_data['last_discards'])
