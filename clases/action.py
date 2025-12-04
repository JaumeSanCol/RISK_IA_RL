import json

class RiskAction():
    """Stores the information about an action in a risk game"""
    
    def __init__(self, type, to_territory, from_territory, unidades ,to_player=None, from_player=None):
        """Initializes a RiskAction"""
        
        self.type = type
        """
         What kind of action this is? Should be a string
         possible types = (PreAssign, PrePlace, Place, Attack, Occupy, Fortify) + (Invest, Comprar Soldados, Pasar,...)
        """
        
        self.to_territory = to_territory
        """
         This stores the territory id of the place the action is going
         For Each type it contains:
               
                PreAssign: The territory id being chosen by player
               
                PrePlace:  The territory id of the territory where troop is being placed
               
                Place: The territory id of the territory where troop is being placed
                
                Attack: The territory id of the territory being attacked
               
                Occupy: The territory id of the territory into which troops are moving
               
                Fortify: The territory id of the territory into which troops are moving

                -------------------

                Comprar Soldados: None

                Invertir: None

        """

        self.from_territory = from_territory
        """
         This stores the territory id of the place the action is coming from
         For Each type it contains:

                PreAssign: None
         
                PrePlace:  None
         
                Place: None
         
                Attack: The territory id of the territory doing the attacking
         
                Occupy: The territory id of the territory from which troops are moving
         
                Fortify: The territory id of the territory from which troops are moving

                -------------------

                Comprar Soldados: None

                Invertir: None
        """
        
        self.unidades = unidades
        """
         Guarda el numero de unidades involucrada en la acción:
               
                PreAssign: None
               
                PrePlace:  None
               
                Place: None
               
                Attack: None
               
                Occupy: Number of troops moving into conquered territory
               
                Fortify: Number of troops moving to other territory

                -------------------

                Comprar Soldados: Número de soldados comprados

                Invertir: Número de Inversiones
        """

        self.to_player = to_player
        """
        Indica que jugador recibe la acción (o sobre si mismo): (enfocado a acciones que realcionen jugadores (comercio, etc.)) 

                Invertir: ID del jugador que invierte
             
        """


        self.from_player = from_player
        """
        Indica que jugador realiza la acción sobre otro (no sobre si mismo): (enfocado a acciones que realcionen jugadores (comercio, etc.)) 
             
        """


    def print_action(self):
        """Displays information about this action to the output"""
        print(self.description())
        
    def description(self, newline=False):
        """returns string description of this action, useful for display"""
        
        parts = [str(self.type)]
        
        if self.type in ['Attack', 'Occupy', 'Fortify']:
            parts.append(f'FROM: {self.from_territory}')
        
        if self.type in ['Place', 'PrePlace']:
            parts.append(f'IN: {self.to_territory}')
        elif self.type in ['PreAssign', 'Attack', 'Occupy', 'Fortify']:
            parts.append(f'TO: {self.to_territory}')
        
        if self.type in ['Occupy', 'Fortify', 'Comprar_Soldados','Invertir']:
            parts.append(f'NUM: {self.unidades}')
            
        if self.type == 'Invest':
            parts.append(f'ON_PLAYER: {self.to_player}')
            
        separator = "\n" if newline else " "
        return separator.join(parts)
    
    def to_string(self):
        """Saves this action to a string"""
        s = 'RISKACTION|' + json.dumps(self.type) + '|' + json.dumps(self.to_territory) + '|' + json.dumps(self.from_territory) + '|' + json.dumps(self.unidades)+ '|' + json.dumps(self.to_player)+ '|' + json.dumps(self.from_player)
        return s
        
    def from_string(self, s):
        """Loads this action from a string"""
        ss = s.split('|')
        if ss[0] != 'RISKACTION':
            print('THIS IS NOT A RISK ACTION STRING!')
        self.type = json.loads(ss[1])
        self.to_territory = json.loads(ss[2])
        self.from_territory = json.loads(ss[3])
        self.unidades = json.loads(ss[4])
        self.to_player = json.loads(ss[5])
        self.from_player = json.loads(ss[6])