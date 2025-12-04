from config_atrib import *
from clases.action import *
from atributos.happiness import *

def getAttackActions(state):
    """
     Returns a list of all the Attack actions possible in this state
     An action is to attack another territory from a territory owned by the current_player where 2 or more troops are
    """
    actions = []
    
    for i in range(len(state.owners)):
        if state.owners[i] == state.current_player and state.armies[i] >= 2:
            from_territory = state.board.territories[i].name
            for n in state.board.territories[i].neighbors:
                if state.owners[n] != state.current_player:
                    to_territory = state.board.territories[n].name
                    a = RiskAction('Attack', to_territory, from_territory, None)
                    actions.append(a)
    
    no_action = RiskAction('Attack', None, None, None)
    actions.append(no_action)
    
    return actions

def getNumAttackSuccessors(state, action):
    """
    Determines how many possible states could result from this attack action
    """
    # Get indices of involved territories
    a_idx = state.board.territory_to_id[action.from_territory]
    d_idx = state.board.territory_to_id[action.to_territory]
  
    # --- LOGICA DE INVIERNO ---
    # Si es mes de invierno, el defensor defiende con hasta 3
    max_d_dice = 3 if state.mes in [11, 12, 1, 2] else 2
    
    a_num_dice = min(3, state.armies[a_idx]-1)
    d_num_dice = min(max_d_dice, state.armies[d_idx])
    
    num_outcomes = min(a_num_dice, d_num_dice) + 1
    
    if num_outcomes > 3:
        num_outcomes = 3
        
    return num_outcomes
    
def getAttackOutcome(a_num_dice, d_num_dice, outcome_index):
    """
    This will compute the probability of the outcome_index'th possible 
    result of a battle between the given number of dice.
    It will return the attacker_loss, defender_loss, outcome_probability
    """
    
    #Index by attacker dice, defender dice, outcome number
    outcome_probabilities = [
        # 1 Dado Atacante vs [1, 2, 3] Dados Defensor
        [
            [0.4167, 0.5833],           # 1v1
            [0.2546, 0.7454],           # 1v2
            [0.1500, 0.8500]            # 1v3 (Estimado: muy difícil para el atacante)
        ],
        # 2 Dados Atacante vs [1, 2, 3] Dados Defensor
        [
            [0.5787, 0.4213],           # 2v1
            [0.2276, 0.3241, 0.4483],   # 2v2
            [0.1000, 0.3000, 0.6000]    # 2v3 (Estimado: el defensor gana más a menudo)
        ],
        # 3 Dados Atacante vs [1, 2, 3] Dados Defensor
        [
            [0.6597, 0.3404],           # 3v1
            [0.3717, 0.3358, 0.2926],   # 3v2
            [0.2500, 0.4000, 0.3500]    # 3v3 (Estimado: batalla muy reñida con ventaja defensiva)
        ]
    ]
    attacker_loss = 0
    defender_loss = 0
    # Accedemos a la probabilidad
    outcome_probability = outcome_probabilities[a_num_dice-1][d_num_dice-1][outcome_index]
    
    total_loss = min(a_num_dice, d_num_dice)
    if d_num_dice == 3 and a_num_dice >= 2:
        total_loss = 2 # Capamos la pérdida a 2 aunque haya 3 dados defensivos
    elif d_num_dice == 3 and a_num_dice == 1:
        total_loss = 1

    if total_loss == 1:
        if outcome_index == 0:
            defender_loss = 1
        elif outcome_index == 1:
            attacker_loss = 1
        else:
            print('Attack Outcome Index invalid')
        
    elif total_loss == 2:
        if outcome_index == 0:
            defender_loss = 2
        elif outcome_index == 1:
            defender_loss = 1
            attacker_loss = 1
        elif outcome_index == 2:
            attacker_loss = 2
        else:
            print('Attack Outcome index invalid')
    else:
        print('Total Loss is invalid or 3v3 logic not implemented fully. Total Loss:', total_loss)
   
    return attacker_loss, defender_loss, outcome_probability
   
def simulateAttack(input_state, action):
    """
    Simulates attack action.  Returns a list of possible successor states and a 
    list of their probabilities.  This copies the input_state, so it is not modified.
    NO CAMBIA DE FASE.
    """
    
    if action.from_territory is None:
        # Esta es la acción de "dejar de atacar". No hay cambio de estado.
        cur_state = input_state.copy_state()
        return [cur_state], [1]
    
    # How many possible attack outcomes are there
    num_successors = getNumAttackSuccessors(input_state, action)
    
    successor_states = []
    successor_probs = []
    
    for i in range(num_successors):
        cur_state = input_state.copy_state()
        cur_prob = 0
        if action.type == 'Attack':
            cur_prob = simulateAttackAction(cur_state, action, i)
        else:
            print(f'ILLEGAL ACTION TYPE{action.type}4')
        
        successor_states.append(cur_state)
        successor_probs.append(cur_prob)
        
    return successor_states, successor_probs
   
def simulateAttackAction(state, action, outcome_index):
    """
    Execute the given action in the given state, assuming that the outcome of the battle is given by outcome_index.  This will modify the state to 
    reflect the outcome of the state.
    """            
    #a is attacker and d is defender
    
    #Get indices of involved territories
    a_idx = state.board.territory_to_id[action.from_territory]
    d_idx = state.board.territory_to_id[action.to_territory]
  
    #MAKE SURE THIS IS VALID
    if state.owners[a_idx] != state.current_player or state.owners[d_idx] == state.current_player or state.armies[a_idx] <= 1: 
        print('INVALID ATTACK ACTION: ')
        action.print_action()
        print('NO ATTACK ACTION WILL BE TAKEN')
        return 
  
    #Set last attacker and defender variables in the state
    state.last_attacker = a_idx
    state.last_defender = d_idx
  
    #Player id of defender
    defender = state.owners[d_idx]

    # Si es invierno el defensor puede tener hasta 3 dados para defenderse
    max_dice_d = 3 if state.mes in [11, 12, 1, 2] else 2

    #Get number of dice that will be involved (This assumes attacker always attacks with all dice)
    a_num_dice = min(3, state.armies[a_idx]-1)
    d_num_dice = min(max_dice_d, state.armies[d_idx])

    if state.armies[d_idx] == 0:
        print('THERE ARE NO ARMIES IN TERRITORY: ', state.board.territories[d_idx].name)
        print('ACTION: ', action.print_action())
        print('State: ', state.print_state())
        
    #Get the outcome and probability for the input outcome index
    a_loss, d_loss, outcome_probability = getAttackOutcome(a_num_dice, d_num_dice, outcome_index)
    
    state.armies[d_idx] = max(state.armies[d_idx] - d_loss, 0)
    state.armies[a_idx] = state.armies[a_idx] - a_loss
    
    #Check if the defender is at zero, then change owner (armies will be moved in with the next action (Occupy)
    if state.armies[d_idx] == 0:
        # Significa que el ataque ha sido exitoso, por lo que el defensor pierde felicidad y el atacante la gana
        if state.owners[d_idx]!=None:
            #Si el territorio enemigo no era independiente pierde felicidad
            updateHappiness(state,state.owners[d_idx],BONO_HAPP_DEFEND_WIN)
            updateHappiness(state,state.current_player,BONO_HAPP_ATTACK_WIN)
        state.owners[d_idx] = state.current_player
    else:
        # Significa que el ataque ha sido un fracaso, por lo que el defensor gana felicidad y el atacante la pierde
        if state.owners[d_idx]!=None:
            #Si el territorio enemigo no era independiente gana felicidad
            updateHappiness(state,state.owners[d_idx],BONO_HAPP_DEFEND_WIN)
            updateHappiness(state,state.current_player,BONO_HAPP_ATTACK_LOSS)
  
    
    return outcome_probability
