"""
Simulador de Partidas: RL vs RL
================================

Este script enfrenta múltiples modelos PPO entre sí, generando logs
en el mismo formato que play_risk_ai.py para poder visualizarlos en la GUI.

Características:
- Soporta enfrentamientos de 2, 3, 4 o más jugadores RL
- Genera logs automáticos en la carpeta logs/
- Estadísticas de victorias por jugador
- Compatible con risk_game_viewer.py

Ejemplo de uso:
---------------
    python play_rl_vs_rl.py \\
        logs_ppo/risk_ppo_aggressive_final.zip \\
        logs_ppo/risk_ppo_defensive_final.zip \\
        -n 5 \\
        -w \\
        -v

Esto enfrenta 5 partidas donde cada modelo es jugador inicial en orden.
"""

import sys
import os
import time
import argparse
import random
import traceback
import itertools
from pathlib import Path

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, current_dir)  # Prioridad a PPO/
sys.path.insert(0, parent_dir)   # Acceso a risktools

import risktools
from config_atrib import *
from ppo_loader import PPOPlayer

# ============================================================================
# Nombres reales para darle más vida al juego
# ============================================================================

REAL_KINGDOM_NAMES = [
    "Castilla", "Aragón", "Prusia", "Baviera", "Bohemia",
    "Hungría", "Polonia", "Borgoña", "Nápoles", "Sicilia",
    "Austria", "Francia", "Inglaterra", "Escocia", "Macedonia",
    "Judea", "Persia", "Numidia", "Cartago", "Esparta",
    "Suecia", "Noruega", "Dinamarca", "Rusia", "Moscovia",
    "Lituania", "Valaquia", "Navarra", "Portugal", "León",
    "Sajonia", "Lombardía", "Cerdeña", "Granada", "Livonia"
]


def parse_args():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Enfrenta modelos RL entre sí, generando logs para la GUI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Enfrentar 2 modelos RL, 3 partidas por jugador inicial
  python play_rl_vs_rl.py logs_ppo/model1.zip logs_ppo/model2.zip -n 3 -w
  
  # Enfrentar 3 modelos RL en modo verbose sin guardar logs
  python play_rl_vs_rl.py model1.zip model2.zip model3.zip -v
        """
    )
    
    parser.add_argument(
        "models",
        type=str,
        nargs='+',
        help="Rutas a archivos .zip de modelos PPO entrenados"
    )
    
    parser.add_argument(
        "-n", "--num",
        dest='num',
        type=int,
        default=5,
        help="Número de partidas donde cada RL es jugador inicial (default: 5)"
    )
    
    parser.add_argument(
        "-w", "--write",
        dest='save',
        action='store_true',
        help="Guardar logs de partidas en carpeta logs/"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        dest='verbose',
        action='store_true',
        help="Modo verbose: mostrar detalles durante la ejecución"
    )
    
    return parser.parse_args()


def is_valid_action(state, action):
    """Verifica que una acción sea legal en el estado actual."""
    action_string = action.to_string()
    actions = risktools.getAllowedFaseActions(state)
    for a in list(itertools.chain.from_iterable(actions.values())):
        astring = a.to_string()
        if astring == action_string:
            return True
    return False


def select_state_by_probs(states, probs):
    """Selecciona un estado según probabilidades (para acciones con múltiples resultados)."""
    if len(states) == 1:
        return states[0]
    
    r = random.random()
    i = 0
    prob_sum = probs[0]
    while prob_sum < r and i < len(probs) - 1:
        i += 1
        prob_sum += probs[i]
    return states[i]


class Statistics:
    """Almacena y reporta estadísticas de un torneo."""
    
    def __init__(self, player_names):
        self.games_played = 0
        self.winners = {i: 0 for i in range(len(player_names))}
        self.total_turns = 0
        self.wins = 0
        self.ties = 0
        self.timeouts = 0
        self.player_names = player_names
    
    def print_stats(self):
        """Imprime un resumen de estadísticas."""
        print('\n' + '='*60)
        print('ESTADÍSTICAS DEL TORNEO RL vs RL')
        print('='*60)
        print(f'  PARTIDAS JUGADAS  : {self.games_played}')
        print(f'  VICTORIAS NORMALES: {self.wins}')
        print(f'  EMPATES           : {self.ties}')
        print(f'  TIMEOUTS          : {self.timeouts}')
        print(f'  TURNOS PROMEDIO   : {float(self.total_turns) / float(self.games_played) if self.games_played > 0 else 0:.2f}')
        print('\n  VICTORIAS POR JUGADOR:')
        for i, name in enumerate(self.player_names):
            print(f'    {name}: {self.winners[i]} victorias')
        print('='*60 + '\n')


def play_game(ppo_players, player_names, board_base, stats, save_logfile, verbose=False):
    """
    Simula una partida completa entre los IAs RL.
    
    Parámetros:
    -----------
    ppo_players : list[PPOPlayer]
        Lista de objetos PPOPlayer ya cargados.
    player_names : list[str]
        Nombres que llevará cada jugador.
    board_base : RiskBoard
        Tablero base del juego.
    stats : Statistics
        Objeto para almacenar estadísticas.
    save_logfile : bool
        Si guardar o no el log de la partida.
    verbose : bool
        Si mostrar detalles durante el juego.
    """
    
    # Recargar el tablero para cada partida (no usar copy)
    world_path = "world.zip"
    if not os.path.exists(world_path):
        world_path = os.path.join(parent_dir, "world.zip")
    board = risktools.loadBoard(world_path)
    
    time_left = {i: 600.0 for i in range(len(player_names))}  # 10 minutos por jugador
    
    action_limit = 5000
    logname = None
    logfile = None
    
    # Crear tablero con jugadores
    for i, name in enumerate(player_names):
        player = risktools.RiskPlayer(
            name, 
            len(board.players), 
            0, 
            False, 
            ECON_START, 
            HAPP_START, 
            DEVP_START
        )
        board.add_player(player)
    
    state = risktools.getInitialState(board)
    
    action_count = 0
    turn_count = 0
    done = False
    last_player_name = None
    
    # Abrir archivo de log si es necesario
    if save_logfile:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        logname = f"logs{os.path.sep}RISKGAME_RLVRL_{timestr}.log"
        os.makedirs("logs", exist_ok=True)
        logfile = open(logname, 'w', encoding='utf-8')
        logfile.write(board.to_string())
        logfile.write('\n')
    
    if verbose:
        print(f"\n[PARTIDA] Orden de jugadores: {player_names}")
    
    # ========================================================================
    # BUCLE PRINCIPAL DEL JUEGO
    # ========================================================================
    
    while not done:
        current_player_index = state.current_player
        current_player_name = state.players[current_player_index].name
        
        if verbose:
            print(f"\n[TURNO {action_count}] Jugador: {current_player_name} | "
                  f"Tipo: {state.turn_type} | Tiempo: {time_left[current_player_index]:.1f}s")
        
        if save_logfile:
            logfile.write(state.to_string())
            logfile.write('\n')
        
        # Obtener IA del jugador actual
        current_ppo = ppo_players[current_player_index]
        
        # Hacer copia para seguridad
        ai_state = state.copy_state()
        
        # Obtener acción del modelo
        start_time = time.perf_counter()
        try:
            current_action = current_ppo.getAction(ai_state)
        except Exception as e:
            print(f'[ERROR] Fallo en {current_player_name}: {e}')
            traceback.print_exc()
            time_left[current_player_index] = -1.0
            current_action = None
        
        end_time = time.perf_counter()
        action_time = end_time - start_time
        time_left[current_player_index] -= action_time
        
        # Validar acción
        if current_action is None or not is_valid_action(state, current_action):
            if verbose:
                print(f"[ADVERTENCIA] {current_player_name} jugó acción inválida")
            
            # Fallback: acción aleatoria válida
            actions_dict = risktools.getAllowedFaseActions(state)
            all_actions = list(itertools.chain.from_iterable(actions_dict.values()))
            if all_actions:
                current_action = random.choice(all_actions)
            else:
                current_action = risktools.RiskAction('Pasar', None, None, None)
            
            time_left[current_player_index] = -1.0  # Penalizar por acción inválida
        
        if verbose:
            print(f"  Acción: {current_action.description()}")
            print(f"  Tiempo: {action_time:.3f}s")
        
        # Ejecutar acción
        new_states, new_state_probs = risktools.simulateAction(state, current_action)
        state = select_state_by_probs(new_states, new_state_probs)
        
        if save_logfile:
            logfile.write(current_action.to_string())
            logfile.write('\n')
        
        # Contar turnos (cambio de jugador)
        if current_player_name != last_player_name:
            turn_count += 1
            last_player_name = current_player_name
        
        # Verificar condiciones de fin de juego
        if state.turn_type == 'GameOver' or action_count > action_limit or time_left[current_player_index] < 0:
            done = True
            winning_player_index = current_player_index
            final_string = ""
            
            if state.turn_type == 'GameOver':
                print(f'\n[FIN] {state.players[winning_player_index].name} ganó la partida!')
                final_string = "RISKRESULT|" + state.players[winning_player_index].name + ",1|"
                for i in range(len(player_names)):
                    if i != winning_player_index:
                        final_string += state.players[i].name + ",0|"
                final_string += 'Game End'
                stats.winners[winning_player_index] += 1
                stats.wins += 1
            
            elif action_count > action_limit:
                print(f'\n[FIN] Límite de acciones alcanzado. Empate.')
                tie_score = round(1.0 / len(player_names), 2)
                final_string = "RISKRESULT|"
                for i in range(len(player_names)):
                    final_string += state.players[i].name + "," + str(tie_score) + "|"
                    stats.winners[i] += tie_score
                final_string += 'Action Limit Reached'
                stats.ties += 1
            
            elif time_left[current_player_index] < 0:
                print(f'\n[FIN] {state.players[winning_player_index].name} excedió el tiempo. Pierde.')
                final_string = "RISKRESULT|" + state.players[winning_player_index].name + ",0|"
                time_out_score = round(1.0 / (len(player_names) - 1), 2)
                for i in range(len(player_names)):
                    if i != winning_player_index:
                        final_string += state.players[i].name + "," + str(time_out_score) + "|"
                        stats.winners[i] += time_out_score
                final_string += 'Time Out'
                stats.timeouts += 1
            
            final_string += f'|Turn Count = {turn_count}'
            
            if save_logfile:
                logfile.write(state.to_string())
                logfile.write('\n')
                logfile.write(final_string)
                logfile.write('\n')
        
        action_count += 1
    
    stats.total_turns += turn_count
    stats.games_played += 1
    
    if save_logfile:
        logfile.close()
        print(f"  Log guardado: {logname}")


def play_match(ppo_players, player_names, board_base, stats, games_per_agent, save_logfile, verbose):
    """
    Ejecuta un torneo donde cada IA es jugador inicial.
    
    Parámetros:
    -----------
    ppo_players : list[PPOPlayer]
        Lista de IAs RL.
    player_names : list[str]
        Nombres de los jugadores.
    board_base : RiskBoard
        Tablero base del juego.
    stats : Statistics
        Objeto de estadísticas.
    games_per_agent : int
        Número de partidas donde cada IA es la primera.
    save_logfile : bool
        Si guardar logs.
    verbose : bool
        Si mostrar detalles.
    """
    
    match_length = games_per_agent
    print(f'\n[TORNEO] Iniciando torneo de {match_length} partidas...')
    
    for game_num in range(match_length):
        # Rotar orden de jugadores (cada uno es primero en su turno)
        temp_names = player_names[1:] + [player_names[0]]
        player_names = temp_names
        temp_ppos = ppo_players[1:] + [ppo_players[0]]
        ppo_players = temp_ppos
        
        print(f'\n[PARTIDA {game_num + 1}/{match_length}] Orden: {player_names}')
        
        play_game(
            ppo_players,
            player_names,
            board_base,
            stats,
            save_logfile,
            verbose
        )
    
    stats.print_stats()


def main():
    """Función principal."""
    
    args = parse_args()
    
    # Cargar tablero base
    print("[CARGA] Cargando tablero...")
    # Buscar world.zip en el directorio actual o en el parent_dir
    world_path = "world.zip"
    if not os.path.exists(world_path):
        world_path = os.path.join(parent_dir, "world.zip")
    board_base = risktools.loadBoard(world_path)
    
    # Cargar modelos PPO
    print(f"[CARGA] Cargando {len(args.models)} modelos PPO...\n")
    
    ppo_players = []
    player_names = []
    nombres_disponibles = list(REAL_KINGDOM_NAMES)
    random.shuffle(nombres_disponibles)
    
    for i, model_path in enumerate(args.models):
        try:
            # Asignar nombre único
            if nombres_disponibles:
                player_name = nombres_disponibles.pop()
            else:
                player_name = f"RL-Agent-{i}"
            
            # Cargar modelo
            ppo = PPOPlayer(model_path, player_name=player_name)
            ppo_players.append(ppo)
            player_names.append(player_name)
            
        except Exception as e:
            print(f"[ERROR] No se pudo cargar {model_path}: {e}")
            return
    
    # Crear estadísticas y ejecutar torneo
    stats = Statistics(player_names)
    
    play_match(
        ppo_players,
        player_names,
        board_base,
        stats,
        args.num,
        args.save,
        args.verbose
    )


if __name__ == "__main__":
    main()
