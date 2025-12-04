from atributos.happiness import *
from config_atrib import *
from clases.action import *
import random
def getCasinoActions(state):
    """
     Devuelve las apuestas que puedes realizar
    """
    actions = []
    # Calculamos el máximo de soldados que puede comprar
    max_inversion=int(state.players[state.current_player].economy//CASINO_PRC)
    if max_inversion<1:return None
    for i in range(1,max_inversion+1):
        action=RiskAction('Casino', None, None,i)
        actions.append(action)
    return actions

def simulateCasinoAction(state, action):
    """Realiza las apuestas"""
    prev=state.players[state.current_player].economy
    state.players[state.current_player].economy-=round(INVERTIR_PRC*action.unidades,1)

    if random.random() > 0.48:
        state.players[state.current_player].economy+=round(INVERTIR_PRC*action.unidades,1)
    else:
        state.players[state.current_player].economy-=round(INVERTIR_PRC*action.unidades,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    
    #print(f"El jugador {state.current_player} tenia {prev} monedas y se ha hecho {action.unidades} Inversiones. Su nuevo desarrollo es de {state.players[state.current_player].development}. Le quedan {state.players[state.current_player].economy} monedas")
