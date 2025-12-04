
import random
from risktools import *
#For interacting with interactive GUI
from gui.aihelper import *
from gui.turbohelper import *
import itertools

### ATTACKER AI ####
# 
#  This AI always chooses to attack if it is possible
#  Complete description for all turn types: 
#    - PreAssign - Chooses territories randomly
#    - PrePlace, Place - Places troops on random territory that is bordering an opponent territory (a front)
#    - Occupy - Chooses random action
#    - Fortify - Chooses random action that moves troops to front
#  
#  This results in an AI that is very aggressive and fairly successful.  Not trivial to beat this agent a significant portion of the time


def getAction(state, time_left=None):
    """Main AI function.  It should return a valid AI action for this state."""
    
    #Get the possible actions in this state
    actions = getAllowedFaseActions(state)
        
    #Select a Random Action (to use for unspecified turn types)
    myaction = random.choice(list(itertools.chain.from_iterable(actions.values())))
    
    if 'Attack' in actions:
        myaction = actions['Attack'][0] #The final action in the list will be the "stop attacking" action, so this will always choose to attack if possible
    # Si puede comprar soldados los compra todos
    elif 'Comprar_Soldados' in actions:
        myaction = actions['Comprar_Soldados'][-1]
    else: 
        # Create a list of all actions that move troops to a territory bordering an opponent
        possible_actions = []
        if 'PreAssing' in actions:
            for a in actions["PreAssign"]:
                if a.to_territory is not None:
                    for n in state.board.territories[state.board.territory_to_id[a.to_territory]].neighbors:
                        if state.owners[n] != state.current_player:
                            possible_actions.append(a)
        if 'Preplace' in actions:
            for a in actions["Preplace"]:
                if a.to_territory is not None:
                    for n in state.board.territories[state.board.territory_to_id[a.to_territory]].neighbors:
                        if state.owners[n] != state.current_player:
                            possible_actions.append(a)
        else:
            for a in list(itertools.chain.from_iterable(actions.values())):
                if a.to_territory is not None:
                    for n in state.board.territories[state.board.territory_to_id[a.to_territory]].neighbors:
                        if state.owners[n] != state.current_player:
                            possible_actions.append(a)
                    
        #Randomly select one of these actions, if there were any
        if len(possible_actions) > 0:
            myaction = random.choice(possible_actions)

    #Return the chosen action
    return myaction

#Code below this is the interface with Risk.pyw GUI version
#DO NOT MODIFY
    
def aiWrapper(function_name, occupying=None):
    game_board = createRiskBoard()
    game_state = createRiskState(game_board, function_name, occupying)
    action = getAction(game_state)
    return translateAction(game_state, action)
            
def Assignment(player):
#Need to Return the name of the chosen territory
    return aiWrapper('Assignment')
     
def Placement(player):
#Need to return the name of the chosen territory
     return aiWrapper('Placement')

def ComprarSoldados(player):
 #Need to return the name of the attacking territory, then the name of the defender territory    
    return aiWrapper('Comprar_Soldados')
    
def Attack(player):
 #Need to return the name of the attacking territory, then the name of the defender territory    
    return aiWrapper('Attack')

def Occupation(player,t1,t2):
 #Need to return the number of armies moving into new territory      
    occupying = [t1.name,t2.name]
    return aiWrapper('Occupation',occupying)
   
def Fortification(player):
    return aiWrapper('Fortification')

  