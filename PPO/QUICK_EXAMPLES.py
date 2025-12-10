"""
EJEMPLOS RÁPIDOS DE USO - Play RL Simulation
=============================================

Este archivo contiene comandos listos para ejecutar con diferentes escenarios.
Cópia, pega y modifica según tus necesidades.

PREREQUISITOS:
- Estar en el directorio PPO/
- Tener modelos .zip en logs_ppo/
- Tener IAs .py en ../ai/
"""

# ==============================================================================
# ESCENARIO 1: RL vs RL (Dos modelos)
# ==============================================================================

# Comando:
# python play_rl_vs_rl.py logs_ppo/model1.zip logs_ppo/model2.zip -n 5 -w -v

# Explicación:
#   - logs_ppo/model1.zip      : Primera IA RL
#   - logs_ppo/model2.zip      : Segunda IA RL
#   - -n 5                     : 5 partidas donde cada uno es jugador inicial
#   - -w                       : Guardar logs en logs/
#   - -v                       : Modo verbose (ver detalles)
#
# Total de partidas: 5 (model1 es 1er jugador) + 5 (model2 es 1er jugador) = 10 partidas


# ==============================================================================
# ESCENARIO 2: RL vs RL (Tres modelos)
# ==============================================================================

# Comando:
# python play_rl_vs_rl.py \
#     logs_ppo/risk_ppo_aggressive.zip \
#     logs_ppo/risk_ppo_defensive.zip \
#     logs_ppo/risk_ppo_balanced.zip \
#     -n 3 -w

# Explicación:
#   - 3 modelos RL enfrentados
#   - -n 3 : 3 partidas por modelo como inicial = 9 partidas totales
#   - -w : Guardar todos los logs en logs/
#   - (sin -v) Ejecución silenciosa, rápida


# ==============================================================================
# ESCENARIO 3: RL vs Heurísticas (1 RL + 2 Heurísticas)
# ==============================================================================

# Comando:
# python play_rl_vs_heuristics.py \
#     logs_ppo/risk_ppo_aggressive_final.zip \
#     ../ai/attacker_ai.py \
#     ../ai/random_ai.py \
#     -n 4 -w -v

# Explicación:
#   - Modelo RL agresivo
#   - IA Heurística: Atacante
#   - IA Heurística: Random
#   - -n 4 : 4 partidas donde cada uno es inicial = 12 partidas totales
#   - Muestra tipo de IA en estadísticas finales


# ==============================================================================
# ESCENARIO 4: RL vs RL vs Heurística (Mezcla)
# ==============================================================================

# Comando:
# python play_rl_vs_heuristics.py \
#     logs_ppo/model1.zip \
#     logs_ppo/model2.zip \
#     ../ai/random_ai.py \
#     -n 6 -w

# Explicación:
#   - 2 modelos RL + 1 heurística random
#   - 6 partidas por inicial = 18 partidas totales
#   - Los scripts detectan automáticamente si es .zip (RL) o .py (heurística)


# ==============================================================================
# ESCENARIO 5: Prueba rápida en modo verbose (sin guardar)
# ==============================================================================

# Comando:
# python play_rl_vs_rl.py logs_ppo/model1.zip logs_ppo/model2.zip -n 1 -v

# Explicación:
#   - -n 1 : Solo 2 partidas (una por cada modelo como inicial)
#   - -v : Ver todos los detalles de cada turno
#   - (sin -w) No guardar logs (para pruebas)


# ==============================================================================
# ESCENARIO 6: Torneo extenso (10 partidas por jugador)
# ==============================================================================

# Comando:
# python play_rl_vs_rl.py \
#     logs_ppo/aggressive.zip \
#     logs_ppo/defensive.zip \
#     logs_ppo/balanced.zip \
#     -n 10 -w

# Explicación:
#   - 3 modelos
#   - -n 10 : 10 partidas por modelo = 30 partidas totales
#   - Tarda bastante pero da estadísticas robustas


# ==============================================================================
# ESCENARIO 7: Comparar dos versiones del mismo modelo
# ==============================================================================

# Comando:
# python play_rl_vs_rl.py \
#     logs_ppo/MaskablePPO_5/risk_ppo_aggressive.zip \
#     logs_ppo/MaskablePPO_8/risk_ppo_aggressive.zip \
#     -n 10 -w -v

# Explicación:
#   - Versión antigua del modelo vs versión nueva
#   - Muchas partidas (-n 10) para ver cuál mejoró
#   - Análisis de mejora en las estadísticas finales


# ==============================================================================
# ESCENARIO 8: RL vs Todas las heurísticas disponibles
# ==============================================================================

# Comando:
# python play_rl_vs_heuristics.py \
#     logs_ppo/risk_ppo_aggressive_final.zip \
#     ../ai/attacker_ai.py \
#     ../ai/heuristic_ai.py \
#     ../ai/random_ai.py \
#     ../ai/donothing_ai.py \
#     -n 3 -w

# Explicación:
#   - 1 RL contra 4 heurísticas diferentes
#   - 5 jugadores totales × 3 inicios = 15 partidas
#   - Prueba el RL contra diferentes estrategias


# ==============================================================================
# ESCENARIO 9: Generación masiva de datos (sin verbose)
# ==============================================================================

# Comando:
# python play_rl_vs_rl.py \
#     logs_ppo/model1.zip \
#     logs_ppo/model2.zip \
#     logs_ppo/model3.zip \
#     -n 50 -w
#
# # Y en otra terminal simultáneamente:
# python play_rl_vs_heuristics.py \
#     logs_ppo/model4.zip \
#     ../ai/random_ai.py \
#     -n 50 -w

# Explicación:
#   - Dos procesos en paralelo
#   - Sin -v para máxima velocidad
#   - Generan 300 partidas totales
#   - Útil para análisis estadístico posterior


# ==============================================================================
# ESCENARIO 10: Reproducir una partida específica en GUI
# ==============================================================================

# Comando:
# # 1. Generar logs
# python play_rl_vs_rl.py model1.zip model2.zip -n 1 -w
#
# # 2. Ver qué logs se crearon
# ls -lrt logs/ | tail -5
#
# # 3. Reproducir en GUI
# cd ..
# python risk_game_viewer.py logs/RISKGAME_RLVRL_20241210-153045.log

# Explicación:
#   - Primero simulas
#   - Luego abres el log más reciente en la GUI
#   - Visualizas toda la partida paso a paso


# ==============================================================================
# TIPS Y TRUCOS
# ==============================================================================

"""
1. RUTAS RELATIVAS:
   Los scripts buscan modelos en:
   - ./logs_ppo/modelo.zip (desde PPO/)
   - ../ai/script.py (desde PPO/)
   
   Puedes usar rutas absolutas también:
   - /path/to/PPO/logs_ppo/modelo.zip

2. WILDCARDS (si tu shell lo permite):
   python play_rl_vs_rl.py logs_ppo/MaskablePPO_*.zip -n 2 -w
   Esto cargará todos los modelos que coincidan.

3. REDIRECCIONAR SALIDA:
   python play_rl_vs_rl.py ... -w > results.txt 2>&1
   Guarda toda la salida en un archivo.

4. EJECUTAR EN BACKGROUND (Linux/Mac):
   python play_rl_vs_rl.py ... -n 50 -w &
   Ejecuta en segundo plano, puedes cerrar la terminal.

5. TIMEOUT (si se cuelga):
   timeout 3600 python play_rl_vs_rl.py ...
   Mata el proceso después de 3600 segundos (1 hora).

6. MEDIR TIEMPO:
   time python play_rl_vs_rl.py ... -n 10 -w
   Muestra cuánto tardó la ejecución.
"""


# ==============================================================================
# BENCHMARKING
# ==============================================================================

"""
Para comparar sistemáticamente dos modelos:

1. Ejecuta múltiples veces (10+ partidas):
   python play_rl_vs_rl.py model1.zip model2.zip -n 10 -w

2. Anota las estadísticas finales:
   - % de victorias de model1 / (victorias totales)
   - Promedio de turnos

3. Invierte el orden y repite:
   python play_rl_vs_rl.py model2.zip model1.zip -n 10 -w
   
   Esto controla si el orden de turno afecta (en Risk, sí).

4. Compara heurísticas de referencia:
   python play_rl_vs_heuristics.py \
       model1.zip ../ai/random_ai.py \
       -n 10 -w
   
   Si model1 gana >80% contra random, está bien.
   Si model1 pierde contra heurísticas, necesita más entrenamiento.
"""


# ==============================================================================
# INTEGRACIÓN CON TRAIN_PPO.PY
# ==============================================================================

"""
Flujo típico de desarrollo:

1. Entrenar:
   python train_ppo.py
   → Genera logs_ppo/risk_ppo_aggressive_final.zip

2. Simular:
   python play_rl_vs_rl.py logs_ppo/risk_ppo_aggressive_final.zip ...
   → Genera logs/RISKGAME_*.log

3. Visualizar:
   python ../risk_game_viewer.py logs/RISKGAME_*.log
   → Ver la partida en GUI

4. Analizar:
   - ¿Qué hizo bien el RL?
   - ¿Dónde comete errores?
   - ¿Necesita más entrenamiento?

5. Volver a entrenar con ajustes:
   python train_ppo.py  # Con hiperparámetros diferentes
   → Nuevos logs_ppo/...

6. Repetir desde paso 2.
"""

print("Este archivo es referencia. No ejecutes directamente.")
print("Copia los comandos a tu terminal.")
