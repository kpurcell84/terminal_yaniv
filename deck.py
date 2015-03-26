#!/usr/bin/env python

import random
import itertools

class Deck:
	def __init__(self):
		self.cards = []
		self.discards = []

		vals = 'A23456789TJQK'
		suits = 'cdhs'

		# make the deck
		deck_list = []
		for val in vals:
			for suit in suits:
				card_list = []
				card_list.append(val)
				card_list.append(suit)
				deck_list.append(card_list)

		for c in deck_list:
			# give it a value for sorting
			sort_val = 0
			try:
				sort_val = int(c[0])
			except ValueError:
				if c[0] == 'A':
					sort_val = 1
				elif c[0] == 'T':
					sort_val = 10
				elif c[0] == 'J':
					sort_val = 11
				elif c[0] == 'Q':
					sort_val = 12
				elif c[0] == 'K':
					sort_val = 13
			card = [c[0], c[1], sort_val]
			self.cards.append(card)

		random.shuffle(self.cards)
		# add one card to discard pile
		self.discards.append(self.cards.pop())

	def drawCard(self):
		# reshuffle case when draw pile is empty
		if len(self.cards) == 0:
			last_discard = self.discards.pop(0)
			self.cards = self.discards
			self.discards = []
			self.discards.append(last_discard)
			random.shuffle(self.cards)

		card = self.cards.pop(0)
		return card

	def drawDiscard(self):
		card = self.discards.pop(0)
		return card

	def discardCards(self, dcards):
		for dcard in dcards:
			self.discards.insert(0, dcard)


# deck = Deck()
# hand = deck.drawCards(5)
# print hand