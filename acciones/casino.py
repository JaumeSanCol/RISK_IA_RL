from atributos.happiness import *
from config_atrib import *
from clases.action import *
import random
def getCasinoActions(state):
    """
     Devuelve las apuestas que puedes realizar (25%, 50%, 75%, 100%)
     Optimizada para no calcular porcentajes repetidos.
    """
    actions = []
    
    # Máximo que puedes gastar
    max_inversion = int(state.players[state.current_player].economy // CASINO_PRC)
    
    if max_inversion < 1:
        return None

    quarter = max_inversion // 4
    
    if quarter == 0:
        actions.append(RiskAction('Casino', None, None, max_inversion))
        
    else:
        amounts = [quarter, quarter * 2, quarter * 3, max_inversion]
        
        prev_val = 0
        for amount in amounts:
            if amount > prev_val: 
                actions.append(RiskAction('Casino', None, None, amount))
                prev_val = amount

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

