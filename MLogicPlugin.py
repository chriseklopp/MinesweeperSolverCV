"""
Contains solving logic for a Minesweeper puzzle
Acts only on an MBoardState object.
Makes ONE decision each update cycle.

Takes in board information and returns an action at a location

"""


def logic_plugin(grid_array, flags):
    print("This is an active logic plugin")
    location = 0
    action = 'left'
    return location, action
