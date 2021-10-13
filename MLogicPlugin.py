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


# Implement backtracking algorithm.


import random
import time
import numpy as np
from MCoordinate import MCoordinate
import cv2
from itertools import product

import sys
rec_limit=1500
sys.setrecursionlimit(rec_limit)

class MLogicPlugin:

    def __init__(self, grid_array):
        self.bombs_remaining = 99
        self.grid_array = grid_array
        self.tiles_examined = []
        self.previous_focus = MCoordinate(0, 0)
        self.crop_handler_unchecked = []
        self.crop_handler_checked = []
        self.crop_handler_counter = 0

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

        # print("FOCUS = ", focus_value, (focus.values()))
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
                    print(focus.values(), "RULE2 RETURN")
                    self.previous_focus = focus
                    return focus, 'double_left'

                    # print(location.values(), "RULE2 RETURN")
                    # self.previous_focus = focus
                    # return location, 'left'

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
            self.tiles_examined = []
            section_results = []
            if not np.isnan(focus_value):
                while True:
                    location = self.find_disconnected_focus(allow_satisfied=False)
                    if location:
                        self.tiles_examined.append(location.values())
                        location_surrounding_tiles = self.get_surrounding_tiles(location)
                        for adj_location, value in location_surrounding_tiles:
                            if np.isnan(value):
                                break

                        # generated_subsets = self.new_create_subset(adj_location)
                        generated_subsets = self.create_subset(adj_location)
                        for grid_location, subplot in generated_subsets:
                            subplot_number_unrevealed = np.count_nonzero(np.isnan(subplot))

                            if subplot_number_unrevealed <= 1: # protects against a case where theres only 1 tile (should fix this in the generate subset function)
                                continue

                            # offset, probability, action = self.backtracking_method(subplot)
                            # print(result)
                            offset, probability, action = self.brute_force_method(subplot)

                            if probability == 1:
                                print(f"LOCATION: {(grid_location + offset).values()} PROBABILITY: {probability}")
                                return grid_location + offset, action
                            else:
                                section_results.append((grid_location + offset, probability, action))

                    else:  # occurs when all possible starting locations have been exhausted.
                        self.previous_focus = focus
                        if not section_results:
                            print("ERROR. NO SUBSETS WERE CREATED.")
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
        return self.random_location()

    def is_satisfied(self, focus, alternative_grid=None):
        if alternative_grid is None:
            value = self.grid_array[focus.x, focus.y]
            surrounding_flags = 0
            for adjacent_location, adjacent_value in self.get_surrounding_tiles(focus):
                if adjacent_value == 99:
                    surrounding_flags += 1
            if surrounding_flags == value:
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
            if surrounding_flags == value:
                return True
            else:
                return False

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

    def get_surrounding_tiles(self, focus, alternative_grid=None):
        if alternative_grid is None:
            row_num, col_num = np.shape(self.grid_array)
            x_min = -1
            x_max = 2
            y_min = -1
            y_max = 2
            if focus.x == 0:
                x_min += 1
            if focus.x == row_num - 1:
                x_max -= 1
            if focus.y == 0:
                y_min += 1
            if focus.y == col_num - 1:
                y_max -= 1
            x_range = range(x_min, x_max)
            y_range = range(y_min, y_max)

            surrounding_tiles = []
            for i in x_range:
                for j in y_range:
                    if i or j:
                        x_location = focus.x + i
                        y_location = focus.y + j
                        tile_value = self.grid_array[x_location, y_location]
                        surrounding_tiles.append((MCoordinate(x_location, y_location), tile_value))

            return surrounding_tiles

        else:
            row_num, col_num = np.shape(alternative_grid)
            x_min = -1
            x_max = 2
            y_min = -1
            y_max = 2
            if focus.x == 0:
                x_min += 1
            if focus.x == row_num - 1:
                x_max -= 1
            if focus.y == 0:
                y_min += 1
            if focus.y == col_num - 1:
                y_max -= 1
            x_range = range(x_min, x_max)
            y_range = range(y_min, y_max)

            surrounding_tiles = []
            for i in x_range:
                for j in y_range:
                    if i or j:
                        x_location = focus.x + i
                        y_location = focus.y + j
                        tile_value = alternative_grid[x_location, y_location]
                        surrounding_tiles.append((MCoordinate(x_location, y_location), tile_value))

            return surrounding_tiles

    def find_disconnected_focus(self, allow_examined=False, allow_satisfied=True):
        # WHEN USING THIS FUNCTION YOU MUST ALWAYS CHECK THE EXISTENCE OF THE OUTPUT, IF NO FOCUS FOUND WILL RETURN 0
        # Will find a potential numeric focus target elsewhere.
        if allow_examined and allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        # print((i, j), "DISCONNECTED FOCUS JUMP, EX = True")
                        return location

        if allow_examined and not allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        if not self.is_satisfied(location):
                            # print((i, j), "DISCONNECTED FOCUS JUMP, EX = True")
                            return location

        if not allow_examined and allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        if location.values() not in self.tiles_examined:
                            # print((i, j), "DISCONNECTED FOCUS JUMP, EX = False")
                            return location

        if not allow_examined and not allow_satisfied:
            for i in range(0, 30):
                for j in range(0, 16):
                    tile_value = self.grid_array[i, j]
                    if tile_value and not np.isnan(tile_value) and tile_value != 99:
                        location = MCoordinate(i, j)
                        if location.values() not in self.tiles_examined and not self.is_satisfied(location):
                            # print((i, j), "DISCONNECTED FOCUS JUMP, EX = False")
                            return location
        return 0

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

    def create_subset(self, focus):

        grid_copy = np.copy(self.grid_array)
        valid_list = []
        checked_list = []
        unchecked_list = [focus.values()]

        while unchecked_list:  # creates LIST of all relevant unrevealed tiles.
            location = unchecked_list[0]
            m_location = MCoordinate(location[0], location[1])
            checked_list.append(m_location.values())
            unchecked_list.remove(m_location.values())

            adj_locations, adj_values = zip(*self.get_surrounding_tiles(m_location))
            value_vector = np.array(adj_values)
            mask = (value_vector >= 1) & (value_vector < 99)
            number_nonzero = np.count_nonzero(mask)

            if number_nonzero:  # if location has a numeric adjacent
                valid_list.append(m_location.values())
                for cardinal_location, cardinal_value in self.get_cardinal_tiles(m_location):
                    if np.isnan(cardinal_value) and cardinal_location.values() not in checked_list:
                        unchecked_list.append(cardinal_location.values())

        tile_list = valid_list.copy()  # adds locations of all adjacent numeric values surrounding the unrevealed tiles.
        for location in valid_list:
            m_location = MCoordinate(location[0], location[1])
            location_value = self.grid_array[m_location.values()]
            for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                if adj_location.values() not in tile_list and 1 <= adj_value < 10:
                    tile_list.append(adj_location.values())

        final_tile_list = tile_list.copy()  # adds all adj tiles to listed numerics, and sets any new numeric to 0
        for location in tile_list:
            m_location = MCoordinate(location[0], location[1])
            location_value = self.grid_array[m_location.values()]
            if 1 <= location_value < 10 and not np.isnan(location_value):
                for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                    if adj_location.values() not in final_tile_list:
                        if 1 <= adj_value < 10:
                            grid_copy[adj_location.values()] = 0
                        final_tile_list.append(adj_location.values())

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

        generated_subsets = []
        cleaned_results = self.clean_subset(subset)  # this step may result in the subset getting split if its too large
        for offset, subset in cleaned_results:
            generated_subsets.append((lower_coordinate_pair+offset, subset))

        return generated_subsets

    def clean_subset(self, subset):
        row_num, col_num = np.shape(subset)
        for row in range(0, row_num):
            for column in range(0, col_num):
                location = MCoordinate(row, column)
                value = subset[location.values()]
                surrounding_tiles, surrounding_values = zip(*self.get_surrounding_tiles(location,
                                                                                        alternative_grid=subset))
                value_vector = np.array(surrounding_values)
                mask = (value_vector >= 1) & (value_vector < 99)
                number_nonzero = np.count_nonzero(mask)

                if np.isnan(value) and not number_nonzero:
                    subset[location.values()] = 0

        subset_number_unrevealed = np.count_nonzero(np.isnan(subset))
        if subset_number_unrevealed < 14:  # Return subset if it is "small enough"
            return [(MCoordinate(0, 0), subset)]  # return offset from original subset and cleaned subsets

        cleaned_split = []
        split_results = self.split_subset(subset)
        for offset, subplot in split_results:
            subset_number_unrevealed = np.count_nonzero(np.isnan(subplot))
            if subset_number_unrevealed < 14:
                cleaned_split.append((offset, subplot))
            else:
                result = self.split_subset(subplot)
                for location, plot in result:
                    cleaned_split.append((offset + location, plot))

        return cleaned_split

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

    def brute_force_method(self, subset):
        # Handles a subset of the grid. Generates all 2^n, n= # unrevealed tiles possible mine layouts.
        # Validate each layout to determine which ones are possible
        # Find proportion of valid layouts with a mine for each square.
        # Select a space with the HIGHEST probability of being a mine for flagging. Or select a space with the
        # LOWEST probability of being a mine for left clicking.

        # KNOWN ISSUES: Nan is considered a probability. This SHOULD NOT happen.
        # SHOULDN'T MAKE A PARTIAL DECISION UNTIL IT IS THE BEST POSSIBLE

        # set numeric tiles on the edges to 0. and mines not touching any numerics to 0
        # 'CLEAN GRID"

        valid_combinations = []
        row_num, col_num = np.shape(subset)

        # for row in range(0, row_num):
        #     for column in range(0, col_num):
        #         location = MCoordinate(row, column)
        #         value = subset[location.values()]
        #         surrounding_tiles, surrounding_values = zip(*self.get_surrounding_tiles(location,alternative_grid=subset))
        #         value_vector = np.array(surrounding_values)
        #         # adj_unrevealed = np.count_nonzero(np.isnan(value_vector)) + np.count_nonzero(value_vector == 99)
        #         mask = (value_vector >= 1) & (value_vector < 99)
        #         number_nonzero = np.count_nonzero(mask)
        #
        #         if np.isnan(value) and not number_nonzero:
        #             subset[location.values()] = 0




        number_unrevealed = np.count_nonzero(np.isnan(subset))
        unrevealed_locations = np.asarray(np.isnan(subset)).nonzero()
        print(f"Simulating all {2 ** number_unrevealed} outcomes")
        combinations_list = list(product((0, 1), repeat=number_unrevealed))  # list of all 2^n combinations. list of sets of values
        for combination in combinations_list:
            is_valid = True
            combination_grid = np.copy(subset)
            for i, tile in enumerate(combination):
                if tile:
                    combination_grid[unrevealed_locations[0][i], unrevealed_locations[1][i]] = 99

            for row in range(0, row_num):
                for column in range(0, col_num):
                    location = MCoordinate(row, column)
                    value = combination_grid[location.values()]
                    loc, values = zip(*self.get_surrounding_tiles(location, alternative_grid=combination_grid))
                    value_vector = np.array(values)
                    adj_unrevealed = np.count_nonzero(np.isnan(value_vector)) + np.count_nonzero(value_vector == 99)
                    if value and value != 99 and not np.isnan(value) and value <= adj_unrevealed:
                        if not self.is_satisfied(location, alternative_grid=combination_grid):
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
            return location, max_value,'right'

        location = MCoordinate(unrevealed_locations[0][min_value_position],
                               unrevealed_locations[1][min_value_position])
        print(f"PROB: {1-min_value}")
        return location, 1-min_value, 'left'

        # else:
        #     location = MCoordinate(unrevealed_locations[0][max_value_position],
        #                            unrevealed_locations[1][max_value_position])
        #     print(f"LOCATION: {location.values()}, PROB: {max_value}")
        #     return location, 'right'

        # return 0 # this shouldnt get hit ever

    def random_location(self):
        unrevealed_locations = []
        row_num, col_num = np.shape(self.grid_array)
        for row in range(0, row_num):
            for column in range(0, col_num):
                if np.isnan(self.grid_array[row, column]):
                    unrevealed_locations.append((row, column))

        if unrevealed_locations:
            rand_number = random.randint(0, len(unrevealed_locations)-1)
            rand_location = unrevealed_locations[rand_number]
            m_rand_location = MCoordinate(rand_location[0], rand_location[1])
            self.previous_focus = m_rand_location
            print(m_rand_location.values(), "RANDOM RETURN")
            return m_rand_location, 'left'

        else:
            print("ERROR: Random return found no unrevealed tiles")
            print('ERROR RETURN: (0,0)')
            return MCoordinate(0, 0), 'left'

    def get_cardinal_tiles(self, focus):
        surrounding_tiles = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (i and not j) or (not i and j):
                    x_location = focus.x + i
                    y_location = focus.y + j
                    if 30 > x_location >= 0 and 16 > y_location >= 0:
                        tile_value = self.grid_array[x_location, y_location]
                        surrounding_tiles.append((MCoordinate(x_location, y_location), tile_value))

        return surrounding_tiles
