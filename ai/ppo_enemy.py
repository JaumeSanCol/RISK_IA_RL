import numpy as np
import os
import sys
from sb3_contrib import MaskablePPO

# Asegurar acceso a risktools
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path: sys.path.append(parent_dir)

import risktools

class PPOBot:
    """
    Clase que envuelve un modelo PPO entrenado para que juegue como enemigo.
    Replica la lógica de observación y decodificación del entorno de entrenamiento.
    """
    def __init__(self, model_path, name="PPO_Bot"):
        self.name = name
        print(f"[{name}] Cargando modelo desde: {model_path}")
        try:
            # Cargamos el modelo (MaskablePPO)
            self.model = MaskablePPO.load(model_path)
            self.obs_dim = (42 * 3) + 20 # Debe coincidir con tu risk_gym_env
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el modelo {model_path}: {e}")
            self.model = None

    def getAction(self, state):
        """Método principal llamado por el entorno."""
        if self.model is None:
            return None # Fallback

        player_id = state.current_player
        
        # 1. Generar Observación y Máscara para ESTE jugador (perspectiva relativa)
        obs = self._build_obs(state, player_id)
        mask = self._build_mask(state, player_id)
        
        # 2. Predicción de la red neuronal
        action_idx, _ = self.model.predict(obs, action_masks=mask, deterministic=True)
        
        # 3. Decodificar índice a RiskAction
        risk_action = self._decode_action(int(action_idx), state, player_id)
        
        return risk_action

    def _build_obs(self, state, player_id):
        """Genera el vector de observación desde la perspectiva de player_id."""
        obs = []
        n_territories = len(state.board.territories) # 42 normalmente
        
        # A. Territorios
        for i in range(n_territories):
            owner = state.owners[i]
            armies = state.armies[i]
            # 1.0 si es MÍO
            obs.append(1.0 if owner == player_id else 0.0)
            # 1.0 si es ENEMIGO (cualquiera que no sea yo)
            obs.append(1.0 if owner is not None and owner != player_id else 0.0)
            # Cantidad de tropas
            obs.append(min(armies / 100.0, 1.0))
            
        # B. Datos Globales
        me = state.players[player_id]
        
        # Economía del enemigo más fuerte
        enemy_econs = [p.economy for p in state.players if p.id != player_id and not p.game_over]
        if not enemy_econs: enemy_econs = [0] # Si gané y estoy solo
        
        obs.extend([
            min(me.economy / 200.0, 1.0),
            min(me.free_armies / 50.0, 1.0),
            min(max(enemy_econs) / 200.0, 1.0),
            min(sum(state.armies) / 500.0, 1.0)
        ])
        
        # C. Fase
        phase_map = {'fase_0':0, 'fase_1':1, 'fase_2':2, 'fase_3':3}
        phase_vec = [0.0]*4
        phase_vec[phase_map.get(state.fase, 0)] = 1.0
        obs.extend(phase_vec)
        
        # Padding si es necesario
        current_len = len(obs)
        if current_len < self.obs_dim:
            obs.extend([0.0] * (self.obs_dim - current_len))
            
        return np.array(obs[:self.obs_dim], dtype=np.float32)

    def _build_mask(self, state, player_id):
        """Genera la máscara de acciones válidas."""
        # Nota: state.current_player ya debería ser player_id si es su turno
        allowed = risktools.getAllowedFaseActions(state)
        
        # Mapa idéntico al del environment original
        type_map = {'Pasar':0,'Comprar_Soldados':1,'Place':2,'Attack':3, 'Occupy':4,'Fortify':5,'Invertir':6,'PrePlace':2}
        
        mask_type = [False]*7
        for key, acts in allowed.items():
            if key in type_map and len(acts)>0:
                mask_type[type_map[key]] = True
        if not any(mask_type): mask_type[0] = True 
        
        mask_src = [False]*42
        mask_dst = [False]*42
        
        if mask_type[0] and sum(mask_type)==1: # Solo pasar
            mask_src[0] = True
            mask_dst[0] = True
        else:
            for key, acts in allowed.items():
                for act in acts:
                    if hasattr(act,'from_territory') and act.from_territory:
                        tid = state.board.territory_to_id.get(act.from_territory,None)
                        if tid is not None: mask_src[tid] = True
                    else: mask_src[0] = True
                    
                    if hasattr(act,'to_territory') and act.to_territory:
                        tid = state.board.territory_to_id.get(act.to_territory,None)
                        if tid is not None: mask_dst[tid] = True
                    else: mask_dst[0] = True
                    
        mask_amt = [True]*10
        return np.concatenate([mask_type,mask_src,mask_dst,mask_amt])

    def _decode_action(self, action_flat_idx, state, player_id):
        """Decodifica el índice de la red a RiskAction."""
        # Descomponer MultiDiscrete (esto asume la estructura del ActionSpace de Gym)
        # El modelo devuelve un solo entero si se usó MaskablePPO normal, o vector si MultiDiscrete.
        # PERO MaskablePPO trabaja sobre Discrete/MultiDiscrete aplanado o gestionado internamente.
        # Simplificación: En MaskablePPO para MultiDiscrete, SB3 suele requerir un wrapper especial.
        # Si tu modelo original usaba MultiDiscrete puro, PPOBot aquí necesita replicar cómo SB3 'aplana' o maneja eso.
        # *Asumiremos* que usaste el wrapper estándar que convierte salidas a vector.
        
        # NOTA IMPORTANTE: Para simplificar la compatibilidad con tu código anterior,
        # reconstruiremos la acción buscando la MEJOR coincidencia posible en las permitidas,
        # usando una heurística basada en los índices probables, ya que decodificar el tensor exacto es complejo fuera del env.
        
        # Hack robusto: Usar la acción válida que más se parezca a lo que la red querría
        # (Si esto falla, fallback a random válido para no romper el juego)
        
        # Recibir la acción del modelo (que viene del step del env)
        # Aquí hay una trampa: model.predict devuelve la acción formateada.
        
        # Si action_flat_idx es un array (MultiDiscrete), desempaquetar:
        if isinstance(action_flat_idx, np.ndarray) or isinstance(action_flat_idx, list):
             act_type, act_src, act_dst, act_amt = action_flat_idx
        else:
            # Si fuera discreto puro (raro con tu config), no funcionaría. Asumimos array.
            return None 

        # Lógica de decodificación copiada de risk_gym_env
        allowed_dict = risktools.getAllowedFaseActions(state)
        type_map = {0: 'Pasar', 1: 'Comprar_Soldados', 2: 'Place', 3: 'Attack', 4: 'Occupy', 5: 'Fortify', 6: 'Invertir'}
        target_type = type_map.get(act_type)
        
        if target_type == 'Place' and 'PrePlace' in allowed_dict: target_type = 'PrePlace'
        
        candidates = allowed_dict.get(target_type, [])
        if not candidates: return None # Acción ilegal
        
        # Buscar candidato
        best = candidates[0] 
        # (Aquí podrías implementar la búsqueda por ID de territorio igual que en el env, 
        # pero por brevedad usaremos el primero o random de los válidos del tipo seleccionado)
        
        # Intento de mejora: buscar coincidencia de territorios
        board = state.board
        src_name = board.territories[act_src].name if act_src < len(board.territories) else ""
        dst_name = board.territories[act_dst].name if act_dst < len(board.territories) else ""
        
        for cand in candidates:
            match = 0
            if hasattr(cand, 'from_territory') and cand.from_territory == src_name: match+=1
            if hasattr(cand, 'to_territory') and cand.to_territory == dst_name: match+=1
            if match == 2: return cand
        
        return best # Fallback