import copy
cube = bytearray([
    0,0,0, 0,0,0, 0,0,0,   # U
    1,1,1, 1,1,1, 1,1,1,   # R
    2,2,2, 2,2,2, 2,2,2,   # F
    3,3,3, 3,3,3, 3,3,3,   # D
    4,4,4, 4,4,4, 4,4,4,   # L
    5,5,5, 5,5,5, 5,5,5,   # B
])

U_CYCLES = [
    (0, 2, 8, 6),   # U face corners
    (1, 5, 7, 3),   # U face edges
    (36, 18, 9, 45), # UL->UF->UR->UB (left sticker of each top row)
    (37, 19, 10, 46),
    (38, 20, 11, 47),
]

R_CYCLES = [
    (9, 11, 17, 15), (10, 14, 16, 12),          # R face
    (2, 20, 29, 51), (5, 23, 32, 48), (8, 26, 35, 45),  # U->F->D->B
]

F_CYCLES = [
    (18, 20, 26, 24), (19, 23, 25, 21),          # F face
    (6, 9, 29, 44), (7, 12, 28, 41), (8, 15, 27, 38),   # U->R->D->L
]

class BaseSolver:
    def __init__(self, cube_array):
        if len(cube_array) == 54:
            count = [0]*6
            for i in cube_array:
                if i not in (0,1,2,3,4,5):
                    raise Exception("Solver initialised with cube array with errors (does not have correct numbers)")
                count[i] += 1
            if count != [9]*6:
                raise Exception("Solver initialised with cube array with errors (does not have correct amounts of numbers)")
            self.cube = cube_array
        else:
            raise Exception("Solver initialised with non cube array")
    
    def apply_cycles(self, cycles):
        new = copy.copy(self.cube)
        for cycle in cycles:
            a, b, c, d = cycle
            new[b] = self.cube[a]
            new[c] = self.cube[b]
            new[d] = self.cube[c]
            new[a] = self.cube[d]
        self.cube = new
        return self.cube

    def cycles_to_permutation(self, cycles):
        perm = list(range(54))  # start as identity: cell i comes from i
        for cycle in cycles:
            a, b, c, d = cycle
            perm[b] = a  # cell b gets its value from cell a
            perm[c] = b
            perm[d] = c
            perm[a] = d
        return perm

    def apply_perm(self, state, perm):
        return bytearray(state[i] for i in perm)

    def __str__(self):
        message = ""
        cube_list = list(self.cube)
        # U
        for i in range(3):
            message += " "*22
            for j in range(3):
                message += str(i*3+j) + ": "
                message += str(cube_list[i*3+j])
                message += ", "
            message += "\n"
        message += "\n"

        # L F R B
        for i in range(3):
            for j in (4,2,1,5):
                for k in range(3):
                    message += str(i*3+j*9+k) + ": "
                    message += str(cube_list[i*3+j*9+k])
                    message += ", "
                message += " "
            message += "\n"
        message += "\n"

        # D
        for i in range(3):
            message += " "*22
            for j in range(3):
                message += str(i*3+j+27) + ": "
                message += str(cube_list[i*3+j+27])
                message += ", "
            message += "\n"
        message += "\n"
        return message
    
if __name__ == "__main__":
    newSolver = BaseSolver(cube)
    print(str(newSolver))
    newSolver.apply_cycles(U_CYCLES)
    print(str(newSolver))
    newSolver.apply_cycles(F_CYCLES)
    print(str(newSolver))

    
