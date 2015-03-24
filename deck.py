import random
import itertools

class Deck:
	def __init__(self):
		self.cards = []
		self.discards = []

		vals = 'A23456789TJQK'
		suits = 'cdhs'
		deck_tuple = tuple(''.join(card) for card in itertools.product(vals, suits))
		for c in deck_tuple:
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
			card = (c[0], c[1], sort_val)
			self.cards.append(card)

	def drawCards(self, num):
		# reshuffle case when draw pile is almost empty
		if num > len(self.cards):
			self.cards = self.discards
			self.discards = []

		hand = random.sample(self.cards, num)
		for card in hand:
			self.cards.remove(card)
		return hand

	def discardCards(self, dcards):
		for dcard in dcards:
			self.discards.append(dcard)


# deck = Deck()
# hand = deck.drawCards(5)
# print hand