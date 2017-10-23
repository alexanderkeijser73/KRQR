import itertools
from collections import defaultdict
from copy import deepcopy

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
            if (rel, qt_a) not in self.rels[qt_b.name]:
                self.rels[qt_b.name].append((rel, qt_a))     #key van dict is nu "ontvangende" quantity
        else:
            raise ValueError("Either one of the quantities or the relationship is not defined")

    def addVC(self, qt_a, val_a, qt_b, val_b):
        qts = self.getState()
        if qt_a in qts.asList and qt_a in qts.asList:
            if val_a not in qt_a.dom[1]:
                raise ValueError("Value of first quantity not valid")
            if val_b not in qt_b.dom[1]:
                raise ValueError("Value of second quantity not valid")
            if (qt_b.name, val_a, val_b) not in self.vc[qt_a.name]:
                self.vc[qt_a.name].append((qt_b.name, val_a, val_b))     #key van dict is nu "ontvangende" quantity
            if (qt_a.name, val_b, val_a) not in self.vc[qt_b.name]:
                self.vc[qt_b.name].append((qt_a.name, val_b, val_a))     #key van dict is nu "ontvangende" quantity

    def checkValidVC(self, state):
        valid = True
        for qt_a in state:
            vcs = self.vc[qt_a.name]
            for vc in vcs:
                qt_b_name = vc[0]
                qt_a_val = vc[1]
                qt_b_val = vc[2]
                for qt_b in state:
                    if qt_b.name == qt_b_name:
                        if qt_a.val == qt_a_val and qt_b.val != qt_b_val:
                            valid = False
                        elif qt_a.val != qt_a_val and qt_b.val == qt_b_val:
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


    def generateStates(self, init_state):
        # error catcher???
        explored_states = []
        states_to_explore = [init_state]
        connections = []
        while len(states_to_explore) > 0:
            for state in states_to_explore:
                next_states = self.nextStates(state)
                state_connections = [(state,next_state) for next_state in next_states]
                for next_state in next_states:
                    deltas = [qt.delta for qt in next_state.asList]
                    explored_state_vals = [explored_state.toTuples() for explored_state in explored_states]
                    if not next_state.toTuples() in explored_state_vals:
                        states_to_explore.append(next_state)
                    # else: print("Already explored: {}\n".format(next_state.toTuples()))
                    # else: print("Derivative termination")
                if not state in explored_states:
                    explored_states.append(state)
                print("All explored states: {}\n".format(explored_state_vals))
                # else: print("Already in explored states\n")
                states_to_explore.remove(state)
            print("States to explore: ",[state.toTuples() for state in states_to_explore], "\n")
        return explored_states, connections

    def nextStates(self,state):
        nextStates = [[]]
        for qt in state.asList:
            ambiguous = False
            qt_rels = self.rels[qt.name]
            nextValues, nextDeltas = qt.getNextValues()
            # nextDelta = qt.getNextDelta(qt_rels)
            if nextDeltas is None:
                nextDeltas, ambiguous = qt.getNextDelta(qt_rels)
            if ambiguous:
                break
            # print("nextValues for {}: {}".format(qt.name,nextValues))
            # print("nextDelta for {}: {}\n".format(qt.name, nextDeltas))
            nextStatesPerQt = []
            for nextDelta in nextDeltas:
                for nextValue in nextValues:
                    qtcopy = deepcopy(qt)
                    qtcopy.setDelta(nextDelta)
                    qtcopy.setValue(nextValue)
                    nextStatesPerQt.append(qtcopy)
            nextStates = [i+[j] for i in nextStates for j in nextStatesPerQt]
            # print("Shape nextStates: ".format(shape(nextStates)))
        if not(ambiguous):
            nonValidStates = []
            for nextState in nextStates:
                if not(self.checkValidVC(nextState)) or CausalModel.isSame(State(nextState), state):
                    nonValidStates.append(nextState)
            for nextState in nonValidStates:
                nextStates.remove(nextState)
        nextStatesAsStateObjs = [State(state) for state in nextStates]
        return nextStatesAsStateObjs


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

    def __init__(self, name, dom=None):
        if dom is None:
            self.dom = ('zpm',Quantity.zpmdom)
        elif dom == 'zp':
            self.dom = ('zp',Quantity.zpdom)
        else:
            raise ValueError("The only possible quantity domains are 'zpm' and 'zp'")
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


    # def getNextValues(self):
    #     delta = None
    #     if self.delta == -1:      #check if derivative is negative
    #         if self.val == Quantity.zpmdom[2]:
    #             posvals = [self.val-1]
    #         elif self.val == Quantity.zpmdom[1]:
    #             posvals = [self.val-1, self.val]
    #             # self.setDelta(0) moet in bepaalde tak komen..
    #         else:
    #             delta = 0
    #             posvals = [self.val]
    #     elif self.delta == 0:    #check if derivative is zero
    #         posvals = [self.val]
    #     else:
    #         if self.val == Quantity.zpmdom[0]:
    #             posvals = [self.val+1]
    #         elif self.val == Quantity.zpmdom[1]:
    #             posvals = [self.val, self.val+1]
    #             # self.setDelta(0) moet in bepaalde tak komen..
    #         else:
    #             delta = 0
    #             posvals = [self.val]
    #     return posvals, delta
    def getNextValues(self):
        nextDeltas = None
        if self.delta == -1:      #check if derivative is negative
            if self.decreaseValue():
                if self.val == Quantity.zpmdom[2]:
                    """EPSILON ORDERING"""
                    posvals = [self.val-1]
                else: posvals = [self.val, self.val-1]
            else:
                """CHECK OF DIT HOORT"""
                nextDeltas = [0]
                posvals = [self.val]
        elif self.delta == 0:    #check if derivative is zero
            posvals = [self.val]
        else:
            if self.increaseValue():
                if self.val == Quantity.zpmdom[0]:
                    """EPSILON ORDERING"""
                    posvals = [self.val+1]
                else: posvals = [self.val, self.val+1]
            else:
                """CHECK OF DIT HOORT"""
                nextDeltas = [0]
                # self.setDelta(0)
                posvals = [self.val]
        return posvals, nextDeltas



    def getNextDelta(self, rels):
        ambiguous = False
        signs = []
        nextDeltas = [self.delta]
        for (relType, qt_a) in rels:
            val = qt_a.val
            delta = qt_a.delta
            if relType == 'i+':
                if val != 0:
                    signs.append(1)
            if relType == 'i-':
                if val != 0:
                    signs.append(-1)
            if relType == 'p+':
                if delta != 0:
                    signs.append(1)
            if relType == 'p-':
                if delta != 0:
                    signs.append(-1)
        if 1 in signs and -1 in signs:
            #raise ValueError('Shit is AMBIGU!')
            ambiguous = True
        if 1 in signs:
            if self.increaseDelta():
                nextDeltas = [self.delta + 1]
        if -1 in signs:
            if self.decreaseDelta():
                nextDeltas = [self.delta - 1]
        """DERIVATIVES VAN EXOGENEOUS QTS KUNNEN IN ELKE STATE VERANDEREN"""
        if self.exog:
            if self.increaseDelta():
                nextDeltas.append(self.delta + 1)
            if self.decreaseDelta():
                nextDeltas.append(self.delta -1)
        return nextDeltas , ambiguous
