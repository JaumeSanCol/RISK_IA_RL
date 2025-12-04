"""This file helps match ai's based upon 
TurboRisk ai's to work in this game
"""


import gui.riskengine as riskengine
import gui.riskgui as riskgui

def run_preplace(player):
    """Runs when the player is supposed to select 
    and support his first territory
    """
    riskengine.logai("run_preplace")
    freeplaces = [x for x in riskengine.territories.values() if x.armies == 0]
    if freeplaces:
        terr = player.ai.Assignment(player)
        if terr is not None and terr.armies == 0:
            player.place_army(terr)
            riskgui.drawterritory(terr, 0)
        else:
            riskengine.logai("AI " + player.name + " couldn't place armies, gave up")
            

    else:
        terr = player.ai.Placement(player)
        if terr is not None:  
            player.place_army(terr)
            riskgui.drawterritory(terr, 0)
        else:
            riskengine.logai("AI" + player.name + "couldn't place armies, gave up")

def run_place(player):
    """Place a player's units at the beginning of the turn"""
    #See if the AI wants to turn in cards
    
    for i in range(player.freeArmies):
        terr = player.ai.Placement(player)
        if terr is not None:
            player.place_army(terr)
            riskgui.drawterritory(terr, 0)

def run_attack(player):
    """Have a player run his attacks, and then his fortification"""
    riskengine.logai("run_attack")
    while 1:
        fromterr, toterr = player.ai.Attack(player)
            
        if fromterr is None or toterr is None or fromterr.armies <= 1:
            break
        riskengine.logai("AI %s attacks %s with %s" % 
                            (player.name, toterr.name, fromterr.name))
        riskengine.attack(fromterr, toterr)
        riskgui.drawterritory(fromterr, 0)
        riskgui.drawterritory(toterr, 0)
        
        if toterr.player == player: #we won
            movarm = player.ai.Occupation(player, fromterr, toterr)
            if movarm <= 0:
                continue
            movarm = min(movarm, fromterr.armies - 1)
            fromterr.armies -= movarm
            toterr.armies += movarm
            riskgui.drawterritory(fromterr, 0)
            riskgui.drawterritory(toterr, 0)
    
    fromterr, toterr, armies = player.ai.Fortification(player)
    if fromterr is not None and toterr is not None and armies > 0:
        armies = min(armies, fromterr.armies - 1)
        fromterr.armies -= armies
        toterr.armies += armies
        riskgui.drawterritory(fromterr, 0)
        riskgui.drawterritory(toterr, 0)

def saveddata():
    return ""

def loaddata(indata):
    pass