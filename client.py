#!/usr/bin/env python 

from render import RenderUI
import logger

import socket
import jsocket
import sys
import json

port = 50000
num_players = 0

client = jsocket.JsonClient(port=50000)
client.connect()

name = raw_input("Enter your initials: ")
client.send_obj({'name':name})
name_data = client.read_obj()
if name_data['name'] == name:
	print "Successfully joined"
game_data = client.read_obj()
num_players = game_data['num_players']

ui = RenderUI()
while 1:
	# receive updates from server
	update_data = client.read_obj()
	ui.renderUpdate(update_data)
	if update_data['player']['name'] != name:
		continue

	pre_turn_data = client.read_obj()
	# check if round/game ended
	if pre_turn_data['roundover']:
		# TODO display end of round stats
		if pre_turn_data['gameover']:
			break
	
	ui.renderDiscards(pre_turn_data['last_discards'])
	discards = ui.chooseHand(pre_turn_data['hand'])
	ui.renderHand(pre_turn_data['hand'])
	cur_card = ui.chooseDiscards(pre_turn_data['last_discards'])

	post_turn_data = {}
	post_turn_data['pick_up_idx'] = cur_card
	post_turn_data['discards'] = discards
	post_turn_data['yaniv'] = False
	client.send_obj(post_turn_data)

	# receive updated data and display
	pre_turn_data = client.read_obj()
	ui.renderHand(pre_turn_data['hand'])
	ui.renderDiscards(pre_turn_data['last_discards'])
