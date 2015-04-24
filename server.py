#!/usr/bin/env python

from deck import Deck
import ai
import logger
import jsocket

import socket
import os
import fcntl
import struct
import sys
import time
import json
import pickle
from copy import deepcopy

class Server:
    server = None
    host_ip = "127.0.0.1"
    port = 50005
    num_humans = 1
    num_ai = 7
    ai_level = 1
    ai_think_secs = 3
    round_break = 30
    score_max = 200

    deck = None
    yaniv = False
    yaniv_pid = 0
    winner_pid = 0
    players = []
    last_pick_up = None
    lucky_draw = False

    cur_pid = 0
    round_count = 0
    turn_count = 0

    saved_game = False
    resuming_game = False

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

    # checks if the card the player just picked up from the deck can be placed
    # down again immediately and if so, inserts the card into the discards
    def _isLuckyDraw(self, discards, new_card):
        # determine if it's a set or a straight
        is_set = True
        prev_card = []
        for discard in discards:
            if prev_card and discard[0] != prev_card[0]:
                is_set = False
            prev_card = discard

        if is_set:
            if discards[0][0] == new_card[0]:
                discards.append(new_card)
                return True
            else:
                return False
        # is a straight
        else:
            # check if same suit
            if new_card[1] != discards[0][1]:
                return False
            # check if card comes before discards
            if new_card[2] == discards[0][2]-1:
                discards.insert(0, new_card)
                return True
            # check if card comes after discards
            if new_card[2] == discards[len(discards)-1][2]+1:
                discards.append(new_card)
                return True

            return False

    # moves the cards from hand and draws discards after a turn
    def _endTurn(self, pid, post_turn_data):
        if post_turn_data['yaniv']:
            self.yaniv = True
            self.yaniv_pid = pid
            return
        
        # if chosen, draw card from deck
        self.lucky_draw = False
        if post_turn_data['pick_up_idx'] == 0:
            new_card = self.deck.drawCard()
            # check for lucky draw
            self.lucky_draw = self._isLuckyDraw(post_turn_data['discards'], new_card)
            if self.lucky_draw:
                self.last_pick_up = new_card
            else:
                self.last_pick_up = ["D", "D", 0]
        # else draw top discard card
        else:
            new_card = self.deck.drawDiscard(post_turn_data['pick_up_idx'])
            self.last_pick_up = new_card

        logger.write("Player discards:\n"+self._cardsString(post_turn_data['discards']))
        logger.write("Player picks up:\n"+new_card[0]+new_card[1])

        if not self.lucky_draw:
            self._insertCard(pid, new_card)

        # get rid of client's discards
        self.deck.discardCards(post_turn_data['discards'])
        for discard in post_turn_data['discards']:
            if self.players[pid]['hand'].count(discard): 
                self.players[pid]['hand'].remove(discard)

    def _humanTurn(self):
        # send pre turn data to client
        pre_turn_data = {}
        pre_turn_data['hand'] = self.players[self.cur_pid]['hand']
        pre_turn_data['last_discards'] = self.deck.getLastDiscards()

        logger.write("Last discards:\n"+self._cardsString(pre_turn_data['last_discards']))
        logger.write("Pre-turn hand:\n"+self._cardsString(pre_turn_data['hand']))

        self.server.conn = self.players[self.cur_pid]['conn']
        self.server.send_obj(pre_turn_data)

        # wait for client to make a decision
        post_turn_data = self.server.read_obj()

        self._endTurn(self.cur_pid, post_turn_data)
        
    def _aiTurn(self):
        # thinking.....
        time.sleep(self.ai_think_secs)

        logger.write("Last discards:\n"+self._cardsString(self.deck.getLastDiscards()))
        logger.write("Pre-turn hand:\n"+self._cardsString(self.players[self.cur_pid]['hand']))

        post_turn_data = ai.makeDecision(self.deck, self.players, self.cur_pid)

        self._endTurn(self.cur_pid, post_turn_data)

    # update all the human players as to what's going on
    def _sendUpdate(self, yaniv=False, gameover=False, hand_sums=None):
        update_data = {}
        update_data['yaniv'] = yaniv
        update_data['gameover'] = gameover
        update_data['hand_sums'] = hand_sums
        update_data['lucky_draw'] = self.lucky_draw
        update_data['last_pick_up'] = self.last_pick_up
        update_data['cur_pid'] = self.cur_pid
        # make a deep copy and remove connection info before serializing
        players_copy = deepcopy(self.players)
        for player in players_copy:
            player.pop('conn', None)
            
        update_data['players'] = players_copy
        update_data['last_discards'] = self.deck.getLastDiscards()
        # send out updates to everyone
        for player in self.players:
            if not player['ai']:
                self.server.conn = player['conn']
                self.server.send_obj(update_data)

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
        # remove winner if tied and called yaniv
        if len(winners) > 1 and winners.count(self.yaniv_pid) == 1:
            winners.remove(self.yaniv_pid)
        self.winner_pid = winners[0]

        # add points
        for pid,player in enumerate(self.players):
            # check if player won and don't add any points
            if winners.count(pid) == 1:
                player['yaniv_count'] += 1
                continue
            # player called yaniv and lost
            if pid == self.yaniv_pid:
                player['score'] += 30

            player['score'] += hand_sums[pid]
            # check for halving
            if player['score'] % 50 == 0:
                player['score'] /= 2

        self._sendUpdate(yaniv=True, hand_sums=hand_sums)
        time.sleep(self.round_break)

    # for logging/debugging purposes
    def _playersString(self):
        string = ""
        for player in self.players:
            string += str(player['pid'])+" "+player['name']+" | score:"+\
                      str(player['score'])+" yaniv_count:"+\
                      str(player['yaniv_count'])+" ai:"+str(player['ai'])+"\n"
            string += "\tHand:"
            for card in player['hand']:
                string += " "+card[0]+card[1]
            string += "\n"
        return string

     # for logging/debugging purposes
    def _cardsString(self, cards):
        string = ""
        for card in cards:
            string += card[0]+card[1]+" "
        return string

    def _saveGame(self):
        # save the variables to vars.data file
        var_dic = {}
        var_dic['num_humans'] = self.num_humans
        var_dic['num_ai'] = self.num_ai
        var_dic['ai_level'] = self.ai_level
        var_dic['ai_think_secs'] = self.ai_think_secs
        var_dic['round_break'] = self.round_break
        var_dic['score_max'] = self.score_max
        var_dic['last_pick_up'] = self.last_pick_up
        var_dic['lucky_draw'] = self.lucky_draw
        var_dic['round_count'] = self.round_count
        var_dic['turn_count'] = self.turn_count
        next_pid = self.cur_pid + 1
        if next_pid >= len(self.players):
            next_pid = 0
        var_dic['cur_pid'] = next_pid

        pickle.dump(var_dic, open("game_data/vars.data", "wb"))

        # save the player data to players.data file
        # make a deep copy and remove connection info before saving
        players_copy = deepcopy(self.players)
        for player in players_copy:
            player.pop('conn', None)
        pickle.dump(players_copy, open("game_data/players.data", "wb"))

        # save the deck to deck.data file
        deck_dic = {}
        deck_dic['cards'] = self.deck.cards
        deck_dic['discards'] = self.deck.discards
        deck_dic['last_discard_num'] = self.deck.last_discard_num

        pickle.dump(deck_dic, open("game_data/deck.data", "wb"))

    def _loadGame(self):
        # load variables
        var_dic = pickle.load(open("game_data/vars.data", "rb"))

        self.num_humans = var_dic['num_humans']
        self.num_ai = var_dic['num_ai']
        self.ai_level = var_dic['ai_level']
        self.ai_think_secs = var_dic['ai_think_secs']
        self.round_break = var_dic['round_break']
        self.score_max = var_dic['score_max']
        self.last_pick_up = var_dic['last_pick_up']
        self.lucky_draw = var_dic['lucky_draw']
        self.round_count = var_dic['round_count']
        self.turn_count = var_dic['turn_count']
        self.winner_pid = var_dic['cur_pid']

        # load players
        self.players = pickle.load(open("game_data/players.data", "rb"))

        # load deck
        deck_dic = pickle.load(open("game_data/deck.data", "rb"))

        self.deck = Deck(len(self.players))
        self.deck.cards = deck_dic['cards']
        self.deck.discards = deck_dic['discards']
        self.deck.last_discard_num = deck_dic['last_discard_num']

    def configureServer(self, autoload=False):
        # read properly formatted lines in config file into a dic
        try:
            config = {}
            with open("server.config", "r") as config_read: 
                for option in config_read:
                    option = option.rstrip('\n')
                    option = option.split()
                    if len(option) == 3 and option[1] == '=':
                        config[option[0]] = option[2]     
        except IOError:
            print "Could not open server.config, make sure it exists"
            sys.exit(1)

        # config variable parsing
        if 'port' in config:
            try:
                port = int(config['port'])
                if port > 0 and port < 65535:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        # port is open
                       self.port = port
            except ValueError:
                pass
        if 'host_ip' in config:
            try:
                self.host_ip = config['host_ip']
                self.server = jsocket.JsonServer(port=self.port, address=self.host_ip)
            except:
                print "host_ip not valid"
                sys.exit(1)
        else:
            try:
                self.host_ip = self._get_ip("wlan0")
                self.server = jsocket.JsonServer(port=self.port, address=self.host_ip)
            except:
                print "Please enter a host_ip in the server.config file"
                sys.exit(1)
        if 'num_humans' in config:
            try:
                num_humans = int(config['num_humans'])
                if num_humans >= 0 and num_humans <= 8:
                    self.num_humans = num_humans
            except ValueError:
                pass
        if 'num_ai' in config:
            try:
                num_ai = int(config['num_ai'])
                if num_ai >= 0 and num_ai+self.num_humans <= 8:
                    self.num_ai = num_ai
            except ValueError:
                pass
        if 'ai_level' in config:
            try:
                ai_level = int(config['ai_level'])
                if ai_level > 0 and ai_level <= 3:
                    self.ai_level = ai_level
            except ValueError:
                pass
        if 'ai_think_secs' in config:
            try:
                ai_think_secs = int(config['ai_think_secs'])
                if ai_think_secs >= 0:
                    self.ai_think_secs = ai_think_secs
            except ValueError:
                pass
        if 'round_break' in config:
            try:
                round_break = int(config['round_break'])
                if round_break > 0:
                    self.round_break = round_break
            except ValueError:
                pass
        if 'score_max' in config:
            try:
                score_max = int(config['score_max'])
                if score_max > 0:
                    self.score_max = score_max
            except ValueError:
                pass

        self.saved_game = True
        try:
            open("game_data/vars.data", "r")
            open("game_data/players.data", "r")
            open("game_data/deck.data", "r")
        except IOError:
            self.saved_game = False
        if self.saved_game:
            if not autoload:
                answer = raw_input("Would you like to continue your saved game from %s? (Y/n) " % time.ctime(os.path.getmtime("game_data/vars.data")))
            else:
                answer = "Y"
            if answer == "Y" or answer == "y":
                print "Loading saved game..."
                self._loadGame()
                self.resuming_game = True
                logger.write("Resuming game from %s" % time.ctime(os.path.getmtime("game_data/vars.data")))
            else:
                self.saved_game = False

        
        config_str = "Config options:\n"
        config_str += "\thost_ip = " + self.host_ip + "\n"\
                      "\tport = " + str(self.port) + "\n"\
                      "\tnum_humans = " + str(self.num_humans) + "\n"\
                      "\tnum_ai = " + str(self.num_ai) + "\n"\
                      "\tai_level = " + str(self.ai_level) + "\n"\
                      "\tai_think_secs = " + str(self.ai_think_secs) + "\n"\
                      "\tround_break = " + str(self.round_break) + "\n"\
                      "\tscore_max = " + str(self.score_max) + "\n"
        print config_str
        print "Hosting server on " + self.host_ip + ":" + str(self.port)

        logger.write(config_str)

    def getPlayers(self):
        if not self.saved_game:
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
                logger.write(name_data['name'] + " has joined")

                player = {}
                player['pid'] = humans_joined
                player['name'] = name_data['name']
                player['score'] = 0
                player['yaniv_count'] = 0
                player['hand'] = []
                player['ai'] = 0
                player['conn'] = self.server.conn
                self.players.append(player)
                name_data['pid'] = player['pid']
                # respond to client with name
                self.server.send_obj(name_data)
                humans_joined += 1

            # fill in rest of spots with ai players
            for i in range(self.num_humans, self.num_humans+self.num_ai):
                player = {}
                player['pid'] = i
                player['name'] = "ai" + str(i)
                player['score'] = 0
                player['yaniv_count'] = 0
                player['hand'] = []
                player['ai'] = self.ai_level
                self.players.append(player)

        # game was saved
        else: 
            humans_str = ""
            for player in self.players:
                if not player['ai']:
                    humans_str += player['name'] + " "
            print "Waiting for players: " + humans_str + "\n..."

            humans_joined = 0
            while humans_joined < self.num_humans: 
                self.server.accept_connection()
                player_pid = -1
                while 1:
                    name_data = self.server.read_obj()
                    name_valid = False
                    for pid,player in enumerate(self.players):
                        if player['name'] == name_data['name']:
                            name_valid = True
                            player_pid = pid
                            break
                    if name_valid:
                        break
                    else:
                        print "Incorrect player name attemped to join"
                        self.server.send_obj({'name':"Invalid"})

                print name_data['name'] + " has joined"
                logger.write(name_data['name'] + " has joined")

                self.players[player_pid]['conn'] = self.server.conn

                self.server.send_obj(name_data)
                humans_joined += 1

        # send game initialization data to clients
        game_data = {'score_max':self.score_max,'round_break':self.round_break}
        for player in self.players:
            if not player['ai']:
                self.server.conn = player['conn']
                self.server.send_obj(game_data)

    def driver(self):
        # game loop
        while self._checkWin() == False:
            if not self.resuming_game:
                self.round_count += 1
                logger.write("Start of round "+str(self.round_count))
                # reset the deck
                self.deck = Deck(len(self.players))
                # deal cards to players
                for pid,player in enumerate(self.players):
                    # reset player hand
                    player['hand'] = []
                    # if player['ai']:
                    for i in range(5):
                        dealt_card = self.deck.drawCard()
                        self._insertCard(pid, dealt_card)
                    # else: # FOR TESTING
                        # dealt_card = self.deck.drawSpecificCard(["2", "d", 2])
                        # self._insertCard(pid, dealt_card)
                        # dealt_card = self.deck.drawSpecificCard(["3", "d", 3])
                        # self._insertCard(pid, dealt_card)
                        # dealt_card = self.deck.drawSpecificCard(["4", "d", 4])
                        # self._insertCard(pid, dealt_card)
                        # dealt_card = self.deck.drawSpecificCard(["5", "d", 5])
                        # self._insertCard(pid, dealt_card)
                        # dealt_card = self.deck.drawSpecificCard(["6", "d", 6])
                        # self._insertCard(pid, dealt_card)
                logger.write("Initial players:\n"+self._playersString())
                
                # round loop
                self.yaniv = False
                self.turn_count = 0

            first_turn = True
            while 1:
                self.resuming_game = False
                for self.cur_pid,player in enumerate(self.players):
                    if first_turn and self.cur_pid != self.winner_pid:
                        continue
                    else:
                        first_turn = False
                    self.turn_count += 1
                    logger.write(player['name']+"'s turn")
                    # automatic yaniv call for empty hand
                    if len(player['hand']) == 0:
                        self.yaniv = True
                        self.yaniv_pid = self.cur_pid
                        break

                    self._sendUpdate()
                    
                    if player['ai']:
                        self._aiTurn()
                    else:
                        self._humanTurn()

                    logger.write("Players after turn "+str(self.turn_count)+"\n"+ self._playersString())
                    if self.yaniv:
                        break
                    self._saveGame()
                if self.yaniv:    
                    break
            self._addRoundScores()

        self._sendUpdate(gameover=True)
        # clean up data files
        os.remove("game_data/vars.data")
        os.remove("game_data/players.data")
        os.remove("game_data/deck.data")
        self.server.close()

if __name__=='__main__':
    autoload = False
    while 1:
        server = Server()
        server.configureServer(autoload=autoload)
        server.getPlayers()
        try:
            server.driver()
        except RuntimeError as error:
            if error.message == "socket connection broken":
                print "Player has disconnected, relaunching server..."
                server.server.close()
                autoload = True
