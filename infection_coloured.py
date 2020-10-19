# INSTRUCTIONS
# 1 create a matrix of size i,j
# 2 X percent of cells are "infected"
# 3 after n iterations, on every iteration, all the infected cells have a Y percent chance of infecting neigbouring cells
# 4 cells can only neigbour by horizontal and vertical, no diagonal
# 5 on the nth iteration: give the most optimal route from the (0,0) cell to the (i-1,j-1) cell as a map of cell coordinates
# 6 no lists/arrays/matricies/etc (can use abstractions of lists)

# PLAN
# 1 create initial infection scenario
#     - randomly select X% of cells to infect (not top left or bottom right though)
# 2 develop infection over n iterations
#     - for each iteration, try to infect the neighbours of cells infected in previous generations (if they aren't already infected)
# 3 find optimal path through infection scenario
#     - build an adjacency list from vacancies between infected cells and breadth-first-search for shortest path

# NOTES
# used dictionaries to mostly replace lists, was a little trickier but ultimately a more robust solution
# deques were used to maintain order in the adjacency list and for their O(1) pops and appends
# overall program is pretty robust, handles small matricies well and i think large too (although this is hard to verify)
# if i had more time i would probably like to write a test suite to check edge and corner cases
# was thoroughly stumped by the no lists requirements for a good day or so but was rewarding to find a nice solution to it

import sys
import os
import math
import random
import argparse
from collections import deque, OrderedDict
from termcolor import colored
os.system('color')

# USEAGE AND INPUT HANDLING
# argparse handles input exceptions really well, tidies up code and gets rid of big try/except blocks
parser = argparse.ArgumentParser(
    description = '''Infection propagation and path finding program''',
    epilog = '''Agerris coding problem courtesy of Tys Lowde''')
parser.add_argument('rows', type=int, help='number of rows')
parser.add_argument('cols', type=int, help='number of cols')
parser.add_argument('seed', type=float, help='percentage of initially infected cells')
parser.add_argument('risk', type=float, help='percentage chance of infection transmission')
parser.add_argument('iterations', type=int, help='number of times to propagate the infection')
args = parser.parse_args()

rows = int(sys.argv[1])
cols = int(sys.argv[2])
seed = float(sys.argv[3])
risk = float(sys.argv[4])
iterations = int(sys.argv[5])

# check input args to make sure they are in the correct range since argeparse has already checked type
if rows <= 0:
    print("error: rows must be a positive integer")
    sys.exit(1) # incorrect argument type
elif cols <= 0:
    print("error: cols must be a positive integer")
    sys.exit(1) # incorrect argument type
elif seed < 0 or seed > 1:
    print("error: seed must be a float between 0 and 1")
    sys.exit(1) # incorrect argument type
elif risk < 0 or risk > 1:
    print("error: risk must be an integer between 0 and 1")
    sys.exit(1) # incorrect argument type
elif iterations < 0:
    print("error: iterations must be a positive integer")
    sys.exit(1) # incorrect argument type

# SOLUTION IMPLEMENTATION
# Opted for an OOP approach to keep program logic linear and code tidy
class Infection:

    def __init__(self, rows, cols, seed, risk, iterations):
        self.rows = rows
        self.cols = cols
        self.seed = seed
        self.risk = risk
        self.iterations = iterations
        self.generation = 0
        self.size = rows * cols
        self.route = None
        self.infected = {}
        for i in range(self.size):
            self.infected[i] = None

    def spawn(self): # used a set to prevent top left and bottom right cells being chosen as seeds, then pass to infect() to avoid repeating code later
        '''
        spawn initial infection scenario
        '''
        positions = set(self.infected.keys())
        positions.difference_update({0, self.size - 1})
        for _ in range(math.floor(self.size * self.seed)):
            random_pos = random.choice(tuple(positions))
            self.infect(random_pos, 1)
            positions.remove(random_pos)

    def infect(self, pos, risk=None): # risk is 100% chance of infection for seeds and then user input for rest of the program, if infection is successful the dictionary value for the cell is updated to the current generation
        '''
        try to create an infected cell at a given position
        '''
        ir = self.risk if risk is None else risk
        if random.random() <= ir and pos not in {0, self.size - 1}:
            self.infected[pos] = self.generation

    def get_neighbours(self, pos): # helper function to easily find cell neighbours, defaults to None if no neighbour in a specific direction, returns a dictionary for fast lookup later
        '''
        return the neighbouring positions of a given cell
        '''
        up = None if pos - self.cols < 0 else pos - self.cols
        down = None if pos + self.cols >= self.size else pos + self.cols
        left = None if pos % self.cols == 0 else pos - 1
        right = None if (pos + 1) % self.cols == 0 else pos + 1
        return {'u': up, 'd': down, 'l': left, 'r': right}

    def propagate(self): # main logic loop, dictionary makes it quick and easy to ensures only cells infected on the previous iteration can transmit the infection on the current iteration
        '''
        spread infection from initial scenario
        '''
        while self.generation < self.iterations:
            self.show_infection()
            self.generation += 1
            for pos, gen in self.infected.items():
                if gen is not None and gen < self.generation:
                    neighbours = self.get_neighbours(pos)
                    for _, n in neighbours.items():
                        if n is not None:
                            self.infect(n)
        
    def adjacency_list(self): # main data structure used for path finding, deque() is used for O(1) appends and pops, it also naturally lends to bfs on an unweighted graph
        '''
        return adjacency list of vacancies between infected cells
        '''
        adjacency_list = {}
        for pos, gen in self.infected.items():
            if gen is None:
                adjacency_list[pos] = deque()
                neighbours = self.get_neighbours(pos)
                for _, n in neighbours.items():
                    if n is not None:
                        if self.infected[n] is None:
                            adjacency_list[pos].append(n)
        # print("\n".join("{}\t{}".format(k, v) for k, v in adjacency_list.items()))
        return adjacency_list

    def bfs(self): # standard bfs implementation, maybe slightly faster than usual with deque? treat non-infected cells like nodes in an unweighted graph in order to find shortest path between top left and bottom right
        '''
        try to find shortest path between top left cell and bottom right cell using BFS
        '''
        alist = self.adjacency_list()
        start = deque()
        start.append(0)
        goal = self.size - 1
        queue = deque()
        visited = deque()
        queue.insert(0, start)
        while queue:
            path = queue.popleft()
            cell = path[-1]
            if cell not in visited:
                neighbours = alist[cell]
                for n in neighbours:
                    new_path = deque(path)
                    new_path.append(n)
                    queue.append(new_path)
                    if n == goal:
                        return new_path
                visited.append(cell)
        return None

    def compute_path(self): # logic to compute positions into i, j coordinates and then print them as output to the console
        '''
        computes (i, j) coordinates from shortest path positions
        '''
        self.route = self.bfs()
        if self.route is None:
            print("No path could be found.")
            sys.exit(0) # program finished successfully
        else:
            path = OrderedDict()
            for pos in self.route:
                i = math.floor(pos / self.rows)
                j = pos % self.cols
                path[pos] = (i, j)
            for _, coordinate in path.items():
                print(coordinate)
            self.show_infection()
            sys.exit(0) # program finished successfully

    def show_infection(self): # useful debugging tool, displays a nice little graph of the infection, was fun to write. used the initail None condition for cells in the infected dictionary to work out where to display markers
        '''
        *for debugging* visualises the infection
        '''
        print("  ", end = "")
        for j in range(self.cols):
            print("  {} ".format(j), end = "")
        print("")
        for i in range(self.rows):
            print("  " + ("+" + "-" * 3) * self.cols + "+")
            print("{} ".format(i), end = "")
            for j in range(self.cols):
                if self.route is not None and i * self.cols + j in self.route:
                    print("| ", end="")
                    print(colored("x", "green", attrs=['bold']), end="")
                    print(" ", end="")
                elif self.infected[(i * self.cols + j)] is None:
                    special_char = " "
                    print("|" + " {} ".format(special_char), end="")
                else:
                    print("| ", end="")
                    print(colored("o", "red", attrs=["bold"]), end="")
                    print(" ", end="")
            print("|")
        print("  " + ("+" + "-" * 3) * self.cols + "+")
        print("generation: {}".format(self.generation))


if __name__ == "__main__": # thought it was a bit nicer to instantiate a new "infection" case for each run of the problem. also makes it easier to test method functionality
    infection = Infection(rows, cols, seed, risk, iterations)
    infection.spawn()
    infection.propagate()
    infection.compute_path()
    
