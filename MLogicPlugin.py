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
from itertools import product


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
            self.tiles_examined = []
            section_results = []
            if not np.isnan(focus_value):
                while True:
                    location = self.find_disconnected_focus(allow_satisfied=False)
                    if location:
                        self.tiles_examined.append(location.values())
                        location_surrounding_tiles = self.get_surrounding_tiles(location)
                        for adj_location, value in location_surrounding_tiles:
                            if not np.isnan(value):
                                continue

                        generated_subsets = self.create_subset(adj_location)
                        for grid_location, subplot in generated_subsets:
                            subplot_number_unrevealed = np.count_nonzero(np.isnan(subplot))

                            if subplot_number_unrevealed <= 1: # protects against a case where theres only 1 tile (should fix this in the generate subset function)
                                continue

                            offset, probability, action = self.magic_of_probability(subplot)
                            if probability == 1:
                                print(f"LOCATION: {(grid_location + offset).values()} PROBABILITY: {probability}")
                                return grid_location + offset, action
                            else:
                                section_results.append((grid_location + offset, probability, action))

                    else:  # occurs when all possible starting locations have been exhausted.
                        self.previous_focus = focus
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
            for adjacent_location, adjacent_value in self.get_surrounding_tiles(focus, alternative_grid=alternative_grid):
                if adjacent_value == 99:
                    surrounding_flags += 1
            if surrounding_flags == value:
                return True
            else:
                return False

    def get_surrounding_tiles(self, focus, alternative_grid=None):  # returns list of location = values of surrounding tiles
        if alternative_grid is None:
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

        else:
            row_num, col_num = np.shape(alternative_grid)
            surrounding_tiles = []
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i or j:
                        x_location = focus.x + i
                        y_location = focus.y + j
                        if row_num > x_location >= 0 and col_num > y_location >= 0:
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

    def enumerate_section(self, focus):  # this is recursive, returns two MCoordinate objects, TL and BR corners.
        """
        enumerate all mine possibilities in a section around a tile. SHOULD ONLY BE USED ON AN UNSATISFIED TILE.
        start on an unsatisfied revealed tile. chain along adjacent revealed unsatisfied tiles.
        Adds the focus and its adjacent unrevealed tiles to the subset for cropping.
        """

        self.grid_copy = np.copy(self.grid_array)
        valid_list = []
        checked_list = []
        unchecked_list = [focus.values()]
        while unchecked_list: # while there are unchecked tiles.

            location = unchecked_list[0]
            m_location = MCoordinate(location[0], location[1])
            checked_list.append(m_location.values())
            unchecked_list.remove(m_location.values())

            adj_locations, adj_values = zip(*self.get_surrounding_tiles(m_location))
            value_vector = np.array(adj_values)
            # adj_unrevealed = np.count_nonzero(np.isnan(value_vector)) + np.count_nonzero(value_vector == 99)
            mask = (value_vector >= 1) & (value_vector < 99)
            number_nonzero = np.count_nonzero(mask)

            if number_nonzero: # if location has a numeric adjacent
                valid_list.append(m_location.values())
                for cardinal_location, cardinal_value in self.get_cardinal_tiles(m_location):
                    if np.isnan(cardinal_value) and cardinal_location.values() not in checked_list:
                        unchecked_list.append(cardinal_location.values())

        tile_list = valid_list.copy()
        for location in valid_list:
            m_location = MCoordinate(location[0], location[1])
            location_value = self.grid_array[m_location.values()]
            for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                if adj_location.values() not in tile_list and 1 <= adj_value < 10:
                    tile_list.append(adj_location.values())

        final_tile_list = tile_list.copy()
        for location in tile_list:
            m_location = MCoordinate(location[0], location[1])
            location_value = self.grid_array[m_location.values()]
            if 1 <= location_value < 10 and not np.isnan(location_value):
                for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                    if adj_location.values() not in final_tile_list:
                        if 1 <= adj_value < 10:
                            self.grid_copy[adj_location.values()] = 0
                        final_tile_list.append(adj_location.values())


        x_values = []
        y_values = []
        for location in final_tile_list:
            self.tiles_examined.append(location)
            x_values.append(location[0])
            y_values.append(location[1])

        lower_coordinate_pair = MCoordinate(min(x_values), min(y_values))
        upper_coordinate_pair = MCoordinate(max(x_values), max(y_values))
        return lower_coordinate_pair, upper_coordinate_pair

    def create_subset(self, focus):

        # THIS MAY BE RETURNING INCORRECT LOCATIONS SOMETIMES


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

    def magic_of_probability(self, subset):
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
        rand_location = MCoordinate(random.randint(0, 29), random.randint(0, 15))
        location_value = self.grid_array[rand_location.values()]
        if np.isnan(location_value):
            self.previous_focus = rand_location
            print(rand_location.values(), "RANDOM RETURN")
            return rand_location, 'left'
        else:
            return self.random_location()

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
