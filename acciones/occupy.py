from atributos.happiness import *
from clases.action import *

def getOccupyActions(state):
    """
     Returns a list of all the Occupy actions possible in this state
     An action is to move an amount of troops into the newly conquered country (must leave at least 1 behind, and must move at least min(3,number_there -1))
    """
    actions = []
    
    if state.last_defender is None or state.last_attacker is None:
        return actions
    
    to_territory = state.board.territories[state.last_defender].name
    from_territory = state.board.territories[state.last_attacker].name
        
    for k in range(min(state.armies[state.last_attacker]-1,3), state.armies[state.last_attacker]):
        a = RiskAction('Occupy', to_territory, from_territory, k)
        actions.append(a)
        
    return actions
    
def simulateOccupyAction(state, action):    
    """
    Execute the given action in the given state.  This will modify the state to 
    reflect the outcome of the state.
    """
    to_idx = state.board.territory_to_id[action.to_territory]
    from_idx = state.board.territory_to_id[action.from_territory]
    #Make sure that the occupy action is correctly constructed
    if to_idx != state.last_defender or from_idx != state.last_attacker or state.armies[from_idx] - action.unidades < 1 or state.owners[from_idx] != state.current_player or state.owners[to_idx] != state.current_player:
        #This move is invalid
        print('INVALID OCCUPY ACTION: ')
        action.print_action()
        print('To index = ', to_idx)
        print('Last defender = ', state.last_defender)
        print('From index = ', from_idx)
        print('Last attacker = ', state.last_attacker)
        
        print('NO OCCUPY ACTION WILL BE TAKEN')
        return 

    state.armies[to_idx] = state.armies[to_idx] + action.unidades
    state.armies[from_idx] = state.armies[from_idx] - action.unidades
