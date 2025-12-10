# Análisis del Log de Simulación RL vs RL

**Archivo analizado:** `RISKGAME_RLVRL_20251210-201141.log`

## Resumen Ejecutivo

✅ **Lo que funciona correctamente:**
- La simulación se ejecuta sin errores
- Los logs se generan en formato válido
- Las acciones se registran apropiadamente
- La lógica de asignación inicial de territorios funciona

❌ **Problemas encontrados:**

### 1. **Renombrado de Jugador Derrotado (CRÍTICO)**
**Síntoma:** Un jugador se llama "Muerto" en lugar de su nombre original.

**Evidencia en el log:**
```
Línea ~674:
RISKSTATE|"Muerto"$0$0$false$1673.6$0$0.1$true;"Rusia"$1$0$false$448.6$11$0.0$false;...
                                                                   ↑
                                          defeated=true (jugador eliminado)

Línea final:
RISKRESULT|Muerto,0.5|Rusia,0.5|Action Limit Reached|Turn Count = 154
```

**Causa probable:**
- En `clases/player.py` o en `risktools.py`, cuando un jugador es eliminado, su nombre se cambia a "Muerto"
- Esto afecta los logs, mostrando "Muerto" en lugar del nombre real del IA

**Impacto:**
- Los logs no reflejan correctamente qué jugador RL fue eliminado
- Hace imposible rastrear qué IA ganó/perdió en las estadísticas

**Solución recomendada:**
- NO cambiar el nombre del jugador en el objeto RiskPlayer
- Usar un campo `defeated=true` para marcar eliminación, pero mantener el nombre original
- Modificar formato del log para incluir `defeated=true` sin cambiar nombre

### 2. **Resultado de Empate por Limit de Acciones (IMPORTANTE)**

**Síntoma:** Partida termina con empate (0.5, 0.5) después de 5000 acciones ejecutadas.

**Evidencia:**
```
RISKRESULT|Muerto,0.5|Rusia,0.5|Action Limit Reached|Turn Count = 154
```

**Análisis:**
- 154 turnos / 2 jugadores = ~77 acciones por jugador en promedio
- 5000 acciones límite permitidas con 77 acciones por turno = sistema de acción está funcionando rápido
- **El problema es que sin ganador claro, ambos obtienen 0.5 puntos**

**Causa probable:**
- Los modelos RL entrenados no tienen comportamiento suficientemente agresivo
- Estrategia defensiva muy fuerte vs ofensiva débil
- Ambos IAs están igualados en defensa, ninguno logra breakthrough

**Impacto en entrenamiento:**
- Empates frecuentes reducen señal de aprendizaje
- Ambos modelos reciben recompensa similar aunque uno debería perder
- Puede causar convergencia débil

### 3. **Anomalía en Contador de Turnos (MENOR)**

**Síntoma:** En log `RISKGAME_RLVRL_20251210-201256.log`, el contador de turnos salta de 12 a 1.

**Evidencia:**
```
Línea 220: ...|"fase_3"|...|...|Turn Count = 12
Línea 222: ...|"fase_1"|...|...|Turn Count = 1  ← Debería ser 13
```

**Causa probable:**
- Posible reinicio incorrecto de partida en el loop de torneo
- O la función `play_match` no gestiona correctamente el reset entre partidas

**Impacto:**
- Logs confusos para análisis post-mortem
- Posible bug en lógica de torneos multi-partida

---

## Datos Estadísticos

| Métrica | Valor |
|---------|-------|
| Turnos Totales | 154 |
| Límite de Acciones | 5000 |
| Resultado | Empate (0.5 cada uno) |
| Primera partida completada | Sí |

## Recomendaciones Prioritarias

### 🔴 Prioridad Crítica
1. **Fijar el problema de "Muerto"**: Mantener nombre original del jugador incluso cuando defeated=true
   - Archivo: `clases/player.py` 
   - Buscar dónde se asigna `.name = "Muerto"`

### 🟡 Prioridad Alta  
2. **Investigar estrategia defensiva excesiva**:
   - Revisar recompensas en `risk_gym_env.py`
   - Evaluar si el modelo está siendo demasiado conservador
   - Posible falta de penalización a inactividad/defensa pura

3. **Validar contador de turnos**: 
   - Revisar función `play_match()` en `play_rl_vs_rl.py`
   - Asegurar reset correcto entre partidas

### 🟢 Prioridad Media
4. **Aumentar agresividad del modelo**:
   - Ajustar reward shaping durante entrenamiento
   - Penalizar defender sin atacar
   - Recompensar expansión territorial

---

## Próximos Pasos

1. **Inmediato:** Localizar y fijar el rename a "Muerto"
2. **Luego:** Ejecutar prueba simple con 1 partida para verificar nombres
3. **Después:** Revisar recompensas en environment gym
4. **Final:** Re-entrenar o ajustar modelos para mayor agresividad

