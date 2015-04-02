#!/usr/bin/env python

from deck import Deck
import logger

import socket
import jsocket
import sys
import time
import json
from copy import deepcopy

class Server:
    port = 0
    server = None

    score_max = 200
    deck = None
    yaniv = False
    yaniv_pid = -1
    players = []
    last_pick_up = None

    def __init__(self):
        pass

    def configureServer(self):
        host = '' 
        backlog = 5
        
        # get port number
        while 1:
            if len(sys.argv) == 2:
                port = sys.argv[1]
            else:
                port = raw_input("Enter an unused port to run the server on: ")
            try:
                self.port = int(port)
            except ValueError:
                print "Enter a valid port number"
                continue
            break

        self.server = jsocket.JsonServer(port=self.port)

    def getPlayers(self): 
        # wait for a single player
        print "Waiting for players..."
        while 1: 
            self.server.accept_connection()
            while 1:
                name_data = self.server.read_obj()
                name_valid = True
                for player in self.players:
                    if player['name'] == name_data['name']:
                        name_valid = False
                        break
                if name_valid:
                    break
                else:
                    print "Repeat name"
                    self.server.send_obj({'name':"Repeat"})

            print name_data['name'] + " has joined" 
            player = {}
            player['pid'] = 0
            player['name'] = name_data['name']
            player['score'] = 0
            player['hand'] = []
            player['ai'] = False
            player['server'] = self.server
            self.players.append(player)
            # respond to client with name
            time.sleep(1)
            self.server.send_obj(name_data)
            break

        # hardcoded ai players
        for i in range(1,4):
            player = {}
            player['pid'] = i
            player['name'] = "ai" + str(i)
            player['score'] = 0
            player['hand'] = []
            player['ai'] = True
            self.players.append(player)

        # send game initialization data over
        game_data = {'num_players':len(self.players)}
        for player in self.players:
            if not player['ai']:
                player['server'].send_obj(game_data)

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
        pre_turn_data['last_discards'] = self.deck.getLastDiscards()
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
        if post_turn_data['pick_up_idx'] == 0:
            new_card = self.deck.drawCard()
            self.last_pick_up = ["D", "D", 0]
        # else draw top discard card
        else:
            new_card = self.deck.drawDiscard(post_turn_data['pick_up_idx'])
            self.last_pick_up = new_card

        self.insertCard(pid, new_card)

        # get rid of client's discards
        self.deck.discardCards(post_turn_data['discards'])
        for discard in post_turn_data['discards']:
            self.players[pid]['hand'].remove(discard)

        # send client back new hand
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[pid]['hand']
        pre_turn_data['last_discards'] = self.deck.getLastDiscards()
        pre_turn_data['gameover'] = False
        pre_turn_data['roundover'] = False
        server.send_obj(pre_turn_data)
        

    # extremely basic ai which discards highest card and picks
    # up from the deck
    def aiTurn(self, pid):
        # thinking.....
        time.sleep(5)

        # discard highest card
        dcards = []
        high_card = self.players[pid]['hand'].pop(0)
        dcards.append(high_card)
        self.deck.discardCards(dcards)

        # pick up from deck
        new_card = self.deck.drawCard()
        self.insertCard(pid, new_card)

    # update all the human players as to what's going on
    def sendUpdate(self, pid):
        update_data = {}
        update_data['last_pick_up'] = self.last_pick_up
        update_data['cur_pid'] = pid
        # make a deep copy and remove connection info before serializing
        players_copy = deepcopy(self.players)
        for player in players_copy:
            player.pop('server', None)
            
        update_data['players'] = players_copy
        update_data['last_discards'] = self.deck.getLastDiscards()
        # send out updates to everyone
        for player in self.players:
            if not player['ai']:
                player['server'].send_obj(update_data)

    # add round scores to players totals
    def addRoundScores(self):
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
            logger.write(self.players)
            # break
            # round loop
            while 1:
                for pid,player in enumerate(self.players):
                    self.sendUpdate(pid)
                    
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
            self.addRoundScores()


if __name__=='__main__':
    server = Server()
    server.configureServer()
    server.getPlayers()
    logger.write("Players initialized")
    server.driver()
