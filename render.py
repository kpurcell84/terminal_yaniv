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
	top_margin = 1
	card_height = 7
	card_width = 9
	stats_height = 3
	stats_width = 40
	message_height = 4
	message_width = 40
	pcards = []
	stdscr = None
	hand = None
	# windows
	stats_win = None
	discard_win = None
	hand_win = None
	select_win = None
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
		self.stats_win = curses.newwin(self.stats_height, self.stats_width, self.top_margin, self.left_margin)

		discard_begin_x = self.left_margin
		discard_begin_y = self.stats_win.getbegyx()[0] + self.stats_height + 1
		self.discard_win = curses.newwin(self.card_height, (self.card_width+1)*6, discard_begin_y, discard_begin_x)

		hand_begin_x = self.left_margin
		hand_begin_y = self.discard_win.getbegyx()[0] + self.card_height + 1
		self.hand_win = curses.newwin(self.card_height, (self.card_width+1)*5, hand_begin_y, hand_begin_x)

		select_begin_x = self.left_margin
		select_begin_y = self.hand_win.getbegyx()[0] + self.card_height
		self.select_win = curses.newwin(1, (self.card_width+1)*5, select_begin_y, select_begin_x)

		message_begin_x = self.left_margin
		message_begin_y = self.select_win.getbegyx()[0] + 2
		self.message_win = curses.newwin(self.message_height, self.message_width, message_begin_y, message_begin_x)

		self.stats_win.bkgd(' ', curses.color_pair(1))
		self.discard_win.bkgd(' ', curses.color_pair(1))
		self.hand_win.bkgd(' ', curses.color_pair(1))
		self.select_win.bkgd(' ', curses.color_pair(1))
		self.message_win.bkgd(' ', curses.color_pair(1))

		# self.stats_win.box()
		# self.discard_win.box()
		# self.hand_win.box()
		# self.select_win.box()
		# self.message_win.box()

		# self.stats_win.refresh()
		# self.discard_win.refresh()
		# self.hand_win.refresh()
		# self.select_win.refresh()
		# self.message_win.refresh()

		# time.sleep(5)

	def _nextCard(self):
		# unbold cur_card
		self._displayCard(self.pcards[self.cur_card], False)

		self.cur_card += 1
		if self.cur_card >= len(self.pcards):
			self.cur_card = 0
		self._displayCard(self.pcards[self.cur_card], True)

	def _prevCard(self):
		# unbold cur_card
		self._displayCard(self.pcards[self.cur_card], False)

		self.cur_card -= 1
		if self.cur_card < 0:
			self.cur_card = len(self.pcards)-1
		self._displayCard(self.pcards[self.cur_card], True)

	def _displaySelected(self, display):
		x_coord = self.card_width/2 + self.cur_card*self.card_width
		if display:
			self.select_win.addch(0, x_coord, 'X')
		else:
			self.select_win.addch(0, x_coord, ' ')
		self.select_win.refresh()

	def _displayCards(self, cards, is_hand):
		self._eraseCards(is_hand)
		if not is_hand and cards[0][0] != "D":
				# insert face down deck card for display purposes
				cards.insert(0, ["D", "D", 0])

		self.cur_card = 0
		self.pcards = []
		for i,card in enumerate(cards):
			pcard = {}
			if card[0] == 'T':
				pcard['val'] = "10"
			else:
				pcard['val'] = card[0]
			pcard['suit'] = card[1]
			if is_hand:
				pcard['window'] = self.hand_win.derwin(self.card_height, self.card_width, 0, i*self.card_width)
			else:
				pcard['window'] = self.discard_win.derwin(self.card_height, self.card_width, 0, i*self.card_width)
			# pcard['window'].bkgd(' ', curses.color_pair(1))
			pcard['selected'] = False
			self.pcards.append(pcard)

		for pcard in self.pcards:
			self._displayCard(pcard, False)

	def _displayCard(self, pcard, bold):
		win = pcard['window']
		# face down deck card
		if pcard['suit'] == "D":
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
		elif pcard['suit'] == "d":
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
		elif pcard['suit'] == "h":
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
		elif pcard['suit'] == "c":
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
		elif pcard['suit'] == "s":
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
		if pcard['suit'] != "D":
			if bold:
				win.addstr(1,1, pcard['val'], curses.A_UNDERLINE)
				win.addstr(5,6, pcard['val'], curses.A_UNDERLINE)
			else:
				win.addstr(1,1, pcard['val'])
				win.addstr(5,6, pcard['val'])

		win.box()
		win.refresh()

	def _eraseCards(self, is_hand):
		if is_hand:
			self.hand_win.erase()
			self.select_win.erase()
			self.hand_win.refresh()
			self.select_win.refresh()
		else:
			self.discard_win.erase()
			self.discard_win.refresh()
		
	def renderUpdate(self, update_data):
		self.renderDiscards(update_data['last_discards'])

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
	# else (player is selecting discard to pick up)
	#	returns cur_card
	def _chooseCardsHelper(self, stdscr, cards, is_hand):
		self._displayCards(cards, is_hand)
		# Set first card to bold
		self._displayCard(self.pcards[self.cur_card], True)
		
		while 1:
			c = stdscr.getch()
			if c == ord('q'):
				sys.exit(0)
			elif c == curses.KEY_RIGHT:
				self._nextCard()
			elif c == curses.KEY_LEFT:
				self._prevCard()
			elif c == 32 and is_hand: # space key
				if self.pcards[self.cur_card]['selected']:
					self.pcards[self.cur_card]['selected'] = False
					self._displaySelected(False)
				else:
					self.pcards[self.cur_card]['selected'] = True
					self._displaySelected(True)
			elif c == 10: # enter key
				if is_hand:
					selected_cards = []
					selected_val = ""
					valid = True
					# add cids of selected cards to a list
					for cid,pcard in enumerate(self.pcards):
						if pcard['selected']:
							selected_cards.append(cards[cid])
							# check to make sure they're all the same value
							if selected_val == "":
								selected_val = pcard['val']
							elif pcard['val'] != selected_val:
								valid = False
								break
					if valid and selected_cards:
						self._eraseCards(is_hand)
						return selected_cards
					else:
						# TODO display error message
						continue
				# case for when player is selecting discard
				else:
					self._eraseCards(is_hand)
					return self.cur_card