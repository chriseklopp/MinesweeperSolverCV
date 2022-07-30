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
import time
import numpy as np
from MCoordinate import MCoordinate
import cv2
from itertools import product
from MTileArray import MTileArray

import sys
rec_limit = 1500
sys.setrecursionlimit(rec_limit)


class MLogicPlugin:

    def __init__(self, grid_array: MTileArray):
        self.bombs_remaining = 99
        self.grid_array = grid_array

        self.previous_focus = MCoordinate(0, 0)
        self.crop_handler_unchecked = []
        self.crop_handler_checked = []
        self.crop_handler_counter = 0

    def update(self, grid_array):

        self.grid_array = grid_array
        focus = self.previous_focus
        location, action = self.logic_flow(focus)
        return location, action

    def logic_flow(self, focus):  # this function is recursive

        focus_value, focus_satisfaction, focus_adj_unrevealed = self.grid_array.examine_tile(focus)
        focus_surrounding_tiles = self.grid_array.get_surrounding_tiles(focus)

        if focus_value == 99:
            print("BAD THING HAPPEN")

        #  ##### PART 0) #####
        if not focus_value or focus_value == 99 or np.isnan(focus_value):  # if not nonzero numeric focus
            if self.grid_array.tile_hints:
                location = self.grid_array.tile_hints.pop()
                if location:
                    return self.logic_flow(MCoordinate(location[0], location[1]))

        #  ##### PART 1) #####
        # "RULE 1"
        if not self.grid_array.is_satisfied(focus):

            if (focus_value - focus_satisfaction) == focus_adj_unrevealed:
                for location, tile_info in focus_surrounding_tiles:
                    if np.isnan(tile_info[0]):
                        print(location.values(), "RULE1 RETURN", tile_info[0])
                        self.previous_focus = focus
                        return location, 'right'

        # "RULE 2"
        else:
            for location, tile_info in focus_surrounding_tiles:
                if np.isnan(tile_info[0]):
                    print(focus.values(), "RULE2 RETURN")
                    self.previous_focus = focus
                    return focus, 'double_left'

                    # print(location.values(), "RULE2 RETURN")
                    # self.previous_focus = focus
                    # return location, 'left'

        #  ##### PART 2) #####
        for location, tile_info in focus_surrounding_tiles:
            if (tile_info[0] and not np.isnan(tile_info[0]) and
                    tile_info[0] != 99 and not self.grid_array.is_examined(location)):
                return self.logic_flow(location)

        #  ##### PART 3) #####
        # A)

        while self.grid_array.tile_hints:
            search_loc = self.grid_array.tile_hints.pop()  # type: tuple
            if search_loc and self.grid_array.grid_array[search_loc[0], search_loc[1], 0] != 99 and not \
                    np.isnan(self.grid_array.grid_array[search_loc[0], search_loc[1], 0]):
                return self.logic_flow(MCoordinate(search_loc[0], search_loc[1]))
        # B)
        search_loc = self.grid_array.get_unexamined_tile(allow_satisfied=True)  # type: MCoordinate
        if search_loc:
            return self.logic_flow(search_loc)

        #  ##### PART 4) #####
        else:

            self.grid_array.reset_examined_tiles()  # reset examined array to false
            section_results = []
            if not np.isnan(focus_value):
                while True:
                    location = self.grid_array.get_unexamined_tile(allow_satisfied=False)
                    if location and not self.grid_array.is_satisfied(location):
                        self.grid_array.examine_tile(location)
                        location_surrounding_tiles = self.grid_array.get_surrounding_tiles(location)
                        for adj_location, tile_info in location_surrounding_tiles:
                            if np.isnan(tile_info[0]):
                                break  # look for unsatisfied tile

                        # generated_subsets = self.new_create_subset(adj_location)
                        sub_array = self.create_subarray(adj_location)  # CREATE SUBARRAY FROM A LOCATION STARTING POINT
                        subplot_number_unrevealed = np.count_nonzero(np.isnan(sub_array.grid_array[:, :, 0]))

                        if subplot_number_unrevealed <= 1:  # protects against a case where theres only 1 tile (should fix this in the generate subset function)
                            continue

                        # offset, probability, action = self.backtracking_method(subplot)
                        # print(result)
                        offset, probability, action = self.brute_force_method(sub_array)  # RUN BRUTE FORCE METHOD ON IT

                        if probability == 1:
                            print(f"LOCATION: {offset.values()} PROBABILITY: {probability}")
                            return offset, action
                        else:
                            section_results.append((offset, probability, action))  # ADD TO RESULTS

                    else:  # occurs when all possible starting locations have been exhausted.
                        self.previous_focus = focus
                        if not section_results:
                            print("ERROR. NO SUBARRAYS WERE CREATED.")
                            break
                        sub_plot_location, probability, action = zip(*section_results)
                        max_probability = max(probability)
                        max_index = probability.index(max_probability)
                        print("UN-GUARANTEED MOVE")
                        print(f"POSSIBLE MOVES: {len(probability)}")
                        print(f"LOCATION: {sub_plot_location[max_index].values()} PROBABILITY: {max_probability}")
                        return sub_plot_location[max_index], action[max_index]

                # cv2.waitKey(0)
        #  ##### PART 5) #####
        print('ENTERING PART 5')
        print("RANDOM RETURN")
        return self.grid_array.get_random_unrevealed_location(), "left"

    def exceeds_satisfied(self, focus, alternative_grid=None):
        # similar to the is_satisfied function, but returns true if a tile has more adj mines than its number,
        # used in the backtracking algorithm.
        if alternative_grid is None:
            value = self.grid_array[focus.x, focus.y]
            surrounding_flags = 0
            for adjacent_location, adjacent_value in self.get_surrounding_tiles(focus):
                if adjacent_value == 99:
                    surrounding_flags += 1
            if surrounding_flags > value:
                return True
            else:
                return False

        else:
            value = alternative_grid[focus.x, focus.y]
            surrounding_flags = 0
            for adjacent_location, adjacent_value in self.get_surrounding_tiles(focus,
                                                                                alternative_grid=alternative_grid):
                if adjacent_value == 99:
                    surrounding_flags += 1
            if surrounding_flags > value:
                return True
            else:
                return False

    def new_create_subset(self, focus):

        grid_copy = np.copy(self.grid_array)
        valid_list = []
        checked_list = []

        # populates valid_list with unrevealed tile locations
        self.new_create_subset_recursion(focus, valid_list, checked_list)

        numerics_list = []
        for location in valid_list:  # populate list of adj, numeric locations
            m_location = MCoordinate(location[0], location[1])
            for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                if 1 <= adj_value < 10:
                    numerics_list.append(adj_location.values())

        accessory_list = []
        for location in numerics_list:  # populate list of adj locations (zeroing out numeric)
            m_location = MCoordinate(location[0], location[1])
            for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                if adj_location.values() in numerics_list or adj_location.values() in valid_list:   # skip values already in our list.
                    continue

                accessory_list.append(adj_location.values())
                if 1 <= adj_value < 10:
                    grid_copy[adj_location.values()] = 0

        final_tile_list = valid_list + numerics_list + accessory_list

        x_values = []
        y_values = []
        for location in final_tile_list:
            self.tiles_examined.append(location)
            x_values.append(location[0])
            y_values.append(location[1])

        lower_coordinate_pair = MCoordinate(min(x_values), min(y_values))
        upper_coordinate_pair = MCoordinate(max(x_values), max(y_values))
        subset = grid_copy[lower_coordinate_pair.x:upper_coordinate_pair.x + 1,
                           lower_coordinate_pair.y:upper_coordinate_pair.y + 1]

        adjusted_tile_list = []
        for tile in final_tile_list:
            adjusted_tile_list.append((tile[0] - lower_coordinate_pair.x, tile[1] - lower_coordinate_pair.y))

        row_num, col_num = np.shape(subset)
        for row in range(0, row_num):
            for column in range(0, col_num):
                if (row, column) not in adjusted_tile_list:
                    subset[row, column] = 0

        print("I hope this is good?")

        return [(lower_coordinate_pair, subset)]

    def new_create_subset_recursion(self, focus, valid_list, checked_list):

        checked_list.append(focus.values())  # prevent it from being checked again

        flag_adj = 0
        adj_num = 0
        for adj_location, adj_value in self.get_surrounding_tiles(focus):  # if it has a numeric adjacent add to list.
            if adj_value == 99:
                flag_adj += 1
                continue
            if 1 <= adj_value < 10:
                valid_list.append(focus.values())
                adj_num += 1

        if flag_adj < adj_num:  # only chain to the next if it has more than 1 numeric adjacent.
            for cardinal_location, cardinal_value in self.get_cardinal_tiles(focus):  # check for cardinal unrev not checked
                if np.isnan(cardinal_value) and cardinal_location.values() not in checked_list:
                    self.new_create_subset_recursion(cardinal_location, valid_list, checked_list)

    def create_subarray(self, focus):

        grid_copy = self.grid_array.copy()

        valid_set = set()

        unchecked_set = set()
        unchecked_set.add(focus.values())
        checked_set = set()

        while unchecked_set:  # creates LIST of all relevant unrevealed tiles.
            location = unchecked_set.pop()
            m_location = MCoordinate(location[0], location[1])
            checked_set.add(m_location.values())

            number_nonzero = 0
            for adj_locations, adj_tile_info in grid_copy.get_surrounding_tiles(m_location):
                if 1 <= adj_tile_info[0] < 99:
                    number_nonzero += 1
                    break

            if number_nonzero:  # if location has a numeric adjacent
                valid_set.add(m_location.values())
                for cardinal_location, cardinal_value in grid_copy.get_cardinal_tiles(m_location):
                    if np.isnan(cardinal_value[0]) and cardinal_location.values() not in checked_set:
                        unchecked_set.add(cardinal_location.values())

        tile_set = valid_set.copy()  # adds locations of all adjacent numeric values surrounding the unrevealed tiles.
        for location in valid_set:
            m_location = MCoordinate(location[0], location[1])
            location_value = grid_copy.grid_array[m_location.values()]
            for adj_location, adj_tile_info in grid_copy.get_surrounding_tiles(m_location):
                if adj_location.values() not in tile_set and 1 <= adj_tile_info[0] < 10:
                    tile_set.add(adj_location.values())

        final_tile_set = tile_set.copy()  # adds all adj tiles to listed numerics, and sets any new numeric to 0
        for location in tile_set:
            m_location = MCoordinate(location[0], location[1])
            location_value = grid_copy.grid_array[m_location.values()]
            if 1 <= location_value[0] < 10 and not np.isnan(location_value[0]):
                for adj_location, adj_tile_info in grid_copy.get_surrounding_tiles(m_location):
                    if adj_location.values() not in final_tile_set:
                        if 1 <= adj_tile_info[0] < 10:
                            grid_copy.grid_array[adj_location.x,adj_location.y,0] = 0
                        final_tile_set.add(adj_location.values())

        x_values = []
        y_values = []
        for location in final_tile_set:
            self.grid_array.examine_tile(MCoordinate(location[0], location[1]))
            x_values.append(location[0])
            y_values.append(location[1])

        lower_coordinate_pair = MCoordinate(min(x_values), min(y_values))
        upper_coordinate_pair = MCoordinate(max(x_values)+1, max(y_values)+1)
        sub_array = grid_copy.slice_copy(lower_coordinate_pair, upper_coordinate_pair)

        sub_array = self.clean_subarray(sub_array)

        return sub_array

    @staticmethod
    def clean_subarray(sub_array):
        w, h, d = sub_array.shape
        for row in range(0, h):
            for column in range(0, w):
                location = MCoordinate(column, row)
                value = sub_array.grid_array[location.x, location.y, 0]

                number_nonzero = 0
                for surrounding_tiles, surrounding_tile_info in sub_array.get_surrounding_tiles(location):
                    if 1 <= surrounding_tile_info[0] < 99:
                        number_nonzero += 1
                        break

                if np.isnan(value) and not number_nonzero:
                    sub_array.grid_array[location.x, location.y, 0] = 0

        return sub_array  # return  cleaned sub array

    @staticmethod
    def split_subset(subset):
        subset_list = []
        row_num, col_num = np.shape(subset)
        if row_num % 2 != 0:
            row_num += 1
        if col_num % 2 != 0:
            col_num += 1

        left_subplot = subset[:, :int(col_num / 2)]
        right_subplot = subset[:, int(col_num / 2):]
        upper_subplot = subset[:int(row_num / 2), :]
        lower_subplot = subset[int(row_num / 2):, :]

        left_number_unrevealed = np.count_nonzero(np.isnan(left_subplot))
        right_number_unrevealed = np.count_nonzero(np.isnan(right_subplot))
        upper_number_unrevealed = np.count_nonzero(np.isnan(upper_subplot))
        lower_number_unrevealed = np.count_nonzero(np.isnan(lower_subplot))

        lr_magnitude = abs(left_number_unrevealed - right_number_unrevealed)
        ul_magnitude = abs(upper_number_unrevealed - lower_number_unrevealed)

        if lr_magnitude > ul_magnitude:

            upper_mask = (upper_subplot >= 1) & (upper_subplot < 99)
            upper_mask_slice = upper_mask[-1, :]
            upper_subplot[-1, :][upper_mask_slice] = 0

            lower_mask = (lower_subplot >= 1) & (lower_subplot < 99)
            lower_mask_slice = lower_mask[0, :]
            lower_subplot[0, :][lower_mask_slice] = 0

            subset_list.append((MCoordinate(0, 0), upper_subplot))
            subset_list.append((MCoordinate(int(row_num / 2), 0), lower_subplot))

        else:

            left_mask = (left_subplot >= 1) & (left_subplot < 99)
            left_mask_slice = left_mask[:, -1]
            left_subplot[:, -1][left_mask_slice] = 0

            right_mask = (right_subplot >= 1) & (right_subplot < 99)
            right_mask_slice = right_mask[:, 0]
            right_subplot[:, 0][right_mask_slice] = 0

            subset_list.append((MCoordinate(0, 0), left_subplot))
            subset_list.append((MCoordinate(0, int(col_num / 2)), right_subplot))


        return subset_list  # returns offset (for each) from original subset and the split subsets.

    @staticmethod
    def brute_force_method(subarray):  # TODO: Update this function.
        # Handles a subarray of the grid. Generates all 2^n, n= # unrevealed tiles possible mine layouts.
        # Validate each layout to determine which ones are possible
        # Find proportion of valid layouts with a mine for each square.
        # Select a space with the HIGHEST probability of being a mine for flagging. Or select a space with the
        # LOWEST probability of being a mine for left clicking.

        # KNOWN ISSUES: Nan is considered a probability. This SHOULD NOT happen.
        # SHOULDN'T MAKE A PARTIAL DECISION UNTIL IT IS THE BEST POSSIBLE

        # set numeric tiles on the edges to 0. and mines not touching any numerics to 0
        # 'CLEAN GRID"

        valid_combinations = []
        w, h, d = subarray.shape

        number_unrevealed = np.count_nonzero(np.isnan(subarray.grid_array[:, :, 0]))
        unrevealed_locations = np.asarray(np.isnan(subarray.grid_array[:, :, 0])).nonzero()
        print(f"Simulating all {2 ** number_unrevealed} outcomes")
        combinations_list = list(product((0, 1), repeat=number_unrevealed))  # list of all 2^n combinations. list of sets of values
        for combination in combinations_list:
            is_valid = True
            combination_grid = subarray.copy()  # THIS IS BAD, PROBABLY WILL HAVE TO RECURSION
            for i, tile in enumerate(combination):
                if tile:
                    combination_grid.grid_array[unrevealed_locations[0][i], unrevealed_locations[1][i], 0] = 99

            for row in range(0, h):
                for column in range(0, w):
                    location = MCoordinate(column, row)
                    value = combination_grid.grid_array[location.x, location.y, 0]
                    loc, tile_info = zip(*combination_grid.get_surrounding_tiles(location))
                    value_vector = np.array(tile_info[0])
                    adj_unrevealed = np.count_nonzero(np.isnan(value_vector)) + np.count_nonzero(value_vector == 99)
                    if value and value != 99 and not np.isnan(value) and value <= adj_unrevealed:
                        if not combination_grid.is_satisfied(location):
                            is_valid = False

            if is_valid:
                valid_combinations.append(combination)

        valid_combination_array = np.asarray(valid_combinations)
        column_sums = valid_combination_array.sum(axis=0)
        column_proportions = column_sums/len(valid_combination_array)

        max_value = np.max(column_proportions)
        max_value_position = np.argmax(column_proportions)

        min_value = np.min(column_proportions)
        min_value_position = np.argmin(column_proportions)

        if np.isnan(min_value) or np.isnan(max_value):
            print("POOPOO")

        if min_value == 0:
            location = MCoordinate(unrevealed_locations[0][min_value_position],
                                   unrevealed_locations[1][min_value_position])

            print(f"PROB: {1-min_value}")
            return location, 1-min_value, 'left'

        if max_value == 1:
            location = MCoordinate(unrevealed_locations[0][max_value_position],
                                   unrevealed_locations[1][max_value_position])
            print(f"PROB: {max_value}")
            return location, max_value, 'right'

        location = MCoordinate(unrevealed_locations[0][min_value_position],
                               unrevealed_locations[1][min_value_position])
        print(f"PROB: {1-min_value}")
        return location, 1-min_value, 'left'
