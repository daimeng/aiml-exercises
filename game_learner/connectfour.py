from qlearn import *
import numpy as np
import random

# Set of states: (player, 7-tuple of strings of 0 and 1 of length in [0, 6], winner or None if not terminal)
# Set of actions: integers [0, 6]

class C4MDP(MDP):
    def __init__(self):
        super().__init__(None, range(0, 7), discount=1, num_players=2)
        self.symb = {'0': "O", '1': "X", '': "-"}

    def board_str(self, s):
        rows = ["|" for i in range(6)]
        p, cols, _ = s
        out = ""
        out += f"Current player: {self.symb[str(p)]}\n"
        for col in cols:
            for c in range(6):
                rows[5 - c] += self.symb[''] if c >= len(col) else self.symb[col[c]]
        for row in rows:
            out += f"{row}|\n"
        out += "|1234567|"
        return out

    def get_actions(self, state):
        notfull = []
        for i in range(7):
            if len(state[1][i]) < 6:
                notfull.append(i)
        if len(notfull) > 0:
            return notfull
        else:
            return self.actions
    
    def state_to_tensor(self, state):
        # Ignore player and winner
        tensor = np.zeros((2,7,6), dtype=float)
        for i in range(7):
            for j in range(len(state[1][i])):
                tensor[int(state[1][i][j])][i][j] = 1.
        return tensor
    
    def action_to_tensor(self, action):
        tensor = np.zeroes((7,))
        tensor[action] = 1.
        return tensor

    # Reward is 1 for winning the game, -1 for losing, and 0 for a tie; awarded upon entering terminal state
    def transition(self, state, a):
        # Copy it
        p, s, _ = state
            
        # Check if move is valid, i.e. if the column is full and if a is in the set of actions
        # If it's not a valid move, give a penalty (a large penality; it should learn to never make these moves)
        if a not in self.actions or len(s[a]) >= 6:
            if p == 0:
                penalty = (-1000, 0,)
            else:
                penalty = (0, -1000)
            return state, penalty
        
        # If the move is valid, make it
        b = list(s)
        b[a] += str(p)
        b = tuple(b)

        # Check for a new winner, i.e. a winner made by the current move, which can only be the current player
        # w = (1, -1) if p == 0 else (-1, 1)
        # w = (1 - 2*p, -1 + 2*p)
        if self.four(p, b, a):
            return (1 - p, b, p), (1 - 2*p, -1 + 2*p)
        else:
            return (1 - p, b, None), (0, 0)
    
    def get_initial_state(self, start_player = 0):
        if start_player != 0 and start_player != 1:
            start_player = random.choice((0,1))
        return (start_player, ("","","","","","",""), None)
    
    # The game is short enough that maybe we don't care about intermediate states
    def get_random_state(self):
        return self.get_initial_state()

    def is_terminal(self, state):
        return False if state[2] == None else True
    
    # '0' or '1' for a player, '' for empty
    def get_by_coords(self, s, row, col):
        return '' if (row >= len(s[col]) <= row or row < 0) else s[col][row]

    # Determine if the move in the indicate column created new four
    def four(self, p, s, a):
        # Check the column; it has to be at the top, i.e. end
        if len(s[a]) >= 4 and s[a][-4:] == str(p) * 4:
            return True

        # Check the row
        r = len(s[a]) - 1
        length = 1
        # To the right
        for i in range(a+1, 7):
            if self.get_by_coords(s, r, i) != str(p):
                break
            length += 1
        # To the left
        for i in range(a-1, -1, -1):
            if self.get_by_coords(s, r, i) != str(p):
                break
            length += 1
        if length >= 4:
            return True
        
        # Check the up-diagonal
        length = 1
        # To the right
        for i in range(a+1, 7):
            if self.get_by_coords(s, r+i-a, i) != str(p):
                break
            length += 1
        # To the left
        for i in range(a-1, -1, -1):
            if self.get_by_coords(s, r+i-a, i) != str(p):
                break
            length += 1
        if length >= 4:
            return True
        
        # Check the down-diagonal
        length = 1
        # To the right
        for i in range(a+1, 7):
            if self.get_by_coords(s, r-i+a, i) != str(p):
                break
            length += 1
        # To the left
        for i in range(a-1, -1, -1):
            if self.get_by_coords(s, r-i+a, i) != str(p):
                break
            length += 1
        if length >= 4:
            return True
        
        return False
        

    def is_full(self, state):
        s = state[1]
        for row in s:
            if len(row) < 6:
                return False
        return True
    



# Some prototyping the neural network
# Input tensors have shape (batch, 7, 2, 7, 6)
nn.Flatten(0, 1)
nn.Conv2d(2, 64, (4,4), padding='same')
nn.Unflatten(0, (-1, 7))
nn.ReLU()
nn.Dropout(p=0.2)
nn.BatchNorm2d(64)
nn.Flatten()
nn.Linear(7*2*7*6*64, 7*2*7*6*64)
nn.ReLU()
nn.Linear(7*2*7*6*64, 1) # ok im still confused about whether we are learning q or learning p
