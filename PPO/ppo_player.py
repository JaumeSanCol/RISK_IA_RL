import sys
import os
import numpy as np
import itertools
from sb3_contrib import MaskablePPO

# Configurar rutas para encontrar risktools desde ai/
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Importar risktools (del juego) y RiskTotalControlEnv (del entrenamiento)
import risktools
# Truco: Importamos el entorno solo para usar sus funciones auxiliares de obs/decode
sys.path.append(os.path.join(parent_dir, 'PPO'))
from risk_gym_env import RiskTotalControlEnv

# --- CONFIGURACIÓN ---
MODEL_NAME = "risk_ppo_aggressive_final.zip" # CAMBIA ESTO por tu modelo
MODEL_PATH = os.path.join(parent_dir, "PPO", "logs_ppo", MODEL_NAME)

print(f"Cargando cerebro PPO desde: {MODEL_PATH}")
try:
    model = MaskablePPO.load(MODEL_PATH, device='cpu')
    # Instanciamos el entorno solo para usar sus métodos de utilidad (sin inicializar tablero)
    # Esto nos da acceso a _get_obs, _decode_action y action_masks
    helper_env = RiskTotalControlEnv() 
except Exception as e:
    print(f"Error cargando modelo: {e}")
    model = None

def getAction(state, time_left=None):
    """Función principal llamada por el juego."""
    
    if model is None:
        print("No hay modelo cargado. Jugando Random.")
        return random_action(state)

    # 1. Sincronizar el estado del helper_env con el estado real del juego
    # Esto es necesario para que las funciones auxiliares (como action_masks) funcionen
    helper_env.state = state
    helper_env.board = state.board 
    helper_env.player_idx = state.current_player
    
    # 2. Obtener Observación
    obs = helper_env._get_obs()
    
    # 3. Obtener Máscara de Acciones Válidas
    # Importante: MaskablePPO necesita saber qué es legal ahora mismo
    masks = helper_env.action_masks()
    
    # 4. Predicción
    action_vec, _ = model.predict(obs, action_masks=masks, deterministic=True)
    
    # 5. Decodificar Acción
    act_type, act_src, act_dst, act_amt = action_vec
    real_action = helper_env._decode_action(act_type, act_src, act_dst, act_amt)
    
    # --- LOGS VERBOSE ---
    print("\n" + "="*40)
    print(f"TURNO IA ({state.players[state.current_player].name}) - Fase: {state.fase}")
    print(f"Estado Visto: Tropas={sum(state.armies)}, Dinero={state.players[state.current_player].economy:.1f}")
    print(f"Decisión PPO: Tipo={act_type}, Origen={act_src}, Dest={act_dst}, Cant={act_amt}")
    
    if real_action:
        print(f"Acción Ejecutada: {real_action.to_string()}")
    else:
        print(f"Acción PPO Inválida (NULL). Fallback a Random.")
        real_action = random_action(state)
        print(f"Acción Random: {real_action.to_string()}")
    print("="*40 + "\n")
    
    return real_action

def random_action(state):
    """Fallback de seguridad."""
    import random
    allowed = risktools.getAllowedFaseActions(state)
    flat_list = list(itertools.chain.from_iterable(allowed.values()))
    if flat_list:
        return random.choice(flat_list)
    return None

# Funciones wrapper necesarias para la GUI antigua
def aiWrapper(function_name, occupying=None):
    # Esta función es llamada por risk.pyw para instanciar el tablero en cada paso
    # Reconstruimos el estado y llamamos a getAction
    game_board = risktools.createRiskBoard()
    game_state = risktools.createRiskState(game_board, function_name, occupying)
    return getAction(game_state)

# Bindings para la GUI (Assignment, Placement, etc.)
def Assignment(player): return aiWrapper('Assignment')
def Placement(player): return aiWrapper('Placement')
def Attack(player): return aiWrapper('Attack')
def Occupation(player, t1, t2): return aiWrapper('Occupation', [t1.name, t2.name])
def Fortification(player): return aiWrapper('Fortification')