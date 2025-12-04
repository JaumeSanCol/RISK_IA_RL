"""
This file contains the RISK simulator that consitutes the backbone of the RISK AI Assignment
"""
import gui.riskengine as riskengine
import random
import zipfile
import xml.dom.minidom
import math
import json
import sys

from config_atrib import *

from clases.action import RiskAction
from clases.board import RiskBoard
from clases.continent import RiskContinent
from clases.player import RiskPlayer
from clases.state import RiskState
from clases.territory import RiskTerritory

from acciones.attack import *
from acciones.fortify import *
from acciones.invertir import *
from acciones.comprarSoldados import *
from acciones.place import *
from acciones.preplace import *
from acciones.preassing import *
from acciones.occupy import *
from acciones.pasar import *
from acciones.casino import *
from acciones.festin import *
from acciones.comercio import *

from atributos.dinero import *
from turnos.turnos import *

# def pause():
#     """Utility if you ever want to pause to see output at some point. For debugging"""
#     i = raw_input('Paused. Press a key to continue . . . ')
    

# ------------------------------------------------------------------------------------------
# Turnos y Fases 
# ------------------------------------------------------------------------------------------


def simulateAction(input_state, action):
    """
    Returns a list of all possible future states that this action could lead to, along with the probability of each.  
    This function makes a copy of the input_state, so it is not modified
    Returns: [state0, state1, ....], [probability0, probability1]
    """
    
    rstates = []
    rsprobs = []
    
      
    if action.type == 'Attack':
        rstates,rsprobs = simulateAttack(input_state, action)
    else:
        s = input_state.copy_state()

        if action.type=="Pasar": pass
        elif action.type == 'PreAssign':
            simulatePreAssignAction(s, action)
        elif action.type == 'PrePlace':
            simulatePrePlaceAction(s, action)
        elif action.type == 'Comprar_Soldados':
            simulateComprarSoldadosAction(s, action)
        elif action.type == 'Place':
            simulatePlaceAction(s, action)
        elif action.type == 'Occupy':
            simulateOccupyAction(s, action)
        elif action.type == 'Fortify':
            simulateFortifyAction(s, action)
        elif action.type == 'Invertir':
            simulateInvertirAction(s, action)
        elif action.type == 'Casino':
            simulateCasinoAction(s ,action)
        elif action.type == 'Festin':
            simulateFestinAction(s ,action)
        elif action.type == 'Comercio':
            simulateComercioAction(s ,action)
        else:
            print(f'ILLEGAL ACTION TYPE!{action.type}2')
        
        rstates = [s]
        rsprobs = [1]
        
    # Lógica de Transición de Fase
    for state in rstates:
        avanz_fase = nextFase(state, action)

        if avanz_fase:
            # Si el jugador es el jugador con el numero más alto de la lista owners significa que es el último
            if state.fase!='fase_0' and state.current_player==max([x for x in state.owners if x is not None]):
                state.mes = (state.mes % 12) + 1
            nextPlayer(state) # Avanza al siguiente jugador
    
            if state.fase == 'fase_1': #FIN DEL TURNO
                updateHappinessFinTurno(state)
                beginTurn(state)    
                
        
    return rstates, rsprobs

def nextFase(state, action):
    """
    Establece el turn_type y la fase del estado DESPUÉS de que se realiza una acción.
    Esta es la máquina de estados principal.
    Devuelve True si el jugador actual ha terminado su turno, False en caso contrario.
    """
    
    advance_player = False 

    if state.players[state.current_player].game_over == True:
        # El jugador acaba de morir (por revolución o ataque). 
        # Forzamos el fin inmediato del turno y la transición a Fase 1 del siguiente.
        state.fase = 'fase_1'
        state.turn_type = "Fase 1"
        advance_player = True
        return advance_player# Devuelve True para que simulateAction avance al siguiente jugador
    if state.fase == "fase_0":
        # Organización del tablero
        if action.type == 'PreAssign':
            advance_player = True 
            if len(getPreAssignActions(state)) == 0:
                # Todos los territorios asignados pasamos a PrePlace
                state.turn_type = 'PrePlace'
            
        elif action.type == 'PrePlace':
            advance_player = True 
            all_placed = all(p.free_armies == 0 for p in state.players)
            if all_placed:
                state.fase = 'fase_1'
                state.turn_type = "Fase 1"
                advance_player = False

    elif state.fase == "fase_1":
        # FASE 1 (Comprar, Colocar, Invertir... Cosas para gastarte el dinero)
        if action.type == 'Comprar_Soldados':
            # Acción obligatoria: después de comprar, debes colocar.
            state.turn_type = 'Place'
        elif action.type == 'Festin':
            state.fase = 'fase_2'
            state.turn_type = "Fase 2"
            
        elif action.type == 'Place':
            if state.players[state.current_player].free_armies > 0:
                # Aún tiene tropas: debe seguir colocando.
                state.turn_type = 'Place'
            else:
                # Ha terminado de colocar pasamos la Fase 2.
                state.fase = 'fase_2'
                state.turn_type = "Fase 2"
        elif action.type=="Pasar":
            state.fase = 'fase_2'
            state.turn_type = "Fase 2"
        elif action.type=="Invertir":
            state.fase = 'fase_2'
            state.turn_type = "Fase 2"


    elif state.fase == "fase_2":
        if action.type == 'Attack':
            if state.last_defender is not None and state.armies[state.last_defender] == 0:
                # Ganamos el ataque por lo que debemos ocupar el territorio
                state.turn_type = 'Occupy' 
            elif action.to_territory is None:
                # No se ataca más
                state.fase = 'fase_3'
                state.turn_type = "Fase 3"
        
        elif action.type == 'Occupy':
            state.turn_type = 'Attack'
            if None not in state.owners:
                if max(state.owners) == min(state.owners):
                    state.turn_type = 'GameOver'
        elif action.type=="Pasar":
            state.fase = 'fase_3'
            state.turn_type = "Fase 3"

        elif action.type=="Casino":
            state.fase = 'fase_3'
            state.turn_type = "Fase 3"

        elif action.type=="Comercio":
            state.fase = 'fase_3'
            state.turn_type = "Fase 3"

    elif state.fase == "fase_3":
        if action.type == 'Fortify':
            state.fase = 'fase_1' 
            state.turn_type = "Fase 1"
        elif action.type=="Pasar":
            state.fase = 'fase_1'
            state.turn_type = "Fase 1"
        advance_player = True

    return advance_player        
def getAllowedFaseActions(state):
    """
    Devuelve un diccionario de todas las acciones permitidas, agrupadas por tipo,
    basado en el *estado exacto* actual (fase Y turn_type).
    """
    actions = {}

    # Acciones forzadas por otra acción
    if state.turn_type == 'Place':
        actions['Place'] = getPlaceActions(state)
        return actions 
    
    if state.turn_type == 'Occupy':
        actions['Occupy'] = getOccupyActions(state)
        return actions 

    if state.turn_type == 'PreAssign':
        actions['PreAssign'] = getPreAssignActions(state)
        return actions
        
    if state.turn_type == 'PrePlace':
        actions['PrePlace'] = getPrePlaceActions(state)
        return actions
    
    # Una vez hemos atacado, estamos obligados a seguir atacando o parar, no podemos dejar de atacar y hacer otra acción de fase_2 (ahorrar etc)
    if state.turn_type == 'Attack':
        actions['Attack'] = getAttackActions(state)
        return actions
    
    
    # Acciones que se pueden elegir
    if state.fase == "fase_1":
        acts_comprar = getComprarSoldadosActions(state)
        if acts_comprar: 
            actions['Comprar_Soldados'] = acts_comprar
        if state.players[state.current_player].free_armies > 0:
            actions['Place'] = getPlaceActions(state)
        actions['Pasar'] = getPasarActions()
        acts_invertir = getInvertirActions(state)
        if acts_invertir is not None and len(acts_invertir) > 0:
            actions['Invertir'] = acts_invertir
        acts_festin = getFestinActions(state)
        if acts_festin: 
            actions['Festin'] = acts_festin

    elif state.fase == "fase_2":
        acts_attack = getAttackActions(state)
        if acts_attack is not None and len(acts_attack) > 0:
            actions['Attack'] = acts_attack
        actions['Pasar'] = getPasarActions()
        actions['Comercio'] = getComercioActions(state)
        acts_casino = getCasinoActions(state)
        if acts_casino: 
            actions['Casino'] = acts_casino

            
                
    elif state.fase == "fase_3":
        actions['Fortify'] = getFortifyActions(state)
        actions['Pasar'] = getPasarActions()
    return actions

# ------------------------------------------------------------------------------------------
# Board
# ------------------------------------------------------------------------------------------
    
def createRiskBoard():
    """
     Creates a RiskBoard from the current riskengine state.  
     Used to interface with the GUI that allows humans to play the AIs
    """
    
    board = RiskBoard()
    
    #Create Continents
    for c in riskengine.continents:
        rc = RiskContinent(c[0],c[1])
        board.add_continent(rc)
        
    #Create Territories
    id_counter = 0
    for t in riskengine.territories.values():
        rt = RiskTerritory(t.name, id_counter)    
        board.add_territory(rt)
        tc = board.continents[t.continent]
        tc.add_territory(rt.id)
        id_counter += 1
    
    #Add in neighbors of each territory
    for t in riskengine.territories.values():
        rt = board.territories[board.territory_to_id[t.name]]
        for n in t.neighbors:
            rt.add_neighbor(board.territory_to_id[n.name])
        
    #Create and add players
    id_counter = 0
    for p in riskengine.playerorder:
        rp = RiskPlayer(p.name, id_counter, p.freeArmies, p.conqueredTerritory,p.economy,p.happiness,p.development)
        id_counter += 1
        board.add_player(rp)
        
    board.set_turn_in_values(riskengine.cardvals)
    board.set_increment_value(riskengine.incrementval)
        
    return board
    
def createRiskState(board, function_name, occupying=None):
    """
     Creates a RiskState from the current riskengine state.  
     Used to interface with the GUI that allows humans to play the AIs
    """

    #players, armies, owners, current_player, turn_type
    #Create players and save the current player
    players = []
    id_counter = 0
    current_player = None #To store the current player

    for p in riskengine.playerorder:
        rp = RiskPlayer(p.name, id_counter, p.freeArmies, p.conqueredTerritory,p.economy,p.happiness,p.development)

        #See if this is the current player
        if p.name == riskengine.currentplayer.name:
            current_player = id_counter

        players.append(rp)
        id_counter += 1
    
    if current_player is None:
        print('STATE CREATION ERROR.  NO PLAYER IS CURRENT!')
        sys.exit()

    #Create armies and owners
    armies = [0]*len(board.territories)
    owners = [None]*len(board.territories)
    for t in riskengine.territories.values():
        idx = board.territory_to_id[t.name]
        if t.player is not None:
            armies[idx] = t.armies
            owners[idx] = board.player_to_id[t.player.name]    

    turn_type = None
    fase="fase_0"
    if riskengine.phase == 'Preposition' and function_name == 'Assignment':
        turn_type = 'PreAssign'
    elif riskengine.phase == 'Preposition' and function_name == 'Placement':
        turn_type = 'PrePlace'
    elif riskengine.phase == 'Place' and function_name == 'Placement':
        turn_type = 'Place'
    elif riskengine.phase == 'Attack' and function_name == 'Attack':
        turn_type = 'Attack'
    elif riskengine.phase == 'Attack' and function_name == 'Occupation':
        turn_type = 'Occupy'
    elif riskengine.phase == 'Attack' and function_name == 'Fortification':
        turn_type = 'Fortify'
            
    #current card turn in index
    turn_in_number = riskengine.currentcard
            
    #Determine last attacker and defender
    last_attacker = None
    last_defender = None
    if occupying is not None:
        last_attacker = board.territory_to_id[occupying[0]]
        last_defender = board.territory_to_id[occupying[1]]
        
    state = RiskState(fase,players,armies,owners,current_player,turn_type,turn_in_number, last_attacker, last_defender, board)

    return state
    
def getInitialState(board):
    """Get the initial state for this board."""
    
    #Initialize the state with the information in the board

    free_armies = 45 - 5*(len(board.players)-1)
    fase="fase_0"
    state_players = []
    for p in board.players:
        new_player = p.copy_player()
        state_players.append(new_player)
        new_player.free_armies = free_armies
             
    #Initialize other state elements
    armies = [0]*len(board.territories)
    owners = [None]*len(board.territories)
    current_player = 0
    turn_type = 'PreAssign'
    turn_in_number = 0
    last_attacker = None
    last_defender = None
    
    state = RiskState(fase,state_players, armies, owners, current_player, turn_type, turn_in_number, last_attacker, last_defender, board)
    return state
    
    
def loadBoard(filename):
    """Loads a RiskBoard from the given filename"""
    
    #Open the zip file to get map data
    zfile = zipfile.ZipFile(filename)
    board = RiskBoard()
    loadTerritories(zfile, board)
    
    #Close the zip file
    zfile.close()

    return board
    
def loadTerritories(zfile, board):
    """Load territory (and other) information from a file."""
   
    terr = xml.dom.minidom.parseString(zfile.read("territory.xml"))
    
    terr_structs = terr.getElementsByTagName("territory")
    
    #Create and add territories
    for t in terr_structs:
        name = t.getAttribute("name")
        nt = RiskTerritory(name, len(board.territories))
        board.add_territory(nt)
    
    #Create continents, add in neighbors
    for terrs in terr_structs:
        name = terrs.getAttribute("name")
        cname = terrs.getAttribute("continent")
        tidx = board.territory_to_id[name]
        ncon = RiskContinent(cname, 0)
        board.add_continent(ncon)
        continent = board.continents[cname]
        continent.add_territory(tidx)
        
        neighbors = terrs.getElementsByTagName("neighbor")
        for neigh in neighbors:
            nidx = board.territory_to_id[neigh.childNodes[0].data]
            board.territories[tidx].add_neighbor(nidx)
        
    cont_structs = terr.getElementsByTagName("continent")
    for con in cont_structs:
        continent = board.continents[con.getAttribute("name")] 
        continent.reward = int(con.getAttribute("value"))
    
  