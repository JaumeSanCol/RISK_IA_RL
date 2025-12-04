  
def getVecinos(state):
    """ Devuelve una lista con los id de los jugadores vecinos al jugador actual"""
    vecinos=[]
    for i in range(len(state.owners)):
        if state.owners[i] == state.current_player:
            for n in state.board.territories[i].neighbors:
                if state.owners[n] != state.current_player and state.owners[n] not in vecinos and state.owners[n] != None:
                    vecinos.append(state.owners[n])
    return vecinos

def tropas_enemigas_frontera(state):
    """ Devuelve un dicionario con los números de tropas que tiene cada jugador en la frontera que comparte con el jugador"""
    tropas_enemigas={}
    for i in range(len(state.owners)):
        if state.owners[i] == state.current_player:
            for n in state.board.territories[i].neighbors:
                if state.owners[n] != state.current_player :
                    owner=state.owners[n] 
                    if owner in tropas_enemigas and state.owners[n] != None:
                        tropas_enemigas[owner]+=state.armies[n]
                    else:
                        tropas_enemigas[owner]=state.armies[n]
    return tropas_enemigas

def tropas_aliadas_frontera(state):
    """ Devuelve el número de tropas que tiene el jugador en la frontera"""
    tropas_aliadas=0
    for i in range(len(state.owners)):
        if state.owners[i] == state.current_player:
            if not all(x == state.current_player for x in state.board.territories[i].neighbors):
                tropas_aliadas+=state.armies[i]
    return tropas_aliadas


def tropas_jugador(state,player):
    """ Devuelve el número de tropas total que tiene un jugador """
    tropas_totales=0
    for i in range(len(state.owners)):
        if state.owners[i] == player:
            tropas_totales+=state.armies[i]
    return tropas_totales


                    