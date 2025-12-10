from atributos.happiness import *
from config_atrib import *
from clases.action import *
def getFestinActions(state):
    """
     Devuelve las opciones de gasto en festines (25%, 50%, 75%, 100%)
    """
    actions = []
    
    max_inversion = int(state.players[state.current_player].economy // FESTIN_PRC)
    
    if max_inversion < 1:
        return None

    quarter = max_inversion // 4
    
    if quarter == 0:
        actions.append(RiskAction('Festin', None, None, max_inversion))
    
    else:
        amounts = [quarter, quarter * 2, quarter * 3, max_inversion]
        
        prev_val = 0
        for amount in amounts:
            if amount > prev_val:
                actions.append(RiskAction('Festin', None, None, amount))
                prev_val = amount

    return actions

def simulateFestinAction(state, action):
    """Ejecuta la acción de realizar festines"""
    prev=state.players[state.current_player].economy
    state.players[state.current_player].economy-=round(FESTIN_PRC*action.unidades,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    state.players[state.current_player].happiness+=int(FESTIN_HAPP*action.unidades)
    state.players[state.current_player].happiness=int(state.players[state.current_player].development)
  