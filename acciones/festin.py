from atributos.happiness import *
from config_atrib import *
from clases.action import *
def getFestinActions(state):
    """
     Devuelve la una lista con la cantida que puede gastar el jugador en festines
    """
    actions = []
    # Calculamos el máximo de soldados que puede comprar
    max_inversion=int(state.players[state.current_player].economy//FESTIN_PRC)
    if max_inversion<1:return None
    for i in range(1,max_inversion+1):
        action=RiskAction('Festin', None, None,i)
        actions.append(action)
    return actions

def simulateFestinAction(state, action):
    """Ejecuta la acción de realizar festines"""
    prev=state.players[state.current_player].economy
    state.players[state.current_player].economy-=round(FESTIN_PRC*action.unidades,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    state.players[state.current_player].happiness+=int(FESTIN_HAPP*action.unidades)
    state.players[state.current_player].happiness=int(state.players[state.current_player].development)
  