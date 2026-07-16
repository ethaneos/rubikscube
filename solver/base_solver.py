import copy
from cube_data import *

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
                    
    def find_solns(self):
        pass
 
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
    cube_data = CubeData
    newSolver = BaseSolver(cube_data.cube)
    print(str(newSolver))
    newSolver.apply_cycles(cube_data.U_CYCLES)
    print(str(newSolver))
    newSolver.apply_cycles(cube_data.F_CYCLES)
    print(str(newSolver))

    newSolver.create_check([cube_data.U_CYCLES, cube_data.R_CYCLES, cube_data.M_CYCLES])
    print(newSolver.checks)

    
