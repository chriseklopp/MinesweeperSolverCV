"""
MWindow class
Contains information about physical game window and the play grid
Each MWindow must have a UNIQUE valid location
This class is REQUIRED for MInstance initialization, and then serves only as an information container.
"""

import cv2

class MWindow:

    def __init__(self, cords):

        self.window_loc = self._window_location(cords)

        self._grid_location = self._grid_location(self.window_loc)



        self.cords = "testcoord"
        print("test")

    @staticmethod
    def _window_location(cords):
        x = 50
        return x

    @staticmethod
    def _grid_location():
        x = 70
        return x
