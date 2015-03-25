from cards import RenderCards
from deck import Deck

class Game:
	score_max = 200
	deck = None
	yaniv = False
	yaniv_pid = -1

	def __init__(self):
		self.players = self.getPlayers()
		self.driver()

	def getPlayers(self):
		players = []
		# hardcoded human player
		player = {}
		player['name'] = "Smeagol"
		player['score'] = 0
		player['hand'] = []
		player['ai'] = False
		players.append(player)
		# hardcoded ai players
		for i in range(2,5):
			player = {}
			player['name'] = "Player " + str(i)
			player['score'] = 0
			player['hand'] = []
			player['ai'] = True
			players.append(player)
		return players

	def checkWin(self):
		for player in self.players:
			if player['score'] > self.score_max:
				return True
		return False

	def sortHand(self, pid):
		self.players[pid]['hand'].sort(key=lambda tup: tup[2], reverse=True)

	def humanTurn(self, pid):
		ui = RenderCards()
		# wait for player to choose cards
		selected_cards = ui.chooseCards(self.players[pid]['hand'])
		# remove cards from hand and discard 
		dcards = []
		for card in selected_cards:
			self.players[pid]['hand'].remove(card)
			dcards.append(card)
		self.deck.discardCards(dcards)

		ui = RenderCards()
		ui.displayHand(self.players[pid]['hand'])


	# extremely basic ai which discards highest card and picks
	# up from the deck
	def aiTurn(self, pid):
		# discard highest card
		dcards = []
		high_card = self.players[pid]['hand'].pop(0)
		dcards.append(high_card)
		self.deck.discardCards(dcards)

		# pick up from deck
		new_card = self.deck.drawCard()
		self.players[pid]['hand'].append(new_card)
		self.sortHand(pid)

	def checkRoundScores(self):
		pass


	def driver(self):
		# game loop
		while self.checkWin() == False:
			# reset the deck
			self.deck = Deck()
			# deal cards to players
			for pid,player in enumerate(self.players):
				for i in range(5):
					player['hand'].append(self.deck.drawCard())
				self.sortHand(pid)
			print self.players
			# break
			# round loop
			i = 0
			while 1:
				for pid,player in enumerate(self.players):
					if player['ai']:
						self.aiTurn(pid)
					else:
						self.humanTurn(pid)
					if self.yaniv:
						break
				if i >= 5:
					break
				i += 1
				print self.players
			break
			self.checkRoundScores()


if __name__=='__main__':
    Game()


