from atributos.happiness import *
from config_atrib import *
from clases.action import *
def getComercioActions(state):
    """
     Devuelve la acción de impulsar el comercio
    """
    return [RiskAction('Comercio', None, None,None)]

def simulateComercioAction(state, action):
    """Execute the given action in the given state.  This will modify the state to 
    reflect the outcome of the state."""
    state.players[state.current_player].economy+=round(COMERCIO_DEVP*state.players[state.current_player].development,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    
    #print(f"El jugador {state.current_player} tenia {prev} monedas y se ha hecho {action.unidades} Inversiones. Su nuevo desarrollo es de {state.players[state.current_player].development}. Le quedan {state.players[state.current_player].economy} monedas")
