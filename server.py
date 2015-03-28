#!/usr/bin/env python

from deck import Deck

import socket
import jsocket
import sys
import time
import json

class Game:
    score_max = 200
    deck = None
    yaniv = False
    yaniv_pid = -1
    s = None # socket
    size = 1024 # socket size

    def __init__(self):
        self.players = self.getPlayers()
        self.driver()

    def getPlayers(self):
        players = []
      
        host = '' 
        port = 50000 
        backlog = 5 
        
        # open socket
        try: 
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((host,port)) 
            self.s.listen(backlog) 
        except socket.error, (value,message): 
            if self.s: 
                self.s.close() 
            print "Could not open socket: " + message 
            sys.exit(1) 
        # wait for a single player
        print "Waiting for players..."
        while 1: 
            client, address = self.s.accept() 
            data = client.recv(self.size) 
            if data:
                print str(data) + " has joined" 
                player = {}
                player['name'] = str(data)
                player['score'] = 0
                player['hand'] = []
                player['ai'] = False
                player['client'] = client
                players.append(player)
                # respond to client
                time.sleep(1)
                client.send(data)
                break

        # # hardcoded ai players
        # for i in range(1,4):
        #     player = {}
        #     player['name'] = "Player " + str(i)
        #     player['score'] = 0
        #     player['hand'] = []
        #     player['ai'] = True
        #     players.append(player)
        return players

    def checkWin(self):
        for player in self.players:
            if player['score'] > self.score_max:
                return True
        return False

    # insert card into player's hand and re-sort hand
    def insertCard(self, pid, card):
        self.players[pid]['hand'].insert(0, card)
        self.players[pid]['hand'].sort(key=lambda tup: tup[2], reverse=True)

    def humanTurn(self, pid):
        client = self.players[pid]['client']

        # send pre turn data to client
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[pid]['hand']
        pre_turn_data['discard_top'] = self.deck.discards[0]
        pre_turn_data['gameover'] = False
        pre_turn_data['roundover'] = False
        print "pre_turn_data:"
        print pre_turn_data
        print ""
        client.send(json.dumps(pre_turn_data))

        # wait for client to make a decision
        post_turn_data = json.loads(client.recv(self.size))
        print "post_turn_data:"
        print post_turn_data
        print ""

        print "BEFORE HAND:"
        print self.players[pid]['hand']
        print ""

        # check if client called a valid yaniv
        if post_turn_data['yaniv']:
            self.yaniv = True
            return
 
        new_card = None
        # if chosen, draw card from deck
        if post_turn_data['deck_draw']:
            new_card = self.deck.drawCard()
        # else draw top discard card
        else:
            new_card = self.deck.drawDiscard()
        self.insertCard(pid, new_card)

        # get rid of client's discards
        self.deck.discardCards(post_turn_data['discards'])
        for discard in post_turn_data['discards']:
            self.players[pid]['hand'].remove(discard)


        print "AFTER HAND:"
        print self.players[pid]['hand']
        print ""

        # send client back new hand
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[pid]['hand']
        pre_turn_data['discard_top'] = self.deck.discards[0]
        pre_turn_data['gameover'] = False
        pre_turn_data['roundover'] = False
        client.send(json.dumps(pre_turn_data))
        

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
        self.insertCard(pid, new_card)

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
                    dealt_card = self.deck.drawCard()
                    self.insertCard(pid, dealt_card)
            print self.players
            print ""
            # break
            # round loop
            while 1:
                for pid,player in enumerate(self.players):
                    if player['ai']:
                        self.aiTurn(pid)
                    else:
                        self.humanTurn(pid)
                    if self.yaniv:
                        break
                print "players:"
                print self.players
                print ""
            break
            self.checkRoundScores()


if __name__=='__main__':
    Game()


