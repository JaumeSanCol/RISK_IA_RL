from atributos.dinero import *
def nextPlayer(state):
    """
    Moves the state's current_player to the next player in the order
    Also ensures that when it exits, the new state.current_player is still in the game
    Input: RiskState object
    """
    incrementPlayer(state)
    while state.players[state.current_player].game_over==True:
        incrementPlayer(state)
    
def incrementPlayer(state):
    """
    Increments the current_player of the input state
    Input: RiskState object
    """
    state.current_player = state.current_player + 1
    if state.current_player >= len(state.players):
        state.current_player = 0

def beginTurn(state):
    """
    Takes care of beginning-of-turn stuff
    Calculamos cuanto dinero debe recibir el jugador segun sus territorios, continentes y desarrollo.
    """
    #Update the player's money
    dinero=getMoney(state, state.current_player)
    if dinero>0:
        state.players[state.current_player].economy += getMoney(state, state.current_player)
    else:
        #print(f"El jugador {state.players[state.current_player].name} ha empezado el turno pero no tiene territorios")
        state.players[state.current_player].game_over=True
