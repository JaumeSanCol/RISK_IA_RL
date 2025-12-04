import sys
import os
import risktools

# Añadir carpeta ai/ al path para importar el jugador
current_dir = os.getcwd()
ai_dir = os.path.abspath(os.path.join(current_dir, '../ai'))
sys.path.append(ai_dir)

print(f"Buscando ppo_player en: {ai_dir}")

try:
    import ppo_player
    print("Módulo ppo_player importado correctamente.")
except ImportError as e:
    print(f"Error importando ppo_player: {e}")
    print("Asegúrate de que el archivo 'ppo_player.py' existe en 'RISK-AI/ai/'.")
    exit()

# --- CREAR ESTADO DUMMY ---
print("Creando estado de prueba...")
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
world_path = os.path.join(parent_dir, "world.zip")

board = risktools.loadBoard(world_path)
# Config manual para evitar error GUI
board.set_turn_in_values([4,6,8]) 
board.set_increment_value(5)

# Crear un jugador de prueba
p1 = risktools.RiskPlayer("TestBot", 0, 0, False, 50, 50, 0.1)
# Parche atributos
p1.freeArmies = 0
p1.conqueredTerritory = False

board.add_player(p1)
state = risktools.getInitialState(board)

# Forzar una fase donde seguro hay acciones (ej. Comprar con dinero)
state.fase = "fase_1"
state.turn_type = "Comprar_Soldados"

print("\n--- INICIANDO TEST DE DECISIÓN ---")
try:
    # Pedimos una acción a la IA
    action = ppo_player.getAction(state)
    
    if action:
        print(f"ÉXITO! La IA devolvió una acción válida.")
        print(f"Detalle: {action.to_string()}")
    else:
        print("La IA devolvió None (¿Quizás el modelo no cargó?).")
        
except Exception as e:
    print(f"ERROR EJECUTANDO LA IA: {e}")
    import traceback
    traceback.print_exc()