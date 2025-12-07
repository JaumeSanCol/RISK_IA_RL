import os
import sys
import random
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import itertools

# Configuración de rutas para encontrar risktools.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import risktools

import risktools
from config_atrib import *

class RiskTotalControlEnv(gym.Env):
    """
    Entorno Gymnasium para entrenar agentes de RISK.
    
    Características principales:
    - Control Total: El agente decide Fase, Origen, Destino y Cantidad.
    - Personalidades: Soporta estilos de juego (Agresivo, Defensivo, etc.) mediante Reward Shaping.
    - Headless: No requiere interfaz gráfica para entrenar.
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, enemy_ai_class=None, style="standard"):
        """
        Inicializa el entorno.
        
        Args:
            enemy_ai_class: (Opcional) Clase de IA para el oponente. Si es None, usa Random.
            style (str): Personalidad del agente ('standard', 'aggressive', 'defensive', 'capitalist').
                         Define qué comportamientos se recompensan más.
        """
        super(RiskTotalControlEnv, self).__init__()
        
        self.style = style
        print(f"[ENV] Inicializando entorno RISK con personalidad: {self.style.upper()}")

        # 1. Cargar el tablero base (Mapa)
        # Usamos loadBoard para leer la geometría, pero no usamos su estado de juego.
        world_path = os.path.join(parent_dir, "world.zip")
        self.board_base = risktools.loadBoard(world_path)
        self.n_territories = len(self.board_base.territories)
        
        # Configuración manual de reglas (valores de cartas)
        # Esto sustituye a la configuración que normalmente hace la GUI.
        self.board_base.set_turn_in_values([4, 6, 8, 10, 12, 15])
        self.board_base.set_increment_value(5)
        
        # --- DEFINICIÓN DEL ESPACIO DE ACCIÓN (OUTPUT) ---
        # Usamos MultiDiscrete para tener 4 "perillas" independientes de decisión.
        # [0] Tipo de Acción (7 opciones): Pasar, Comprar, Colocar, Atacar, Ocupar, Fortificar, Invertir.
        # [1] Territorio Origen (42 opciones): ID del territorio (0-41).
        # [2] Territorio Destino (42 opciones): ID del territorio (0-41).
        # [3] Cantidad (10 opciones): Intensidad de la acción (0=Mínimo, 9=Todo/Máximo).
        self.action_space = spaces.MultiDiscrete([7, 42, 42, 10])
        
        # --- DEFINICIÓN DEL ESPACIO DE OBSERVACIÓN (INPUT) ---
        # Vector plano de floats que representa todo el estado del juego.
        # Tamaño: (42 territorios * 3 datos) + 20 variables globales = 146 neuronas de entrada.
        self.obs_dim = (self.n_territories * 3) + 20 
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.obs_dim,), dtype=np.float32)

        # Variables de estado interno
        self.state = None
        self.player_idx = 0 # La IA siempre entrena como el Jugador 0
        self.enemy_ai = enemy_ai_class

    def reset(self, seed=None, options=None):
        """
        Reinicia la partida. Se llama al principio de cada episodio de entrenamiento.
        """
        super().reset(seed=seed)
        
        # 1. Crear Jugadores Nuevos
        # Usamos nombres descriptivos para facilitar el debug en logs.
        p1 = risktools.RiskPlayer(f"Agent_{self.style}", 0, 0, False, ECON_START, HAPP_START, DEVP_START)
        p2 = risktools.RiskPlayer("Enemy_Bot", 1, 0, False, ECON_START, HAPP_START, DEVP_START)
        
        # --- PARCHE DE COMPATIBILIDAD ---
        # El motor antiguo usa camelCase (freeArmies) pero la clase nueva usa snake_case (free_armies).
        # Creamos alias para evitar errores de atributo durante la simulación.
        for p in [p1, p2]:
            p.freeArmies = p.free_armies
            p.conqueredTerritory = p.conquered_territory

        # 2. Configurar Tablero Limpio
        # Reutilizamos la geometría cargada en __init__ pero reseteamos la posesión.
        self.board = self.board_base 
        self.board.players = []      
        self.board.player_to_id = {} 
        self.board.id_to_player = {}
        self.board.add_player(p1)
        self.board.add_player(p2)

        # 3. Configurar Variables Globales del Motor
        # risktools.py usa variables globales para el estado del turno. Las reiniciamos aquí.
        risktools.riskengine.playerorder = [p1, p2]
        risktools.riskengine.currentplayer = p1
        risktools.riskengine.phase = 'Preposition'
        
        # 4. Generar Estado Inicial
        self.state = risktools.getInitialState(self.board)
        
        # 5. Setup Rápido (Fast Forward)
        # Saltamos la fase de elegir territorios uno a uno (es lenta y aporta poco aprendizaje táctico).
        # Asignamos territorios aleatoriamente y empezamos con dinero en Fase 1.
        self._fast_random_setup()
        
        return self._get_obs(), {}

    def step(self, action):
        """
        Ejecuta un paso de simulación.
        1. Traduce la acción numérica de la IA a una acción del juego.
        2. Ejecuta la acción en el motor (tirando dados si hace falta).
        3. Calcula la recompensa y verifica si el juego terminó.
        """
        act_type, act_src, act_dst, act_amt = action
        
        # --- 1. DECODIFICACIÓN ---
        # Buscamos si la combinación elegida (ej: Atacar Alaska->Kamchatka) es legal.
        game_action = self._decode_action(act_type, act_src, act_dst, act_amt)
        
        info = {"valid": game_action is not None}
        
        if game_action is None:
            # ACCIÓN ILEGAL: La IA intentó algo prohibido (ej. atacar con 0 tropas).
            # La penalizamos levemente y no cambiamos el estado.
            # Esto enseña a la red a respetar las reglas.
            return self._get_obs(), -1.0, False, False, info

        # --- 2. EJECUCIÓN ---
        try:
            # simulateAction devuelve posibles futuros y sus probabilidades (ej. ganar/perder dados).
            next_states, probs = risktools.simulateAction(self.state, game_action)
            
            # Resolvemos la incertidumbre (Dados)
            if len(next_states) > 1:
                # Normalizamos probabilidades para evitar errores de float de numpy
                probs = np.array(probs, dtype=np.float64)
                probs /= probs.sum()
                idx = np.random.choice(len(next_states), p=probs)
                self.state = next_states[idx]
            else:
                self.state = next_states[0]
        except Exception as e:
            # Si el motor falla, penalizamos fuerte y terminamos para no romper el loop.
            return self._get_obs(), -10, True, False, {"error": str(e), "valid": True}

        # --- 3. RECOMPENSA ---
        reward = self._calculate_reward()
        terminated = False
        
        # --- 4. CONTROL DE FLUJO ---
        if self.state.turn_type == 'GameOver':
            terminated = True
            # Verificamos quién ganó
            winners = [i for i, p in enumerate(self.state.players) if not p.game_over]
            if self.player_idx in winners and len(winners) == 1:
                reward += 100 # ¡VICTORIA!
            else:
                reward -= 100 # DERROTA
        
        # Si pasamos turno, simular al enemigo hasta que nos toque otra vez
        elif self.state.current_player != self.player_idx:
            self._simulate_enemy_turn()
            
            # Verificar si morimos durante el turno enemigo
            if self.state.players[self.player_idx].game_over:
                terminated = True
                reward -= 100
            elif self.state.turn_type == 'GameOver':
                 terminated = True

        return self._get_obs(), reward, terminated, False, info

    def _calculate_reward(self):
        """Define la 'personalidad' del agente mediante premios y castigos."""
        me = self.state.players[self.player_idx]
        # Contar territorios propios
        my_territories = sum(1 for o in self.state.owners if o == self.player_idx)
        reward = 0
        # --- ESTILO: STANDARD (Equilibrado) ---
        if self.style == "standard":
            # Premia expandirse
            reward += my_territories * 0.05
            
        # --- ESTILO: AGGRESSIVE (El Conquistador) ---
        elif self.style == "aggressive":
            # Puntos base por territorio
            reward += my_territories * 0.1
            # GRAN premio por conquistar al menos un territorio en este turno
            if me.conquered_territory:
                reward += 2.0  
            # Pequeña penalización por tener tropas ociosas (incentiva usarlas)
            reward -= me.free_armies * 0.01

        # --- ESTILO: DEFENSIVE (La Tortuga) ---
        elif self.style == "defensive":
            # Premia la cantidad total de tropas vivas
            total_troops = sum(self.state.armies[i] for i in range(self.n_territories) if self.state.owners[i] == self.player_idx)
            reward += total_troops * 0.05
            # Premia simplemente sobrevivir
            reward += 0.5

        # --- ESTILO: CAPITALIST (El Banquero) ---
        elif self.style == "capitalist":
            # Premia acumular dinero
            reward += me.economy * 0.05
            # Premia el desarrollo económico
            reward += me.development * 0.1

        return reward

    def action_masks(self):
        allowed = risktools.getAllowedFaseActions(self.state)

        # 1) mask del tipo de acción
        type_map = {'Pasar':0,'Comprar_Soldados':1,'Place':2,'Attack':3,
                    'Occupy':4,'Fortify':5,'Invertir':6,'PrePlace':2}

        mask_type = [False]*7
        for key, acts in allowed.items():
            if key in type_map and len(acts)>0:
                mask_type[type_map[key]] = True

        if not any(mask_type):
            mask_type[0] = True    # fallback

        # 2) máscaras específicas según el tipo habilitado
        mask_src = [False]*42
        mask_dst = [False]*42

        # --- Si solo se puede Pasar / Comprar → todo es 0
        if mask_type[0] and sum(mask_type)==1:
            mask_src[0] = True
            mask_dst[0] = True

        else:
            # Si hay acciones con territorios reales
            for key, acts in allowed.items():
                for act in acts:
                    if hasattr(act,'from_territory') and act.from_territory:
                        tid = self.board.territory_to_id.get(act.from_territory,None)
                        if tid is not None:
                            mask_src[tid] = True
                    else:
                        mask_src[0] = True

                    if hasattr(act,'to_territory') and act.to_territory:
                        tid = self.board.territory_to_id.get(act.to_territory,None)
                        if tid is not None:
                            mask_dst[tid] = True
                    else:
                        mask_dst[0] = True

        # Cantidad siempre válida
        mask_amt = [True]*10

        return np.concatenate([mask_type,mask_src,mask_dst,mask_amt])
    def _decode_action(self, type_idx, src_id, dst_id, amt_idx):
        """Convierte la acción MultiDiscrete en una acción real del motor RISK."""

        allowed_dict = risktools.getAllowedFaseActions(self.state)

        # Mapeo numérico -> nombre motor
        type_map = {
            0: 'Pasar',
            1: 'Comprar_Soldados',
            2: 'Place',
            3: 'Attack',
            4: 'Occupy',
            5: 'Fortify',
            6: 'Invertir'
        }

        # Caso especial: PrePlace se usa en fase 0
        target_type = type_map.get(type_idx)
        if target_type == 'Place' and 'PrePlace' in allowed_dict:
            target_type = 'PrePlace'

        # Si el tipo de acción no existe en esta fase → ilegal
        if target_type not in allowed_dict:
            return None

        candidates = allowed_dict[target_type]

        # Si no hay acciones para este tipo → ilegal
        if not candidates:
            return None

        # Normalizador de nombres (evita mismatches por acentos/espacios/mayúsculas)
        def norm(s):
            if s is None:
                return ""
            return str(s).lower().replace(" ", "").replace("_","")

        # Obtener nombres de territorios elegidos por la IA
        src_name = None
        dst_name = None

        if src_id < self.n_territories:
            src_name = norm(self.board.territories[src_id].name)

        if dst_id < self.n_territories:
            dst_name = norm(self.board.territories[dst_id].name)

        best_match = None

        # Buscar coincidencia entre acción del motor y selección discreta
        for act in candidates:

            match_src = True
            match_dst = True

            # ----- ORIGEN -----
            if hasattr(act, "from_territory") and act.from_territory:
                act_src = norm(act.from_territory)
                match_src = (act_src == src_name)

            # ----- DESTINO -----
            if hasattr(act, "to_territory") and act.to_territory:
                act_dst = norm(act.to_territory)
                match_dst = (act_dst == dst_name)

            # ✓ Si ambos coinciden, acción encontrada
            if match_src and match_dst:
                best_match = act
                break

        # Si no se encontró acción → ilegal
        if best_match is None:
            return None

        # ----- INYECCIÓN DE CANTIDAD -----
        amount = max(1, amt_idx)

        if hasattr(best_match, "armies"):
            best_match.armies = amount

        if hasattr(best_match, "amount"):
            best_match.amount = amount

        return best_match


    def _get_obs(self):
        """Construye el vector de entrada para la red neuronal."""
        obs = []
        
        # A. Datos de Territorios (42 x 3 features)
        for i in range(self.n_territories):
            owner = self.state.owners[i]
            armies = self.state.armies[i]
            
            # One-Hot encoding del dueño (Mío vs Enemigo)
            obs.append(1.0 if owner == self.player_idx else 0.0)
            obs.append(1.0 if owner is not None and owner != self.player_idx else 0.0)
            # Cantidad de tropas normalizada (para que esté entre 0 y 1)
            obs.append(min(armies / 100.0, 1.0))
            
        # B. Datos Económicos y Globales
        me = self.state.players[self.player_idx]
        enemy = self.state.players[1 if self.player_idx == 0 else 0]
        
        obs.extend([
            min(me.economy / 200.0, 1.0),      # Mi dinero
            min(me.free_armies / 50.0, 1.0),   # Mis refuerzos
            min(enemy.economy / 200.0, 1.0),   # Dinero rival (Intel)
            min(sum(self.state.armies) / 500.0, 1.0) # Total tropas en juego
        ])
        
        # C. Fase del Turno (One-Hot)
        phase_map = {'fase_0':0, 'fase_1':1, 'fase_2':2, 'fase_3':3}
        phase_vec = [0.0]*4
        phase_vec[phase_map.get(self.state.fase, 0)] = 1.0
        obs.extend(phase_vec)
        
        # D. Padding (Relleno de seguridad)
        current_len = len(obs)
        if current_len < self.obs_dim:
            obs.extend([0.0] * (self.obs_dim - current_len))
            
        return np.array(obs[:self.obs_dim], dtype=np.float32)

    def _simulate_enemy_turn(self):
        """Simula el turno del rival usando acciones aleatorias válidas."""
        steps = 0
        while self.state.current_player != self.player_idx and self.state.turn_type != 'GameOver' and steps < 50:
            actions_dict = risktools.getAllowedFaseActions(self.state)
            all_actions = list(itertools.chain.from_iterable(actions_dict.values()))
            
            if not all_actions: break
            
            # IA Random para el enemigo
            action = random.choice(all_actions)
            
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
        """Asignación inicial rápida para entrenamiento."""
        ids = list(range(self.n_territories))
        random.shuffle(ids)
        for i, tid in enumerate(ids):
            owner = i % 2
            self.state.owners[tid] = owner
            self.state.armies[tid] = 3
        self.state.fase = 'fase_1'
        self.state.turn_type = 'Comprar_Soldados'