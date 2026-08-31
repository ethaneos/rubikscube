from cube_data import *

class MoveTranslator:
    """A class that translates move information from text to cycles"""
    def translate_move(self, move: str) -> list:
        """Translates most possible moves to a cycle that can be used by a solver

        Parameters
        ----------
        move : str
            The move to translate

        Returns
        -------
        list
            The corresponding cycles
        """

        cube_data = CubeData()
        assert len(move) in [1,2,3]
        cycles = getattr(cube_data, move[0].upper() + "_CYCLES")
        if len(move) == 1:
            return cycles
        elif len(move) == 2:
            if move[1] == "2":
                return self.multiply_cycles(cycles, 2)
            if move[1] == "'":
                return self.multiply_cycles(cycles, 3)
            if move[1] == "w":
                cycles += self.translate_move(getattr(cube_data, "wide")[move[0].upper])
                return cycles
        elif len(move) == 3:
            if move[1] == 'w':
                if move[2] == "2":
                    return self.multiply_cycles(cycles, 2)
                if move[2] == "'":
                    return self.multiply_cycles(cycles, 3)


    def multiply_cycles(self, cycles: list, factor: int) -> list:
        """Creates cycles from an existing group of cycles corresponding to when the cycle is applied multiple times

        Parameters
        ----------
        cycles : list
            The cycles to multiply
        factor : int
            The number of times the cycle is repeates

        Returns
        -------
        list
            The new list of cycles
        """
        
        new_cycles = []
        used_faces = []
        for cycle in cycles:
            for i in range(len(cycle)):
                if cycle[i] not in used_faces:
                    new_cycle = [cycle[i]]
                    for j in range(1,5):
                        if cycle[i] != cycle[(i + factor * j) % len(cycle)]:
                            new_cycle.append(cycle[(i + factor * j) % len(cycle)])
                        else:
                            break
                    new_cycles.append(tuple(new_cycle))
                    used_faces += new_cycle
        return new_cycles

    def cycles_to_permutation(self, cycles: list) -> list:
        """Converts a list of cycles to a permutation (translates an set of moves into an algorithm)

        Parameters
        ----------
        cycles : list
            The cycles that form the permutation

        Returns
        -------
        perm : list
            The resultant permutation
        """

        perm = list(range(54))  # start as identity: cell i comes from i
        for cycle in cycles:
            a, b, c, d = cycle
            perm[b] = a  # cell b gets its value from cell a
            perm[c] = b
            perm[d] = c
            perm[a] = d
        return perm

if __name__ == "__main__":
    t = MoveTranslator()
    print(t.translate_move("U"))
    print(t.translate_move("U'"))
    print(t.translate_move("F"))
    print(t.translate_move("F'"))