#!/usr/bin/env python 

from deck import Deck
import logger

# selects the appropriate decision based on AI skill level and
# returns card picked up or None for yaniv
def makeDecision(deck, players, pid):
    if players[pid]['ai'] == 1:
        return easyAi(deck, players, pid)
    # elif players[pid]['ai'] == 2:
    #     return mediumAi(deck, players, pid)
    # elif players[pid]['ai'] == 3:
    #     return hardAi(deck, players, pid)

# returns card picked up or None for yaniv
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
        return None

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

    # decide whether to pick up from deck or pick up discard
    if pick_up_idx == 0:
        new_card = deck.drawCard()
        return_card = ["D", "D", 0]
    else:
        new_card = deck.drawDiscard(pick_up_idx)
        return_card = new_card

    # discard highest cards with most sets (that aren't a future set)
    for card in biggest_set:
        players[pid]['hand'].remove(card)
    deck.discardCards(biggest_set)

    # insert new card and sort hand
    players[pid]['hand'].insert(0, new_card)
    players[pid]['hand'].sort(key=lambda tup: tup[2], reverse=True)

    logger.write("ai discards")
    logger.write(biggest_set)
    logger.write("ai new card")
    logger.write(new_card)

    return return_card

def mediumAi(deck, players, pid):
    pass

def hardAi(deck, players, pid):
    pass