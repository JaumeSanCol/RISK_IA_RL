"""
Cargador de Modelos PPO para Risk - Wrapper de IAs
=====================================================

Este módulo proporciona la clase PPOPlayer que encapsula un modelo entrenado
de MaskablePPO para usarlo como una IA compatible con el sistema de Risk.

La clase actúa como un puente entre:
  - El modelo PPO entrenado (que trabaja con observaciones y máscaras de acción)
  - El sistema de Risk (que trabaja con objetos RiskAction)

Permite usar modelos RL en:
  - play_rl_vs_rl.py (RL vs RL)
  - play_rl_vs_heuristics.py (RL vs Heurísticas)
  - Cualquier juego que use la interfaz getAction(state)
"""

import os
import sys
import numpy as np
import itertools
from pathlib import Path

# Configurar rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from sb3_contrib import MaskablePPO
import risktools
from risk_gym_env import RiskTotalControlEnv


class PPOPlayer:
    """
    Encapsula un modelo PPO entrenado para usarlo como IA en Risk.
    
    Ejemplos de uso:
    ----------------
    # Crear una IA RL
    ppo_ai = PPOPlayer(
        model_path="logs_ppo/risk_ppo_aggressive_final.zip",
        player_name="RL-Agresivo"
    )
    
    # Usar en una partida
    state = risktools.getInitialState(board)
    action = ppo_ai.getAction(state)
    
    # En play_rl_vs_rl.py se carga automáticamente pasando la ruta del modelo
    """
    
    def __init__(self, model_path, player_name="RL-Agent", device='cpu'):
        """
        Inicializa el cargador de modelo PPO.
        
        Parámetros:
        -----------
        model_path : str
            Ruta absoluta o relativa al archivo .zip del modelo entrenado.
            Ejemplo: "logs_ppo/risk_ppo_aggressive_final.zip"
            o "PPO/logs_ppo/risk_ppo_aggressive_final.zip"
        
        player_name : str
            Nombre que llevará este jugador en la partida.
        
        device : str
            Dispositivo donde cargar el modelo: 'cpu' o 'cuda'
        
        Raises:
        -------
        FileNotFoundError
            Si no encuentra el archivo del modelo.
        """
        self.player_name = player_name
        self.device = device
        self.model = None
        self.helper_env = None
        
        # Resolver ruta del modelo
        self.model_path = self._resolve_model_path(model_path)
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Modelo no encontrado: {self.model_path}\n"
                f"Asegúrate de que el archivo .zip existe en la ruta especificada."
            )
        
        # Cargar modelo
        self._load_model()
        
    def _resolve_model_path(self, model_path):
        """
        Resuelve la ruta del modelo a una ruta absoluta.
        
        Soporta rutas relativas desde:
        1. El directorio actual
        2. El directorio PPO/
        3. El directorio raíz del proyecto
        """
        # Si es ruta absoluta, devolverla tal cual
        if os.path.isabs(model_path):
            return model_path
        
        # Intentar resolver desde directorio actual
        if os.path.exists(model_path):
            return os.path.abspath(model_path)
        
        # Intentar resolver desde PPO/
        ppo_path = os.path.join(parent_dir, "PPO", model_path)
        if os.path.exists(ppo_path):
            return ppo_path
        
        # Intentar resolver desde parent_dir/model_path
        parent_path = os.path.join(parent_dir, model_path)
        if os.path.exists(parent_path):
            return parent_path
        
        # Si no existe, devolver el original (para mensaje de error claro)
        return os.path.abspath(model_path)
    
    def _load_model(self):
        """Carga el modelo PPO desde el archivo .zip"""
        try:
            self.model = MaskablePPO.load(self.model_path, device=self.device)
            
            # Crear entorno auxiliar para funciones helper
            # (se usa solo para métodos auxiliares, no para paso por paso)
            self.helper_env = RiskTotalControlEnv()
            
            print(f"[PPOPlayer] Modelo cargado exitosamente: {self.player_name}")
            print(f"[PPOPlayer] Ruta: {self.model_path}")
            
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el modelo: {e}")
            raise
    
    def getAction(self, state, time_left=None):
        """
        Devuelve la siguiente acción que debe ejecutar este jugador.
        
        Esta función es llamada por play_rl_vs_rl.py y play_rl_vs_heuristics.py
        en el mismo punto donde se llamaría getAction de una IA heurística.
        
        Parámetros:
        -----------
        state : RiskState
            El estado actual del juego desde la perspectiva del jugador actual.
        
        time_left : float, opcional
            Tiempo disponible (no se usa en RL, pero se mantiene para compatibilidad).
        
        Devuelve:
        ---------
        RiskAction
            La acción que debe ejecutar el modelo.
        """
        
        if self.model is None:
            print("[WARNING] Modelo no cargado, devolviendo acción aleatoria.")
            return self._get_random_action(state)
        
        try:
            # 1. Sincronizar estado del entorno auxiliar
            self.helper_env.state = state
            self.helper_env.board = state.board
            self.helper_env.player_idx = state.current_player
            self.helper_env.n_territories = len(state.board.territories)
            
            # 2. Obtener observación normalizada
            obs = self.helper_env._get_obs()
            
            # 3. Obtener máscara de acciones válidas
            action_mask = self.helper_env.action_masks()
            
            # 4. Predicción del modelo
            # MaskablePPO requiere: observación + máscara de acciones
            action_encoded, _ = self.model.predict(
                obs, 
                action_masks=action_mask,
                deterministic=True  # Modo determinista (greedy, no exploratorio)
            )
            
            # 5. Decodificar la acción de índices numéricos a RiskAction
            action_decoded = self._decode_action_from_encoded(state, action_encoded)
            
            if action_decoded is None:
                # Fallback: acción aleatoria
                return self._get_random_action(state)
            
            return action_decoded
            
        except Exception as e:
            print(f"[ERROR] Error en PPOPlayer.getAction: {e}")
            import traceback
            traceback.print_exc()
            return self._get_random_action(state)
    
    def _decode_action_from_encoded(self, state, action_encoded):
        """
        Decodifica el vector numérico devuelto por el modelo a un RiskAction.
        
        action_encoded es un MultiDiscrete de 4 valores:
        - Índice 0: Tipo de acción (0-6)
        - Índice 1: Territorio origen (0-41)
        - Índice 2: Territorio destino (0-41)
        - Índice 3: Cantidad (0-9)
        """
        
        type_idx, src_id, dst_id, amt_idx = action_encoded
        
        # Usar el método auxiliar del entorno
        best_match = self.helper_env._decode_action(
            int(type_idx), 
            int(src_id), 
            int(dst_id), 
            int(amt_idx)
        )
        
        return best_match
    
    def _get_random_action(self, state):
        """
        Fallback: devuelve una acción aleatoria válida.
        
        Se usa cuando el modelo falla o no se puede cargar.
        """
        actions_dict = risktools.getAllowedFaseActions(state)
        all_actions = list(itertools.chain.from_iterable(actions_dict.values()))
        
        if all_actions:
            import random
            return random.choice(all_actions)
        else:
            # Acción vacía de último recurso
            return risktools.RiskAction('Pasar', None, None, None)
    
    def __repr__(self):
        return f"PPOPlayer(name='{self.player_name}', model='{os.path.basename(self.model_path)}')"
