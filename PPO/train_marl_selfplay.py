import os
import multiprocessing
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

from risk_selfplay_env import RiskSelfPlayEnv

LOG_DIR = "./logs_marl/"
MODEL_NAME = "risk_selfplay_grandmaster"
TIMESTEPS = 2_000_000 # Self-play requiere más tiempo
N_PLAYERS = 4

def make_env():
    env = RiskSelfPlayEnv(n_players=N_PLAYERS)
    env = Monitor(env, LOG_DIR)
    env = ActionMasker(env, lambda e: e.get_wrapper_attr("action_masks")())
    return env

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Paralelismo
    num_cpu = multiprocessing.cpu_count() - 2
    env = SubprocVecEnv([make_env for _ in range(num_cpu)])

    # Modelo
    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=LOG_DIR,
        learning_rate=3e-4,
        batch_size=1024,   # Batches grandes para estabilizar la varianza
        n_steps=1024,      
        gamma=0.995,
        ent_coef=0.01
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=50_000,
        save_path=LOG_DIR,
        name_prefix=MODEL_NAME
    )

    print("[MARL] Iniciando entrenamiento Self-Play...")
    print("La red controla a los 4 jugadores y aprende a ganarse a sí misma.")
    
    model.learn(total_timesteps=TIMESTEPS, callback=checkpoint_callback, progress_bar=True)
    
    model.save(os.path.join(LOG_DIR, f"{MODEL_NAME}_final"))

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()