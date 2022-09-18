

from enum import Enum
import numpy as np


class ActionTypes(Enum):
    SOLVE = 1
    RESET = 2
    END = 3


class MAction:
    def __init__(self, atype: ActionTypes, instid: int, data: list):
        self.atype = atype
        self.instance_id = instid
        self.data = data


"""
MCoordinate is a container for X/Y coordinates.
Can be added or subtracted to/from other objects of the same time
Cuts down on the amount of nested indexing required
MCoordinate knows no distinction between pixel coordinates, and array coordinates. So it is up to the user to ensure
they don't mix them together.



x ----------->
y
|
|
|
V

"""


class MCoordinate:

    def __init__(self, x, y):
        self.x = np.intc(x)
        self.y = np.intc(y)

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        return MCoordinate(x, y)

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return MCoordinate(x, y)

    def values(self):
        return self.x, self.y


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
