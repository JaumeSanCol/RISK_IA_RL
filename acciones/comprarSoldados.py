from risktools import *
from config_atrib import *
from clases.action import *

def getComprarSoldadosActions(state):
    """
     Devuelve las opciones de compra de soldados (25%, 50%, 75%, 100%)
    """
    actions = []
    
    # Calculamos el máximo de soldados que puede comprar
    max_soldados = int(state.players[state.current_player].economy // SOLDADOS_PRC)
    
    if max_soldados < 1:
        return None

    quarter = max_soldados // 4
    
    if quarter == 0:
        actions.append(RiskAction('Comprar_Soldados', None, None, max_soldados))
    
    else:
        amounts = [quarter, quarter * 2, quarter * 3, max_soldados]
        
        prev_val = 0
        for amount in amounts:
            if amount > prev_val:
                actions.append(RiskAction('Comprar_Soldados', None, None, amount))
                prev_val = amount

    return actions

def simulateComprarSoldadosAction(state, action):
    """Compra los soldados"""
    prev=state.players[state.current_player].economy
    state.players[state.current_player].economy-=round(SOLDADOS_PRC*action.unidades,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    state.players[state.current_player].free_armies+=action.unidades
    #print(f"El jugador {state.current_player} tenia {prev} monedas y se han comprado {action.unidades} soldados. Le quedan {state.players[state.current_player].economy} monedas")
