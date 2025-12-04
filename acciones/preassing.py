from atributos.happiness import *
from clases.action import *

def getPreAssignActions(state):
    """Returns a list of all the PreAssign actions possible in this state"""
    
    #An Action is to select an unoccupied territory
    actions = []
    
    for i in range(len(state.owners)):
        if state.owners[i] is None:
            to_territory = state.board.territories[i].name
            a = RiskAction('PreAssign', to_territory, None, None)
            actions.append(a)
            
    return actions

def simulatePreAssignAction(state, action):
    """Execute the given action in the given state.  This will modify the state to 
    reflect the outcome of the state."""

    idx = state.board.territory_to_id[action.to_territory]
    
    if state.owners[idx] != None or state.armies[idx] != 0 or state.players[state.current_player].free_armies < 1:
        print('INVALID PREASSIGN ACTION!')
        
    state.owners[idx] = state.current_player
    state.armies[idx] = 1
    state.players[state.current_player].free_armies -= 1
