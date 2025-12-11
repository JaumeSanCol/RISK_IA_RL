import os
import sys
import time
import multiprocessing
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

# --- IMPORTACIÓN DE MÓDULOS PROPIOS ---
# Aseguramos que Python encuentre la carpeta 'ai' y 'risktools'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from risk_gym_env import RiskTotalControlEnv
from ai import attacker_ai  # <--- AQUÍ IMPORTAMOS LA HEURÍSTICA AGRESIVA

# --- CONFIGURACIÓN GLOBAL ---
TIMESTEPS_PER_MODEL = 300_000  # Pasos por cada personalidad
LOG_DIR = "./logs_multi_ppo/"
N_PLAYERS = 4  # 1 Agente RL vs 3 Bots Heurísticos

# Lista de personalidades a entrenar
STYLES_TO_TRAIN = ["aggressive", "defensive", "capitalist", "standard"]

def make_env(style, n_players, enemy_ai_module):
    """
    Función factoría para crear el entorno con parámetros específicos.
    Necesaria para SubprocVecEnv.
    """
    def _init():
        # Pasamos attacker_ai como la clase de IA enemiga
        env = RiskTotalControlEnv(style=style, n_players=n_players, enemy_ai_class=enemy_ai_module)
        # Monitor para logs individuales
        env = Monitor(env, os.path.join(LOG_DIR, style))
        # Masking para acciones inválidas
        env = ActionMasker(env, lambda e: e.get_wrapper_attr("action_masks")())
        return env
    return _init

def train_style(style):
    """Ejecuta el entrenamiento completo para un estilo específico."""
    model_name = f"risk_ppo_{style}_vs_attackerAI"
    print(f"\n{'='*50}")
    print(f"[START] Entrenando Agente: {style.upper()}")
    print(f"[OPONENTE] Heurística: Attacker AI (Agresiva)")
    print(f"{'='*50}\n")

    # Configuración de paralelismo
    num_cpu = multiprocessing.cpu_count() - 2
    if num_cpu < 1: num_cpu = 1
    
    # Crear vector de entornos
    # Nota: Pasamos 'attacker_ai' (el módulo importado) al entorno
    env = SubprocVecEnv([make_env(style, N_PLAYERS, attacker_ai) for _ in range(num_cpu)])

    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=LOG_DIR,
        learning_rate=3e-4,
        gamma=0.99,
        batch_size=256,
        n_steps=256,
        ent_coef=0.01
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=10_000,
        save_path=os.path.join(LOG_DIR, f"{style}_checkpoints"),
        name_prefix=model_name
    )

    try:
        model.learn(
            total_timesteps=TIMESTEPS_PER_MODEL,
            callback=checkpoint_callback,
            progress_bar=True,
            tb_log_name=f"PPO_{style}"
        )
        
        # Guardar modelo final
        final_path = os.path.join(LOG_DIR, f"{model_name}_final")
        model.save(final_path)
        print(f"[SUCCESS] Modelo {style} guardado en {final_path}.zip")
        
    except Exception as e:
        print(f"[ERROR] Falló el entrenamiento de {style}: {e}")
    finally:
        env.close()

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"[MULTI-TRAIN] Iniciando secuencia de entrenamiento para {len(STYLES_TO_TRAIN)} estilos.")
    
    for style in STYLES_TO_TRAIN:
        train_style(style)
        # Pequeña pausa para liberar memoria y sockets
        time.sleep(5) 

    print("\n[FIN] Todos los entrenamientos finalizados.")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()