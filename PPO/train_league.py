import os
import sys
import random
import multiprocessing
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path: sys.path.append(parent_dir)

from risk_gym_env import RiskTotalControlEnv
# Importamos el nuevo adaptador
from ai.ppo_enemy import PPOBot

# --- CONFIGURACIÓN DE LA LIGA ---
LOG_DIR = "./logs_league/"
MODEL_NAME = "risk_master_agent"
TIMESTEPS = 1_000_000
N_PLAYERS = 4

# RUTAS A TUS MODELOS ENTRENADOS (Ajusta los nombres según tus archivos reales en logs_multi_ppo)
# Si no tienes alguno, comenta la línea.
OPPONENT_POOL = [
    os.path.join(current_dir, "logs_multi_ppo", "risk_ppo_aggressive_vs_attackerAI_final.zip"),
    os.path.join(current_dir, "logs_multi_ppo", "risk_ppo_defensive_vs_attackerAI_final.zip"),
    os.path.join(current_dir, "logs_multi_ppo", "risk_ppo_capitalist_vs_attackerAI_final.zip"),
    os.path.join(current_dir, "logs_multi_ppo", "risk_ppo_standard_vs_attackerAI_final.zip"),
]

class LeagueHandler:
    """
    Clase gestora que elige qué IA usa cada enemigo en cada partida.
    """
    def __init__(self, model_paths):
        self.bots = []
        for path in model_paths:
            if os.path.exists(path):
                # Cargamos el bot en memoria
                bot = PPOBot(path, name=os.path.basename(path))
                if bot.model is not None:
                    self.bots.append(bot)
            else:
                print(f"[WARNING] Modelo no encontrado: {path}")
        
        if not self.bots:
            print("[CRITICAL] No se cargaron modelos PPO. Usando comportamiento Random por defecto.")

    def getAction(self, state):
        """
        El entorno llama a esto para CUALQUIER enemigo (Jugadores 1, 2, 3...)
        """
        if not self.bots: return None # Fallback a random del env

        # Estrategia: Asignar un estilo consistente basado en el ID del jugador
        # Jugador 1 usa Bot 0, Jugador 2 usa Bot 1... (cíclico)
        bot_idx = state.current_player % len(self.bots)
        chosen_bot = self.bots[bot_idx]
        
        return chosen_bot.getAction(state)

# Instancia global de la liga (para evitar recargar modelos en cada fork del proceso)
# Nota: En multiprocessing 'spawn', esto se reinicializa, lo cual está bien.
league_controller = None

def make_league_env():
    """Factoría del entorno de Liga."""
    def _init():
        global league_controller
        if league_controller is None:
            league_controller = LeagueHandler(OPPONENT_POOL)
            
        env = RiskTotalControlEnv(
            style="standard", # Nombre para el log
            n_players=N_PLAYERS,
            enemy_ai_class=league_controller # Pasamos el gestor como la IA enemiga
        )
        env = Monitor(env, LOG_DIR)
        env = ActionMasker(env, lambda e: e.get_wrapper_attr("action_masks")())
        return env
    return _init

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"[LEAGUE] Iniciando entrenamiento de Liga.")
    print(f"[LEAGUE] Oponentes disponibles: {len(OPPONENT_POOL)}")

    num_cpu = multiprocessing.cpu_count() - 2
    if num_cpu < 1: num_cpu = 1
    
    # Entornos paralelos
    env = SubprocVecEnv([make_league_env() for _ in range(num_cpu)])

    # Creamos el Agente Maestro
    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=LOG_DIR,
        learning_rate=2e-4, # Un poco más bajo para refinar
        batch_size=512,     # Batch más grande para estabilizar
        n_steps=512,
        gamma=0.995         # Visión a más largo plazo
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=25_000,
        save_path=LOG_DIR,
        name_prefix=MODEL_NAME
    )

    print("[TRAIN] Entrenando contra la Liga de Agentes PPO...")
    model.learn(total_timesteps=TIMESTEPS, callback=checkpoint_callback, progress_bar=True)
    
    model.save(os.path.join(LOG_DIR, f"{MODEL_NAME}_final"))
    print("[FIN] Entrenamiento completado.")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()