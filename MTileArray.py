import numpy as np
from dataclasses import dataclass
from MCoordinate import MCoordinate
import random
"""
MTileArray
Is a wrapper around a numpy array of MTileObjects that facilitates operations on the array in a safe way
Provides efficient and useful information to be acted on by an MLogicPlugin
Should be much much much more time efficient than the old method.
"""


class MTileArray:
    def __init__(self, dims: tuple):

        # (value, satisfaction, adjacent_unrevealed)
        self.grid_array = np.full((dims[0], dims[1], 3), (77, 0, 0))
        self.shape = self.grid_array.shape
        self.examined_array = np.full(dims, False)
        self.debugarray = self.grid_array[:, :, 0]
        self.is_fixed_satisfaction = False
        self.fixed_satisfaction = np.full((dims[0], dims[1]), 0)
        # set of tiles that were modified in the previous update,helps logic plugin find useful moves more efficiently
        self.tile_hints = set()

    def is_satisfied(self, location: MCoordinate):
        if self.grid_array[location.x, location.y, 0] == self.grid_array[location.x, location.y, 1]:
            return True
        else:
            return False

    def get_surrounding_tiles(self, location: MCoordinate):
        w, h, d = self.shape
        x_min = -1
        x_max = 2
        y_min = -1
        y_max = 2
        if location.x == 0:
            x_min += 1
        if location.x == w - 1:
            x_max -= 1
        if location.y == 0:
            y_min += 1
        if location.y == h - 1:
            y_max -= 1
        x_range = range(x_min, x_max)
        y_range = range(y_min, y_max)

        surrounding_tiles = []
        for i in x_range:
            for j in y_range:
                if i or j:
                    x_location = location.x + i
                    y_location = location.y + j
                    tile_info = self.grid_array[x_location, y_location]
                    surrounding_tiles.append((MCoordinate(x_location, y_location), tile_info))  # location tile info

        return surrounding_tiles

    def get_cardinal_tiles(self, location: MCoordinate):
        w, h, d = self.shape
        x_min = -1
        x_max = 2
        y_min = -1
        y_max = 2
        if location.x == 0:
            x_min += 1
        if location.x == w - 1:
            x_max -= 1
        if location.y == 0:
            y_min += 1
        if location.y == h - 1:
            y_max -= 1
        x_range = range(x_min, x_max)
        y_range = range(y_min, y_max)

        surrounding_tiles = []
        for i in x_range:
            for j in y_range:
                if (i and not j) or (not i and j):
                    x_location = location.x + i
                    y_location = location.y + j
                    tile_info = self.grid_array[x_location, y_location]
                    surrounding_tiles.append((MCoordinate(x_location, y_location), tile_info))  # location tile info

        return surrounding_tiles

    def is_examined(self, location: MCoordinate):
        return True if self.examined_array[location.values()] else False

    def get_unexamined_tile(self, allow_satisfied=False):
        # returns the first unexamined non-zero numeric tile
        # if none found returns none, YOU MUST CHECK FOR THIS
        """
        This should theoretically be slower than looping through the array to find the first unexamined
        But since it has non-python efficiency it may ironically end up being faster on average

        TODO: Test if looping through and storing index of last result is faster
        """

        conditional_array = self.examined_array == False
        if not allow_satisfied:
            unsatisfied_indices = self.grid_array[:, :, 0] != self.grid_array[:, :, 1]
            conditional_array = np.logical_and(conditional_array, unsatisfied_indices)

        # exclude tiles with flags or unrevealed tiles, or zero
        nonzero = self.grid_array[:, :, 0] > 0
        nonflag = self.grid_array[:, :, 0] < 77
        nonzero_numeric = np.logical_and(nonzero, nonflag)

        conditional_array = np.logical_and(conditional_array, nonzero_numeric)

        desired_indices = np.argwhere(conditional_array == True)
        if desired_indices.any():
            return MCoordinate(desired_indices[0][0], desired_indices[0][1])
        else:
            return None

    def examine_tile(self, location: MCoordinate):
        # set tile status to examined and return its info
        self.examined_array[location.values()] = True
        return self.grid_array[location.x, location.y, :]

    def reset_examined_tiles(self):
        self.examined_array = np.full((30, 16), False)

    def get_random_unrevealed_location(self):
        #  returns random unrevealed location, usually first move or last ditch effort
        # if no unrevealed_location found (how???) returns (0,0)

        unrevealed_locations = np.argwhere(self.grid_array[:, :, 0] == 77)  # this may break lol

        if unrevealed_locations.any():
            rand_number = random.randint(0, len(unrevealed_locations)-1)
            rand_location = unrevealed_locations[rand_number]
            m_rand_location = MCoordinate(rand_location[0], rand_location[1])
            return m_rand_location  # type: MCoordinate

        else:
            return MCoordinate(0, 0)  # type: MCoordinate

    def set_fixed_satisfaction(self):
        # Saves the adjacent mines of edge numerics of subarrays so that when it gets chopped they can still "remember"
        # that they were partially satisfied.
        # this CANNOT be disabled on an array so it should only be called on a subarray or everything will explode
        # Any COPY of an array with this enabled will also have it enabled.
        # fixed_sat = curr_sat - sliced_sat
        self.is_fixed_satisfaction = True

        w, h, d = self.shape
        borders = np.full((w, h), False)
        borders[-1, :] = True
        borders[0, :] = True
        borders[:, -1] = True
        borders[:, 0] = True
        non_borders = ~borders
        old_satisfaction = self.grid_array[:, :, 1].copy()

        # We need to refresh the edges of our array now to determine which flags we've lost.
        # TODO: Change this to just edges for speeeeeed boost.
        for i in range(0,w):
            for j in range(0,h):
                coord_location = MCoordinate(i, j)
                surrounding_tiles = self.get_surrounding_tiles(coord_location)
                adjacent_flags = 0
                adjacent_unrevealed = 0
                for location, tile_info in surrounding_tiles:
                    if tile_info[0] == 77:
                        adjacent_unrevealed += 1
                    elif tile_info[0] == 99:
                        adjacent_flags += 1
                self.grid_array[coord_location.x, coord_location.y, 1] = adjacent_flags
                self.grid_array[coord_location.x, coord_location.y, 2] = adjacent_unrevealed

        sliced_satisfaction = self.grid_array[:, :, 1]
        # Find difference
        self.fixed_satisfaction = old_satisfaction - sliced_satisfaction
        # Ignore where it doesn't matter
        self.fixed_satisfaction[non_borders] = 0

    def update(self, snapshot_array: np.array):
        # Receives a np array of np.numerics parsed from a screenshot.
        # This function determines which values have changed in game and updates them in the grid array
        # Also keeps a list of indices changed to provide hints of where to look for the logic plugin.

        self.reset_examined_tiles()
        my_value_array = self.grid_array[:, :, 0]

        # numerics only
        diff_values = my_value_array != snapshot_array
        #my_value_array_numerics = np.logical_and(my_value_array > 0, my_value_array < 99)
        #snapshot_array_numerics = np.logical_and(snapshot_array > 0, snapshot_array < 99)

        #diff_values = my_value_array_numerics != snapshot_array_numerics

        diff_indices = np.argwhere(diff_values)
        self.grid_array[:, :, 0] = snapshot_array

        # Update tiles that were directly changed
        adj_indices = set()
        og_indices = set()
        for indices in diff_indices:
            og_indices.add((indices[0], indices[1]))
            coord_location = MCoordinate(indices[0], indices[1])
            surrounding_tiles = self.get_surrounding_tiles(coord_location)
            adjacent_flags = 0
            adjacent_unrevealed = 0

            for location, tile_info in surrounding_tiles:
                adj_indices.add(location.values())

                if tile_info[0] == 77:
                    adjacent_unrevealed += 1
                elif tile_info[0] == 99:
                    adjacent_flags += 1
            self.grid_array[coord_location.x, coord_location.y, 1] = adjacent_flags + self.fixed_satisfaction[coord_location.x, coord_location.y]
            self.grid_array[coord_location.x, coord_location.y, 2] = adjacent_unrevealed

        # Update any adjacent tiles to those that were changed.
        for adj_loc in adj_indices:
            coord_location = MCoordinate(adj_loc[0], adj_loc[1])
            surrounding_tiles = self.get_surrounding_tiles(coord_location)
            adjacent_flags = 0
            adjacent_unrevealed = 0

            for location, tile_info in surrounding_tiles:
                if tile_info[0] == 77:
                    adjacent_unrevealed += 1
                elif tile_info[0] == 99:
                    adjacent_flags += 1
            self.grid_array[coord_location.x, coord_location.y, 1] = adjacent_flags + self.fixed_satisfaction[coord_location.x, coord_location.y]
            self.grid_array[coord_location.x, coord_location.y, 2] = adjacent_unrevealed

        self.tile_hints = og_indices.union(adj_indices)
        self.debugarray = self.grid_array[:, :, 0]

        # if self.is_fixed_satisfaction:
        #     self.grid_array[:, :, 1] += self.fixed_satisfaction

    def slice_copy(self, topleft: MCoordinate, bottomright: MCoordinate, fix_sat=False):
        # Slice this array object to the given coordinates and return a copy
        w = bottomright.x - topleft.x
        h = bottomright.y - topleft.y
        aslice = MTileArray((w, h))
        aslice.grid_array = self.grid_array[topleft.x:bottomright.x, topleft.y:bottomright.y, :].copy()
        aslice.debugarray = aslice.grid_array[:, :, 0]
        if fix_sat:
            aslice.set_fixed_satisfaction()
        return aslice

    def copy(self):
        # return a copy of this array object
        w, h, d = self.shape

        acopy = MTileArray((w,h))
        acopy.grid_array = self.grid_array[0:w, 0:h, :].copy()
        acopy.debugarray = acopy.grid_array[:, :, 0]

        if self.is_fixed_satisfaction:
            acopy.fixed_satisfaction = self.fixed_satisfaction
            acopy.is_fixed_satisfaction = True

        return acopy


if __name__ == "__main__":

    MTileArray((30, 16))
    print()
