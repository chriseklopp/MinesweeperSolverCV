"""
Contains solving logic for a Minesweeper puzzle
Makes ONE decision each update cycle. Though this may be changed to allow for multiple flags to be added in one cycle
Takes in board information and returns an action and a location
Though this was originally just a function, it has been made a class to make it easier to act upon previous moves
Having this isolated from the rest of the code allows for increased readability and allows for implementation of new
solving logic without breaking and other parts of the code
This class can have whatever you want in it as long as it contains an update function that returns (location, action)

WANT:
- goes down the list in order. if one is true it will start over.
0) IF FOCUS NOT NUMERIC, focus finder on numeric.
1) OBVIOUS MOVES. (Exit)
2) JUMP TO NEARBY NUMERIC <REPEAT> -add to tiles-examined
3) IF CANT JUMP TO NEARBY NUMERIC, focus finder on numeric not in tiles-examined
4) IF CANT FIND a numeric not in tiles-examined, find a numeric unsatisfied.
and Enumerate section and run Simulation on area. Make a probabilistic mine selection. (Exit)
5) RANDOM RETURN (eventually this should happen as 4) will always make better selections.) (Exit)

(marked EXIT, allow potentially escaping the recursive loop and return an action)
"""


import random
import numpy as np
from MCoordinate import MCoordinate
import cv2


class MLogicPlugin:

    def __init__(self, grid_array):
        self.bombs_remaining = 99
        self.grid_array = grid_array
        self.tiles_examined = []
        self.previous_focus = MCoordinate(0, 0)
        self.crop_handler = []

    def update(self, grid_array):
        self.tiles_examined = []
        self.grid_array = grid_array
        focus = self.previous_focus
        location, action = self.logic_flow(focus)
        return location, action

    def logic_flow(self, focus):  # this function is recursive
        self.tiles_examined.append(focus.values())
        focus_value = self.grid_array[focus.values()]
        if focus_value == 99:
            print("BAD THING HAPPEN")
            # cv2.waitKey(0)

        print("FOCUS = ", focus_value)
        focus_surrounding_tiles = self.get_surrounding_tiles(focus)

        #  ##### PART 0) #####
        if not focus_value or focus_value == 99 or np.isnan(focus_value):  # if not nonzero numeric focus
            location = self.find_disconnected_focus()
            if location:
                return self.logic_flow(location)

        #  ##### PART 1) #####
        # "RULE 1"
        if not self.is_satisfied(focus):
            adjacent_flags = 0
            adjacent_unrevealed = 0
            for location, value in focus_surrounding_tiles:
                if np.isnan(value):
                    adjacent_unrevealed += 1
                if value == 99:
                    adjacent_flags += 1
            if (focus_value - adjacent_flags) == adjacent_unrevealed:
                for location, value in focus_surrounding_tiles:
                    if np.isnan(value):
                        print(location.values(), "RULE1 RETURN", value)
                        self.previous_focus = focus
                        return location, 'right'
        # "RULE 2"
        if self.is_satisfied(focus):
            for location, value in focus_surrounding_tiles:
                if np.isnan(value):
                    print(location.values(), "RULE2 RETURN")
                    self.previous_focus = focus
                    return location, 'left'
        #  ##### PART 2) #####
        for location, value in focus_surrounding_tiles:
            if value and not np.isnan(value) and value != 99 and location.values() not in self.tiles_examined:
                return self.logic_flow(location)

        #  ##### PART 3) #####
        location = self.find_disconnected_focus(allow_examined=False, allow_satisfied=True)
        if location:
            return self.logic_flow(location)
        #  ##### PART 4) #####
        else:
            location = self.find_disconnected_focus(allow_examined=True, allow_satisfied=False)
            if location:
                crop = self.enumerate_section(location)
                sub_plot = self.grid_array[crop[0].x:crop[1].x + 1, crop[0].y:crop[1].y + 1]
                print("---------------------")
                # cv2.waitKey(0)
        #  ##### PART 5) #####
        while True:
            location = MCoordinate(random.randint(0, 29), random.randint(0, 15))
            location_value = self.grid_array[location.values()]
            if np.isnan(location_value):
                self.previous_focus = location
                print(location.values(), "RANDOM RETURN")
                return location, 'left'

    def is_satisfied(self, focus):
        value = self.grid_array[focus.x, focus.y]
        surrounding_flags = 0
        for adjacent_location, adjacent_value in self.get_surrounding_tiles(focus):
            if adjacent_value == 99:
                surrounding_flags += 1
        if surrounding_flags == value:
            return True
        else:
            return False

    def get_surrounding_tiles(self, focus):  # returns list of location = values of surrounding tiles
        surrounding_tiles = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i or j:
                    x_location = focus.x + i
                    y_location = focus.y + j
                    if 30 > x_location >= 0 and 16 > y_location >= 0:
                        tile_value = self.grid_array[x_location, y_location]
                        surrounding_tiles.append((MCoordinate(x_location, y_location), tile_value))

        return surrounding_tiles

    def find_disconnected_focus(self, allow_examined=False, allow_satisfied=True):
        # Will find a potential numeric focus target elsewhere.
        if allow_examined and allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        print((i, j), "DISCONNECTED FOCUS JUMP, EX = True")
                        return location

        if allow_examined and not allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        if not self.is_satisfied(location):
                            print((i, j), "DISCONNECTED FOCUS JUMP, EX = True")
                            return location

        if not allow_examined and allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        if location.values() not in self.tiles_examined:
                            print((i, j), "DISCONNECTED FOCUS JUMP, EX = False")
                            return location

        if not allow_examined and not allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        if location.values() not in self.tiles_examined and not self.is_satisfied(location):
                            print((i, j), "DISCONNECTED FOCUS JUMP, EX = False")
                            return location
        return 0

    def enumerate_section(self, focus):  # this is recursive, returns two MCoordinate objects, TL and BR corners.
        """
        enumerate all mine possibilities in a section around a tile. SHOULD ONLY BE USED ON AN UNSATISFIED TILE.
        start on an unsatisfied revealed tile. chain along adjacent revealed unsatisfied tiles.
        Adds the focus and its adjacent unrevealed tiles to the subset for cropping.
        """

        # THIS MAY NEED TO BE FIXED SO IT DOESNT ONLY MOVE IN 1 DIRECTION.

        self.crop_handler.append(focus.values())
        if not self.is_satisfied(focus):
            focus_surrounding_tiles = self.get_surrounding_tiles(focus)
            for location, value in focus_surrounding_tiles:
                if location not in self.crop_handler:
                    if value and not (np.isnan(value) or value == 99) and location.values() not in self.crop_handler:
                        self.crop_handler.append(location.values())
                        return self.enumerate_section(location)
                    self.crop_handler.append(location.values())

        x_values = []
        y_values = []
        for location in self.crop_handler:
            x_values.append(location[0])
            y_values.append(location[1])

        lower_coordinate_pair = MCoordinate(min(x_values), min(y_values))
        upper_coordinate_pair = MCoordinate(max(x_values), max(y_values))
        self.crop_handler = []
        return lower_coordinate_pair, upper_coordinate_pair
