#!/usr/bin/env python 

from render import RenderUI
import logger

import socket
import jsocket
import sys
import json

class Client:
    port = 0
    name = ""
    pid = 0
    ui = None
    client = None
    server_ip = ""

    def __init__(self):
        pass

    # optional command line args:
    #   ./client.py [server_ip] [port]
    def joinServer(self):
        # get server ip address
        while 1:
            if len(sys.argv) >= 2:
                server_ip = sys.argv[1]
            else:
                server_ip = raw_input("Enter the server IP address: ")
            try:
                socket.inet_aton(server_ip)
                self.server_ip = server_ip
                break
            except socket.error as msg:
                print "Enter a valid IP address\n" + str(msg)

        # get port number
        while 1:
            if len(sys.argv) >= 3:
                port = sys.argv[2]
            else:
                port = raw_input("Enter the server port: ")
            try:
                self.port = int(port)
                break
            except ValueError:
                print "Enter a valid port number"   

        # connect to server
        self.client = jsocket.JsonClient(port=self.port, address=self.server_ip)
        self.client.connect()

        # enter initials and join game on server
        while 1:
            self.name = raw_input("Enter your initials: ")
            while len(self.name) > 3 or len(self.name) == 0:
                print "Please enter 1-3 letters"
                self.name = raw_input("Enter your initials: ")

            self.client.send_obj({'name':self.name,'pid':0})
            name_data = self.client.read_obj()
            if name_data['name'] == self.name:
                print "Successfully joined"
                self.pid = name_data['pid']
                break
            elif name_data['name'] == "Repeat":
                print "Those initials are already in use"
            elif name_data['name'] == "Invalid":
                print "Invalid name, check with server admin"

        print "Waiting for other players..."
        game_data = self.client.read_obj()
        self.score_max = game_data['score_max']
        self.round_break = game_data['round_break']

    def playGame(self):
        self.ui = RenderUI(self.score_max, self.round_break)
        while 1:
            # receive updates from server
            update_data = self.client.read_obj()
            self.ui.renderUpdate(self.pid, update_data)
            
            if update_data['gameover']:
                break

            cur_pid = update_data['cur_pid']
            cur_name = update_data['players'][cur_pid]['name']
            if cur_name != self.name or update_data['yaniv']:
                # go back to look for another update if not your turn
                continue

            pre_turn_data = self.client.read_obj()
            
            self.ui.renderDiscards(pre_turn_data['last_discards'])
            discards = self.ui.chooseHand(pre_turn_data['hand'])
            # check if player called yaniv
            if not discards:
                 post_turn_data = {}
                 post_turn_data['yaniv'] = True
                 self.client.send_obj(post_turn_data)
            else:
                # remove discards from hand for display purposes
                for card in discards:
                    pre_turn_data['hand'].remove(card)
                self.ui.renderHand(pre_turn_data['hand'])

                pick_up_idx = self.ui.chooseDiscards(pre_turn_data['last_discards'])

                post_turn_data = {}
                post_turn_data['pick_up_idx'] = pick_up_idx
                post_turn_data['discards'] = discards
                post_turn_data['yaniv'] = False
                self.client.send_obj(post_turn_data)

        self.client.close()


if __name__=='__main__':
    client = Client()
    try:
        client.joinServer()
        client.playGame()
    except RuntimeError as error:
        client.ui.cleanUp()
        client.client.close()
        if error.message == "socket connection broken":
            print "Lost connection to server, player may have disconnected\n" + \
           "Check with server admin and attempt to rejoin"  
    except socket.error:
        client.ui.cleanUp()
        client.client.close()
        print "Lost connection to server, player may have disconnected\n" + \
               "Check with server admin and attempt to rejoin"
    except KeyboardInterrupt:
        client.ui.cleanUp()
        client.client.close()
        print "\nQuitting..."
    except:
        client.ui.cleanUp()
        client.client.close()