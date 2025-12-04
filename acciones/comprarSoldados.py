from risktools import *
from config_atrib import *
from clases.action import *

def getComprarSoldadosActions(state):
    """
     Devuelve la una lista con la cantidad de soldados que puede comprar el jugador
    """
    actions = []
    # Calculamos el máximo de soldados que puede comprar
    max_soldados=int(state.players[state.current_player].economy//SOLDADOS_PRC)
    if max_soldados<1:return None
    for i in range(1,max_soldados+1):
        action=RiskAction('Comprar_Soldados', None, None,i)
        actions.append(action)
    return actions

def simulateComprarSoldadosAction(state, action):
    """Compra los soldados"""
    prev=state.players[state.current_player].economy
    state.players[state.current_player].economy-=round(SOLDADOS_PRC*action.unidades,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    state.players[state.current_player].free_armies+=action.unidades
    #print(f"El jugador {state.current_player} tenia {prev} monedas y se han comprado {action.unidades} soldados. Le quedan {state.players[state.current_player].economy} monedas")
