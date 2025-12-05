import os
import time
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

# Importamos nuestro entorno personalizado
from risk_gym_env import RiskTotalControlEnv

# --- CONFIGURACIÓN DEL ENTRENAMIENTO ---
TIMESTEPS = 1_000_000  # Pasos totales (1M es un buen comienzo)
LOG_DIR = "./logs_ppo/"

SAVE_FREQ = 5_000

# ¡ELIGE TU PERSONALIDAD AQUÍ!
# Opciones: "aggressive", "defensive", "capitalist", "standard"
STYLE = "aggressive"  

MODEL_NAME = f"risk_ppo_{STYLE}" # El nombre del archivo final dependerá del estilo

def make_env():
    """Crea y envuelve el entorno para RL."""
    # 1. Instanciamos el entorno con la personalidad elegida
    env = RiskTotalControlEnv(style=STYLE)
    
    # 2. Monitor para registrar logs (recompensas, duración)
    env = Monitor(env, LOG_DIR)
    
    # 3. ActionMasker para prohibir acciones ilegales
    # Usamos get_wrapper_attr para atravesar el Monitor y llegar a la función
    env = ActionMasker(env, lambda e: e.get_wrapper_attr("action_masks")())
    
    return env

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    
    print(f"[TRAIN] Iniciando entrenamiento de Agente con personalidad: {STYLE.upper()}")
    print(f"[CONFIG] Almacenamos los pesos cada {SAVE_FREQ} pasos")
    print(f"[TRAIN] Los logs se guardarán en: {LOG_DIR}")

    # Crear entorno vectorizado (DummyVecEnv gestiona el reset automático)
    env = DummyVecEnv([make_env])

    # Inicializar el modelo PPO con soporte de máscaras
    model = MaskablePPO(
        "MlpPolicy",            # Red neuronal estándar
        env,
        verbose=1,              # Mostrar info en consola
        tensorboard_log=LOG_DIR, # Logs para visualizar en Tensorboard
        learning_rate=3e-4,     # Velocidad de aprendizaje
        gamma=0.99,             # Factor de descuento
        batch_size=64,          # Tamaño de lote
        ent_coef=0.01           # Coeficiente de entropía (fomenta exploración)
    )

    # Callback para guardar el modelo cada 50k pasos (por si se va la luz)
    checkpoint_callback = CheckpointCallback(
        save_freq=SAVE_FREQ,
        save_path=LOG_DIR,
        name_prefix=MODEL_NAME
    )

    inicio = time.time()
    
    try:
        # ¡A aprender!
        model.learn(
            total_timesteps=TIMESTEPS,
            callback=checkpoint_callback,
            progress_bar=True
        )
    except Exception as e:
        print(f"[ERROR] El entrenamiento falló: {e}")
        model.save(os.path.join(LOG_DIR, f"{MODEL_NAME}_emergency"))
        raise e

    tiempo_total = (time.time() - inicio) / 60
    print(f"[FIN] Entrenamiento completado en {tiempo_total:.2f} minutos.")

    # Guardar modelo final
    ruta_final = os.path.join(LOG_DIR, f"{MODEL_NAME}_final")
    model.save(ruta_final)
    print(f"[GUARDADO] Modelo listo en: {ruta_final}.zip")

if __name__ == "__main__":
    main()