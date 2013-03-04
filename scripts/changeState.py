# Code to change a state file
from twitterApp import *
import cPickle

def updateState(stateIn, stateOut):
    state = State.readStateFile(stateIn)

    # Set attributes of the state
    state.inspectedUnits = set()
    state.numBreaks = 18
    state.numFixes = 38
    
    state.write(stateOut)


if __name__ == '__main__':
    updateState('twitterApp.state', 'twitterApp.state')
