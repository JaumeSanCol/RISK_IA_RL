# Simulación de Partidas: RL vs RL y RL vs Heurísticas

**Documentación completa para simular partidas de RISK con modelos entrenados y visualizarlas en la GUI.**

---

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Componentes](#componentes)
3. [Instalación](#instalación)
4. [Uso](#uso)
5. [Ejemplos Prácticos](#ejemplos-prácticos)
6. [Formato de Logs](#formato-de-logs)
7. [Visualización en GUI](#visualización-en-gui)
8. [Troubleshooting](#troubleshooting)

---

## Descripción General

Este conjunto de herramientas permite:

✅ **Enfrentar modelos RL entre sí** y generar logs para visualización  
✅ **Enfrentar modelos RL contra IAs heurísticas** (clásicas)  
✅ **Generar logs en formato compatible** con `risk_game_viewer.py`  
✅ **Recopilar estadísticas** de victorias y turnos  
✅ **Modo verbose** para debugging  

### Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Entrenar modelos PPO (train_ppo.py)                      │
│    → Genera archivos .zip en logs_ppo/                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Simular partidas (play_rl_vs_rl.py o                     │
│    play_rl_vs_heuristics.py)                                │
│    → Genera logs en logs/RISKGAME_*.log                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Visualizar en GUI (risk_game_viewer.py)                  │
│    → Carga y reproduce logs de partidas                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes

### 1. **`ppo_loader.py`** - Cargador de Modelos PPO

Proporciona la clase `PPOPlayer` que encapsula un modelo PPO entrenado.

**Responsabilidades:**
- Cargar archivos `.zip` del modelo
- Convertir estados de Risk a observaciones normalizadas
- Generar máscaras de acciones válidas
- Decodificar predicciones del modelo a `RiskAction`
- Manejar fallbacks en caso de error

**API:**
```python
from ppo_loader import PPOPlayer

# Crear una IA RL
ppo_ai = PPOPlayer(
    model_path="logs_ppo/risk_ppo_aggressive_final.zip",
    player_name="RL-Agresivo"
)

# Usar en partida
state = risktools.getInitialState(board)
action = ppo_ai.getAction(state)  # Devuelve RiskAction
```

---

### 2. **`play_rl_vs_rl.py`** - Simulador RL vs RL

Enfrenta múltiples modelos PPO entre sí.

**Características:**
- Soporta 2+ jugadores RL
- Genera logs automáticos
- Estadísticas de victorias
- Modo verbose para debugging
- Compatible con GUI

**Uso:**
```bash
python play_rl_vs_rl.py <modelo1.zip> <modelo2.zip> [modelo3.zip ...] [opciones]
```

**Opciones:**
```
-n, --num N          Número de partidas donde cada RL es inicial (default: 5)
-w, --write          Guardar logs en logs/
-v, --verbose        Mostrar detalles durante ejecución
```

---

### 3. **`play_rl_vs_heuristics.py`** - Simulador RL vs Heurísticas

Enfrenta modelos PPO contra IAs heurísticas (y otros PPOs).

**Características:**
- Mezcla libre de RL y heurísticas
- Detección automática de tipo por extensión (`.zip` o `.py`)
- Estadísticas separadas por tipo de IA
- Modo verbose

**Uso:**
```bash
python play_rl_vs_heuristics.py <ia1> <ia2> [ia3 ...] [opciones]
```

Donde cada `<ia>` es:
- `ruta/modelo.zip` → Modelo PPO
- `ruta/ai.py` → IA heurística

**Opciones:**
```
-n, --num N          Número de partidas donde cada IA es inicial (default: 5)
-w, --write          Guardar logs en logs/
-v, --verbose        Mostrar detalles durante ejecución
```

---

## Instalación

### Requisitos Previos

```bash
pip install stable-baselines3[extra]
pip install sb3-contrib
pip install gymnasium
pip install numpy
```

### Estructura de Directorios

```
RISK_IA_RL/
├── PPO/
│   ├── ppo_loader.py              ← Nuevo
│   ├── play_rl_vs_rl.py            ← Nuevo
│   ├── play_rl_vs_heuristics.py    ← Nuevo
│   ├── logs_ppo/
│   │   ├── risk_ppo_aggressive_final.zip
│   │   ├── risk_ppo_defensive_final.zip
│   │   └── ...
│   └── risk_gym_env.py
├── ai/
│   ├── attacker_ai.py
│   ├── random_ai.py
│   ├── heuristic_ai.py
│   └── ...
├── logs/                          ← Logs generados aquí
│   └── RISKGAME_*.log
├── risktools.py
├── play_risk_ai.py               ← Script antiguo (para referencia)
└── risk_game_viewer.py           ← GUI para visualizar
```

---

## Uso

### Escenario 1: RL vs RL

Enfrenta 2 modelos entrenados en 3 partidas cada uno como jugador inicial.

```bash
cd PPO
python play_rl_vs_rl.py \
    logs_ppo/risk_ppo_aggressive_final.zip \
    logs_ppo/risk_ppo_defensive_final.zip \
    -n 3 \
    -w \
    -v
```

**Salida esperada:**
```
[CARGA] Cargando tablero...
[CARGA] Cargando 2 modelos PPO...

  [PPOPlayer] Modelo cargado: Castilla
  [PPOPlayer] Modelo cargado: Aragón

[TORNEO] Iniciando torneo de 3 partidas...

[PARTIDA 1/3] Orden: ['Castilla', 'Aragón']
[TURNO 0] Jugador: Castilla | Tipo: Comprar_Soldados | Tiempo: 600.0s
  Acción: Place IN: Argentina NUM: 2
  Tiempo: 0.052s
...
[FIN] Castilla ganó la partida!
  Log guardado: logs/RISKGAME_RLVRL_20241210-153045.log

[ESTADÍSTICAS DEL TORNEO RL vs RL]
  PARTIDAS JUGADAS  : 3
  VICTORIAS NORMALES: 2
  EMPATES           : 1
  TURNOS PROMEDIO   : 45.33
  
  VICTORIAS POR JUGADOR:
    Castilla: 2 victorias
    Aragón: 1 victorias
```

---

### Escenario 2: RL vs Heurísticas

Enfrenta 1 modelo RL contra 2 IAs clásicas.

```bash
cd PPO
python play_rl_vs_heuristics.py \
    logs_ppo/risk_ppo_aggressive_final.zip \
    ../ai/attacker_ai.py \
    ../ai/random_ai.py \
    -n 4 \
    -w \
    -v
```

**Salida esperada:**
```
[CARGA] Cargando tablero...
[CARGA] Cargando 3 IAs (PPO + Heurísticas)...

  ✓ PPO cargado: Prusia
  ✓ Heurística cargada: Baviera (attacker_ai)
  ✓ Heurística cargada: Bohemia (random_ai)

[TORNEO] Iniciando torneo de 4 partidas...

[PARTIDA 1/4] Orden: ['Prusia', 'Baviera', 'Bohemia']
  1. Prusia (PPO)
  2. Baviera (Heuristic)
  3. Bohemia (Heuristic)

[TURNO 0] Prusia (PPO) | Tipo: Comprar_Soldados | Tiempo: 600.0s
...
[FIN] Prusia ganó!
  Log guardado: logs/RISKGAME_RLVSHEUR_20241210-153125.log

[ESTADÍSTICAS DEL TORNEO RL vs HEURÍSTICAS]
  PARTIDAS JUGADAS  : 4
  VICTORIAS NORMALES: 3
  EMPATES           : 1
  TURNOS PROMEDIO   : 48.50
  
  VICTORIAS POR JUGADOR:
    [PPO       ] Prusia: 3 victorias
    [Heuristic] Baviera: 1 victorias
    [Heuristic] Bohemia: 0 victorias
```

---

### Escenario 3: Solo generación de logs (sin verbose)

```bash
cd PPO
python play_rl_vs_rl.py \
    logs_ppo/risk_ppo_aggressive.zip \
    logs_ppo/risk_ppo_defensive.zip \
    -n 10 \
    -w
```

Se ejecutará silenciosamente y guardará 10 partidas en `logs/`.

---

## Ejemplos Prácticos

### Ejemplo 1: Comparar 3 modelos diferentes

```bash
python play_rl_vs_rl.py \
    logs_ppo/MaskablePPO_5/risk_ppo_aggressive.zip \
    logs_ppo/MaskablePPO_6/risk_ppo_defensive.zip \
    logs_ppo/MaskablePPO_7/risk_ppo_balanced.zip \
    -n 6 -w
```

Esto ejecutará **18 partidas** en total (6 por modelo como jugador inicial) y las guardará en logs/.

---

### Ejemplo 2: RL vs Heurísticas con múltiples IAs

```bash
python play_rl_vs_heuristics.py \
    logs_ppo/risk_ppo_aggressive_final.zip \
    ../ai/attacker_ai.py \
    ../ai/heuristic_ai.py \
    ../ai/random_ai.py \
    -n 5 -w -v
```

**Resultado:** Un torneo de 5×4=20 partidas con 1 RL vs 3 heurísticas.

---

### Ejemplo 3: Prueba rápida en modo verbose

```bash
python play_rl_vs_heuristics.py \
    logs_ppo/risk_ppo_aggressive_final.zip \
    ../ai/random_ai.py \
    -n 1 -v
```

Ejecuta **1 partida** con máximo detalle, sin guardar logs.

---

## Formato de Logs

Los logs se generan en formato **idéntico a `play_risk_ai.py`** para compatibilidad total con la GUI.

### Estructura del Archivo Log

```
RISKBOARD|...
RISKSTATE|...
RISKACTION|"Attack"|"Argentina"|"Brasil"|null|null|null
RISKSTATE|...
RISKACTION|"Fortify"|null|"Canada"|5|null|null
RISKSTATE|...
...
RISKSTATE|...
RISKRESULT|NombreCampeón,1|OtroJugador,0|..."Game End"|Turn Count = 45
```

### Campos de Acción

```python
RISKACTION | type | to_territory | from_territory | unidades | to_player | from_player
```

**Ejemplo descodificado:**
- `type`: "Attack", "Fortify", "Place", "Occupy", "Pasar", etc.
- `to_territory`: ID o nombre del territorio destino
- `from_territory`: ID o nombre del territorio origen
- `unidades`: Número de unidades involucradas
- `to_player`: ID del jugador destino (para acciones entre jugadores)
- `from_player`: ID del jugador origen

---

## Visualización en GUI

Una vez generados los logs, puedes visualizarlos en la GUI:

```bash
python risk_game_viewer.py logs/RISKGAME_RLVRL_20241210-153045.log
```

La GUI reproducirá la partida paso a paso, mostrando:
- Estado del tablero después de cada acción
- Soldados y dinero de cada jugador
- Turno y tipo de acción
- Historial completo de la partida

---

## Troubleshooting

### Error: `FileNotFoundError: Modelo no encontrado`

**Causa:** La ruta del modelo es incorrecta.

**Solución:**
```bash
# Asegúrate de que el archivo .zip existe
ls logs_ppo/

# Usa ruta relativa desde PPO/ o ruta absoluta
python play_rl_vs_rl.py logs_ppo/modelo.zip -w
```

---

### Error: `ModuleNotFoundError: No module named 'risktools'`

**Causa:** Ejecutas el script desde fuera del directorio `PPO/`.

**Solución:**
```bash
cd PPO
python play_rl_vs_rl.py [modelos] -w
```

O ajusta `sys.path` en el script.

---

### Error: `ImportError: cannot import name 'RiskTotalControlEnv'`

**Causa:** El archivo `risk_gym_env.py` no está en el directorio `PPO/`.

**Solución:**
```bash
# Verifica que exista
ls PPO/risk_gym_env.py

# Si no existe, cópialo desde el backup
cp PPO/backup_ia/risk_gym_env.py PPO/
```

---

### Las IAs juegan acciones inválidas constantemente

**Causa:** El modelo no se cargó correctamente o hay incompatibilidad.

**Solución:**
1. Recarga el modelo desde cero
2. Prueba en modo `deterministic=False` en `ppo_loader.py` para exploración
3. Revisa que el modelo se entrenó con `n_players=N` igual al número de jugadores

---

### Logs muy cortos (solo 1-2 turnos)

**Causa:** El modelo colapsa o hay error en la decodificación de acciones.

**Solución:**
```bash
# Prueba con -v para ver dónde falla
python play_rl_vs_rl.py logs_ppo/modelo.zip -n 1 -v

# Si hay muchos "ADVERTENCIA acción inválida", el modelo necesita reentrenamiento
```

---

### ¿Cómo aumentar velocidad de simulación?

Edita en `play_rl_vs_rl.py`:

```python
# Antes (verbose)
python play_rl_vs_rl.py modelo1.zip modelo2.zip -n 100 -w

# Después (sin verbose, múltiples en paralelo si tienes CPU)
python play_rl_vs_rl.py modelo1.zip modelo2.zip -n 100 -w &
python play_rl_vs_rl.py modelo3.zip modelo4.zip -n 100 -w &
```

---

## API Reference

### PPOPlayer

```python
class PPOPlayer:
    def __init__(self, model_path: str, player_name: str = "RL-Agent", device: str = 'cpu')
    def getAction(self, state: RiskState) -> RiskAction
```

**Métodos privados (uso interno):**
- `_resolve_model_path(model_path)` - Resuelve rutas relativas
- `_load_model()` - Carga el archivo .zip
- `_decode_action_from_encoded(state, action)` - Decodifica predicción
- `_get_random_action(state)` - Fallback aleatorio

---

## Configuración Avanzada

### Cambiar Tiempo Límite por Jugador

En `play_rl_vs_rl.py`, línea ~185:

```python
time_left = {i: 300.0 for i in range(len(player_names))}  # 5 minutos en lugar de 10
```

### Cambiar Límite de Acciones

En `play_rl_vs_rl.py`, línea ~186:

```python
action_limit = 10000  # Permitir más turnos
```

### Usar GPU para Inferencia

En `ppo_loader.py`, línea ~50:

```python
ppo = PPOPlayer(model_path, device='cuda')  # En lugar de 'cpu'
```

---

## Preguntas Frecuentes

**P: ¿Puedo entrenar mientras simulo?**  
R: Sí, los scripts de simulación no interfieren con `train_ppo.py`. Usa diferentes procesos/terminales.

**P: ¿Los logs son deterministicos?**  
R: Casi (determinstic=True en modelo), pero algunas acciones tienen probabilidades inherentes en Risk (dados de batalla).

**P: ¿Cómo comparo dos modelos?**  
R: Enfréntalos muchas veces: `python play_rl_vs_rl.py model1.zip model2.zip -n 50 -w`

**P: ¿Debo usar nombres específicos para jugadores?**  
R: No, se asignan automáticamente de una lista de reinos reales. Puedes editarla en el script.

---

## Notas Finales

- Los logs son **100% compatibles** con `risk_game_viewer.py`
- La velocidad depende de tu CPU; modelos complejos son más lentos
- Para análisis estadístico, extrae datos de la salida del script o parsea los logs
- Puedes combinar RL + heurísticas en `play_rl_vs_heuristics.py` sin límite

---

**Última actualización:** Diciembre 2024  
**Autor:** Sistema de Simulación RL para RISK
