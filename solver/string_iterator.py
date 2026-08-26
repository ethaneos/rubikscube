class StringIterator:
    """This class allows you to iterate through combinations of moves"""
    
    def __init__(self, move_list: list) -> None:
        """Init creation function for StringIterator

        Parameters
        ----------
        move_list : list
            A list of possible moves
        """

        self.move_list = move_list
        self.up_to = [0]

    def iterate(self, up_to_index: int) -> None:
        """Increments the up_to list

        Parameters
        ----------
        up_to_index : int
            The index of up_to to check
        """

        if up_to_index == -1:
            for i in range(len(self.up_to)):
                self.up_to[i] = 0
            self.up_to.append(0)
        else:
            self.up_to[up_to_index] += 1
            if self.up_to[up_to_index] == len(self.move_list):
                self.up_to[up_to_index] = 0
                self.iterate(up_to_index-1)

    def get_next(self) -> str:
        """Returns the next combination of possible moves to try

        Returns
        -------
        str
            A sequence of the next combination of moves
        """

        self.iterate(len(self.up_to)-1)
        return " ".join([self.move_list[i] for i in self.up_to])

    def get_now(self) -> str:
        """Gets the current combination of possible moves

        Returns
        -------
        str
            A sequence of the current combination of moves
        """

        return " ".join([self.move_list[i] for i in self.up_to])

if __name__ == "__main__":
    si = StringIterator(("A", "B", "C", "D"))

    print(si.get_now())
    for i in range(20):
        print(si.get_next())
        