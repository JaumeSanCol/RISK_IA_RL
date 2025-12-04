import json


class RiskContinent():
    """Stores all information related to a continent"""
    def __init__(self, name, reward):
        """Initializes the continent information"""
        self.name = name
        """The name of this continent (string) """
        
        self.reward = reward
        """
         The reward for this continent 
         This is the number of troops bonus that a player gets if the player 
         owns all of the territories in this continent
        """
        self.territories = []
        """ A list of the territory id numbers of the territories in this continent"""        

    def add_territory(self, territory):
        """Adds a territory to this continent"""
        if territory not in self.territories:
            self.territories.append(territory)
    
    def print_continent(self,board,indent=0):
        """Displays information about continent to output"""
        for i in range(indent):
            print(' ',)
        print('{', self.name, '} : ', self.reward)
        for t in self.territories:
            board.territories[t].print_territory(board, indent+2)
    
    def to_string(self):
        """Save continent information to string"""
        s = json.dumps(self.name) + '&' + json.dumps(self.reward) + '&' + json.dumps(self.territories)
        return s
    
    def from_string(self, s):
        """Load continent information from string"""
        ss = s.split('&')
        self.name = json.loads(ss[0])
        self.reward = json.loads(ss[1])
        self.territories = json.loads(ss[2])

 