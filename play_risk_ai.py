import sys
import imp
import risktools
import time
import os
import argparse
import random
import traceback
from config_atrib import *
import itertools

# --- BATERÍA DE NOMBRES DE REINOS REALES ---
nombres_reales = [
    "Castilla", "Aragón", "Prusia", "Baviera", "Bohemia",
    "Hungría", "Polonia", "Borgoña", "Nápoles", "Sicilia",
    "Austria", "Francia", "Inglaterra", "Escocia", "Macedonia",
    "Judea", "Persia", "Numidia", "Cartago", "Esparta",
    "Suecia", "Noruega", "Dinamarca", "Rusia", "Moscovia",
    "Lituania", "Valaquia", "Navarra", "Portugal", "León",
    "Sajonia", "Lombardía", "Cerdeña", "Granada", "Livonia"
]

def parse_args():
    parser = argparse.ArgumentParser(description='Play a RISK match between some AIs')
    # MODIFICADO: La ayuda ahora refleja que solo se necesitan los archivos de IA
    parser.add_argument("ais", type=str, nargs='+', help="List of the AI files for match: ai_1.py ai_2.py ai_3.py ...")
    parser.add_argument("-n, --num", dest='num', type=int, help="Specify the number of games each player goes first in match", default=5)
    parser.add_argument("-w, --write", dest='save', action='store_true', help="Indicate that logfiles for games in the match should be saved to the logs directory", default=False)
    parser.add_argument("-v, --verbose", dest='verbose', action='store_true', help="Indicate that the match should be run in verbose mode", default=False)
    return parser.parse_args()

def select_state_by_probs(states, probs):
    if len(states) == 1:
        return states[0]

    r = random.random()
    i = 0
    prob_sum = probs[0]
    while prob_sum < r:
        i += 1
        prob_sum += probs[i]
    return states[i]

def is_valid_action(state, action):
    action_string = action.to_string()
    actions = risktools.getAllowedFaseActions(state)
    for a in list(itertools.chain.from_iterable(actions.values())):
        astring = a.to_string()
        if astring == action_string:
            return True
    return False

class Statistics():
    def __init__(self, player_names):
        self.games_played = 0
        self.winners = dict()
        for i in range(len(player_names)):
            self.winners[i] = 0
            
        self.total_turns = 0
        self.wins = 0
        self.ties = 0
        self.time_outs = 0
        
    def print_stats(self):
        print('MATCH STATISTICS:')
        print('  GAMES PLAYED : ', self.games_played)
        print('  NORMAL WINS  : ', self.wins)
        print('  TIES         : ', self.ties)
        print('  TIME OUTS    : ', self.time_outs)
        print('  WINNERS      : ', self.winners)
        print('  AVERAGE TURNS: ', float(self.total_turns) / float(self.games_played))
    
def play_game(player_names, ai_players, ai_files, stats, save_logfile, verbose=False):
    """
    This will actually play a single game between the players given
    """
    board = risktools.loadBoard("world.zip")
    
    time_left = dict()
    logname = 'logs' + os.path.sep + 'RISKGAME'
    
    action_limit = 5000 
    player_time_limit = 600 
    
    for i, name in enumerate(player_names):
        time_left[i] = player_time_limit 
        # Inicializamos con el nombre base. La lógica de "República de...", etc.
        # ocurrirá dentro del juego si tu código de revolución está implementado.
        ap = risktools.RiskPlayer(name, len(board.players), 0, False, ECON_START, HAPP_START, DEVP_START)
        board.add_player(ap)
        
    state = risktools.getInitialState(board)
    
    action_count = 0
    turn_count = 0
    done = False
    last_player_name = None
    
    if save_logfile: 
        timestr = time.strftime("%Y%m%d-%H%M%S")
        logname = logname +'_' + timestr + '.log'
        logfile = open(logname, 'w')
        logfile.write(board.to_string())
        logfile.write('\n')
        final_string = ''
    
    print('Players order for game: ', player_names)
    
    while not done:
        current_player_index = state.current_player
        
        if verbose:
            print('--*TURN', action_count, 'BEGIN*--')
            print('CURRENT PLAYER: ', state.players[current_player_index].name)
            print('TURN-TYPE: ', state.turn_type)
            print('TIME-LEFT: ', time_left[current_player_index])
        
        if save_logfile:
            logfile.write(state.to_string())
            logfile.write('\n')

        try:
            current_ai = ai_players[current_player_index]
        except KeyError:
            pass
            
        ai_state = state.copy_state()
        start_action = time.perf_counter()
        current_player_name = state.players[current_player_index].name

        error_actions = risktools.getAllowedFaseActions(state)
        try:
            tipo_de_accion = list(itertools.chain.from_iterable(error_actions.values()))
            # Fallback action
            current_action = random.choice(tipo_de_accion) if tipo_de_accion else None
        except Exception as e:
            print(f"ERROR:{e}")
            print(f"Acction_list={error_actions}")
            print(f"State: {state.to_string()}")
        
        try:
            current_action = current_ai.getAction(ai_state)
        except Exception as e:
            print('There was an error for player: ', current_player_name, '  THEY LOSE!')
            print(' ERROR INFORMATION: ')
            print(e)
            traceback.print_exc()
            time_left[current_player_index] = -1.0 
            
        if not is_valid_action(state, current_action):
            print('Player selected invalid action.  ERROR, THEY LOSE!')
            print('  Action selected: ', current_action.to_string())
            print('  Possible valid actions: ')
            if tipo_de_accion:
                for ea in tipo_de_accion:
                    print('   ', ea.to_string())
                current_action = random.choice(tipo_de_accion)
            time_left[current_player_index] = -1.0 
        
        if current_player_name != last_player_name:
            turn_count += 1                   
            last_player_name = current_player_name

        end_action = time.perf_counter()
        action_length = end_action - start_action
        time_left[current_player_index] = time_left[current_player_index] - action_length
        current_time_left = time_left[current_player_index]
       
        if verbose:
            print('IN ', action_length, ' SECONDS CHOSE ACTION: ', current_action.description())
        
        new_states, new_state_probabilities = risktools.simulateAction(state, current_action)

        if len(new_states) > 1:
            state = select_state_by_probs(new_states, new_state_probabilities)
        else:
            state = new_states[0]

        if save_logfile:
            logfile.write(current_action.to_string())
            logfile.write('\n')
        
        if state.turn_type == 'GameOver' or action_count > action_limit or current_time_left < 0:
            done = True
            winning_player_index = current_player_index
                
            if state.turn_type == 'GameOver':
                print('Game is over.', state.players[winning_player_index].name, ' is the winner.')
                final_string = "RISKRESULT|" + state.players[winning_player_index].name + ",1|"
                for i in range(len(player_names)):
                    if i != winning_player_index:
                        final_string = final_string + state.players[i].name + ",0|"
                final_string = final_string + 'Game End'
                stats.winners[winning_player_index] += 1 
                stats.wins += 1

            if action_count > action_limit:
                print('Action limit exceeded.  Game ends in a tie')
                tie_score = round((1.0 / float(len(player_names))), 2)
                final_string = "RISKRESULT|"
                for i in range(len(player_names)):
                    final_string = final_string + state.players[i].name + "," + str(tie_score) + "|"
                    stats.winners[i] += tie_score 
                final_string = final_string + 'Action Limit Reached'
                stats.ties += 1

            if current_time_left < 0:
                print('Agent time limit exceeded. ', state.players[winning_player_index].name, ' loses by time-out.')
                final_string = "RISKRESULT|" + state.players[winning_player_index].name + ",0|"
                time_out_score = round((1.0 / float(len(player_names) - 1)), 2)
                for i in range(len(player_names)):
                    if i != winning_player_index:
                        final_string = final_string + state.players[i].name + "," + str(time_out_score) + "|"
                        stats.winners[i] += time_out_score 
                final_string = final_string + 'Time Out'
                stats.time_outs += 1
        
        action_count = action_count + 1
        if verbose:
            print('--*TURN END*--')
        
    stats.total_turns += turn_count
    stats.games_played += 1
    final_string = final_string + '|Turn Count = ' + str(turn_count)
    if verbose:
        print(' Final State at end of game:')
        state.print_state()
    print(final_string)
    if save_logfile:
        print('Game log saved to: ', logname)
        logfile.write(state.to_string())
        logfile.write('\n')
        logfile.write(final_string)
        logfile.write('\n')
        logfile.close()    

def play_match(player_names, ai_players, ai_files, stats, games_per_agent, save_logfile, verbose):
    match_length = games_per_agent 
    print('Playing match of length: ', match_length)

    for i in range(match_length):
        if (i % len(player_names) == 0):
            random.shuffle(player_names)
            print('Randomizing player names')
            
        temp_names = player_names[1:]
        temp_names.append(player_names[0])
        player_names = temp_names
        
        print('PLAYING GAME', i, 'OF', match_length, 'LENGTH MATCH :', player_names)
        play_game(player_names, ai_players, ai_files, stats, save_logfile, verbose)
        
    print('\n*******************************\nMATCH IS OVER.  PLAYED', match_length, 'GAMES\n*******************************\n')
    stats.print_stats()

if __name__ == "__main__":
    
    args = parse_args()

    ai_players = dict()
    ai_files = dict()
    player_names = []
    
    # Preparamos los nombres disponibles y los mezclamos
    nombres_disponibles = list(nombres_reales)
    random.shuffle(nombres_disponibles)
  
    # MODIFICADO: Iteramos directamente sobre los archivos, de 1 en 1
    for i, ai_filename in enumerate(args.ais):
        gai = imp.new_module("ai")
        
        # Carga del módulo
        filecode = open(ai_filename)
        exec(filecode.read(), gai.__dict__)
        filecode.close()
        
        # Nombre del archivo limpio (para logs internos si se requiere)
        ai_file_clean = os.path.basename(ai_filename)
        ai_file_clean = ai_file_clean[0:-3]
        
        # SELECCIÓN AUTOMÁTICA DE NOMBRE
        if len(nombres_disponibles) > 0:
            # Sacamos un nombre (pop) para que no se repita
            player_name = nombres_disponibles.pop()
        else:
            # Fallback por si pones más de 35 IAs a jugar
            player_name = f"Nacion_{i}"

        player_index = i
        
        print(f"Cargando IA: {ai_filename} -> Asignado nombre: {player_name}")
        
        ai_files[player_index] = (player_name, ai_file_clean)
        player_names.append(player_name)
        ai_players[player_index] = gai
    
    stats = Statistics(player_names)
    play_match(player_names, ai_players, ai_files, stats, args.num, args.save, args.verbose)