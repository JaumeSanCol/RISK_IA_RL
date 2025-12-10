from atributos.happiness import *
from config_atrib import *
from clases.action import *
def getInvertirActions(state):
    """
     Devuelve las opciones de inversión (25%, 50%, 75%, 100%)
    """
    actions = []
    
    # Calculamos la cantidad máxima que puede invertir
    max_inversion = int(state.players[state.current_player].economy // INVERTIR_PRC)
    
    if max_inversion < 1:
        return None

    quarter = max_inversion // 4
    
    if quarter == 0:
        actions.append(RiskAction('Invertir', None, None, max_inversion))
        
    else:
        amounts = [quarter, quarter * 2, quarter * 3, max_inversion]
        
        prev_val = 0
        for amount in amounts:
            if amount > prev_val:
                actions.append(RiskAction('Invertir', None, None, amount))
                prev_val = amount

    return actions

def simulateInvertirAction(state, action):
    """Ejecuta la acción de invertir"""
    prev=state.players[state.current_player].economy
    state.players[state.current_player].economy-=round(INVERTIR_PRC*action.unidades,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    state.players[state.current_player].development+=round(INVERTIR_DEVP*action.unidades,1)
    state.players[state.current_player].development=round(min(state.players[state.current_player].development,10.0),1)
    
    #print(f"El jugador {state.current_player} tenia {prev} monedas y se ha hecho {action.unidades} Inversiones. Su nuevo desarrollo es de {state.players[state.current_player].development}. Le quedan {state.players[state.current_player].economy} monedas")
