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
        if rel in CausalModel.pos_rels and qt_a in qts and qt_a in qts:
            if (rel, qt_a) not in self.rels[qt_b.name]:
                self.rels[qt_b.name].append((rel, qt_a))     #key van dict is nu "ontvangende" quantity
        else:
            raise ValueError("Either one of the quantities or the relationship is not defined")

    def addVC(self, qt_a, val_a, qt_b, val_b):
        qts = self.getState()
        if qt_a in qts and qt_a in qts:
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
                        """Werkt niet omdat qt_a niet meer in state zit"""
                        if not(qt_a == qt_a_val and qt_b.val == qt_b_val):
                            valid = False
                        elif not(qt_a.val != val_a and qt_b.val != val_b):
                            valid = False
        return valid

    def getState(self):
        return list(itertools.chain(*[ent.qts for ent in self.ents]))

    def setState(self, vals):
        for val in vals:
            val[0].setValue(val[1])
            val[0].setDelta(val[2])


    def generateStates(self, init_state):
        # if beginStateKlopt:
        notTerminated = True
        states = [init_state]
        for
            nextStates = self.nextStates()
            self.stateGraph.append(nextStates)


    def nextStates(self,state):
        # Error catcher????
        nextStates = [[]]
        for qt in state:
            qt_rels = self.rels[qt.name]
            nextValues = qt.getNextValues()
            nextDelta = qt.getNextDelta(qt_rels)
            print(qt.name)
            print("nextValues: {}".format(nextValues))
            print("nextDelta: {}\n".format(nextDelta))
            nextStatesPerQt = []
            for nextValue in nextValues:
                qtcopy = deepcopy(qt)
                qtcopy.setDelta(nextDelta)
                qtcopy.setValue(nextValue)
                nextStatesPerQt.append(qtcopy)
            nextStates = [i+[j] for i in nextStates for j in nextStatesPerQt]
        for state in nextStates:
            if not self.checkValidVC(state): # todo
                 nextStates.remove(state)  # todo
        return nextStates


class State(object):
    """docstring for State."""
    def __init__(self, statelist):
        self.dict


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


    def increaseDelta(self):
        return (self.delta + 1 in Quantity.deltadom)


    def decreaseDelta(self):
        return (self.delta - 1 in Quantity.deltadom)

    def getNextValues(self):
        if self.delta == -1:      #check if derivative is negative
            if self.decreaseValue():
                posvals = [self.val, self.val-1]
            else:
                """CHECK OF DIT HOORT"""
                self.setDelta(0)
                posvals = [self.val]
        elif self.delta == 0:    #check if derivative is zero
            posvals = [self.val]
        else:
            if self.increaseValue():
                posvals = [self.val, self.val+1]
            else:
                """CHECK OF DIT HOORT"""
                self.setDelta(0)
                posvals = [self.val]
        return posvals

    def getNextDelta(self, rels):
        signs = []
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
            raise ValueError('Shit is AMBIGU!')
        new_delta = self.delta
        if 1 in signs:
            if new_delta != 1:
                new_delta += 1
        if -1 in signs:
            if new_delta != -1:
                new_delta -= 1
        return new_delta
