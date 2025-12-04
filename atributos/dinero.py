from config_atrib import *

def getMoney(state, player_id):
    """
    Determine how many troop reinforcements the indicated player should get in the given state.
    This is calculated from the number of territories and continents they occupy
    """
    #Count territories owned by the current player
    num_territorios = state.owners.count(player_id)
    #Calcular los valores en base a los territorios y los impuestos
    ingreso_por_territorio = round(num_territorios*IMPUESTOS,1)
    #See if they own all of any continents
    ingreso_por_continente = 0
    for c in iter(state.board.continents.values()):
        owned = True
        for t in c.territories:
            if state.owners[t] != player_id:
                owned = False
                break
        if owned:
            ingreso_por_continente = ingreso_por_continente + c.reward*10
    # Calculamos el ingreso por posesión como el dinero obtenido por los territorios individuales + el dinero obtenido por continente
    ingreso_por_posesion=ingreso_por_territorio+ingreso_por_continente
    # Calculamos el ingreso por desarrollo como un multiplicador del ingreso por posesión
    ingreso_por_desarrollo=ingreso_por_posesion*state.players[state.current_player].development

    # El total sera el ingreso por posesión + el desarrollo
    ingreso_total=ingreso_por_posesion+ingreso_por_desarrollo
    
    return round(ingreso_total, 1)