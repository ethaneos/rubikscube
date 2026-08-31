import copy
from cube_data import *
from move_translator import *
from string_iterator import *

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
            if len(cycle) == 1:
                continue
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
                    if self.curr_state[group[i]] != self.curr_state[group[i+1]]:
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

    def reset_curr(self):
        self.curr_state = self.init_state.copy()
                  
    def find_move_solns(self, min_solns: int, max_solve_len: int, *args: str) -> list[str]:
        """Finds all non-duplicate solutions using certain moves

        Parameters
        ----------
        min_solns : int
            The minimum number of solutions you want
        max_solve_len : int
            The maximum number of moves that can be used (has priority over min_solns)
        *args: str
            The moves that are allowed

        Returns
        -------
        list[str]
            A list of the combinations of moves that are solutions
        """
        translator = MoveTranslator()
        iterator = StringIterator(list(args))
        solns = []
        p_solns = []
        iterator.get_now()
        while (len(solns) < min_solns and iterator.get_length() <= max_solve_len):
            while (len(p_solns) < min_solns and iterator.get_length() <= max_solve_len):
                combination = iterator.get_next()
                move_seq = combination.split(" ")

                for move in move_seq:
                    move_cycles = translator.translate_move(move)
                    self.apply_cycles(move_cycles)
                if self.check():
                    p_solns.append(combination)
                self.reset_curr()

            # Remove any "duplicates"
            to_remove = []
            print(p_solns)
            for i in range(len(p_solns)-1):
                for j in range(i+1, len(p_solns)):
                    if p_solns[j].startswith(p_solns[i]):
                        to_remove.append(j)

            solns = []
            for i in range(len(p_solns)):
                if i not in to_remove: solns.append(p_solns[i])
            p_solns = solns
            
        return solns
                
    def find_alg_solves(self, *args):
        pass

    def save_state(self):
        self.init_state = self.curr_state
 
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
    newSolver.save_state()


    newSolver.create_check([cube_data.U_CYCLES, cube_data.R_CYCLES, cube_data.M_CYCLES])
    print(newSolver.checks)
    print(newSolver.find_move_solns(10,5, "U", "F", "F'", "U'"))

    
