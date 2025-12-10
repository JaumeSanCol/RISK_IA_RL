"""
ARQUITECTURA Y FLUJO DE DATOS
==============================

Este documento describe cómo interactúan los componentes del sistema.
"""

# ==============================================================================
# ARQUITECTURA DEL SISTEMA
# ==============================================================================

"""
┌────────────────────────────────────────────────────────────────────────────┐
│                        SIMULACIÓN DE RISK CON RL                            │
└────────────────────────────────────────────────────────────────────────────┘

NIVEL 1: ENTRENAMIENTO (Fuera del scope de estos scripts)
──────────────────────────────────────────────────────────
    ┌─────────────────────────────────────────┐
    │   train_ppo.py                          │
    │   (Entrena modelos con PPO)             │
    └────────────────────┬────────────────────┘
                         │
                         ↓
                    logs_ppo/*.zip
              (Modelos entrenados guardados)
    
    
NIVEL 2: CARGA DE MODELOS
──────────────────────────────────────────────────────────
    ┌──────────────────────────────────────┐
    │        ppo_loader.py                 │
    │  (Encapsula modelo PPO como IA)      │
    │                                      │
    │  • Carga archivo .zip                │
    │  • Convierte estado → observación    │
    │  • Genera máscaras de acciones       │
    │  • Decodifica predicción → acción    │
    │  • Maneja excepciones                │
    └──────────────────────────────────────┘


NIVEL 3: SIMULACIÓN DE PARTIDAS
──────────────────────────────────────────────────────────

    Flujo para play_rl_vs_rl.py:
    ───────────────────────────
    
    ┌─────────────────────────────────┐
    │  play_rl_vs_rl.py               │
    │                                 │
    │  1. Carga tablero (world.zip)  │
    │  2. Crea PPOPlayers             │
    │  3. Inicia bucle de partidas    │
    └────────────┬────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
    ┌──────────────┐  ┌──────────────┐
    │ PPOPlayer 1  │  │ PPOPlayer 2  │
    │ (Modelo RL1) │  │ (Modelo RL2) │
    └──────┬───────┘  └──────┬───────┘
           │                 │
           │   getAction()   │
           │                 │
        ┌──┴─────────────────┴──┐
        │                       │
        ↓                       ↓
    ┌─────────────────────────────────┐
    │    simulateAction()             │
    │    (risktools)                  │
    │                                 │
    │  • Ejecuta acción               │
    │  • Calcula nuevo estado         │
    │  • Maneja probabilidades        │
    └────────────┬────────────────────┘
                 │
                 ↓
           ¿Fin de juego?
           /    |    \
          /     |     \
      SÍ       NO     SÍ (timeout)
      │        │        │
      ▼        ▼        ▼
    [Victoria] [Siguiente turno] [Timeout]
      │        │                  │
      └───────┬┴──────────────────┘
              │
              ↓
        ┌──────────────────┐
        │ Guardar log      │
        │ (format original)│
        └──────────────────┘


    Flujo para play_rl_vs_heuristics.py:
    ────────────────────────────────────
    
    ┌───────────────────────────────────────┐
    │  play_rl_vs_heuristics.py             │
    │                                       │
    │  1. Factory.create_ai() para cada IA │
    │  2. Detecta si es .zip (RL) o .py   │
    │  3. Inicia bucle de partidas         │
    └────────────┬─────────────────────────┘
                 │
        ┌────────┼────────┐
        │        │        │
        ↓        ↓        ↓
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │PPOPlayer │ │Module.py │ │Module.py │
    │(Model.zip)│ │(Heur)    │ │(Heur)    │
    └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │
         └────┬──────┬┴──────┬─────┘
              │      │      │
              └──────┼──────┘
                     │
              Todos tienen
              getAction(state)
              método compatible
                     │
                     ↓
            (Mismo flujo que arriba)


NIVEL 4: GENERACIÓN DE LOGS
──────────────────────────────────────────────────────────

    ┌──────────────────────────────┐
    │  RiskState → RISKSTATE|...   │
    │  RiskAction → RISKACTION|... │
    │  RiskBoard → RISKBOARD|...   │
    │                              │
    │  (Métodos to_string())       │
    └────────────┬─────────────────┘
                 │
                 ↓
        ┌────────────────────┐
        │  logs/RISKGAME_*.log│
        │                    │
        │  Formato idéntico  │
        │  a play_risk_ai.py │
        └────────┬───────────┘
                 │
                 ↓


NIVEL 5: VISUALIZACIÓN
──────────────────────────────────────────────────────────

    ┌──────────────────────────────┐
    │  risk_game_viewer.py         │
    │                              │
    │  1. Lee RISKGAME_*.log       │
    │  2. Parsea estados/acciones  │
    │  3. Anima tablero            │
    │  4. Reproduce paso a paso    │
    └──────────────────────────────┘


NIVEL 6: ANÁLISIS ESTADÍSTICO
──────────────────────────────────────────────────────────

    ┌──────────────────────────────────┐
    │  Statistics class                │
    │  (en scripts de simulación)      │
    │                                  │
    │  • Cuenta victorias              │
    │  • Calcula promedio de turnos    │
    │  • Reporta timeouts              │
    │  • Genera tabla resumen          │
    └──────────────────────────────────┘
"""


# ==============================================================================
# FLUJO DE DATOS: UN TURNO EN DETALLE
# ==============================================================================

"""
┌──────────────────────────────────────────────────────────────────────────────┐
│                   DESGLOSE DE UN TURNO ÚNICO EN LA PARTIDA                   │
└──────────────────────────────────────────────────────────────────────────────┘

[1] OBTENER ESTADO ACTUAL
    │
    ├─→ RiskState (estado del juego completo)
    │   • Territorios y dueños
    │   • Soldados por territorio
    │   • Dinero de jugadores
    │   • Turno actual
    │   • Fase actual (Comprar_Soldados, Attack, Fortify, etc.)
    │
    └─→ current_player_index = 0 (quien tiene turno)

[2] OBTENER IA DEL JUGADOR ACTUAL (play_rl_vs_rl.py)
    │
    ├─→ ppo_players[0] = PPOPlayer instance
    │   • Modelo cargado: risk_ppo_aggressive.zip
    │   • Método: getAction(state)
    │
    └─→ IA heurística (play_rl_vs_heuristics.py)
        • Módulo .py cargado
        • Método: getAction(state)

[3] GENERAR OBSERVACIÓN (PPOPlayer.getAction)
    │
    ├─→ helper_env.state = state (copiar estado)
    │
    ├─→ obs = helper_env._get_obs()
    │   │
    │   └─→ Normalización:
    │       • [0:n_territories] → Dueños de territorios (0/1)
    │       • [n:2n] → Cantidad de ejércitos (normalizado 0-1)
    │       • [...] → Dinero, fase, datos globales
    │       • Resultado: vector np.float32[obs_dim]
    │
    └─→ obs.shape = (245,)  # o el tamaño configurado

[4] GENERAR MÁSCARA DE ACCIONES (PPOPlayer.getAction)
    │
    ├─→ actions_dict = risktools.getAllowedFaseActions(state)
    │   • Acciones válidas en esta fase
    │
    ├─→ action_mask = helper_env.action_masks()
    │   │
    │   └─→ Vector binario [49] con:
    │       • [0:7] → Tipo de acción (Attack, Place, etc.)
    │       • [7:49] → Territorios origen/destino
    │       • Ejemplo: [1, 0, 0, ..., 1, 1, ...] = acciones legales
    │
    └─→ Máscara usada para MaskablePPO

[5] PREDICCIÓN DEL MODELO (PPOPlayer.getAction)
    │
    ├─→ action_encoded, _ = model.predict(
    │       obs,
    │       action_masks=action_mask,
    │       deterministic=True
    │   )
    │
    ├─→ action_encoded = [type_idx, src_id, dst_id, amt_idx]
    │   • type_idx: 0-6 (tipo de acción)
    │   • src_id: 0-41 (territorio origen)
    │   • dst_id: 0-41 (territorio destino)
    │   • amt_idx: 0-9 (cantidad de unidades)
    │
    └─→ Modelo respeta máscara (no produce acciones ilegales)

[6] DECODIFICAR A RiskAction (PPOPlayer._decode_action_from_encoded)
    │
    ├─→ Buscar acción en actions_dict que coincida con:
    │   • type_idx → tipo correcto
    │   • src_id → territorio origen correcto
    │   • dst_id → territorio destino correcto
    │
    ├─→ Ejemplo resultado:
    │   RiskAction(
    │       type='Attack',
    │       from_territory='Canada',
    │       to_territory='Argentina',
    │       unidades=None
    │   )
    │
    └─→ action = RiskAction instance

[7] VALIDACIÓN DE ACCIÓN
    │
    ├─→ is_valid_action(state, action)?
    │
    ├─→ SÍ → Continuar a [8]
    │
    └─→ NO → Fallback a acción aleatoria
        └─→ time_left[player] = -1.0 (penalizar timeout)

[8] EJECUTAR ACCIÓN EN EL SIMULADOR (risktools.simulateAction)
    │
    ├─→ new_states, probabilities = simulateAction(state, action)
    │   │
    │   └─→ Procesar según tipo:
    │       • Attack → Tirar dados (múltiples resultados posibles)
    │       • Place → Colocar ejercitos
    │       • Fortify → Mover ejercitos
    │       • etc.
    │
    ├─→ Si len(new_states) > 1 (múltiples resultados):
    │   └─→ Seleccionar uno según probabilidades
    │
    └─→ state = new_states[0] (nuevo estado)

[9] GUARDAR EN LOG
    │
    ├─→ logfile.write(state.to_string())
    │
    ├─→ logfile.write(action.to_string())
    │   │
    │   └─→ Formato: RISKACTION|"type"|to_territory|from_territory|unidades|...|
    │
    └─→ Logs acumulan iteración a iteración

[10] VERIFICAR FIN DE JUEGO
    │
    ├─→ ¿state.turn_type == 'GameOver'?
    │   └─→ SÍ: Juego terminó, registrar ganador
    │
    ├─→ ¿action_count > action_limit?
    │   └─→ SÍ: Empate, registrar
    │
    ├─→ ¿time_left[player] < 0?
    │   └─→ SÍ: Timeout, penalizar jugador
    │
    └─→ NO: Continuar a siguiente turno (vuelta a [1])

[11] SIGUIENTE TURNO
    │
    └─→ nextPlayer(state)  # Avanza al siguiente jugador
        └─→ Vuelve a [1]
"""


# ==============================================================================
# ESTRUCTURA DE DATOS: RiskState
# ==============================================================================

"""
RiskState (estado del tablero):
┌─────────────────────────────────────┐
│                                     │
│  state.current_player       = 0     │ Índice del jugador actual (0-3)
│  state.turn_type            = 'X'  │ 'Comprar_Soldados', 'Attack', etc.
│  state.fase                 = 'Y'  │ 'fase_0', 'fase_1', etc.
│                                     │
│  state.owners[]             = [...] │ owner[i] = dueño del territorio i
│  state.armies[]             = [...] │ armies[i] = ejércitos en territorio i
│                                     │
│  state.players[i]           = {...} │ RiskPlayer
│      .name                  = 'X'  │ "Castilla"
│      .economy               = 100   │ Dinero
│      .free_armies           = 10    │ Ejércitos sin colocar
│      .happiness             = 50    │ Felicidad
│      .development           = 0.5   │ Desarrollo
│      .game_over             = False │ Si está derrotado
│      .conquered_territory   = True  │ Si conquistó algo este turno
│                                     │
│  state.board                = {...} │ RiskBoard
│      .territories[]         = [...] │ Lista de territorios
│      .continents[]          = [...] │ Lista de continentes
│      .territory_to_id       = {...} │ Mapeo: nombre → índice
│                                     │
└─────────────────────────────────────┘
"""


# ==============================================================================
# DEPENDENCIAS Y IMPORTS
# ==============================================================================

"""
play_rl_vs_rl.py
└── ppo_loader.py
    ├── sb3_contrib.MaskablePPO (modelo)
    ├── risk_gym_env.py (para métodos auxiliares)
    └── risktools (interfaz de Risk)
        ├── RiskAction
        ├── RiskState
        ├── RiskPlayer
        ├── RiskBoard
        ├── simulateAction()
        ├── getAllowedFaseActions()
        └── getInitialState()

play_rl_vs_heuristics.py
├── ppo_loader.py (para modelos RL)
├── AIFactory
│   ├── PPOPlayer (para .zip)
│   └── Módulos .py dinámicos (para heurísticas)
└── risktools (mismo que arriba)
"""


# ==============================================================================
# CONFIGURACIÓN DE HIPERPARÁMETROS
# ==============================================================================

"""
Valores actuales (se pueden cambiar):

TIEMPOS:
  time_left[i] = 600.0        # 10 minutos por jugador
  action_limit = 5000         # Máximo 5000 acciones por partida

ESTRATEGIAS RL (train_ppo.py):
  multiplicador = {
    "standard": 2.5,
    "aggressive": 5,           # RL agresivo gana más rápido
    "defensive": 8,            # RL defensivo se enfoca en defensa
    "capitalist": 1.5          # RL capitalista busca dinero
  }

MODELOS:
  n_players = 4               # Cambiar para 2, 3, 5, etc. jugadores
  obs_dim = 245               # Tamaño del vector de observación
  action_space = [7, 42, 42, 10]  # MultiDiscrete
  
ESTADÍSTICAS:
  stats.winners[i]            # Contador de victorias por jugador
  stats.total_turns           # Suma de turnos de todas las partidas
  stats.games_played          # Contador de partidas

Cambiar estos valores afecta:
  • Velocidad de ejecución
  • Complejidad de decisiones del RL
  • Equilibrio entre IAs
  • Estadísticas finales
"""

print("Referencia de arquitectura completada.")
