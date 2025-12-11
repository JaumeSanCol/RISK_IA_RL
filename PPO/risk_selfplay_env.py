import os
import sys
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import itertools
import random

# Rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path: sys.path.append(parent_dir)

import risktools
from config_atrib import *

class RiskSelfPlayEnv(gym.Env):
    """
    Entorno MARL / Self-Play:
    - Una sola red controla a TODOS los jugadores.
    - 'step()' avanza una acción y devuelve la observación desde la perspectiva del SIGUIENTE jugador.
    """
    def __init__(self, max_steps=4000, n_players=4):
        super(RiskSelfPlayEnv, self).__init__()
        self.max_steps = max_steps
        self.n_players = n_players
        
        # Cargar tablero
        world_path = os.path.join(parent_dir, "world.zip")
        self.board_base = risktools.loadBoard(world_path)
        self.n_territories = len(self.board_base.territories)
        
        # Action Space (Igual)
        self.action_space = spaces.MultiDiscrete([7, 42, 42, 10])
        
        # Obs Space (Igual)
        self.obs_dim = (self.n_territories * 3) + 20 
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.obs_dim,), dtype=np.float32)

        self.state = None
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step_count = 0

        # 1. Setup Jugadores (Todos clónicos al inicio)
        players = []
        for i in range(self.n_players):
            # No importa el nombre, la red es agnóstica
            p = risktools.RiskPlayer(f"Player_{i}", i, 0, False, ECON_START, HAPP_START, DEVP_START)
            p.freeArmies = p.free_armies # Compatibilidad
            p.conqueredTerritory = p.conquered_territory
            players.append(p)

        self.board = self.board_base 
        self.board.players = []      
        self.board.player_to_id = {} 
        for p in players: self.board.add_player(p)

        risktools.riskengine.playerorder = players
        risktools.riskengine.currentplayer = players[0]
        risktools.riskengine.phase = 'Preposition'
        
        self.state = risktools.getInitialState(self.board)
        
        # 2. Setup Rápido
        self._fast_random_setup()
        
        # 3. Devolver observación del jugador actual (Player 0)
        return self._get_obs(self.state.current_player), {}

    def step(self, action):
        self.current_step_count += 1
        
        # 1. Identificar quién está jugando
        player_playing_idx = self.state.current_player
        
        # 2. Decodificar y Ejecutar
        act_type, act_src, act_dst, act_amt = action
        game_action = self._decode_action(act_type, act_src, act_dst, act_amt)
        
        info = {"player": player_playing_idx}
        
        if game_action is None:
            # Penalización fuerte por acción ilegal
            # Truco: Si hace ilegal, penalizamos y NO avanzamos el juego (o pasamos turno forzado)
            # Para self-play, mejor penalizar y forzar 'Pasar' o terminar si es grave.
            return self._get_obs(player_playing_idx), -1.0, False, False, info

        try:
            next_states, probs = risktools.simulateAction(self.state, game_action)
            # Selección estocástica del resultado
            idx = np.random.choice(len(next_states), p=np.array(probs)/sum(probs)) if len(next_states) > 1 else 0
            self.state = next_states[idx]
        except Exception:
            return self._get_obs(player_playing_idx), -10.0, True, False, info

        # 3. Calcular Recompensa para el jugador QUE ACABA DE JUGAR
        reward = self._calculate_reward(player_playing_idx)
        
        terminated = False
        if self.state.turn_type == 'GameOver':
            terminated = True
            winners = [i for i, p in enumerate(self.state.players) if not p.game_over]
            if player_playing_idx in winners:
                reward += 100.0 # Gran premio por ganar
            else:
                reward -= 100.0 # Castigo por perder (si es que llega a jugar en Game Over)

        truncated = (self.current_step_count >= self.max_steps)

        # 4. OBS PARA EL SIGUIENTE (!! CLAVE !!)
        # Ahora self.state.current_player ha cambiado (o no, si sigue siendo mi turno)
        next_player_idx = self.state.current_player
        
        return self._get_obs(next_player_idx), reward, terminated, truncated, info

    def _get_obs(self, player_perspective_idx):
        """
        Genera la observación RELATIVA al 'player_perspective_idx'.
        Para la red, 'Yo' siempre soy el índice 0 de la observación.
        """
        obs = []
        # A. Territorios (Perspectiva Egocéntrica)
        for i in range(self.n_territories):
            owner = self.state.owners[i]
            armies = self.state.armies[i]
            
            # Es mío?
            obs.append(1.0 if owner == player_perspective_idx else 0.0)
            # Es enemigo?
            obs.append(1.0 if owner is not None and owner != player_perspective_idx else 0.0)
            obs.append(min(armies / 100.0, 1.0))
            
        # B. Datos Globales
        me = self.state.players[player_perspective_idx]
        enemy_econs = [p.economy for p in self.state.players if p.id != player_perspective_idx and not p.game_over]
        max_enemy_econ = max(enemy_econs) if enemy_econs else 0
        
        obs.extend([
            min(me.economy / 200.0, 1.0),
            min(me.free_armies / 50.0, 1.0),
            min(max_enemy_econ / 200.0, 1.0),
            min(sum(self.state.armies) / 500.0, 1.0)
        ])
        
        # C. Fase
        phase_map = {'fase_0':0, 'fase_1':1, 'fase_2':2, 'fase_3':3}
        phase_vec = [0.0]*4
        phase_vec[phase_map.get(self.state.fase, 0)] = 1.0
        obs.extend(phase_vec)
        
        # Padding
        if len(obs) < self.obs_dim:
            obs.extend([0.0] * (self.obs_dim - len(obs)))
            
        return np.array(obs[:self.obs_dim], dtype=np.float32)

    def _calculate_reward(self, player_idx):
        # Recompensa densa genérica para aprender
        me = self.state.players[player_idx]
        my_territories = sum(1 for o in self.state.owners if o == player_idx)
        return my_territories * 0.1

    def action_masks(self):
        # Wrapper para usar la máscara del jugador actual
        return self._get_action_mask(self.state.current_player)

    def _get_action_mask(self, player_idx):
        # Lógica idéntica a risk_gym_env pero asegurando usar el estado actual
        allowed = risktools.getAllowedFaseActions(self.state)
        # ... (Copiar lógica de action_masks de risk_gym_env tal cual) ...
        # (Por brevedad, asume que copias la lógica del script anterior aquí)
        # Importante: MaskablePPO llamará a esto antes de predecir.
        
        # --- COPIA PEGA DE LA LÓGICA DE MÁSCARAS ---
        type_map = {'Pasar':0,'Comprar_Soldados':1,'Place':2,'Attack':3, 'Occupy':4,'Fortify':5,'Invertir':6,'PrePlace':2}
        mask_type = [False]*7
        for key, acts in allowed.items():
            if key in type_map and len(acts)>0: mask_type[type_map[key]] = True
        if not any(mask_type): mask_type[0] = True 
        mask_src = [False]*42
        mask_dst = [False]*42
        if mask_type[0] and sum(mask_type)==1:
            mask_src[0] = True; mask_dst[0] = True
        else:
            for key, acts in allowed.items():
                for act in acts:
                    if hasattr(act,'from_territory') and act.from_territory:
                        tid = self.board.territory_to_id.get(act.from_territory,None)
                        if tid is not None: mask_src[tid] = True
                    else: mask_src[0] = True
                    if hasattr(act,'to_territory') and act.to_territory:
                        tid = self.board.territory_to_id.get(act.to_territory,None)
                        if tid is not None: mask_dst[tid] = True
                    else: mask_dst[0] = True
        mask_amt = [True]*10
        return np.concatenate([mask_type,mask_src,mask_dst,mask_amt])

    # Métodos auxiliares _decode_action y _fast_random_setup iguales al original
    def _decode_action(self, type_idx, src_id, dst_id, amt_idx):
        """
        Decodifica índices numéricos a RiskAction.
        Tipo: 0=Pasar, 1=Comprar_Soldados, 2=Place, 3=Attack, 4=Occupy, 5=Fortify, 6=Invertir
        Robusto: Busca coincidir por nombre de territorio, con varios niveles de fallback.
        """
        allowed_dict = risktools.getAllowedFaseActions(self.state)
        type_map = {0: 'Pasar', 1: 'Comprar_Soldados', 2: 'Place', 3: 'Attack', 4: 'Occupy', 5: 'Fortify', 6: 'Invertir'}
        target_type = type_map.get(type_idx)
        
        # Ajustar tipo si es PrePlace
        if target_type == 'Place' and 'PrePlace' in allowed_dict: 
            target_type = 'PrePlace'
        
        if target_type not in allowed_dict: 
            return None
        
        candidates = allowed_dict[target_type]
        if not candidates: 
            return None
        
    def _fast_random_setup(self):
        """Asignación inicial distribuida entre N jugadores."""
        ids = list(range(self.n_territories))
        random.shuffle(ids)
        for i, tid in enumerate(ids):
            # Asignar territorios en ciclo: Jugador 0, 1, 2, 3, 0...
            owner = i % self.n_players
            self.state.owners[tid] = owner
            self.state.armies[tid] = 3
        
        self.state.fase = 'fase_1'
        self.state.turn_type = 'Comprar_Soldados'