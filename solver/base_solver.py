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
    (18, 20, 26, 24), (19, 23, 25, 21),
    (6, 9, 29, 44), (7, 12, 28, 41), (8, 15, 27, 38),
]

D_CYCLES = [
    (27, 29, 35, 33), (28, 32, 34, 30),
    (42, 24, 15, 51), (43, 25, 16, 52), (44, 26, 17, 53),
]

L_CYCLES = [
    (36, 38, 44, 42), (37, 41, 43, 39),
    (0, 18, 27, 53), (3, 21, 30, 50), (6, 24, 33, 47),
]

B_CYCLES = [
    (45, 47, 53, 51), (46, 50, 52, 48),
    (2, 36, 33, 17), (1, 39, 34, 14), (0, 42, 35, 11),
]

M_CYCLES = [
    (1, 19, 28, 52), (4, 22, 31, 49),
    (7, 25, 34, 46),
]

E_CYCLES = [
    (39, 21, 12, 48), (40, 22, 13, 49),
    (41, 23, 14, 50), 
]

S_CYCLES = [
    (3, 10, 32, 43), (4, 13, 31, 40),
    (5, 16, 30, 37), 
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
            self.init_state = cube_array
            self.curr_state = cube_array
        else:
            raise Exception("Solver initialised with non cube array")
        
        self.checks = []
    
    def apply_cycles(self, cycles):
        new = copy.copy(self.curr_state)
        for cycle in cycles:
            a, b, c, d = cycle
            new[b] = self.curr_state[a]
            new[c] = self.curr_state[b]
            new[d] = self.curr_state[c]
            new[a] = self.curr_state[d]
        self.curr_state = new
        return self.curr_state

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


    def check(self):
        for check in self.checks:
            for group in check:
                for i in range(len(group)-1):
                    if self.curr_state[i] != self.curr_state[i+1]:
                        return False
        return True

    def create_check(self, *cycle_intersects):
        checks = []
        for i in range(len(cycle_intersects)):
            check = []
            part_sides = []
            for j in range(len(cycle_intersects[i])-1):
                other_cycles_full = []
                for k in range(j+1, len(cycle_intersects[i])):
                    for cycle_part in cycle_intersects[i][k]:
                        for part_side in cycle_part:
                            other_cycles_full.append(part_side)
                for cycle_part in cycle_intersects[i][j]:
                    for part_side in cycle_part:
                        if part_side in other_cycles_full and part_side not in part_sides:
                            part_sides.append(part_side)
            
            for part_side in part_sides:
                assigned = False
                if len(check) > 0:
                    for group in check:
                        if group[0] // 9 == part_side // 9:
                            group.append(part_side)
                            assigned = True
                            break
                    if assigned == False:
                        check.append([part_side])
                else:
                    check.append([part_side])
            
            new_check = []
            for group in check:
                if len(group) != 1:
                    new_check.append(group)
            
            checks.append(new_check)
        self.checks += checks
                    


 
    def __str__(self):
        message = ""
        cube_list = list(self.curr_state)
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

    newSolver.create_check([U_CYCLES, R_CYCLES, M_CYCLES])
    print(newSolver.checks)

    
