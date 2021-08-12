"""
MCoordinate is a container for pixel coordinates (X,Y).
Can be added or subtracted to/from other objects of the same time
Cuts down on the amount of nested indexing required
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
        x = self.x - other.y
        y = self.x - other.y
        return MCoordinate(x, y)

    def values(self):
        return self.x, self.y
