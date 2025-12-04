import json

class RiskTerritory():
    """Stores all of the information for a territory"""
    def __init__(self, name, id):
        self.name = name
        """ The name of the territory (a string) """
        
        self.id = id
        """ The id number of the territory (an integer) """

        self.neighbors = []
        """ An list of the id numbers of all territories neighboring this one """

    
    def add_neighbor(self, neighbor):
        """Add a neighbor id to the neighbor list"""
        self.neighbors.append(neighbor)
    
    def print_territory(self, board, indent=0):
        """Display information about this territory to the output"""
        for i in range(indent):
            print(' ',)
        print('[', self.name, '] (', self.id, ')')
        for i in range(indent+2):
            print(' ',)
        print('Neighbors:')
        for n in self.neighbors:
            for i in range(indent+3):
                print(' ',)
            print(board.territories[n].name)
    
    def to_string(self):
        """Save the current Territory information to a string"""
        s = json.dumps(self.name) + '&' + json.dumps(self.id) + '&' + json.dumps(self.neighbors) 
        return s
        
    def from_string(self, s):
        """Load information about this territory from a string"""
        ss = s.split('&')
        self.name = json.loads(ss[0])
        self.id = json.loads(ss[1])
        self.neighbors = json.loads(ss[2])
   