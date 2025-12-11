import os
import sys
import random
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import itertools

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import risktools
from config_atrib import *

multiplicador={
    "standard":3,
    "aggressive":7,
    "defensive":10,
    "capitalist":2# 
}
MAX_STEPS=3000

class RiskTotalControlEnv(gym.Env):
    """
    Entorno Gymnasium para entrenar agentes de RISK contra MÚLTIPLES oponentes.
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, enemy_ai_class=None, style="standard", max_steps=MAX_STEPS, n_players=4):
        """
        Args:
            n_players (int): Número total de jugadores (1 Agente + n-1 Bots).
        """
        super(RiskTotalControlEnv, self).__init__()
        self.max_steps = max_steps
        self.style = style
        self.n_players = n_players # Nueva variable
        
        print(f"[ENV] Inicializando entorno RISK ({self.n_players} Jugadores) - Personalidad: {self.style.upper()}")

        # 1. Cargar el tablero base
        world_path = os.path.join(parent_dir, "world.zip")
        self.board_base = risktools.loadBoard(world_path)
        self.n_territories = len(self.board_base.territories)
        
        # Configuración manual de reglas
        self.board_base.set_turn_in_values([4, 6, 8, 10, 12, 15])
        self.board_base.set_increment_value(5)
        
        # --- ESPACIO DE ACCIÓN (Sin cambios) ---
        self.action_space = spaces.MultiDiscrete([7, 42, 42, 10])
        
        # --- ESPACIO DE OBSERVACIÓN ---
        # Mantenemos el tamaño fijo para no romper la red neuronal.
        # La info de "El Enemigo" ahora será "El Enemigo más fuerte" o "Agregado".
        self.obs_dim = (self.n_territories * 3) + 20 
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.obs_dim,), dtype=np.float32)

        self.state = None
        self.player_idx = 0 # La IA siempre es el Jugador 0
        self.enemy_ai = enemy_ai_class

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step_count = 0

        # 1. Crear Lista de Jugadores (Soporte Multi-Jugador)
        players = []
        
        # El Agente (Jugador 0)
        p_agent = risktools.RiskPlayer(f"Agent_{self.style}", 0, 0, False, ECON_START, HAPP_START, DEVP_START)
        players.append(p_agent)

        # Los Bots (Jugadores 1 a N-1)
        for i in range(1, self.n_players):
            p_bot = risktools.RiskPlayer(f"Enemy_Bot_{i}", i, 0, False, ECON_START, HAPP_START, DEVP_START)
            players.append(p_bot)
        
        # --- PARCHE DE COMPATIBILIDAD ---
        for p in players:
            p.freeArmies = p.free_armies
            p.conqueredTerritory = p.conquered_territory

        # 2. Configurar Tablero Limpio
        self.board = self.board_base 
        self.board.players = []      
        self.board.player_to_id = {} 
        self.board.id_to_player = {}
        
        for p in players:
            self.board.add_player(p)

        # 3. Configurar Variables Globales del Motor
        risktools.riskengine.playerorder = players
        risktools.riskengine.currentplayer = players[0]
        risktools.riskengine.phase = 'Preposition'
        
        # 4. Generar Estado Inicial
        self.state = risktools.getInitialState(self.board)
        
        # 5. Setup Rápido (Distribuir entre N jugadores)
        self._fast_random_setup()
        
        return self._get_obs(), {}

    def step(self, action):
        act_type, act_src, act_dst, act_amt = action
        self.current_step_count += 1

        # 1. DECODIFICACIÓN
        game_action = self._decode_action(act_type, act_src, act_dst, act_amt)
        info = {"valid": game_action is not None}
        
        if game_action is None:
            return self._get_obs(), -1.0, False, False, info

        # 2. EJECUCIÓN
        try:
            next_states, probs = risktools.simulateAction(self.state, game_action)
            if len(next_states) > 1:
                probs = np.array(probs, dtype=np.float64)
                probs /= probs.sum()
                idx = np.random.choice(len(next_states), p=probs)
                self.state = next_states[idx]
            else:
                self.state = next_states[0]
        except Exception as e:
            return self._get_obs(), -10, True, False, {"error": str(e), "valid": True}

        # 3. RECOMPENSA
        reward = self._calculate_reward()
        terminated = False
        
        # 4. CONTROL DE FLUJO
        if self.state.turn_type == 'GameOver':
            terminated = True
            winners = [i for i, p in enumerate(self.state.players) if not p.game_over]
            
            # Si estoy en la lista de ganadores y soy el único vivo (o gané por objetivo)
            if self.player_idx in winners and len(winners) == 1:
                b_r = MAX_STEPS - self.current_step_count
                reward += 10_000 + (b_r * multiplicador[self.style])
            else:
                reward -= 10_000 # Perdí
        
        # Si NO es mi turno, simular a TODOS los enemigos hasta que me toque
        elif self.state.current_player != self.player_idx:
            self._simulate_enemy_turn()
            
            # Chequear si morí mientras jugaban los otros
            if self.state.players[self.player_idx].game_over:
                terminated = True
                reward -= 5_000 * multiplicador[self.style]
            elif self.state.turn_type == 'GameOver':
                 terminated = True
                 # (Aquí se podría añadir lógica extra si ganamos pasivamente, raro en Risk)

        truncated = False
        if self.current_step_count >= self.max_steps:
            truncated = True
            if not terminated:
                my_territories = sum(1 for o in self.state.owners if o == self.player_idx)
                dif=42-my_territories
                reward -= 15_000*dif # Penalización por empate eterno

        return self._get_obs(), reward, terminated, truncated, info

    def _get_obs(self):
        """
        Vector de entrada adaptado para N jugadores.
        Estrategia: 'Yo' vs 'El resto del mundo'.
        """
        obs = []
        
        # A. Datos de Territorios
        for i in range(self.n_territories):
            owner = self.state.owners[i]
            armies = self.state.armies[i]
            
            # 1.0 si es mío, 0.0 si es de CUALQUIER enemigo
            obs.append(1.0 if owner == self.player_idx else 0.0)
            
            # 1.0 si es enemigo (antes era owner != idx, sigue siendo válido para N jugadores)
            obs.append(1.0 if owner is not None and owner != self.player_idx else 0.0)
            
            obs.append(min(armies / 100.0, 1.0))
            
        # B. Datos Económicos y Globales (AGREGADOS)
        me = self.state.players[self.player_idx]
        
        # Recopilar stats de todos los enemigos vivos
        enemy_econs = []
        for p in self.state.players:
            if p.id != self.player_idx and not p.game_over:
                enemy_econs.append(p.economy)
            elif p.id != self.player_idx and p.game_over:
                 enemy_econs.append(0) # Muertos tienen 0

        # Tomamos la economía del enemigo MÁS FUERTE como referencia para la red
        max_enemy_econ = max(enemy_econs) if enemy_econs else 0
        
        obs.extend([
            min(me.economy / 200.0, 1.0),      # Mi dinero
            min(me.free_armies / 50.0, 1.0),   # Mis refuerzos
            min(max_enemy_econ / 200.0, 1.0),  # Dinero del RIVAL MÁS RICO
            min(sum(self.state.armies) / 500.0, 1.0) # Total tropas en juego
        ])
        
        # C. Fase del Turno
        phase_map = {'fase_0':0, 'fase_1':1, 'fase_2':2, 'fase_3':3}
        phase_vec = [0.0]*4
        phase_vec[phase_map.get(self.state.fase, 0)] = 1.0
        obs.extend(phase_vec)
        
        # D. Padding
        current_len = len(obs)
        if current_len < self.obs_dim:
            obs.extend([0.0] * (self.obs_dim - current_len))
            
        return np.array(obs[:self.obs_dim], dtype=np.float32)

    def _simulate_enemy_turn(self):
        """Simula turnos de TODOS los rivales hasta que vuelva a ser mi turno."""
        steps = 0
        # Aumentamos el límite de pasos de simulación porque hay más jugadores
        max_sim_steps = 100 * (self.n_players - 1) 
        
        while self.state.current_player != self.player_idx and \
              self.state.turn_type != 'GameOver' and \
              steps < max_sim_steps:
            
            # --- LÓGICA DE IA ENEMIGA ---
            action = None
            
            # 1. Si se proporcionó una IA Heurística (ej: attacker_ai), usarla
            if self.enemy_ai is not None:
                try:
                    # attacker_ai.getAction(state) devuelve la acción elegida
                    action = self.enemy_ai.getAction(self.state)
                except Exception as e:
                    # Si la heurística falla, hacemos fallback a random para no romper el training
                    # print(f"[WARNING] Heuristic Error: {e}")
                    pass

            # 2. Si no hay IA o falló, usar Random (Comportamiento por defecto)
            if action is None:
                actions_dict = risktools.getAllowedFaseActions(self.state)
                all_actions = list(itertools.chain.from_iterable(actions_dict.values()))
                
                if not all_actions: 
                    break # Deadlock o error raro
                action = random.choice(all_actions)
            
            # --- EJECUCIÓN EN EL SIMULADOR ---
            next_states, probs = risktools.simulateAction(self.state, action)
            
            if len(next_states) > 1:
                probs = np.array(probs, dtype=np.float64)
                probs /= probs.sum()
                idx = np.random.choice(len(next_states), p=probs)
                self.state = next_states[idx]
            else:
                self.state = next_states[0]
            steps += 1

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

    # --- MÉTODOS AUXILIARES SIN CAMBIOS (Action Masking, Decode, Reward) ---
    def _calculate_reward(self):
        # Mismo cálculo, funciona igual para N jugadores
        me = self.state.players[self.player_idx]
        my_territories = sum(1 for o in self.state.owners if o == self.player_idx)
        reward = 0
        reward+=min(me.happiness,50)*0.01
        if self.style == "standard":
            reward += my_territories * 0.05
        elif self.style == "aggressive":
            reward += my_territories * 0.1
            if me.conquered_territory:
                reward += 2.0  
        elif self.style == "defensive":
            total_troops = sum(self.state.armies[i] for i in range(self.n_territories) if self.state.owners[i] == self.player_idx)
            reward += total_troops * 0.001
            reward += 0.5
        elif self.style == "capitalist":
            reward += me.development * 0.1
        return reward

    def action_masks(self):
        # Mismo código anterior
        allowed = risktools.getAllowedFaseActions(self.state)
        type_map = {'Pasar':0,'Comprar_Soldados':1,'Place':2,'Attack':3, 'Occupy':4,'Fortify':5,'Invertir':6,'PrePlace':2}
        mask_type = [False]*7
        for key, acts in allowed.items():
            if key in type_map and len(acts)>0:
                mask_type[type_map[key]] = True
        if not any(mask_type): mask_type[0] = True 
        mask_src = [False]*42
        mask_dst = [False]*42
        if mask_type[0] and sum(mask_type)==1:
            mask_src[0] = True
            mask_dst[0] = True
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
        
        def norm(s): 
            return str(s).lower().replace(" ", "").replace("_","") if s else ""
        
        # Obtener nombres de territorios desde IDs
        src_name = norm(self.board.territories[src_id].name) if src_id < self.n_territories else None
        dst_name = norm(self.board.territories[dst_id].name) if dst_id < self.n_territories else None
        
        # NIVEL 1: Buscar acciones con parámetros (no vacías)
        candidates_with_params = [act for act in candidates 
                                   if not (act.from_territory is None and act.to_territory is None)]
        
        # NIVEL 2: Si no hay acciones con parámetros, usar todas
        if not candidates_with_params:
            candidates_with_params = candidates
        
        # Buscar mejor coincidencia por nombre
        best_match = None
        best_score = -1
        
        for act in candidates_with_params:
            match_score = 0
            
            # Verificar coincidencia de from_territory
            if hasattr(act, "from_territory") and act.from_territory:
                if norm(act.from_territory) == src_name:
                    match_score += 1
            
            # Verificar coincidencia de to_territory
            if hasattr(act, "to_territory") and act.to_territory:
                if norm(act.to_territory) == dst_name:
                    match_score += 1
            
            # Guardar la mejor coincidencia
            if match_score > best_score:
                best_score = match_score
                best_match = act
        
        # NIVEL 3: Si no hay coincidencia por nombre, usar la primera acción con parámetros
        if best_match is None:
            # Preferir acciones con parámetros
            for act in candidates:
                if not (act.from_territory is None and act.to_territory is None):
                    best_match = act
                    break
        
        # NIVEL 4: Último recurso - usar cualquier candidato
        if best_match is None and candidates:
            best_match = candidates[0]
        
        # Asignar cantidad si corresponde
        if best_match:
            amount = max(1, amt_idx)
            if hasattr(best_match, "armies"): 
                best_match.armies = amount
            if hasattr(best_match, "amount"): 
                best_match.amount = amount
        
        return best_match