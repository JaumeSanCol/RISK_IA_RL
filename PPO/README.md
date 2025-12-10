# 🎮 Simulación de Risk: RL vs RL y RL vs Heurísticas

**Sistema completo para simular partidas de RISK con modelos entrenados y visualizarlas en la GUI.**

---

## 📍 ¿DÓNDE ESTOY? - Guía de Navegación

**Si estás en el directorio `PPO/`:**

1. **Primero lee:** `PPO/README_RL_SIMULATION.md` ← DOCUMENTACIÓN PRINCIPAL
2. **Luego ejecuta:** `python validate_installation.py all`
3. **Después copia un comando de:** `PPO/QUICK_EXAMPLES.py`
4. **Para entender internals:** `PPO/ARCHITECTURE.py`
5. **Si tienes problemas:** `PPO/validate_installation.py troubleshoot`

---

## 🚀 Inicio Rápido (5 minutos)

### 1. Valida tu instalación

```bash
cd PPO
python validate_installation.py all
```

### 2. Ejecuta una partida de prueba

```bash
# RL vs RL
python play_rl_vs_rl.py logs_ppo/modelo1.zip logs_ppo/modelo2.zip -n 1 -w -v

# O RL vs Heurísticas
python play_rl_vs_heuristics.py logs_ppo/modelo.zip ../ai/random_ai.py -n 1 -w -v
```

### 3. Visualiza en la GUI

```bash
cd ..
python risk_game_viewer.py logs/RISKGAME_RLVRL_*.log
```

---

## 📚 Documentación

| Archivo | Para Qué |
|---------|----------|
| `PPO/README_RL_SIMULATION.md` | **Guía completa del sistema** (START HERE) |
| `PPO/QUICK_EXAMPLES.py` | 10 comandos listos para copiar/pegar |
| `PPO/ARCHITECTURE.py` | Diagramas y flujos técnicos |
| `PPO/validate_installation.py` | Validar instalación y troubleshooting |
| `PPO/INDEX.txt` | Overview de todos los archivos |

---

## 📋 Archivos Nuevos Creados

### En `PPO/` directorio:

```
ppo_loader.py                    ← Cargador de modelos PPO
play_rl_vs_rl.py                ← Simulador: RL vs RL
play_rl_vs_heuristics.py        ← Simulador: RL vs Heurísticas
README_RL_SIMULATION.md          ← Documentación PRINCIPAL
QUICK_EXAMPLES.py               ← Ejemplos de comandos
ARCHITECTURE.py                 ← Documentación técnica
validate_installation.py         ← Script de validación
INDEX.txt                        ← Index de archivos
```

---

## ✨ Características

✅ **Enfrentar modelos RL entre sí**
- Soporta 2+ jugadores RL simultáneos
- Estadísticas automáticas de victorias

✅ **Enfrentar RL contra Heurísticas**
- Detección automática de tipo (`.zip` o `.py`)
- Estadísticas separadas por tipo de IA

✅ **Logs compatibles con GUI**
- Formato idéntico a `play_risk_ai.py`
- Visualización interactiva en `risk_game_viewer.py`

✅ **Debugging fácil**
- Modo verbose con detalles de cada turno
- Script de validación para solucionar problemas
- Manejo robusto de excepciones

---

## 🎯 Casos de Uso

### Caso 1: Comparar dos modelos RL

```bash
cd PPO
python play_rl_vs_rl.py \
    logs_ppo/aggressive.zip \
    logs_ppo/defensive.zip \
    -n 10 -w
```

**Resultado:** 20 partidas (10 por modelo como jugador inicial), estadísticas finales.

---

### Caso 2: Probar RL contra Heurísticas

```bash
cd PPO
python play_rl_vs_heuristics.py \
    logs_ppo/modelo.zip \
    ../ai/attacker_ai.py \
    ../ai/random_ai.py \
    -n 5 -w
```

**Resultado:** 15 partidas, tabla de victorias por tipo de IA.

---

### Caso 3: Reproducir en GUI

```bash
# 1. Generar logs
cd PPO
python play_rl_vs_rl.py logs_ppo/m1.zip logs_ppo/m2.zip -n 1 -w

# 2. Abrir en GUI
cd ..
python risk_game_viewer.py logs/RISKGAME_RLVRL_*.log
```

**Resultado:** Visualización paso a paso de la partida.

---

## ⚙️ Requisitos

### Instalados

```bash
pip install stable-baselines3[extra]
pip install sb3-contrib
pip install gymnasium
pip install numpy
```

### Estructura de directorios

```
RISK_IA_RL/
├── PPO/                        ← Estás aquí
│   ├── ppo_loader.py          ✓ Nuevo
│   ├── play_rl_vs_rl.py       ✓ Nuevo
│   ├── play_rl_vs_heuristics.py ✓ Nuevo
│   ├── README_RL_SIMULATION.md ✓ Nuevo
│   ├── logs_ppo/              ← Modelos .zip aquí
│   └── risk_gym_env.py        ✓ Debe existir
│
├── ai/                         ← IAs heurísticas (.py)
├── logs/                       ← Logs generados aquí
├── risktools.py              ← Motor de Risk
├── world.zip                 ← Tablero
└── risk_game_viewer.py       ← GUI
```

---

## 🔧 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: risktools` | Ejecuta desde `PPO/` |
| `FileNotFoundError: modelo no encontrado` | Verifica `ls logs_ppo/` |
| `ImportError: risk_gym_env` | Verifica que está en `PPO/` |
| `world.zip not found` | Debe estar en directorio raíz |
| Las IAs juegan inválido constantemente | Usa `-v` para debug, reentrana el modelo |

**Más detalles:** `python validate_installation.py troubleshoot`

---

## 📊 Flujo Completo

```
┌─────────────────────────────────────────────────────────┐
│ 1. Entrenar (train_ppo.py)                              │
│    → logs_ppo/*.zip                                     │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Simular (play_rl_vs_*.py)                            │
│    → logs/RISKGAME_*.log                                │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Visualizar (risk_game_viewer.py)                     │
│    → Reproducción interactiva en GUI                    │
└─────────────────────────────────────────────────────────┘
```

---

## 📖 Próximos Pasos

1. **Lee la documentación principal:**
   ```bash
   cd PPO
   cat README_RL_SIMULATION.md  # o abre en tu editor
   ```

2. **Valida tu sistema:**
   ```bash
   python validate_installation.py all
   ```

3. **Ejecuta tu primer ejemplo:**
   ```bash
   cat QUICK_EXAMPLES.py  # Copia un comando
   python play_rl_vs_rl.py [modelos] -n 1 -w -v
   ```

4. **Visualiza en GUI:**
   ```bash
   cd ..
   python risk_game_viewer.py logs/RISKGAME_*.log
   ```

---

## 🤔 Preguntas Frecuentes

**P: ¿Qué modelos necesito?**
R: Modelos `.zip` entrenados con `train_ppo.py` en `PPO/logs_ppo/`

**P: ¿Puedo enfrentar diferentes tipos de IAs?**
R: Sí, `play_rl_vs_heuristics.py` soporta mezcla libre de `.zip` (RL) y `.py` (heurística)

**P: ¿Los logs son compatibles con la GUI?**
R: Completamente. Formato idéntico a `play_risk_ai.py`

**P: ¿Puedo entrenar mientras simulo?**
R: Sí, usa diferentes procesos/terminales

**P: ¿Cómo mido el rendimiento?**
R: Las estadísticas finales muestran victorias, empates, timeouts y turnos promedio

**Más en:** `PPO/README_RL_SIMULATION.md` → FAQ

---

## 📞 Soporte

- **Documentación:** `PPO/README_RL_SIMULATION.md`
- **Ejemplos:** `PPO/QUICK_EXAMPLES.py`
- **Troubleshooting:** `python PPO/validate_installation.py troubleshoot`
- **Técnico:** `PPO/ARCHITECTURE.py`

---

## 📝 Notas

- **Compatibilidad:** 100% compatible con `risk_game_viewer.py` y `play_risk_ai.py`
- **No hay cambios:** Código existente sin modificaciones
- **Modular:** Puedes importar `PPOPlayer` en tus propios scripts
- **Robusto:** Manejo de excepciones y fallback a acciones aleatorias

---

**¡Listo para usar!** Comienza por: `cd PPO && python validate_installation.py all`
