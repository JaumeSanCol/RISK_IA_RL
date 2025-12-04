from atributos.happiness import *
from clases.action import *

def getPlaceActions(state):
    """
     Returns a list of all the Place actions possible in this state
     An action is to place a troop in a territory occupied by the current player
    """
    actions = []
    
    for i in range(len(state.owners)):
        if state.owners[i] == state.current_player:
            to_territory = state.board.territories[i].name
            a = RiskAction('Place', to_territory, None, None)
            actions.append(a)
            
    return actions

def simulatePlaceAction(state, action):
    """
    Execute the given action in the given state.  This will modify the state to 
    reflect the outcome of the state.
    """
    idx = state.board.territory_to_id[action.to_territory]
    if state.owners[idx] == state.current_player and state.players[state.current_player].free_armies >= 1:
        state.armies[idx] = state.armies[idx] + 1
        state.players[state.current_player].free_armies -= 1
        state.turn_type = "Occupy"
    else:
        print('INVALID PLACE ACTION: ')
        action.print_action()
        print('NO PLACE ACTION WILL OCCUR')

