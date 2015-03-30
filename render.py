#!/usr/bin/env python

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
logger = open("render.log", 'a')

class RenderUI:
	cur_card = 0
	hand_begin_x = 5
	hand_begin_y = 14
	card_height = 7
	card_width = 9
	discard_begin_x = 5
	discard_begin_y = 5
	pcards = []
	select_win = None
	stdscr = None
	hand = None

	def __init__(self):
		pass

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
		logger.write(str(self.cur_card) + " " + str(x_coord) + "\n")
		if display:
			self.select_win.addch(0, x_coord, 'X')
		else:
			self.select_win.addch(0, x_coord, ' ')
		self.select_win.refresh()

	def _displayCards(self, cards, begin_y, begin_x):
		self.cur_card = 0
		self.pcards = []
		for i,card in enumerate(cards):
			pcard = {}
			if card[0] == 'T':
				pcard['val'] = "10"
			else:
				pcard['val'] = card[0]
			pcard['suit'] = card[1]
			pcard['window'] = curses.newwin(self.card_height, self.card_width, begin_y, begin_x+(i*self.card_width))
			pcard['window'].bkgd(' ', curses.color_pair(1))
			pcard['selected'] = False
			self.pcards.append(pcard)

		for pcard in self.pcards:
			self._displayCard(pcard, False)

	def _displayCard(self, pcard, bold):
		win = pcard['window']
		# diamonds
		if pcard['suit'] == "d":
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
		if bold:
			win.addstr(1,1, pcard['val'], curses.A_UNDERLINE)
			win.addstr(5,6, pcard['val'], curses.A_UNDERLINE)
		else:
			win.addstr(1,1, pcard['val'])
			win.addstr(5,6, pcard['val'])

		win.box()
		win.refresh()

	def _eraseCards(self):
		self.select_win.erase()
		self.select_win.refresh()
		for pcard in self.pcards:
			pcard['window'].erase()
			pcard['window'].refresh()

	def renderDiscards(self, cards):
		self._displayCards(cards, self.discard_begin_y, self.discard_begin_x)

	def renderHand(self, hand):
		self._displayCards(hand, self.hand_begin_y, self.hand_begin_x)

	def chooseHand(self, hand):
		return curses.wrapper(self._chooseHandHelper, hand)

	def _chooseHandHelper(self, stdscr, hand):
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
		stdscr.bkgd(' ', curses.color_pair(1))
		stdscr.clear()
		curses.curs_set(0)
		stdscr.refresh()
		self.stdscr = stdscr

		# build window beneath hand for card selection
		self.select_win = curses.newwin(1, (self.card_width+1)*5, self.hand_begin_y + self.card_height, self.hand_begin_x)
		self.select_win.bkgd(' ', curses.color_pair(1))

		self._displayCards(hand, self.hand_begin_y, self.hand_begin_x)
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
			elif c == 32: # space key
				if self.pcards[self.cur_card]['selected']:
					self.pcards[self.cur_card]['selected'] = False
					self._displaySelected(False)
				else:
					self.pcards[self.cur_card]['selected'] = True
					self._displaySelected(True)
			elif c == 10: # enter key
				selected_cards = []
				selected_val = ""
				valid = True
				# add cids of selected cards to a list
				for cid,pcard in enumerate(self.pcards):
					if pcard['selected']:
						selected_cards.append(hand[cid])
						# check to make sure they're all the same value
						if selected_val == "":
							selected_val = pcard['val']
						elif pcard['val'] != selected_val:
							valid = False
							break
				if valid and selected_cards:
					self._eraseCards()
					return selected_cards
				else:
					# TODO display error message
					continue
	
if __name__=='__main__':
    RenderCards()