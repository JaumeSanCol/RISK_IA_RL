import os
import time
import multiprocessing
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

# Importamos nuestro entorno personalizado
# Asegúrate de que risk_gym_env.py esté en la misma carpeta
from risk_gym_env import RiskTotalControlEnv

# --- CONFIGURACIÓN DE LA REANUDACIÓN ---
TIMESTEPS_EXTRA = 180_000  # Cuántos pasos MÁS quieres entrenar
TIMESTEPS_PREVIAS=420_000
LOG_DIR = "./logs_ppo/"
SAVE_FREQ = 5_000
STYLE = "aggressive"

NOMBRE_MODELO_ORIGEN = f"risk_ppo_aggressive_{TIMESTEPS_PREVIAS}_steps" 
RUTA_MODELO_CARGA = os.path.join(LOG_DIR, f"{NOMBRE_MODELO_ORIGEN}.zip")

# Nombre para el nuevo modelo (para no sobrescribir el viejo inmediatamente)
MODEL_NAME_NUEVO = f"risk_ppo_{STYLE}_{TIMESTEPS_PREVIAS+TIMESTEPS_EXTRA}_continued"

def make_env():
    """Crea y envuelve el entorno para RL (Debe ser IDÉNTICO al original)."""
    env = RiskTotalControlEnv(style=STYLE)
    env = Monitor(env, LOG_DIR)
    env = ActionMasker(env, lambda e: e.get_wrapper_attr("action_masks")())
    return env

def main():
    # 1. Configuración inicial
    os.makedirs(LOG_DIR, exist_ok=True)
    num_cpu = multiprocessing.cpu_count() - 1
    
    print(f"[INIT] Preparando para continuar entrenamiento: {STYLE.upper()}")
    print(f"[CPU] Usando {num_cpu} núcleos.")

    # 2. Crear entorno vectorizado
    # Es vital recrear el entorno para que el modelo tenga dónde interactuar
    env = SubprocVecEnv([make_env for _ in range(num_cpu)])

    # 3. CARGAR EL MODELO EXISTENTE
    print(f"[LOAD] Cargando modelo desde: {RUTA_MODELO_CARGA}")
    
    # Check si el archivo existe
    if not os.path.exists(RUTA_MODELO_CARGA):
        print(f"[ERROR] No se encuentra el archivo: {RUTA_MODELO_CARGA}")
        return

    # Cargamos el modelo pasando el nuevo 'env'.
    # tensorboard_log=LOG_DIR asegura que siga escribiendo gráficas en la misma carpeta.
    model = MaskablePPO.load(
        RUTA_MODELO_CARGA, 
        env=env, 
        tensorboard_log=LOG_DIR,
        print_system_info=True 
    )

    # 4. Configurar Callback para el nuevo entrenamiento
    checkpoint_callback = CheckpointCallback(
        save_freq=SAVE_FREQ,
        save_path=LOG_DIR,
        name_prefix=MODEL_NAME_NUEVO
    )

    inicio = time.time()
    
    print(f"[TRAIN] Entrenando por {TIMESTEPS_EXTRA} pasos adicionales...")

    try:
        # 5. REANUDAR ENTRENAMIENTO
        # reset_num_timesteps=False hace que en TensorBoard la gráfica continúe
        # en el paso 420k (o donde se quedó) en lugar de volver a 0.
        model.learn(
            total_timesteps=TIMESTEPS_EXTRA,
            callback=checkpoint_callback,
            progress_bar=True,
            reset_num_timesteps=False 
        )
    except Exception as e:
        print(f"[ERROR] El entrenamiento falló: {e}")
        model.save(os.path.join(LOG_DIR, f"{MODEL_NAME_NUEVO}_emergency"))
        raise e

    tiempo_total = (time.time() - inicio) / 60
    print(f"[FIN] Entrenamiento adicional completado en {tiempo_total:.2f} minutos.")

    # Guardar modelo final de esta etapa
    ruta_final = os.path.join(LOG_DIR, f"{MODEL_NAME_NUEVO}_final")
    model.save(ruta_final)
    print(f"[GUARDADO] Modelo actualizado guardado en: {ruta_final}.zip")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()