import json
from .player import RiskPlayer
from .continent import RiskContinent
from .territory import RiskTerritory
class RiskBoard():
    """
    Stores all of the information about the current Risk game that doesn't change
    over the course of the game, things like:
        
        Which territories make up the map
        
        Which territories are connected to which
        
        What the continents are and which territories they are composed of
        
        What the sequence of card turn-in values is
        
        What players are in the game

    """
    def __init__(self):
        """
        Initialize a Risk Board.
        All of the variables are initially empty.  
        They should be filled in through other function calls
        """
        
        self.players = []               
        """ An array of RiskPlayer objects """
        
        self.player_to_id = dict()
        """ A dictionary which is indexed by player name and stores the id number of that player """

        self.id_to_player = dict()
        """ A dictionary which is indexed by player id and stores the player name of that player """
        
        self.territories = []           
        """ An array of RiskTerritory objects """
        self.territory_to_id = dict()
        """ A dictionary which is indexed by territory name and stores the id number of that territory """        

        self.continents = dict()        
        """ A dictionary of RiskContinent objects indexed by continent name, stores corresponding RiskContinent object """
        
        self.turn_in_values = []
        """ 
         An array of the card turn-in-values 
         turn_in_values[i] gives the number of troops
         received for the i-th card turn-in
        """

        self.increment_value = 0
        """ A number specifying the incremental gain in received troops for card turn-ins beyond the length of turn-in-values array """
        
        
    def from_string(self, s):
        """
        Load RiskBoard information from a string.  
        We assume the string was created by the to_string 
        function.
        """
        ss = s.split('|')
        #Players
        ssp = ss[1].split(';')
        for p in ssp:
            if len(p) > 0:
                np = RiskPlayer(None,None,None,None,None,None)
                np.from_string(p)
                self.add_player(np)
        #Territories
        sst = ss[2].split(';')
        for t in sst:
            if t:
                nt = RiskTerritory(None,None)
                nt.from_string(t)
                self.add_territory(nt)
        #Continents
        ssc = ss[3].split(';')
        for c in ssc:
            if c:
            
                nc = RiskContinent(None,None)
                nc.from_string(c)
                self.add_continent(nc)
        
    def to_string(self):
        """Save the current RiskBoard to a string.  This is used to save games."""
        output_string = 'RISKBOARD|'
        #Players
        for p in self.players:
            output_string = output_string + p.to_string()
            output_string = output_string + ';'
        output_string = output_string + '|'
        #Territories
        for t in self.territories:
            output_string = output_string + t.to_string()
            output_string = output_string + ';'
        output_string = output_string + '|'
        #Continents
        for n,c in iter(self.continents.items()):
            output_string = output_string + c.to_string() + ';'
        output_string = output_string + '|'
    
        return output_string
        
    def add_player(self, player):
        """
        Add a player object to the list of players.
        Modify player_to_id and id_to_player to include new player
        """
        self.players.append(player)
        self.player_to_id[player.name] = player.id
        self.id_to_player[player.id] = player.name
        
    def add_territory(self, territory):
        """
        Add a territory object to the list of territories.
        Modify territory_to_id to include new territory
        """
        self.territories.append(territory)
        self.territory_to_id[territory.name] = territory.id
        
    def add_continent(self, continent):
        """Add a continent object to the list of continents"""
        if continent.name not in self.continents:
            self.continents[continent.name] = continent
            
    def set_turn_in_values(self, tiv):
        """Set the array of turn-in values (for card turn-ins)"""
        self.turn_in_values = tiv
        
    def set_increment_value(self, iv):
        """Set the increment value for card turn-ins beyond the end of turn_in_values"""
        self.increment_value = iv    
            
    def print_board(self):
        """Display the Risk Board to the output."""
        print('RISK BOARD')
        #PRINT TERRITORIES BY CONTINENT
        print('CONTINENTS')
        for c in self.continents.values():
            c.print_continent(self)
        #PRINT PLAYERS
        print('PLAYERS')
        for p in self.players:
            p.print_player(self)