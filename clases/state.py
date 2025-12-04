import json
from .player import RiskPlayer
class RiskState():
    """Stores all the information about a state of a Risk game"""
    
    def __init__(self,fase, players, armies, owners, current_player, turn_type, turn_in_number, last_attacker, last_defender, board,mes=6):
        """Initializes a RiskState object"""
    
        self.fase=fase
        """Indica en cual de las fases del turno nos encontramos"""

        self.players = players
        """An array of RiskPlayer objects (the players in the game)"""
        
        self.armies = armies
        """
         An array of integers, indexed by territory id number, that 
         stores the number of armies on that territory
        """
        self.owners = owners
        """
         An array of integers, indexed by territory id number, that 
         stores the player id number of the player who owns that territory
        """
        self.current_player = current_player
        """ The player id number of the current player (player whose turn it is) """
        
        self.turn_type = turn_type
        """
         What kind of turn is it currently 
         Choices = (PreAssign, PrePlace, Place, Attack, Occupy, Fortify, GameOver)
        """

        self.turn_in_number = turn_in_number
        """ How many card sets have been turned in? """
        
        self.last_attacker = last_attacker
        """
         What is the territory id of the last territory that was attacking 
         Important to determine troop movements after territory is conquered
        """
        self.last_defender = last_defender
        """
         What is the territory id of the last territory that was defending 
         Important to determine troop movements after territory is conquered
        """
        
        self.board = board
        """
         A RiskBoard object that stores all the non-changing information about
         this risk game
        """

        self.mes = mes
        """Indica en que més del año estamos"""

    def to_string(self):
        """Saves this state to a string"""
        s = 'RISKSTATE|'
        #players
        for p in self.players:
            s = s + p.to_string()
            s = s + ';'
        s = s + '|' + json.dumps(self.fase)+'|' + json.dumps(self.armies) + '|' + json.dumps(self.owners) + '|'
        s = s + json.dumps(self.current_player) + '|' + json.dumps(self.turn_type) + '|'+json.dumps(self.turn_in_number)+"|"
        s = s + json.dumps(self.last_attacker) + '|' + json.dumps(self.last_defender)+ '|' + json.dumps(self.mes) 
        return s
        
    def from_string(self, s, board):
        """Loads this state from a string"""
        ss = s.split('|')
        if ss[0] != 'RISKSTATE':
            print('THIS IS AN INVALID RISKSTATE')
        ps = ss[1].split(';')
        self.players = []
        for p in ps:
            if p:#len(p) > 0:
                np = RiskPlayer(None, None, None, None,None,None,None)
                np.from_string(p)
                self.players.append(np)
        
        self.fase= json.loads(ss[2])
        self.armies = json.loads(ss[3])
        self.owners = json.loads(ss[4])
        self.current_player = json.loads(ss[5])
        self.turn_type = json.loads(ss[6])
        self.turn_in_number = json.loads(ss[7])
        self.last_attacker = json.loads(ss[8])
        self.last_defender = json.loads(ss[9])
        self.mes=json.loads(ss[10])
        self.board = board
        
    def print_state(self):
        """Displays information about this state to the output"""
        print('PLAYERS')
        for p in self.players:
            p.print_player(self.board)
        
        print('OWNERS/ARMIES')
        for i in range(len(self.armies)):
            if self.owners[i] in self.board.id_to_player:
                print(self.board.territories[i].name, '[', self.board.id_to_player[self.owners[i]], '] : ', self.armies[i])
            else:
                print(self.board.territories[i].name, '[', self.owners[i], '] : ', self.armies[i])
        
        if self.current_player < len(self.players):
            print('CURRENT PLAYER: ', self.players[self.current_player].name, '[', self.current_player, ']')
        else:
            print('CURRENT PLAYER: ??? [', self.current_player, ']')
        
    def copy_state(self):
        """
        Creates a (deep) copy of this state and return it. Modifications to new state won't change original, except for the risk board, of which there is only one (it shouldn't be modified!)
        """
        copy_players = []
        for p in self.players:
            copy_players.append(p.copy_player())
        return RiskState(self.fase,copy_players,self.armies[:],self.owners[:],self.current_player,self.turn_type,self.turn_in_number, self.last_attacker, self.last_defender,self.board,self.mes)

