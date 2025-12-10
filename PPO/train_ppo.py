import os
import time
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
import multiprocessing
from stable_baselines3.common.callbacks import CheckpointCallback

# Importamos nuestro entorno personalizado
# Asegúrate de que el archivo del entorno se llame 'risk_gym_env.py'
from risk_gym_env import RiskTotalControlEnv

# --- CONFIGURACIÓN DEL ENTRENAMIENTO ---
TIMESTEPS = 1_000_000  
LOG_DIR = "./logs_ppo/"
SAVE_FREQ = 5_000

# 1. ELIGE TU PERSONALIDAD
STYLE = "aggressive"  # "standard", "aggressive", "defensive", "capitalist"

# 2. ELIGE LA CANTIDAD DE JUGADORES 
# 2 = 1vs1 
# 4 = 1 Agente vs 3 Bots 
# 6 = 1 Agente vs 5 Bots 
N_PLAYERS = 6

# Actualizamos el nombre para distinguir modelos de duelo vs modelos de 4 jugadores
MODEL_NAME = f"risk_ppo_{STYLE}_{N_PLAYERS}p" 

def make_env():
    """Crea y envuelve el entorno para RL."""
    # 1. Instanciamos el entorno pasando el estilo Y el número de jugadores
    env = RiskTotalControlEnv(style=STYLE, n_players=N_PLAYERS)
    
    # 2. Monitor para registrar logs
    env = Monitor(env, LOG_DIR)
    
    # 3. ActionMasker para prohibir acciones ilegales
    env = ActionMasker(env, lambda e: e.get_wrapper_attr("action_masks")())
    
    return env

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    
    print(f"[TRAIN] Iniciando entrenamiento: {STYLE.upper()} contra {N_PLAYERS - 1} enemigos.")
    print(f"[CONFIG] Guardado cada {SAVE_FREQ} pasos.")
    print(f"[LOGS] Directorio: {LOG_DIR}")
    print(f"[MODELO] Nombre archivo: {MODEL_NAME}")

    # Detectar núcleos y dejar uno libre para que el PC no se congele
    num_cpu = multiprocessing.cpu_count() - 1
    # Seguridad: si tienes muchos núcleos, no abras más entornos que jugadores tiene sentido simular
    # aunque aquí son entornos paralelos independientes, así que usa todos los que puedas.
    if num_cpu < 1: num_cpu = 1
    
    print(f"[PARALELISMO] Usando {num_cpu} entornos simultáneos.")

    # Crear entornos paralelos
    env = SubprocVecEnv([make_env for _ in range(num_cpu)])

    # Definición del Modelo PPO
    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=LOG_DIR,
        learning_rate=3e-4,
        gamma=0.99,
        # batch_size: Cuantas experiencias recoge antes de actualizar.
        # Al haber más jugadores, los turnos son más largos y complejos.
        batch_size=256,  
        n_steps=256,    
        ent_coef=0.01
    )   

    checkpoint_callback = CheckpointCallback(
        save_freq=SAVE_FREQ,
        save_path=LOG_DIR,
        name_prefix=MODEL_NAME
    )

    inicio = time.time()
    
    try:
        model.learn(
            total_timesteps=TIMESTEPS,
            callback=checkpoint_callback,
            progress_bar=True
        )
    except Exception as e:
        print(f"[ERROR] Entrenamiento interrumpido: {e}")
        model.save(os.path.join(LOG_DIR, f"{MODEL_NAME}_emergency"))
        raise e

    tiempo_total = (time.time() - inicio) / 60
    print(f"[FIN] Completado en {tiempo_total:.2f} minutos.")

    ruta_final = os.path.join(LOG_DIR, f"{MODEL_NAME}_final")
    model.save(ruta_final)
    print(f"[GUARDADO] Modelo final en: {ruta_final}.zip")

if __name__ == "__main__":
    # Necesario para Windows y entornos complejos
    multiprocessing.set_start_method("spawn", force=True)
    main()