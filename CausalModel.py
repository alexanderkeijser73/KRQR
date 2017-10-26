import itertools
from collections import defaultdict
from copy import deepcopy
import random

class CausalModel(object):
    """docstring for CausalModel"""
    pos_rels = ['p+', 'p-','i+','i-']

    def __init__(self, name, ents=None, rels=None, vc=None):
        self.name = name
        if ents is None:
            ents = []
        self.ents = ents
        if rels is None:
            rels = defaultdict(list)
        self.rels = rels
        if vc is None:
            vc = defaultdict(list)
        self.vc = vc

    def addEntity(self, ent):
        if not isinstance(ent, Entity):
            raise TypeError("Only objects of type Entity can be added to the model")
        self.ents.append(ent)

    def addRel(self, qt_a, rel, qt_b):
        qts = self.getState()
        if rel in CausalModel.pos_rels and qt_a in qts.asList and qt_a in qts.asList:
            # add relation to 'receiving' quantity
            if (rel, qt_a) not in self.rels[qt_b.name]:
                self.rels[qt_b.name].append((rel, qt_a.name))
        else:
            raise ValueError("Either one of the quantities or the relationship is not defined")

    def addVC(self, qt_a, val_a, qt_b, val_b):
        qts = self.getState()
        if qt_a in qts.asList and qt_b in qts.asList:
            if not val_a in qt_a.dom[1]:
                raise ValueError("Value of first quantity not valid")
            if not val_b in qt_b.dom[1]:
                raise ValueError("Value of second quantity not valid")
            # add value correspondents to 'receiving' quantity
            if not (val_a, qt_b.name, val_b) in self.vc[qt_a.name]:
                self.vc[qt_a.name].append((val_a, qt_b.name, val_b))
        else: raise ValueError("One of the quanties is not defined in the system {}".format(self.name))

    def checkValidVC(self, state):
        valid = True
        for qt_a in state:
            for (qt_a_val, qt_b_name, qt_b_val) in self.vc[qt_a.name]:
                for qt_b in state:
                    if qt_b.name == qt_b_name and qt_a.val == qt_a_val and qt_b.val != qt_b_val:
                        valid = False
        return valid
            
            
    def getState(self):
        return State(list(itertools.chain(*[ent.qts for ent in self.ents])))

    def setState(self, vals):
        for val in vals:
            val[0].setValue(val[1])
            val[0].setDelta(val[2])

    @staticmethod
    def isSame(nextState, state):
        return nextState.toTuples() == state.toTuples()
    
    @staticmethod
    def isNewConnection(nextState, state, connections):
        isNewConnection = True
        for connection in connections:
            state_a = connection[0]
            state_b = connection[1]
            if state_a == state and state_b == nextState:
                isNewConnection = False
        return isNewConnection

    def nextStates(self,state):
        nextStates = [[]]
        # loop through quantities
        for qt in state.asList:
            # find next values and deltas
            nextValues = state.getNextValues(qt)
            nextDeltas = state.getNextDeltas(qt,self.rels[qt.name])
            # print next values and deltas
            print("\tnextValues for {}: {}".format(qt.name,nextValues))
            print("\tnextDeltas for {}: {}\n".format(qt.name, nextDeltas))
            # create all next states for quantity
            nextStatesPerQt = []
            for nextDelta in nextDeltas:
                for nextValue in nextValues:
                    # if maximum or minimum is reached, set derivative to zero
                    nextDelta_copy = nextDelta
                    if nextDelta == -1 and nextValue == 0:
                        nextDelta_copy = 0
                    elif nextDelta == 1 and nextValue == 2:
                        nextDelta_copy = 0
                    qtcopy = deepcopy(qt)
                    qtcopy.setDelta(nextDelta_copy)
                    qtcopy.setValue(nextValue)
                    nextStatesPerQt.append(qtcopy)
            # combine all states of different quantities
            nextStates = [nextState+[nextState_qt] for nextState in nextStates for nextState_qt in nextStatesPerQt]
        # loop through next states to check whether the next state is valid
        nonValidStates = []
        for nextState in nextStates:
            # check value correspondents
            if not self.checkValidVC(nextState):
                nonValidStates.append(nextState)
            # check if next_state differs from state
            if CausalModel.isSame(State(nextState), state):
                nonValidStates.append(nextState)
        # remove all non-valid next states
        for nextState in nonValidStates:
            nextStates.remove(nextState)
        return [State(state) for state in nextStates]

    def generateStates(self, init_state):
        # error catcher???
        explored_states = []
        states_to_explore = [init_state]
        connections = []

        # loop as long as there are states to explore
        while len(states_to_explore) > 0:
            # print states which we will explore
            print("States to explore: \n")
            for state in states_to_explore:
                print(state.toTuples())
            print("\n")
            # explore all states in states_to_explore
            new_states_to_explore = []
            for i, state in enumerate(states_to_explore):
                print("\tExplore state {}:\n\t----------------------------------------------------".format(i+1))
                # check if state is already explored
                explored_state_vals = [explored_state.toTuples() for explored_state in explored_states]
                if state.toTuples() in explored_state_vals:
                    continue
                else: explored_states.append(state)
                # find next states
                next_states = self.nextStates(state)
                # add new connections and find new states to explore
                for next_state in next_states:
                    next_state_vals = next_state.toTuples()
                    new_states_to_explore_vals = [new_state.toTuples() for new_state in new_states_to_explore]
                    if next_state_vals not in new_states_to_explore_vals and next_state_vals not in explored_state_vals:
                        new_states_to_explore.append(next_state)
                    if self.isNewConnection(next_state_vals, state.toTuples(), connections):
                        connections.append((state.toTuples(), next_state_vals))
            # reset states_to_explore
            states_to_explore = new_states_to_explore
            # print all explored states
            explored_state_vals = [state.toTuples() for state in explored_states]
            print("All explored states:\n")
            for i, state in enumerate(explored_state_vals):
                print("State {}: {}".format(i+1,state))
            print("\n------------------------------------------------------------\n")
        return explored_states, connections
    
class State(object):
    """docstring for State."""
    def __init__(self, qts=None):
        if qts is None:
            qts = []
        self.asList = qts
        # self.parent = None
        # self.children = None

    def toTuples(self):
        qts = self.asList
        return [(qt.name,qt.val,qt.delta) for qt in qts]

    def addQt(self, qt):
        return self.asList.append(qt)

    # get next value based on continuity
    def getNextValues(self, qt):
        posvals = [qt.val]
        # change value for negative derivative
        if qt.delta == -1:
            if qt.val == Quantity.zpmdom[1]:
                posvals = [qt.val, qt.val-1]
            elif qt.val == Quantity.zpmdom[2]:
                # epsilon ordering
                posvals = [qt.val-1]
        # change value for zero derivative
        elif qt.delta == 0:
            posvals = [qt.val]
        # change value for positive derivative
        elif qt.delta == 1:
            if qt.val == Quantity.zpmdom[1]:
                if qt.increaseValue():
                    posvals = [qt.val, qt.val+1]
            elif qt.val == Quantity.zpmdom[0]:
                # epsilon ordering
                posvals = [qt.val+1]
        return posvals

    def getNextDeltas(self, qt, rels):
        signs = []
        nextDeltas = [qt.delta]
        for (relType, qt_a) in rels:
            for qt_in_state in self.asList:
                if qt_in_state.name == qt_a:
                    val = qt_in_state.val
                    delta = qt_in_state.delta
            if relType == 'i+':
                if val != 0:
                    signs.append(1)
            if relType == 'i-':
                if val != 0:
                    signs.append(-1)
            if relType == 'p+':
                if delta == 1:
                    signs.append(1)
                elif delta == -1:
                    signs.append(-1)
            if relType == 'p-':
                if delta == 1:
                    signs.append(-1)
                elif delta == -1:
                    signs.append(1)
        if 1 in signs and -1 in signs:
                nextDeltas = qt.deltadom
        elif 1 in signs:
            if qt.increaseDelta():
                nextDeltas = [qt.delta + 1]
        elif -1 in signs:
            if qt.decreaseDelta():
                nextDeltas = [qt.delta - 1]
        """DERIVATIVES VAN EXOGENEOUS QTS KUNNEN IN ELKE STATE VERANDEREN"""
        if qt.exog:
            if qt.delta == -1:
                nextDeltas = [random.choice([-1,0])]
            if qt.delta == 0:
                nextDeltas = [random.choice(qt.deltadom)]
            if qt.delta == 1:
                nextDeltas = [random.choice([0,1])]
            #if qt.increaseDelta():
                #nextDeltas.append(qt.delta + 1)
            #if qt.decreaseDelta():
                #nextDeltas.append(qt.delta -1)
        return nextDeltas

class Entity(object):
    """docstring for Entity."""
    def __init__(self, name, qts=None):
        if qts is None:
            qts = []
        self.name = name
        self.qts = qts

    def addQuantity(self, qt):
        if not isinstance(qt, Quantity):
            raise TypeError("Only objects of type Quantity can be assigned to the entity")
        self.qts.append(qt)

class Quantity(object):
    """docstring for Quantity."""
    zpdom = [0,1]       #possible values for zero/positive domain
    zpmdom = [0,1,2]    #possible values for zero/positive/max domain
    deltadom = [-1,0,1] #possible values for derivative (delta)

    def __init__(self, name, dom=None, vc=None):
        if dom is None:
            self.dom = ('zpm',Quantity.zpmdom)
        elif dom == 'zp':
            self.dom = ('zp',Quantity.zpdom)
        else:
            raise ValueError("The only possible quantity domains are 'zpm' and 'zp'")
        if vc is None:
            self.vc = []
        self.val = None
        self.delta = None
        self.name = name
        self.exog = False

    def setValue(self, val):
        if val in self.dom[1]:
            self.val = val
        else:
            raise ValueError("The only possible values for the domain {} are {}".format(self.dom[0], self.dom[1]))

    def increaseValue(self):
        return (self.val + 1 in self.dom[1])

    def decreaseValue(self):
        return (self.val - 1 in self.dom[1])

    def setDelta(self, delta):
        if delta in Quantity.deltadom:
            self.delta = delta
        else:
            raise ValueError("The only possible values for delta are -1 (negative) 0 (zero) and 1 (positive)")

    def setExog(self):
        self.exog = True

    def increaseDelta(self):
        return (self.delta + 1 in Quantity.deltadom)
    
    def decreaseDelta(self):
        return (self.delta - 1 in Quantity.deltadom)

    def addVC(self, qt_a, val_a, val_b):
        self.vc.append((qt_a.name, val_a, val_b))
