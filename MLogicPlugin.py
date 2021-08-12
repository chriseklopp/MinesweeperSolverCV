"""
Contains solving logic for a Minesweeper puzzle
Acts only on an MBoardState object.
Makes ONE decision each update cycle.

Takes in board information and returns an action at a location

"""

def MLogicPlugin(grid_array, flags):
    #print("This is an active logic plugin")
    # print("tx= ", MLogicPlugin.testx)
    # print("ty= ", MLogicPlugin.testy)



    location = [MLogicPlugin.testx, MLogicPlugin.testy]
    MLogicPlugin.testx += 1
    MLogicPlugin.testy += 1
    action = 'left'
    action = 'right'
    return location, action


MLogicPlugin.testx = 0
MLogicPlugin.testy = 0
