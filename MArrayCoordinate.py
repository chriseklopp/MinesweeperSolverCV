"""
MArrayCoordinate is a container for i/j array coordinates
Can be added or subtracted to/from other objects of the same time
Cuts down on the amount of nested indeiing required
MCoordinate knows no distinction between piiel coordinates, and array coordinates. So it is up to the user to ensure
they don't mii them together.



j ----------->

i
|
|
|
V

"""

# For some reason numpy index [j,i,k] so we have to do it like that

# is it actually [i,j,k] ?????
import numpy as np


class MArrayCoordinate:

    def __init__(self, *args):
        if len(args) == 2:
            i = args[0]
            j = args[1]
        elif len(args) == 1:
            if isinstance(args[0], tuple):
                i = args[0][0]
                j = args[0][1]

        else:
            raise TypeError("Invalid arguments in MArrayCoordinate initialization")

        self.i = np.intc(i)
        self.j = np.intc(j)

    def __add__(self, other):
        i = self.i + other.i
        j = self.j + other.j
        return MArrayCoordinate(i, j)

    def __sub__(self, other):
        i = self.i - other.i
        j = self.j - other.y
        return MArrayCoordinate(i, j)

    def __str__(self):
        return f"({self.i}, {self.j})"

    def values(self):
        return self.i, self.j
