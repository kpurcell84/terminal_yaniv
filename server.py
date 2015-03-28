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

    def __init__(self):
        self.players = self.getPlayers()
        self.driver()

    def getPlayers(self):
        players = []
      
        host = '' 
        port = 50000 
        backlog = 5
        
        server = jsocket.JsonServer(port=port)
        # wait for a single player
        print "Waiting for players..."
        while 1: 
            server.accept_connection()
            name_data = server.read_obj()
            if name_data:
                print name_data['name'] + " has joined" 
                player = {}
                player['name'] = name_data['name']
                player['score'] = 0
                player['hand'] = []
                player['ai'] = False
                player['server'] = server
                players.append(player)
                # respond to client with name
                time.sleep(1)
                server.send_obj(name_data)
                break

        # hardcoded ai players
        for i in range(1,4):
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

    # insert card into player's hand and re-sort hand
    def insertCard(self, pid, card):
        self.players[pid]['hand'].insert(0, card)
        self.players[pid]['hand'].sort(key=lambda tup: tup[2], reverse=True)

    def humanTurn(self, pid):
        server = self.players[pid]['server']

        # send pre turn data to client
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[pid]['hand']
        pre_turn_data['discard_top'] = self.deck.discards[0]
        pre_turn_data['gameover'] = False
        pre_turn_data['roundover'] = False
        print "pre_turn_data:"
        print pre_turn_data
        print ""
        server.send_obj(pre_turn_data)

        # wait for client to make a decision
        post_turn_data = server.read_obj()
        print "post_turn_data:"
        print post_turn_data
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

        # send client back new hand
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[pid]['hand']
        pre_turn_data['discard_top'] = self.deck.discards[0]
        pre_turn_data['gameover'] = False
        pre_turn_data['roundover'] = False
        server.send_obj(pre_turn_data)

        time.sleep(5)
        

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


