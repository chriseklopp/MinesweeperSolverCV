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

import numpy as np


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

