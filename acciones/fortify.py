from atributos.happiness import *
from clases.action import *

def getFortifyActions(state):
    """
     Returns a list of all the Fortify actions possible in this state
     An action is to move troops from one territory to a neighboring territory (both owned by current_player), leaving at least 1 troop in the from_territory
    """
    actions = []
    
    for i in range(len(state.owners)):
        if state.owners[i] == state.current_player and state.armies[i] >= 2:
            from_territory = state.board.territories[i].name
            for n in state.board.territories[i].neighbors:
                if state.owners[n] == state.current_player:
                    to_territory = state.board.territories[n].name
                    for k in range(1, state.armies[i]):
                        a = RiskAction('Fortify', to_territory, from_territory, k)
                        actions.append(a)
                        
    no_action = RiskAction('Fortify', None, None, 0)
    actions.append(no_action)
    
    return actions    
    
def simulateFortifyAction(state, action):
    """
    Execute the given action in the given state.  This will modify the state to 
    reflect the outcome of the state.
    """
    if action.to_territory is None:
        return
        
    to_idx = state.board.territory_to_id[action.to_territory]
    from_idx = state.board.territory_to_id[action.from_territory]
    
    #Make sure that the fortify action is correctly constructed
    if state.armies[from_idx] - action.unidades < 1 or state.owners[from_idx] != state.current_player or state.owners[to_idx] != state.current_player or to_idx not in state.board.territories[from_idx].neighbors:
        #This move is invalid
        print('INVALID FORTIFY ACTION: ')
        action.print_action()
        print('NO FORTIFY ACTION WILL BE TAKEN')
        return 
        
    state.armies[to_idx] = state.armies[to_idx] + action.unidades
    state.armies[from_idx] = state.armies[from_idx] - action.unidades