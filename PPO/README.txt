# RISK-AI: Proyecto de Aprendizaje por Refuerzo 🤖🎲

Este proyecto implementa un agente de Inteligencia Artificial capaz de aprender a jugar al juego de mesa RISK utilizando **Proximal Policy Optimization (PPO)** con máscaras de acción inválida.

La IA no solo decide a dónde mover tropas, sino que gestiona la economía (comprar soldados, invertir) y las fases del turno.

## Estructura del Proyecto

- **`risktools.py`**: Motor lógico del juego original (reglas, estados, simulador).
- **`ai/`**: Carpeta con los agentes (bots).
  - `ppo_player.py`: **¡NUEVO!** El adaptador que conecta nuestra IA entrenada con el juego gráfico.
  - `random_ai.py`: Bot aleatorio básico.
- **`PPO/`**: Carpeta de entrenamiento y RL.
  - `risk_gym_env.py`: El entorno compatible con Gymnasium (el "traductor" Juego <-> IA).
  - `train_ppo.py`: Script para entrenar nuevos modelos.
  - `logs_ppo/`: Aquí se guardan los modelos `.zip` entrenados.

## Instalación

Necesitas un entorno con Python 3.10+. Instala las dependencias:

```bash
pip install gymnasium stable-baselines3 sb3-contrib numpy tensorboard