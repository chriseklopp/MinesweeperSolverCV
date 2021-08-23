"""
Contains solving logic for a Minesweeper puzzle
Makes ONE decision each update cycle. Though this may be changed to allow for multiple flags to be added in one cycle
Takes in board information and returns an action and a location
Though this was originally just a function, it has been made a class to make it easier to act upon previous moves
Having this isolated from the rest of the code allows for increased readability and allows for implementation of new
solving logic without breaking and other parts of the code

This class can have whatever you want in it as long as it contains an update function that returns (location, action)
"""

import random
import numpy as np
from MCoordinate import MCoordinate


class MLogicPlugin:

    def __init__(self, grid_array):
        self.last_move = MCoordinate(0, 0)
        self.bombs_remaining = 99
        self.grid_array = grid_array
        self.tiles_examined = []


    def update(self, grid_array):
        self.tiles_examined = []
        self.grid_array = grid_array
        focus = self.last_move
        location, action = self.logic_flow(focus)
        return location, action

    def logic_flow(self, focus):  # this function is recursive
        self.tiles_examined.append(focus.values())
        focus_value = self.grid_array[focus.values()]
        print("FOCUS = ", focus_value)
        focus_surrounding_tiles = self.get_surrounding_tiles(focus)

        if focus_value and focus_value != 99:  # if focus tile isn't 0, unrevealed, or empty.

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
                            return location, 'right'

            # "RULE 2"
            if self.is_satisfied(focus):
                for location, value in focus_surrounding_tiles:
                    if np.isnan(value):
                        # self.last_move = location
                        print(location.values(), "RULE2 RETURN")
                        return location, 'left'

            # if this tile has been satisfied, try moving to an adjacent nonzero numeric tile.
            for location, value in focus_surrounding_tiles:
                if value and not np.isnan(value) and location.values() not in self.tiles_examined and value != 99:
                    return self.logic_flow(location)

            # if no adjacent tile satisfies these conditions, allow moving to an empty tile
            for location, value in focus_surrounding_tiles:
                if value == 0:
                    return self.logic_flow(location)
                else:
                    location = self.find_disconnected_focus()
                    if location:
                        self.last_move = location
                        return self.logic_flow(location)
                    else:
                        location = MCoordinate(random.randint(0, 29), random.randint(0, 15))
                        self.last_move = location
                        print(location.values(), "RANDOM RETURN")
                        return location, 'left'


        else:   # else try the next adjacent tile that isn't 0, unrevealed, empty, or has been examined this update
            for location, value in focus_surrounding_tiles:
                if value and not np.isnan(value) and location.values() not in self.tiles_examined:
                    return self.logic_flow(location)

            # if no adjacent tile satisfies these conditions, allow moving to an empty tile
            for location, value in focus_surrounding_tiles:
                if not np.isnan(value) and location.values() not in self.tiles_examined:
                    return self.logic_flow(location)

            # if all else fails to random return
            location = self.find_disconnected_focus()

            if location:
                self.last_move = location
                return self.logic_flow(location)
            else:
                location = MCoordinate(random.randint(0, 29), random.randint(0, 15))
                self.last_move = location
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

    def get_surrounding_tiles(self, focus):  # returns dictionary of location = values of surrounding tiles
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

    def find_disconnected_focus(self): # used when the algorithm cant find any nearby options, will jump elsewhere
        for i in range(0, 30):
            for j in range(0, 16):
                tile_value = self.grid_array[i, j]
                if tile_value and not np.isnan(tile_value) and tile_value != 99:
                    if (i, j) not in self.tiles_examined:
                        print((i, j), "DISCONNECTED FOCUS JUMP")
                        return MCoordinate(i, j)
        return 0




