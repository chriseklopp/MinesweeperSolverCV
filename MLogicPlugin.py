"""
Contains solving logic for a Minesweeper puzzle
Makes ONE decision each update cycle. Though this may be changed to allow for multiple flags to be added in one cycle
Takes in board information and returns an action and a location
Though this was originally just a function, it has been made a class to make it easier to act upon previous moves
Having this isolated from the rest of the code allows for increased readability and allows for implementation of new
solving logic without breaking and other parts of the code
This class can have whatever you want in it as long as it contains an update function that returns list(location, action)

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


import time

import numpy as np

from MDataTypes import MArrayCoordinate

from itertools import product
from MTileArray import MTileArray

import sys

rec_limit = 1500
sys.setrecursionlimit(rec_limit)


class MLogicPlugin:

    def __init__(self, grid_array: MTileArray):
        self.bombs_remaining = 99
        self.grid_array = grid_array

        self.previous_focus = MArrayCoordinate(0, 0)
        self.crop_handler_unchecked = []
        self.crop_handler_checked = []
        self.crop_handler_counter = 0

    def update(self, grid_array):

        self.grid_array = grid_array
        focus = self.previous_focus
        actionlist = self.logic_flow(focus)
        return actionlist

    def logic_flow(self, focus):  # this function is recursive

        focus_value, focus_satisfaction, focus_adj_unrevealed = self.grid_array.examine_tile(focus)
        focus_surrounding_tiles = self.grid_array.get_surrounding_tiles(focus)

        if focus_value == 99:
            print("BAD THING HAPPEN")

        #  ##### PART 0) #####
        if not focus_value or focus_value == 99 or focus_value == 77:  # if not nonzero numeric focus
            if self.grid_array.tile_hints:
                location = self.grid_array.tile_hints.pop()
                if location:
                    return self.logic_flow(MArrayCoordinate(location))

        #  ##### PART 1) #####
        # "RULE 1"
        if not self.grid_array.is_satisfied(focus):

            if (focus_value - focus_satisfaction) == focus_adj_unrevealed:
                unrevealed = []
                for location, tile_info in focus_surrounding_tiles:
                    if tile_info[0] == 77:
                        unrevealed.append((location, 'right'))
                self.previous_focus = focus
                print(f"RULE1 RETURN. Size: {len(unrevealed)}", tile_info[0])
                return unrevealed

        # "RULE 2"
        else:
            for location, tile_info in focus_surrounding_tiles:
                if tile_info[0] == 77:
                    print(focus, "RULE2 RETURN")
                    self.previous_focus = focus
                    return [(focus, 'double_left')]

                    # print(location.values(), "RULE2 RETURN")
                    # self.previous_focus = focus
                    # return location, 'left'

        #  ##### PART 2) #####
        for location, tile_info in focus_surrounding_tiles:
            if (tile_info[0] and tile_info[0] != 77 and
                    tile_info[0] != 99 and not self.grid_array.is_examined(location)):
                return self.logic_flow(location)

        #  ##### PART 3) #####
        # A)

        while self.grid_array.tile_hints:
            search_loc = self.grid_array.tile_hints.pop()  # type: tuple
            if search_loc and self.grid_array.grid_array[search_loc[0], search_loc[1], 0] != 99 and \
                    self.grid_array.grid_array[search_loc[0], search_loc[1], 0] != 77:
                return self.logic_flow(MArrayCoordinate(search_loc))
        # B)
        search_loc = self.grid_array.get_unexamined_tile(allow_satisfied=True)  # type: MCoordinate
        if search_loc:
            return self.logic_flow(search_loc)

        #  ##### PART 4) #####
        else:

            self.grid_array.reset_examined_tiles()  # reset examined array to false
            section_results = []
            #if focus_value != 77:
            while True:
                location = self.grid_array.get_unexamined_tile(allow_satisfied=False)
                if location and not self.grid_array.is_satisfied(location):
                    self.grid_array.examine_tile(location)
                    location_surrounding_tiles = self.grid_array.get_surrounding_tiles(location)
                    for adj_location, tile_info in location_surrounding_tiles:
                        if tile_info[0] == 77:
                            break  # look for unsatisfied tile

                    # generated_subsets = self.new_create_subset(adj_location)
                    # rel_location, sub_array
                    subarray_list = self.create_subarray(
                        adj_location)  # CREATE SUBARRAY FROM A LOCATION STARTING POINT
                    for sub in subarray_list:
                        rel_location, sub_array = sub
                        subplot_number_unrevealed = np.count_nonzero(sub_array.grid_array[:, :, 0] == 77)
                        if subplot_number_unrevealed <= 1:  # protects against a case where theres only 1 tile (should fix this in the generate subset function)
                            continue

                        # offset, probability, action = self.backtracking_method(subplot)
                        # print(result)
                        #bf_list = self.backtracking_method(sub_array)
                        bf_list = self.brute_force_method(sub_array)  # RUN BRUTE FORCE METHOD ON IT

                        if len(bf_list) > 1 or bf_list[0][1] == 1:

                            rem_prob = []
                            for item in bf_list:
                                os, prob, act = item
                                rem_prob.append((rel_location + os, act))
                            print(f"Return guaranteed list of length {len(rem_prob)}")
                            return rem_prob

                        else:
                            os, prob, act = bf_list[0]
                            section_results.append((rel_location + os, prob, act))  # ADD TO RESULTS

                else:  # occurs when all possible starting locations have been exhausted.
                    self.previous_focus = focus
                    if not section_results:
                        print("ERROR. NO SUBARRAYS WERE CREATED.")
                        break
                    sub_plot_location, probability, action = zip(*section_results)
                    max_probability = np.nanmax(probability)
                    if np.isnan(max_probability):
                        print("NAN PROBABILITY, this is probably not good..")
                        print("RANDOM RETURN")
                        return [(self.grid_array.get_random_unrevealed_location(), "left")]
                    max_index = probability.index(max_probability)
                    print("UN-GUARANTEED MOVE")

                    print(f"POSSIBLE MOVES: {len(probability)}")
                    print(f"LOCATION: {sub_plot_location[max_index].values()} PROBABILITY: {max_probability}")
                    return [(sub_plot_location[max_index], action[max_index])]

                # cv2.waitKey(0)
        #  ##### PART 5) #####
        print('ENTERING PART 5')
        print("RANDOM RETURN")
        return [(self.grid_array.get_random_unrevealed_location(), "left")]

    def new_create_subset(self, focus):

        grid_copy = np.copy(self.grid_array)
        valid_list = []
        checked_list = []

        # populates valid_list with unrevealed tile locations
        self.new_create_subset_recursion(focus, valid_list, checked_list)

        numerics_list = []
        for location in valid_list:  # populate list of adj, numeric locations
            m_location = MArrayCoordinate(location[0], location[1])
            for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                if 1 <= adj_value < 10:
                    numerics_list.append(adj_location.values())

        accessory_list = []
        for location in numerics_list:  # populate list of adj locations (zeroing out numeric)
            m_location = MArrayCoordinate(location[0], location[1])
            for adj_location, adj_value in self.get_surrounding_tiles(m_location):
                if adj_location.values() in numerics_list or adj_location.values() in valid_list:  # skip values already in our list.
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

        lower_coordinate_pair = MArrayCoordinate(min(x_values), min(y_values))
        upper_coordinate_pair = MArrayCoordinate(max(x_values), max(y_values))
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
            for cardinal_location, cardinal_value in self.get_cardinal_tiles(
                    focus):  # check for cardinal unrev not checked
                if cardinal_value == 77 and cardinal_location.values() not in checked_list:
                    self.new_create_subset_recursion(cardinal_location, valid_list, checked_list)

    def create_subarray(self, focus):

        grid_copy = self.grid_array.copy()

        valid_set = set()

        unchecked_set = set()
        unchecked_set.add(focus.values())
        checked_set = set()

        while unchecked_set:  # creates LIST of all relevant unrevealed tiles.
            location = unchecked_set.pop()
            m_location = MArrayCoordinate(location)
            checked_set.add(location)

            number_nonzero = 0
            for adj_locations, adj_tile_info in grid_copy.get_surrounding_tiles(m_location):
                if 1 <= adj_tile_info[0] < 77:
                    number_nonzero += 1
                    break

            if number_nonzero:  # if location has a numeric adjacent
                valid_set.add(m_location.values())
                for cardinal_location, cardinal_value in grid_copy.get_cardinal_tiles(m_location):
                    if cardinal_value[0] == 77 and cardinal_location.values() not in checked_set:
                        unchecked_set.add(cardinal_location.values())

        tile_set = valid_set.copy()  # adds locations of all adjacent numeric values surrounding the unrevealed tiles.
        for location in valid_set:
            m_location = MArrayCoordinate(location)
            # location_value = grid_copy.grid_array[m_location.values()]
            for adj_location, adj_tile_info in grid_copy.get_surrounding_tiles(m_location):
                if adj_location.values() not in tile_set and 1 <= adj_tile_info[0] < 10:
                    tile_set.add(adj_location.values())

        final_tile_set = tile_set.copy()  # adds all adj tiles to listed numerics, and sets any new numeric to 0
        for location in tile_set:
            m_location = MArrayCoordinate(location)
            location_value = grid_copy.grid_array[m_location.values()]
            if 1 <= location_value[0] < 10 and location_value[0] != 77:
                for adj_location, adj_tile_info in grid_copy.get_surrounding_tiles(m_location):
                    if adj_location.values() not in final_tile_set:
                        if 1 <= adj_tile_info[0] < 10:
                            grid_copy.grid_array[adj_location.i, adj_location.j, 0] = 0
                        final_tile_set.add(adj_location.values())

        i_values = []
        j_values = []
        for location in final_tile_set:
            self.grid_array.examine_tile(MArrayCoordinate(location))
            i_values.append(location[0])
            j_values.append(location[1])

        lower_coordinate_pair = MArrayCoordinate(min(i_values), min(j_values))
        upper_coordinate_pair = MArrayCoordinate(max(i_values) + 1, max(j_values) + 1)
        sub_array = grid_copy.slice_copy(lower_coordinate_pair, upper_coordinate_pair, fix_sat=True)
        sub_array = self.clean_subarray(sub_array)
        sub_array_number_unrevealed = np.count_nonzero(sub_array.grid_array[:, :, 0] == 77)
        if sub_array_number_unrevealed > 15:
            print("SPLITTING ARRAY")
            split_list = self.split_subarray(sub_array)
            if split_list:
                for i in range(len(split_list)):
                    split_list[i][0] += lower_coordinate_pair

                # for i in range(len(split_list)):
                #     split_list[i] = (split_list[i][0] + lower_coordinate_pair, split_list[i][1])
            return split_list

        return [(lower_coordinate_pair, sub_array)]

    @staticmethod
    def clean_subarray(sub_array):
        h, w, d = sub_array.shape

        # Any unrevealed not adjacent to a nonzero numeric is set to 0
        num_locs = set()
        for i in range(0, h):
            for j in range(0, w):
                location = MArrayCoordinate(i, j)
                value = sub_array.grid_array[location.i, location.j, 0]

                if 1 <= value < 77:
                    num_locs.add(location.values())
                    continue

                number_nonzero = 0
                for surrounding_tiles, surrounding_tile_info in sub_array.get_surrounding_tiles(location):
                    if 1 <= surrounding_tile_info[0] < 77:
                        number_nonzero += 1
                        break

                if value == 77 and not number_nonzero:
                    sub_array.grid_array[location.i, location.j, 0] = 0

        # Any numerics not adjacent to an unrevealed tile are set to 0
        for loc in num_locs:
            m_loc = MArrayCoordinate(loc)
            adjacent_unrevealed = 0
            for surrounding_tiles, surrounding_tile_info in sub_array.get_surrounding_tiles(m_loc):
                if surrounding_tile_info[0] == 77:
                    adjacent_unrevealed += 1

            if 1 <= sub_array.grid_array[m_loc.i, m_loc.j, 0] < 77 and not adjacent_unrevealed:
                sub_array.grid_array[m_loc.i, m_loc.j, 0] = 0

        return sub_array  # return  cleaned sub array

    def split_subarray(self, sub_array):

        height, width, d = sub_array.shape
        subset_list = []
        w = width
        h = height

        if w % 2 != 0:
            w += 1
        if h % 2 != 0:
            h += 1
        unrevealed = (sub_array.grid_array[:, :, 0] == 77)
        number_unrevealed = np.count_nonzero(unrevealed)
        col_sums = np.sum(unrevealed, axis=0)
        row_sums = np.sum(unrevealed, axis=1)

        if max(col_sums) > max(row_sums):
            print("horizontal split")
            mines = 0
            r = 0
            for r in range(number_unrevealed):
                mines += row_sums[r]
                if mines >= number_unrevealed//2:
                    break

            upper = sub_array.slice_copy(MArrayCoordinate(0, 0), MArrayCoordinate(r, width), fix_sat=True)
            upper_mask = (upper.grid_array[:, :, 0] >= 1) & (upper.grid_array[:, :, 0] < 77)
            upper.grid_array[-1, :, 0][upper_mask[-1, :]] = 0
            upper = self.clean_subarray(upper)


            lower = sub_array.slice_copy(MArrayCoordinate(r, 0), MArrayCoordinate(height, width), fix_sat=True)
            lower_mask = (lower.grid_array[:, :, 0] >= 1) & (lower.grid_array[:, :, 0] < 77)
            lower.grid_array[0, :, 0][lower_mask[0, :]] = 0
            lower = self.clean_subarray(lower)

            subset_list.append([MArrayCoordinate(0, 0), upper])
            subset_list.append([MArrayCoordinate(r, 0), lower])

        else:
            print("vertical split")
            mines = 0
            c = 0
            for c in range(number_unrevealed):
                mines += col_sums[c]
                if mines >= number_unrevealed // 2:
                    break

            left = sub_array.slice_copy(MArrayCoordinate(0, 0), MArrayCoordinate(height, c), fix_sat=True)
            left_mask = (left.grid_array[:, :, 0] >= 1) & (left.grid_array[:, :, 0] < 77)
            left.grid_array[:, -1, 0][left_mask[:, -1]] = 0
            left = self.clean_subarray(left)

            right = sub_array.slice_copy(MArrayCoordinate(0, c), MArrayCoordinate(height, width), fix_sat=True)
            right_mask = (right.grid_array[:, :, 0] >= 1) & (right.grid_array[:, :, 0] < 77)
            right.grid_array[:, 0, 0][right_mask[:, 0]] = 0
            right = self.clean_subarray(right)

            subset_list.append([MArrayCoordinate(0, 0), left])
            subset_list.append([MArrayCoordinate(0, c), right])

        return_list = []
        for loc, splitted in subset_list:
            splitted_unrev = (splitted.grid_array[:, :, 0] == 77)
            splitted__num_unrev = np.count_nonzero(splitted_unrev)
            if splitted__num_unrev > 15:
                print(f"Split subarray of: {splitted__num_unrev} again")
                split_list = self.split_subarray(splitted)
                for i in range(len(split_list)):
                    split_list[i][0] += loc
                    return_list.append(split_list[i])
            else:
                return_list.append([loc, splitted])

        return return_list  # returns offset (for each) from original subset and the split subsets.


    @staticmethod
    def brute_force_method(subarray):
        # Handles a subarray of the grid. Generates all 2^n, n= # unrevealed tiles possible mine layouts.
        # Validate each layout to determine which ones are possible
        # Find proportion of valid layouts with a mine for each square.
        # Select a space with the HIGHEST probability of being a mine for flagging. Or select a space with the
        # LOWEST probability of being a mine for left clicking.

        # KNOWN ISSUES: Nan is considered a probability. This SHOULD NOT happen.
        # SHOULDN'T MAKE A PARTIAL DECISION UNTIL IT IS THE BEST POSSIBLE

        # set numeric tiles on the edges to 0. and mines not touching any numerics to 0
        # 'CLEAN GRID"

        s = time.process_time()

        valid_combinations = []
        h, w, d = subarray.shape
        subarray_proxy = subarray.copy()

        number_unrevealed = np.count_nonzero(subarray.grid_array[:, :, 0] == 77)
        unrevealed_locations = np.asarray(subarray.grid_array[:, :, 0] == 77).nonzero()
        print(f"Simulating all {2 ** number_unrevealed} outcomes ({number_unrevealed} tiles)")
        combinations_list = list(
            product((0, 1), repeat=number_unrevealed))  # list of all 2^n combinations. list of sets of values

        for combination in combinations_list:

            combination_grid = subarray.grid_array[:, :, 0].copy()
            for i, tile in enumerate(combination):
                if tile:
                    combination_grid[unrevealed_locations[0][i], unrevealed_locations[1][i]] = 99

            subarray_proxy.update(combination_grid)
            # accept if every nonzero numeric is exactly satisfied.
            # equivalent: reject if any nonzero numeric are NOT satisfied

            nonzero_numeric = np.logical_and(subarray_proxy.grid_array[:, :, 0] > 0,
                                             subarray_proxy.grid_array[:, :, 0] < 77)

            not_satisfied = subarray_proxy.grid_array[:, :, 0] != subarray_proxy.grid_array[:, :, 1]

            rejectance = np.logical_and(nonzero_numeric, not_satisfied)
            if not rejectance.any():
                valid_combinations.append(combination)

        valid_combination_array = np.asarray(valid_combinations)
        column_sums = valid_combination_array.sum(axis=0)
        column_proportions = column_sums / len(valid_combination_array)

        one_locs = np.argwhere(column_proportions == 1)
        zero_locs = np.argwhere(column_proportions == 0)
        return_locs = []

        for loc in one_locs:
            location = MArrayCoordinate(unrevealed_locations[0][loc[0]],
                                        unrevealed_locations[1][loc[0]])
            return_locs.append((location, 1, 'right'))

        for loc in zero_locs:
            location = MArrayCoordinate(unrevealed_locations[0][loc[0]],
                                        unrevealed_locations[1][loc[0]])
            return_locs.append((location, 1, 'left'))

        e = time.process_time()
        print(f"TIME: {e-s}")
        if return_locs:
            return return_locs

        max_value = np.max(column_proportions)
        max_value_position = np.argmax(column_proportions)

        min_value = np.min(column_proportions)
        min_value_position = np.argmin(column_proportions)

        if np.isnan(min_value) or np.isnan(max_value):
            print("WHY IS PROB NAN!?!?")

        location = MArrayCoordinate(unrevealed_locations[0][min_value_position],
                                    unrevealed_locations[1][min_value_position])
        print(f"PROB: {1 - min_value}")
        return [(location, 1 - min_value, 'left')]

    def backtrack_dfs(self, og_array, subarray,
                      used_combinations,
                      valid_combinations,
                      location_coord_map,
                      location_index):

        location_string = "".join(map(str, location_index))
        if location_string in used_combinations:
            return
        used_combinations.add(location_string)

        combination_grid = og_array.grid_array[:, :, 0].copy()
        for i in range(len(location_index)):
            if location_index[i] == 1:
                combination_grid[location_coord_map[i].values()] = 99

        subarray.update(combination_grid)
        # accept if every nonzero numeric is exactly satisfied.
        # equivalent: reject if any nonzero numeric are NOT satisfied
        nonzero_numeric = np.logical_and(subarray.grid_array[:, :, 0] > 0, subarray.grid_array[:, :, 0] < 77)

        satisfaction = subarray.grid_array[:, :, 0] - subarray.grid_array[:, :, 1]

        undersat = np.logical_and(nonzero_numeric, satisfaction > 0)
        if undersat.any():
            for i in range(len(location_index)):
                if location_index[i] == 0:
                    n_index = location_index.copy()
                    n_index[i] = 1
                    self.backtrack_dfs(og_array, subarray,
                                       used_combinations,
                                       valid_combinations,
                                       location_coord_map,
                                       n_index)
            return

        oversat = np.logical_and(nonzero_numeric, satisfaction < 0)
        if oversat.any():
            return

        valid_combinations.append(location_string)
        return

    def backtracking_method(self, subarray):

        s = time.process_time()
        valid_combinations = []
        h, w, d = subarray.shape
        subarray_proxy = subarray.copy()

        number_unrevealed = np.count_nonzero(subarray.grid_array[:, :, 0] == 77)
        unrevealed_locations = np.asarray(subarray.grid_array[:, :, 0] == 77).nonzero()
        print(f"Backtracking on: {number_unrevealed} tiles")
        location_index = [0] * number_unrevealed
        location_coord_map = {}
        for i in range(number_unrevealed):
            location_coord_map[i] = MArrayCoordinate(unrevealed_locations[0][i], unrevealed_locations[1][i])

        used_combinations = set()

        self.backtrack_dfs(subarray, subarray_proxy, used_combinations, valid_combinations, location_coord_map, location_index)

        comb_array = np.array([[[int(x)] for x in y] for y in valid_combinations])
        #valid_combination_array = np.asarray(comb_array)
        column_sums = comb_array.sum(axis=0)
        column_proportions = column_sums / len(comb_array)

        one_locs = np.argwhere(column_proportions == 1)
        zero_locs = np.argwhere(column_proportions == 0)
        return_locs = []

        for loc in one_locs:
            location = location_coord_map[loc[0]]
            return_locs.append((location, 1, 'right'))

        for loc in zero_locs:
            location = location_coord_map[loc[0]]

            return_locs.append((location, 1, 'left'))

        e = time.process_time()
        print(f"TIME: {e-s}")

        if return_locs:
            return return_locs

        max_value = np.max(column_proportions)
        max_value_position = np.argmax(column_proportions)

        min_value = np.min(column_proportions)
        min_value_position = np.argmin(column_proportions)

        if np.isnan(min_value) or np.isnan(max_value):
            print("WHY IS PROB NAN!?!?")

        location = MArrayCoordinate(unrevealed_locations[0][min_value_position],
                                    unrevealed_locations[1][min_value_position])
        print(f"PROB: {1 - min_value}")
        return [(location, 1 - min_value, 'left')]

