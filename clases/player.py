import json
from config_atrib import *

class RiskPlayer():
    """Stores all information about a player in the game"""
    def __init__(self, name, id, free_armies, conquered_territory,economy, happiness,development,game_over=False):
        """Initializes the various components of this RiskPlayer object"""
        self.name = name
        """ The Player's name (string) """
        
        self.id = id
        """ The Player's id (integer) """

        self.free_armies = free_armies
        """ The number of armies this player has in hand, waiting to be placed on the board """

        self.conquered_territory = conquered_territory
        """ A boolean stating whether or not this player conquered a territory on their current turn """

        self.economy=economy
        """ La cantidad de recursos que tiene el jugador para gastar. Permite ciertas acciones"""

        self.happiness=happiness
        """ El nivel de satisfacción de la sociedad. Puede derrocar el gobierno o mejorar la economia"""

        self.development=development
        """ El nivel de desarrollo que tiene el país. Puede mejorar la economia o aumentar el descontento"""
        self.game_over=game_over
    
    def add_armies(self, n):
        """Adds a number (n) of armies to the player's free_armies count"""
        self.free_armies += n
        self.economy-= SOLDADOS_PRC*n
    
    def print_player(self, board, indent=0):
        """Displays information about this player to the output"""
        for i in range(indent):
            print(' ',)
        print('<', self.name, '[', self.id, ']> (', self.free_armies, ' free armies )')
        for i in range(indent+2):
            print(' ',)
        
    def copy_player(self):
        """Creates a copy of this player and returns it"""
        np = RiskPlayer(self.name, self.id, self.free_armies, self.conquered_territory,self.economy,self.happiness,self.development,self.game_over)
        return np
        
    def to_string(self):
        """Saves this player to a string"""
        s = json.dumps(self.name) + '$' + json.dumps(self.id)  + '$' + json.dumps(self.free_armies) + '$' + json.dumps(self.conquered_territory)+'$'+ json.dumps(round(float(self.economy),1)) + '$' + json.dumps(self.happiness)+'$'+ json.dumps(round(float(self.development),1))+ '$' + json.dumps(self.game_over)
        return s
        
    def from_string(self, s):
        """Loads player information from a string"""
        ss = s.split('$')
        self.name = json.loads(ss[0])
        self.id = json.loads(ss[1])
        self.free_armies = json.loads(ss[2])
        self.conquered_territory = json.loads(ss[3])
        self.economy=json.loads(ss[4])
        self.happiness=json.loads(ss[5])
        self.development=json.loads(ss[6])
        self.game_over=json.loads(ss[7])
    