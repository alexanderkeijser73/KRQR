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
                self.rels[qt_b.name].append((rel, qt_a.name))     #key van dict is nu "ontvangende" quantity
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
            qt_a.addVC(qt_b, val_a, val_b)
        else: raise ValueError("One of the quanties is not defined in the system {}".format(self.name))


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
            print("States to explore: \n")
            for bli in states_to_explore:
                print(bli.toTuples())
            print("\n")
            new_states_to_explore = []
            for i, state in enumerate(states_to_explore):
                print("\tState {} to explore:\n\t----------------------------------------------------".format(i+1))
                next_states = self.nextStates(state)
                # print("New connections:\n")
                # for bleh in next_states:
                #     print(bleh.toTuples(),"connected with \n")
                #     print(state.toTuples(),"\n")
                state_connections = [(state,next_state) for next_state in next_states]
                for next_state in next_states:
                    deltas = [qt.delta for qt in next_state.asList]
                    new_states_to_explore_vals = [i.toTuples() for i in new_states_to_explore]
                    if not next_state.toTuples() in new_states_to_explore:
                        new_states_to_explore.append(next_state)
                explored_state_vals = [explored_state.toTuples() for explored_state in explored_states]
                if not state.toTuples() in explored_state_vals:
                    explored_states.append(state)
            states_to_explore = new_states_to_explore
            print("All explored states:\n")
            for bla in explored_state_vals:
                print(bla)
            print("\n------------------------------------------------------------\n")
        return explored_states, connections

    def nextStates(self,state):
        nextStates = [[]]
        for qt in state.asList:
            qt_rels = self.rels[qt.name]
            nextValues, nextDeltas = state.getNextValues(qt)
            if nextDeltas is None:
                nextDeltas = state.getNextDeltas(qt,qt_rels)
            print("\tnextValues for {}: {}".format(qt.name,nextValues))
            print("\tnextDeltas for {}: {}\n".format(qt.name, nextDeltas))
            nextStatesPerQt = []
            for nextDelta in nextDeltas:
                for nextValue in nextValues:
                    qtcopy = deepcopy(qt)
                    qtcopy.setDelta(nextDelta)
                    qtcopy.setValue(nextValue)
                    nextStatesPerQt.append(qtcopy)
            nextStates = [i+[j] for i in nextStates for j in nextStatesPerQt]
            # print("Shape nextStates: ".format(shape(nextStates)))
            nonValidStates = []
            for nextState in nextStates:
                # if not(self.checkValidVC(nextState)):
                #     nonValidStates.append(nextState)
                #     print("State removed because not valid with VC: \n{}".format(State(nextState).toTuples()))
                if CausalModel.isSame(State(nextState), state):
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

    def getNextValues(self, qt):
        nextDeltas = None
        qt_vc = qt.vc
        if qt_vc is not None:
            qt_a_name = qt.vc[0].name
            qt_a_val = qt.vc[1]
            for (qt_name,val,delta) in self.toTuples():
                if qt_a_name == qt_name and qt_a_val == val:
                    if not qt.increaseValue() and qt.delta ==0:
                        nextDeltas = [0]
                    elif not qt.decreaseValue() and qt.delta ==0:
                        nextDeltas = [0]
                    return [qt_a_val], nextDeltas
        if qt.delta == -1:      #check if derivative is negative
            if qt.decreaseValue():
                if qt.val == Quantity.zpmdom[2]:
                    """EPSILON ORDERING"""
                    posvals = [qt.val-1]
                else: posvals = [qt.val, qt.val-1]
            else:
                """CHECK OF DIT HOORT"""
                nextDeltas = [0]
                posvals = [qt.val]
        elif qt.delta == 0:    #check if derivative is zero
            posvals = [qt.val]
        else:                    #derivative is positive
            if qt.increaseValue():
                if qt.val == Quantity.zpmdom[0]:
                    """EPSILON ORDERING"""
                    posvals = [qt.val+1]
                else: posvals = [qt.val, qt.val+1]
            else:
                """CHECK OF DIT HOORT"""
                nextDeltas = [0]
                posvals = [qt.val]
        return posvals, nextDeltas

    def getNextDeltas(self,qt, rels):
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
        if 1 in signs:
            if qt.increaseDelta():
                nextDeltas = [qt.delta + 1]
        if -1 in signs:
            if qt.decreaseDelta():
                nextDeltas = [qt.delta - 1]
        """DERIVATIVES VAN EXOGENEOUS QTS KUNNEN IN ELKE STATE VERANDEREN"""
        if qt.exog:
            if qt.increaseDelta():
                nextDeltas.append(qt.delta + 1)
            if qt.decreaseDelta():
                nextDeltas.append(qt.delta -1)
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
        self.vc = None

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

    def addVC(self, qt_b, val_a, val_b):
        self.vc = (qt_b, val_a, val_b)
