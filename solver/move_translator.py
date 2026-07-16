from cube_data import *
class MoveTranslator:
    def translate_move(self, move):
        cube_data = CubeData()
        assert len(move) == 2 or len(move) == 1
        cycles = getattr(cube_data, move.upper + "_CYCLES")
        if len(move) == 2:
            if move[1] == "2":
                return self.multiply_cycles(cycles, 2)
            if move[1] == "'":
                return self.multiply_cycles(cycles, 3)

    def multiply_cycles(self, cycles, factor):
        new_cycles = []
        used_faces = []
        for cycle in cycles:
            for i in range(len(cycle)):
                if cycle[i] not in used_faces:
                    new_cycle = [cycle[i]]
                    for j in range(1,5):
                        if cycle[i] != cycle[(i + factor * j) % 4]:
                            new_cycle.append(cycle[(i + factor * j) % 4])
                        else:
                            break
                    new_cycles.append(new_cycle)
                    used_faces += new_cycle

    def cycles_to_permutation(self, cycles):
        perm = list(range(54))  # start as identity: cell i comes from i
        for cycle in cycles:
            a, b, c, d = cycle
            perm[b] = a  # cell b gets its value from cell a
            perm[c] = b
            perm[d] = c
            perm[a] = d
        return perm