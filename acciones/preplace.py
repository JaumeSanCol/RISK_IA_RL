from atributos.happiness import *
from clases.action import *

def getPrePlaceActions(state):
    """Returns a list of all the PrePlace actions possible in this state"""
    
    actions = []

    if state.players[state.current_player].free_armies <= 0:
        return actions # Devuelve una lista vacía
  
    for i in range(len(state.owners)):
        if state.owners[i] == state.current_player:
            to_territory = state.board.territories[i].name
            a = RiskAction('PrePlace', to_territory, None, None)
            actions.append(a)
            
    return actions

def simulatePrePlaceAction(state, action):
    """Execute the given action in the given state.  This will modify the state to 
    reflect the outcome of the state."""
    
    idx = state.board.territory_to_id[action.to_territory]
    if state.owners[idx] == state.current_player and state.players[state.current_player].free_armies > 0:
        state.armies[idx] = state.armies[idx] + 1
        state.players[state.current_player].free_armies -= 1
    else:
        print('INVALID PREPLACE ACTION:')
        print('NO PREPLACE ACTION WILL OCCUR')
