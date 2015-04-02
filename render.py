#!/usr/bin/env python

import logger

import curses
import time
import sys

## start curse app
# stdscr = curses.initscr()
# curses.noecho()
# curses.cbreak()
# stdscr.keypad(1)


## end curse app
# curses.nocbreak()
# stdscr.keypad(0)
# curses.echo()
# curses.curs_set(1)
# curses.endwin()

class RenderUI:
	cur_card = 0
	left_margin = 5
	top_margin = 0
	card_height = 7
	card_width = 9
	stats_height = 6
	stats_width = 50
	message_height = 4
	message_width = 50
	rcards = []
	stdscr = None
	hand = None
	suits = {'d':"Diamonds", 'h':"Hearts", 's':"Spades", 'c':"Clubs"}
	# windows
	stats_outer_win = None
	stats_win = None
	discard_win = None
	hand_win = None
	select_win1 = None
	select_win2 = None
	message_win = None
	
	def __init__(self):
		return curses.wrapper(self.__init__helper)

	def __init__helper(self, stdscr):
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
		stdscr.bkgd(' ', curses.color_pair(1))
		stdscr.clear()
		curses.curs_set(0)
		stdscr.refresh()
		self.stdscr = stdscr

		# build windows from top down
		self.stats_outer_win = curses.newwin(self.stats_height, self.stats_width, self.top_margin, self.left_margin)
		self.stats_outer_win.box()
		self.stats_outer_win.bkgd(' ', curses.color_pair(1))
		self.stats_outer_win.addstr(1, 1, "Name  |")
		self.stats_outer_win.addstr(2, 1, "Cards |")
		self.stats_outer_win.addstr(3, 1, "Points|")
		self.stats_outer_win.addstr(4, 1, "Turn  |")
		self.stats_outer_win.refresh()

		self.stats_win = self.stats_outer_win.derwin(self.stats_height-2, self.stats_width-11, 1, 9)

		discard_begin_x = self.left_margin
		discard_begin_y = self.stats_outer_win.getbegyx()[0] + self.stats_height
		self.discard_win = curses.newwin(self.card_height, (self.card_width+1)*6, discard_begin_y, discard_begin_x)

		select1_begin_x = self.left_margin
		select1_begin_y = self.discard_win.getbegyx()[0] + self.card_height
		self.select_win1 = curses.newwin(1, (self.card_width+1)*5, select1_begin_y, select1_begin_x)

		hand_begin_x = self.left_margin
		hand_begin_y = self.select_win1.getbegyx()[0] + 1
		self.hand_win = curses.newwin(self.card_height, (self.card_width+1)*5, hand_begin_y, hand_begin_x)

		select2_begin_x = self.left_margin
		select2_begin_y = self.hand_win.getbegyx()[0] + self.card_height
		self.select_win2 = curses.newwin(1, (self.card_width+1)*5, select2_begin_y, select2_begin_x)

		message_begin_x = self.left_margin
		message_begin_y = self.select_win2.getbegyx()[0] + 1
		self.message_win = curses.newwin(self.message_height, self.message_width, message_begin_y, message_begin_x)

		self.stats_win.bkgd(' ', curses.color_pair(1))
		self.discard_win.bkgd(' ', curses.color_pair(1))
		self.select_win1.bkgd(' ', curses.color_pair(1))
		self.hand_win.bkgd(' ', curses.color_pair(1))
		self.select_win2.bkgd(' ', curses.color_pair(1))
		self.message_win.bkgd(' ', curses.color_pair(1))

		# self.stats_win.box()
		# self.discard_win.box()
		# self.select_win1.box()
		# self.hand_win.box()
		# self.select_win2.box()
		# self.message_win.box()

		# self.stats_win.refresh()
		# self.discard_win.refresh()
		# self.select_win1.box()
		# self.hand_win.refresh()
		# self.select_win2.refresh()
		# self.message_win.refresh()

		# time.sleep(5)

	def _nextCard(self, is_hand):
		# unbold cur_card
		self._displayCard(self.rcards[self.cur_card], False)
		if not is_hand:
			self._displaySelected(False, is_hand)

		self.cur_card += 1
		if self.cur_card >= len(self.rcards):
			self.cur_card = 0
		self._displayCard(self.rcards[self.cur_card], True)
		if not is_hand:
			self._displaySelected(True, is_hand)

	def _prevCard(self, is_hand):
		# unbold cur_card
		self._displayCard(self.rcards[self.cur_card], False)
		if not is_hand:
			self._displaySelected(False, is_hand)

		self.cur_card -= 1
		if self.cur_card < 0:
			self.cur_card = len(self.rcards)-1
		self._displayCard(self.rcards[self.cur_card], True)
		if not is_hand:
			self._displaySelected(True, is_hand)

	def _displaySelected(self, display, is_hand):
		x_coord = self.card_width/2 + self.cur_card*self.card_width
		if display:
			if is_hand:
				self.select_win2.addch(0, x_coord, 'X')
				self.select_win2.refresh()
			else:
				self.select_win1.addch(0, x_coord, '*')
				self.select_win1.refresh()
		else:
			if is_hand:
				self.select_win2.addch(0, x_coord, ' ')
				self.select_win2.refresh()
			else:
				self.select_win1.addch(0, x_coord, ' ')
				self.select_win1.refresh()
		

	def _displayCards(self, cards, is_hand):
		self._eraseCards(is_hand)
		if not is_hand and cards[0][0] != "D":
			# insert face down deck card for display purposes
			cards.insert(0, ["D", "D", 0])

		self.cur_card = 0
		self.rcards = []
		for i,card in enumerate(cards):
			rcard = {}
			if card[0] == 'T':
				rcard['val'] = "10"
			else:
				rcard['val'] = card[0]
			rcard['suit'] = card[1]
			if is_hand:
				rcard['window'] = self.hand_win.derwin(self.card_height, self.card_width, 0, i*self.card_width)
			else:
				rcard['window'] = self.discard_win.derwin(self.card_height, self.card_width, 0, i*self.card_width)
			rcard['selected'] = False
			self.rcards.append(rcard)

		for rcard in self.rcards:
			self._displayCard(rcard, False)

	def _displayCard(self, rcard, bold):
		win = rcard['window']
		# face down deck card
		if rcard['suit'] == "D":
			if bold:
				win.addstr(1,1,"*******", curses.A_BOLD)
				win.addstr(2,1,"*******", curses.A_BOLD)
				win.addstr(3,1,"*******", curses.A_BOLD)
				win.addstr(4,1,"*******", curses.A_BOLD)
				win.addstr(5,1,"*******", curses.A_BOLD)
				win.addstr(6,1,"*******", curses.A_BOLD)
			else:
				win.addstr(1,1,"*******")
				win.addstr(2,1,"*******")
				win.addstr(3,1,"*******")
				win.addstr(4,1,"*******")
				win.addstr(5,1,"*******")
				win.addstr(6,1,"*******")
		# diamonds
		elif rcard['suit'] == "d":
			if bold:
				win.addstr(1,1,"   /\\", curses.A_BOLD)
				win.addstr(2,1,"  /  \\", curses.A_BOLD)
				win.addstr(3,1,"  \  /", curses.A_BOLD)
				win.addstr(4,1,"   \/", curses.A_BOLD)
			else:
				win.addstr(1,1,"   /\\")
				win.addstr(2,1,"  /  \\")
				win.addstr(3,1,"  \  /")
				win.addstr(4,1,"   \/")
		# hearts
		elif rcard['suit'] == "h":
			if bold:
				win.addstr(1,1,"  _  _", curses.A_BOLD)
				win.addstr(2,1," ( \/ )", curses.A_BOLD)
				win.addstr(3,1,"  \  /", curses.A_BOLD)
				win.addstr(4,1,"   \/", curses.A_BOLD)
			else:
				win.addstr(1,1,"  _  _")
				win.addstr(2,1," ( \/ )")
				win.addstr(3,1,"  \  /")
				win.addstr(4,1,"   \/")
		# clubs
		elif rcard['suit'] == "c":
			if bold:
				win.addstr(1,1,"   _", curses.A_BOLD)
				win.addstr(2,1,"  ( )", curses.A_BOLD)
				win.addstr(3,1," (_._)", curses.A_BOLD)
				win.addstr(4,1,"   |", curses.A_BOLD)
			else:
				win.addstr(1,1,"   _")
				win.addstr(2,1,"  ( )")
				win.addstr(3,1," (_._)")
				win.addstr(4,1,"   |")
		# spades
		elif rcard['suit'] == "s":
			if bold:
				win.addstr(1,1,"   .", curses.A_BOLD)
				win.addstr(2,1,"  / \\", curses.A_BOLD)
				win.addstr(3,1," (_._)", curses.A_BOLD)
				win.addstr(4,1,"   |", curses.A_BOLD)
			else:
				win.addstr(1,1,"   .")
				win.addstr(2,1,"  / \\")
				win.addstr(3,1," (_._)")
				win.addstr(4,1,"   |")
		# insert values into corners if not a face down deck card
		if rcard['suit'] != "D":
			if bold:
				win.addstr(1,1, rcard['val'], curses.A_UNDERLINE)
				win.addstr(5,6, rcard['val'], curses.A_UNDERLINE)
			else:
				win.addstr(1,1, rcard['val'])
				win.addstr(5,6, rcard['val'])

		win.box()
		win.refresh()

	def _displayStats(self, players, cur_pid):
		logger.write(cur_pid)
		logger.write(players)

		self.stats_win.erase()

		for pid,player in enumerate(players):
			self.stats_win.addstr(0, pid*5, str(player['name']))
			self.stats_win.addstr(1, pid*5, str(len(player['hand'])))
			self.stats_win.addstr(2, pid*5, str(player['score']))
		self.stats_win.addstr(3, cur_pid*5, "#")

		self.stats_win.refresh()

	def _eraseCards(self, is_hand):
		if is_hand:
			self.hand_win.erase()
			self.hand_win.refresh()
			self.select_win2.erase()
			self.select_win2.refresh()
		else:
			self.discard_win.erase()
			self.discard_win.refresh()
			self.select_win1.erase()
			self.select_win1.refresh()
	
	# message that's rendered for every player's turn
	def _displayTurnMessage(self, update_data):
		message = ""
		cur_pid = update_data['cur_pid']
		cur_name = update_data['players'][cur_pid]['name']
		if update_data['last_pick_up'] != None:
			last_pid = cur_pid - 1
			if last_pid < 0:
				last_pid = len(update_data['players']) - 1
			last_name = update_data['players'][last_pid]['name']
			# render messsages about what's happening
			message += last_name + " put down the "
			for card in update_data['last_discards']:
				# skip deck card
				if card[0] == "D":
					continue
				message += "[" + card[0] + " of " + self.suits[card[1]] + "], "
			# remove last comma and space
			message = message[:-2]
			message += "\n"
			if update_data['last_pick_up'][0] == "D":
				message += "and picked up a card from the deck"
			else:
				message += "and picked up the [" + update_data['last_pick_up'][0] + " of " + self.suits[update_data['last_pick_up'][1]] + "]"
			message += "\n\n"

		message += cur_name + "'s turn..."

		self.renderMessage(message)

	def _checkValidYaniv(self, hand):
		return True

	def renderMessage(self, message):
		self.message_win.erase()
		self.message_win.addstr(0, 0, str(message))
		self.message_win.refresh()

	def renderUpdate(self, update_data):
		self._displayStats(update_data['players'], update_data['cur_pid'])
		self.renderDiscards(update_data['last_discards'])
		self._displayTurnMessage(update_data)

	def renderDiscards(self, cards):
		self._displayCards(cards, False)

	def renderHand(self, hand):
		self._displayCards(hand, True)

	def chooseHand(self, cards):
		return curses.wrapper(self._chooseCardsHelper, cards, True)

	def chooseDiscards(self, cards):
		return curses.wrapper(self._chooseCardsHelper, cards, False)

	# if is_hand == True (player is selecting cards to put down)
	# 	returns list of selected cards
	#	if player calls yaniv:
	#		returns empty list
	# else (player is selecting discard to pick up)
	#	returns cur_card
	def _chooseCardsHelper(self, stdscr, cards, is_hand):
		self._displayCards(cards, is_hand)
		# Set first card to bold
		self._displayCard(self.rcards[self.cur_card], True)
		if not is_hand:
			self._displaySelected(True, is_hand)
		
		while 1:
			c = stdscr.getch()
			if c == ord('q'):
				sys.exit(0)
			elif c == curses.KEY_RIGHT:
				self._nextCard(is_hand)
			elif c == curses.KEY_LEFT:
				self._prevCard(is_hand)
			elif c == 32 and is_hand: # space key
				if self.rcards[self.cur_card]['selected']:
					self.rcards[self.cur_card]['selected'] = False
					self._displaySelected(False, is_hand)
				else:
					self.rcards[self.cur_card]['selected'] = True
					self._displaySelected(True, is_hand)
			elif c == 10: # enter key
				if is_hand:
					selected_cards = []
					selected_val = ""
					valid = True
					# add cids of selected cards to a list
					for cid,rcard in enumerate(self.rcards):
						if rcard['selected']:
							selected_cards.append(cards[cid])
							# check to make sure they're all the same value
							if selected_val == "":
								selected_val = rcard['val']
							elif rcard['val'] != selected_val:
								valid = False
								break
					if valid and selected_cards:
						self._eraseCards(is_hand)
						return selected_cards
					else:
						# do nothing, player did not select valid cards
						continue
				# case for when player is selecting discard
				else:
					self._eraseCards(is_hand)
					return self.cur_card
			# player called yaniv
			elif c == ord('y'):
				if self._checkValidYaniv(cards):
					return []
