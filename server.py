#!/usr/bin/env python

from deck import Deck
import ai
import logger

import socket
import jsocket
import fcntl
import struct
import sys
import time
import json
from copy import deepcopy

class Server:
    port = 0
    server = None
    host_ip = ""
    num_humans = 0
    ai_think_secs = 2

    score_max = 200
    deck = None
    yaniv = False
    yaniv_pid = -1
    players = []
    last_pick_up = None

    def __init__(self):
        pass

    def _get_ip(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    def _checkWin(self):
        for player in self.players:
            if player['score'] > self.score_max:
                return True
        return False

    # insert card into player's hand and re-sort hand
    def _insertCard(self, pid, card):
        self.players[pid]['hand'].insert(0, card)
        self.players[pid]['hand'].sort(key=lambda tup: tup[2], reverse=True)

    # moves the cards from hand and draws discards after a turn
    def _endTurn(self, pid, post_turn_data):
        if post_turn_data['yaniv']:
            self.yaniv = True
            self.yaniv_pid = pid
            return
        
        # if chosen, draw card from deck
        if post_turn_data['pick_up_idx'] == 0:
            new_card = self.deck.drawCard()
            self.last_pick_up = ["D", "D", 0]
        # else draw top discard card
        else:
            new_card = self.deck.drawDiscard(post_turn_data['pick_up_idx'])
            self.last_pick_up = new_card

        self._insertCard(pid, new_card)

        # get rid of client's discards
        self.deck.discardCards(post_turn_data['discards'])
        for discard in post_turn_data['discards']:
            self.players[pid]['hand'].remove(discard)

    def _humanTurn(self, pid):
        server = self.players[pid]['server']

        # send pre turn data to client
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[pid]['hand']
        pre_turn_data['last_discards'] = self.deck.getLastDiscards()
        print "pre_turn_data:"
        print pre_turn_data
        print ""
        server.send_obj(pre_turn_data)

        # wait for client to make a decision
        post_turn_data = server.read_obj()
        print "post_turn_data:"
        print post_turn_data
        print ""

        self._endTurn(pid, post_turn_data)

        # send client back new hand
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[pid]['hand']
        pre_turn_data['last_discards'] = self.deck.getLastDiscards()
        server.send_obj(pre_turn_data)
        
    def _aiTurn(self, pid):
        # thinking.....
        time.sleep(self.ai_think_secs)

        post_turn_data = ai.makeDecision(self.deck, self.players, pid)

        self._endTurn(pid, post_turn_data)

    # update all the human players as to what's going on
    def _sendUpdate(self, pid, yaniv=False, hand_sums=None):
        update_data = {}
        update_data['yaniv'] = yaniv
        update_data['hand_sums'] = hand_sums
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

    # check for a winner and add round scores to player's totals
    def _addRoundScores(self):
        winners = []
        hand_sums = []
        lowest_hand = 100
        for pid,player in enumerate(self.players):
            # sum up score of hand
            hand_sum = 0
            for card in player['hand']:
                point_val = card[2]
                # round down face cards
                if point_val > 10:
                    point_val = 10
                hand_sum += point_val
            
            if hand_sum < lowest_hand:
                lowest_hand = hand_sum
                winners = []
                winners.append(pid)
            elif hand_sum == lowest_hand:
                winners.append(pid)

            hand_sums.append(hand_sum)

        # add points
        for pid,player in enumerate(self.players):
            # check if player won and don't add any points
            if winners.count(pid) == 1:
                continue
            # player called yaniv and lost
            if pid == self.yaniv_pid:
                player['score'] += 30

            player['score'] += hand_sums[pid]
            # check for halving
            if player['score'] % 50 == 0:
                player['score'] /= 2

        self._sendUpdate(self.yaniv_pid, yaniv=True, hand_sums=hand_sums)

    # optional command line args:
    #   ./server.py [port] [num_humans]
    def configureServer(self):
        # get port number
        while 1:
            if len(sys.argv) >= 2:
                port = sys.argv[1]
            else:
                port = raw_input("Enter an unused port to run the server on: ")
            try:
                self.port = int(port)
                break
            except ValueError:
                print "Enter a valid port number"
        # get number of human players
        while 1:
            if len(sys.argv) >= 3:
                num_humans = sys.argv[2]
            else:
                num_humans = raw_input("How many human players would you like to play with: ")
            try:
                num_humans = int(num_humans)
                if num_humans < 1 or num_humans > 8:
                    print "Enter a valid number (1-8)"
                    continue
                else:
                    self.num_humans = num_humans
                    break
            except ValueError:
                print "Enter a valid number (1-8)"

        self.host_ip = self._get_ip("wlan0")
        self.server = jsocket.JsonServer(port=self.port, address=self.host_ip)
        print "Hosting server on " + self.host_ip + ":" + str(self.port)

    def getPlayers(self): 
        # wait for a single player
        print "Waiting for players..."
        humans_joined = 0
        while humans_joined < self.num_humans: 
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
            player['yaniv_count'] = 0
            player['hand'] = []
            player['ai'] = 0
            player['server'] = self.server
            self.players.append(player)
            # respond to client with name
            self.server.send_obj(name_data)
            humans_joined += 1

        # fill in rest of spots with hardcoded ai players
        for i in range(self.num_humans,8):
            player = {}
            player['pid'] = i
            player['name'] = "ai" + str(i)
            player['score'] = 0
            player['yaniv_count'] = 0
            player['hand'] = []
            player['ai'] = 1
            self.players.append(player)

        # send game initialization data over
        game_data = {'num_players':len(self.players)}
        for player in self.players:
            if not player['ai']:
                player['server'].send_obj(game_data)

    def driver(self):
        # game loop
        while self._checkWin() == False:
            # reset the deck
            self.deck = Deck()

            # deal cards to players
            for pid,player in enumerate(self.players):
                # reset player hand
                player['hand'] = []
                for i in range(5):
                    dealt_card = self.deck.drawCard()
                    self._insertCard(pid, dealt_card)
            logger.write(self.players)
            # break
            # round loop
            self.yaniv = False
            while 1:
                for pid,player in enumerate(self.players):
                    self._sendUpdate(pid)
                    
                    if player['ai']:
                        self._aiTurn(pid)
                    else:
                        self._humanTurn(pid)
                    
                    if self.yaniv:
                        break
                if self.yaniv:    
                    break
            self._addRoundScores()


if __name__=='__main__':
    server = Server()
    server.configureServer()
    server.getPlayers()
    logger.write("Players initialized")
    server.driver()
