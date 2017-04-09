from __future__ import print_function
import math
import numpy as np
import random
from simanneal import Annealer

class TravellingSalesmanProblem(Annealer):
    def __init__(self, distance_matrix):
        N = distance_matrix.shape[0]
        self.state = np.array([i for i in range(N)])
        self.distance_matrix = distance_matrix
        super(TravellingSalesmanProblem, self).__init__(state)  # important! 

    def move(self):
        """Swaps two cities in the route."""
        a = random.randint(0, len(self.state) - 1)
        b = random.randint(0, len(self.state) - 1)
        self.state[a], self.state[b] = self.state[b], self.state[a]

    def energy(self):
        """Calculates the length of the route."""
        e = 0
        for i in range(1,len(self.state)):
            e += self.distance_matrix[self.state[i-1]][self.state[i]]
        return e
    
    def solve(self):
        self.copy_strategy = "slice"  
        state, e = self.anneal()
        return state

if __name__ == '__main__':
    
    