from atributos.happiness import *
from config_atrib import *
from clases.action import *
def getInvertirActions(state):
    """
     Devuelve la una lista con la cantida que puede invertir el jugador
    """
    actions = []
    # Calculamos el máximo de soldados que puede comprar
    max_inversion=int(state.players[state.current_player].economy//INVERTIR_PRC)
    if max_inversion<1:return None
    for i in range(1,max_inversion+1):
        action=RiskAction('Invertir', None, None,i)
        actions.append(action)
    return actions

def simulateInvertirAction(state, action):
    """Ejecuta la acción de invertir"""
    prev=state.players[state.current_player].economy
    state.players[state.current_player].economy-=round(INVERTIR_PRC*action.unidades,1)
    state.players[state.current_player].economy=round(state.players[state.current_player].economy,1)
    state.players[state.current_player].development+=round(INVERTIR_DEVP*action.unidades,1)
    state.players[state.current_player].development=round(state.players[state.current_player].development,1)
    
    #print(f"El jugador {state.current_player} tenia {prev} monedas y se ha hecho {action.unidades} Inversiones. Su nuevo desarrollo es de {state.players[state.current_player].development}. Le quedan {state.players[state.current_player].economy} monedas")
