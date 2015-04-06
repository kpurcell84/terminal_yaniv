#!/usr/bin/env python 

from deck import Deck
import logger

# selects the appropriate decision based on AI skill level and
# returns post_turn_data object
def makeDecision(deck, players, pid):
    if players[pid]['ai'] == 1:
        return easyAi(deck, players, pid)
    # elif players[pid]['ai'] == 2:
    #     return mediumAi(deck, players, pid)
    # elif players[pid]['ai'] == 3:
    #     return hardAi(deck, players, pid)

def easyAi(deck, players, pid):
    logger.write("ai last discards")
    logger.write(deck.getLastDiscards())
    logger.write("ai hand")
    logger.write(players[pid]['hand'])

    # call yaniv if hand sum 5 or under
    hand_sum = 0
    yaniv = True
    for card in players[pid]['hand']:
        hand_sum += card[2]
        if hand_sum > 5:
            yaniv = False
            break
    if yaniv:
        post_turn_data = {'yaniv':True}
        return post_turn_data

    # look for largest set that isn't a future set
    prev_card_val = ""
    cur_set = []
    biggest_set = []
    pick_up_idx = 0
    last_dcards = deck.getLastDiscards()
    for cid,card in enumerate(players[pid]['hand']):
        if card[0] == prev_card_val:
            cur_set.append(card)
        if card[0] != prev_card_val or cid == len(players[pid]['hand'])-1:
            if len(cur_set) > len(biggest_set) and not future_set:
                biggest_set = cur_set[:]
            cur_set = []
            cur_set.append(card)
        # check for future set
        future_set = False
        for did,last_dcard in enumerate(last_dcards):
            if last_dcard[0] == card[0][0]:
                future_set = True
                pick_up_idx = did+1
                break

        prev_card_val = card[0]
    # edge case for 1 set left, put down set and pick up discard if < 5
    if not biggest_set:
        biggest_set = cur_set[:]
        pick_up_idx = 0
        for did,last_dcard in enumerate(last_dcards):
            if last_dcard[2] <= 5:
                pick_up_idx = did+1
                break

    # always pick up card if <= 2
    elif pick_up_idx == 0:
        for did,last_dcard in enumerate(last_dcards):
            if last_dcard[2] <= 2:
                pick_up_idx = did+1
                break

    post_turn_data = {'yaniv':False, 'discards':biggest_set, 'pick_up_idx':pick_up_idx}

    logger.write("ai discards")
    logger.write(biggest_set)
    logger.write("ai pick_up_idx:" + str(pick_up_idx))

    return post_turn_data

def mediumAi(deck, players, pid):
    pass

def hardAi(deck, players, pid):
    pass