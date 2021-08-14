"""
Contains solving logic for a Minesweeper puzzle
Makes ONE decision each update cycle.
Takes in board information and returns an action and a location


"""

import random



def MLogicPlugin(grid_array, flags):
    location = [random.randint(0, 29), random.randint(0, 15)]
    action = 'left'
    action = 'right'
    return location, action



# def MLogicPlugin(grid_array, flags):
#     # print("This is an active logic plugin")
#     # print("tx= ", MLogicPlugin.testx)
#     # print("ty= ", MLogicPlugin.testy)
#
#     location = [MLogicPlugin.testx, MLogicPlugin.testy]
#     MLogicPlugin.testx += 1
#     MLogicPlugin.testy += 1
#     action = 'left'
#     action = 'right'
#     return location, action
#
#
# MLogicPlugin.testx = 0
# MLogicPlugin.testy = 0
