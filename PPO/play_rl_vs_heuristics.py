"""
Simulador de Partidas: RL vs Heurísticas
=========================================

Este script enfrenta modelos PPO contra IAs heurísticas clásicas,
generando logs en el mismo formato que play_risk_ai.py para visualización en GUI.

Características:
- Mezcla modelos RL con IAs heurísticas
- Genera logs automáticos en carpeta logs/
- Estadísticas de victorias
- Compatible con risk_game_viewer.py

Ejemplo de uso:
---------------
    python play_rl_vs_heuristics.py \\
        logs_ppo/risk_ppo_aggressive_final.zip \\
        ../ai/attacker_ai.py \\
        ../ai/random_ai.py \\
        -n 5 \\
        -w \\
        -v

Esto enfrenta 5 partidas con 1 RL Agresivo, 1 Atacante Heurístico y 1 Random.
"""

import sys
import os
import time
import argparse
import random
import traceback
import itertools
import imp
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
# Nombres reales
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


class AIFactory:
    """
    Factory para crear IAs tanto PPO como heurísticas.
    
    Detecta automáticamente si un path es:
    - Un archivo .zip (modelo PPO)
    - Un archivo .py (IA heurística)
    """
    
    @staticmethod
    def create_ai(ai_spec, player_name):
        """
        Crea una IA a partir de su especificación.
        
        Parámetros:
        -----------
        ai_spec : str
            Ruta a archivo .zip (PPO) o .py (heurística)
        player_name : str
            Nombre del jugador
        
        Devuelve:
        ---------
        tuple : (ai_object, ai_type_str)
            - ai_object: Objeto con método getAction(state)
            - ai_type_str: "PPO" o "Heuristic"
        """
        
        ai_spec = str(ai_spec)
        
        # Detectar tipo por extensión
        if ai_spec.endswith('.zip'):
            return AIFactory._load_ppo(ai_spec, player_name), "PPO"
        elif ai_spec.endswith('.py'):
            return AIFactory._load_heuristic(ai_spec, player_name), "Heuristic"
        else:
            raise ValueError(
                f"Formato desconocido: {ai_spec}\n"
                f"Debe ser .zip (PPO) o .py (Heurística)"
            )
    
    @staticmethod
    def _load_ppo(model_path, player_name):
        """Carga un modelo PPO."""
        try:
            ppo = PPOPlayer(model_path, player_name=player_name)
            print(f"  ✓ PPO cargado: {player_name}")
            return ppo
        except Exception as e:
            print(f"  ✗ Error al cargar PPO: {e}")
            raise
    
    @staticmethod
    def _load_heuristic(py_path, player_name):
        """Carga una IA heurística desde archivo .py"""
        try:
            # Cargar módulo Python dinámicamente
            module_name = os.path.basename(py_path)[:-3]  # Quitar .py
            gai = imp.new_module(module_name)
            
            with open(py_path, 'r', encoding='utf-8') as f:
                exec(f.read(), gai.__dict__)
            
            print(f"  ✓ Heurística cargada: {player_name} ({module_name})")
            return gai
        except Exception as e:
            print(f"  ✗ Error al cargar heurística: {e}")
            raise


def parse_args():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Enfrenta modelos RL contra IAs heurísticas, generando logs para la GUI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Enfrentar 1 RL + 2 heurísticas, 3 partidas
  python play_rl_vs_heuristics.py \\
      logs_ppo/model.zip \\
      ../ai/attacker_ai.py \\
      ../ai/random_ai.py \\
      -n 3 -w
  
  # Enfrentar 2 RLs + 1 heurística en modo verbose
  python play_rl_vs_heuristics.py \\
      logs_ppo/aggressive.zip \\
      logs_ppo/defensive.zip \\
      ../ai/random_ai.py \\
      -v
        """
    )
    
    parser.add_argument(
        "ais",
        type=str,
        nargs='+',
        help="Mezcla de rutas: archivos .zip (PPO) y/o .py (heurísticas)"
    )
    
    parser.add_argument(
        "-n", "--num",
        dest='num',
        type=int,
        default=5,
        help="Número de partidas donde cada IA es inicial (default: 5)"
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
        help="Modo verbose: mostrar detalles durante ejecución"
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
    """Selecciona un estado según probabilidades."""
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
    
    def __init__(self, player_names, ai_types):
        self.games_played = 0
        self.winners = {i: 0 for i in range(len(player_names))}
        self.total_turns = 0
        self.wins = 0
        self.ties = 0
        self.timeouts = 0
        self.player_names = player_names
        self.ai_types = ai_types  # Almacenar tipos de IA
    
    def print_stats(self):
        """Imprime un resumen de estadísticas."""
        print('\n' + '='*70)
        print('ESTADÍSTICAS DEL TORNEO RL vs HEURÍSTICAS')
        print('='*70)
        print(f'  PARTIDAS JUGADAS  : {self.games_played}')
        print(f'  VICTORIAS NORMALES: {self.wins}')
        print(f'  EMPATES           : {self.ties}')
        print(f'  TIMEOUTS          : {self.timeouts}')
        print(f'  TURNOS PROMEDIO   : {float(self.total_turns) / float(self.games_played) if self.games_played > 0 else 0:.2f}')
        print('\n  VICTORIAS POR JUGADOR:')
        for i, name in enumerate(self.player_names):
            ai_type = self.ai_types[i]
            print(f'    [{ai_type:10}] {name}: {self.winners[i]} victorias')
        print('='*70 + '\n')


def play_game(ais, ai_types, player_names, board_base, stats, save_logfile, verbose=False):
    """
    Simula una partida entre IAs mixtas (RL + Heurísticas).
    """
    
    # Recargar el tablero para cada partida (no usar copy)
    world_path = "world.zip"
    if not os.path.exists(world_path):
        world_path = os.path.join(parent_dir, "world.zip")
    board = risktools.loadBoard(world_path)
    
    time_left = {i: 600.0 for i in range(len(player_names))}
    
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
    
    # Abrir archivo de log
    if save_logfile:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        logname = f"logs{os.path.sep}RISKGAME_RLVSHEUR_{timestr}.log"
        os.makedirs("logs", exist_ok=True)
        logfile = open(logname, 'w', encoding='utf-8')
        logfile.write(board.to_string())
        logfile.write('\n')
    
    if verbose:
        print(f"\n[PARTIDA] Orden de jugadores:")
        for i, name in enumerate(player_names):
            print(f"  {i+1}. {name} ({ai_types[i]})")
    
    # ========================================================================
    # BUCLE PRINCIPAL DEL JUEGO
    # ========================================================================
    
    while not done:
        current_player_index = state.current_player
        current_player_name = state.players[current_player_index].name
        current_ai_type = ai_types[current_player_index]
        
        if verbose:
            print(f"\n[TURNO {action_count}] {current_player_name} ({current_ai_type}) | "
                  f"Tipo: {state.turn_type} | Tiempo: {time_left[current_player_index]:.1f}s")
        
        if save_logfile:
            logfile.write(state.to_string())
            logfile.write('\n')
        
        current_ai = ais[current_player_index]
        ai_state = state.copy_state()
        
        # Obtener acción del AI actual
        start_time = time.perf_counter()
        try:
            # Todos tienen método getAction(state)
            current_action = current_ai.getAction(ai_state)
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
            
            actions_dict = risktools.getAllowedFaseActions(state)
            all_actions = list(itertools.chain.from_iterable(actions_dict.values()))
            if all_actions:
                current_action = random.choice(all_actions)
            else:
                current_action = risktools.RiskAction('Pasar', None, None, None)
            
            time_left[current_player_index] = -1.0
        
        if verbose:
            print(f"  Acción: {current_action.description()}")
            print(f"  Tiempo: {action_time:.3f}s")
        
        # Ejecutar acción
        new_states, new_state_probs = risktools.simulateAction(state, current_action)
        state = select_state_by_probs(new_states, new_state_probs)
        
        if save_logfile:
            logfile.write(current_action.to_string())
            logfile.write('\n')
        
        # Contar turnos
        if current_player_name != last_player_name:
            turn_count += 1
            last_player_name = current_player_name
        
        # Verificar fin de juego
        if state.turn_type == 'GameOver' or action_count > action_limit or time_left[current_player_index] < 0:
            done = True
            winning_player_index = current_player_index
            final_string = ""
            
            if state.turn_type == 'GameOver':
                print(f'\n[FIN] {state.players[winning_player_index].name} ganó!')
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
                print(f'\n[FIN] {state.players[winning_player_index].name} excedió el tiempo.')
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


def play_match(ais, ai_types, player_names, board_base, stats, games_per_agent, save_logfile, verbose):
    """Ejecuta el torneo."""
    
    match_length = games_per_agent
    print(f'\n[TORNEO] Iniciando torneo de {match_length} partidas...')
    
    for game_num in range(match_length):
        # Rotar orden
        temp_names = player_names[1:] + [player_names[0]]
        player_names = temp_names
        temp_ais = ais[1:] + [ais[0]]
        ais = temp_ais
        temp_types = ai_types[1:] + [ai_types[0]]
        ai_types = temp_types
        
        print(f'\n[PARTIDA {game_num + 1}/{match_length}] Orden: {player_names}')
        
        play_game(
            ais,
            ai_types,
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
    
    # Cargar tablero
    print("[CARGA] Cargando tablero...")
    # Buscar world.zip en el directorio actual o en el parent_dir
    world_path = "world.zip"
    if not os.path.exists(world_path):
        world_path = os.path.join(parent_dir, "world.zip")
    board_base = risktools.loadBoard(world_path)
    
    # Cargar IAs (mezcla de RL y heurísticas)
    print(f"[CARGA] Cargando {len(args.ais)} IAs (PPO + Heurísticas)...\n")
    
    ais = []
    ai_types = []
    player_names = []
    nombres_disponibles = list(REAL_KINGDOM_NAMES)
    random.shuffle(nombres_disponibles)
    
    for i, ai_spec in enumerate(args.ais):
        try:
            # Asignar nombre único
            if nombres_disponibles:
                player_name = nombres_disponibles.pop()
            else:
                player_name = f"Agent-{i}"
            
            # Crear IA (detecta tipo automáticamente)
            ai_obj, ai_type = AIFactory.create_ai(ai_spec, player_name)
            ais.append(ai_obj)
            ai_types.append(ai_type)
            player_names.append(player_name)
            
        except Exception as e:
            print(f"[ERROR] No se pudo cargar {ai_spec}: {e}")
            return
    
    # Crear estadísticas y ejecutar torneo
    stats = Statistics(player_names, ai_types)
    
    play_match(
        ais,
        ai_types,
        player_names,
        board_base,
        stats,
        args.num,
        args.save,
        args.verbose
    )


if __name__ == "__main__":
    main()
