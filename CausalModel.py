import itertools
from collections import defaultdict


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
            vc =[]
        self.vc = vc


    def addEntity(self, ent):
        if not isinstance(ent, Entity):
            raise TypeError("Only objects of type Entity can be added to the model")
        self.ents.append(ent)


    def addRel(self, qt_a, rel, qt_b):
        qts = self.getQts()
        if rel in CausalModel.pos_rels and qt_a in qts and qt_a in qts:
            if (rel, qt_a) not in self.rels[qt_b.name]:
                self.rels[qt_b.name].append((rel, qt_a))     #key van dict is nu "ontvangende" quantity
        else:
            raise ValueError("Either one of the quantities or the relationship is not defined")

    def addVC(self, qt_a, val_a, qt_b, val_b):
        if qt_a.dom == 'zpm':
            if val_a not in Quantity.zpmdom:
                raise ValueError("Value of first quantity not valid")
        else:
            if val_a not in Quantity.zpdom:
                raise ValueError("Value of first quantity not valid")
        if qt_b.dom == 'zpm':
            if val_b not in Quantity.zpmdom:
                raise ValueError("Value of second quantity not valid")
        else:
            if val_b not in Quantity.zpdom:
                raise ValueError("Value of second quantity not valid")
        self.vc.append((qt_a, val_a, qt_b, val_b))

    def checkValidVC(self, state):
        valid = False
        cvs = self.vc
        for (qt_a, val_a, qt_b, val_b) in cvs:

            # if qt_a.val == val_a and qt_b.val == val_b:
            #     valid = True
            # elif qt_a.val != val_a and qt_b.val != val_b:
            #     valid = True

            for (qt1, val1, delta1) in state:
                if qt1 == qt_a and val1 == val_a:
                    for (qt2, val2, delta2) in state:
                        if qt2 == qt_b and val2 == val_b:
                            valid = True

                # if qt1 == qt_a and val1 == val_a:
                # elif qt_1.val != val_a
                #     and qt_b.val != val_b:
                #             valid = True
        return valid

    def getQts(self):
        return list(itertools.chain(*[ent.qts for ent in self.ents]))

    def getState(self):
        qts = self.getQts()
        return [(qt.name, qt.val, qt.delta) for qt in qts]

    def setState(self, vals):
        for val in vals:
            val[0].setValue(val[1])
            val[0].setDelta(val[2])


    def generateStates(self):
        if beginStateKlopt:
            while notTerminated():
                nextStates = self.nextStates()
                self.stateGraph.append(nextStates)

    # def findNextStatesPerQt(self, qt):
    #     nextValues = qt.getNextValues()
    #     nextDelta = qt.getNextDelta()
    #     nextStatesPerQt = [(stateQt[0],i,nextDelta) for i in nextValues] # lijst met tuples
    #     return nextStatesPerQt
# next delta is nu waarde ipv list nog aanppassen

    def nextStates(self):
        # Error catcher????
        nextStates = [[]]
        qts = self.getQts()
        for qt in qts:
            qt_rels = self.rels[qt.name]
            nextValues = qt.getNextValues()
            nextDelta = qt.getNextDelta(qt_rels)
            nextStatesPerQt = [(qt,nextValue,nextDelta) for nextValue in nextValues]  #maybe deepcopy object or make dict
            # nextStatesPerQt = findNextStatesPerQt(qt) # creates list with states
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
            self.dom = 'zpm'
        elif dom == 'zp':
            self.dom = 'zp'
        else:
            raise ValueError("The only possible quantity domains are 'zpm' and 'zp'")
        self.val = None
        self.delta = None
        self.name = name

    def setValue(self, val):
        if self.dom == 'zp':
            if val in Quantity.zpdom:
                self.val = val
            else:
                raise ValueError("The only possible values for the domain 'zp' are 0 (zero) and 1 (positive)")
        else:
            if val in Quantity.zpmdom:
                self.val = val
            else:
                raise ValueError("The only possible values for the domain 'zpm' are 0 (zero) , 1 (positive) and 2 (max)")

    def increaseValue(self):
        boolean = False
        if self.dom  == 'zpm':
            if self.val + 1 in Quantity.zpmdom:
                self.val += 1
                boolean = True
        else:
            if self.val + 1 in Quantity.zpdom:
                self.val += 1
                boolean = True
        return boolean


    def decreaseValue(self):
        if self.dom  == 'zpm':
            if self.val - 1 in Quantity.zpmdom:
                self.val -= 1
                return True
            else:
                return False
        else:
            if self.val - 1 in Quantity.zpdom:
                self.val -= 1
                return True
            else:
                return False

    def setDelta(self, delta):
        if delta in Quantity.deltadom:
            self.delta = delta
        else:
            raise ValueError("The only possible values for delta are -1 (negative) 0 (zero) and 1 (positive)")


    def increaseDelta(self):
        boolean = False
        if self.delta + 1 in Quantity.deltadom:
            self.delta += 1
            boolean = True
        return boolean


    def decreaseDelta(self):
        boolean = False
        if self.delta - 1 in Quantity.deltadom:
            self.delta -= 1
            boolean = True
        return boolean

    def getNextValues(self):
        if self.delta == Quantity.deltadom[0]:
            if self.val == Quantity.zpmdom[0]:      #same for zpmdom and zpdom
                posvals = [self.val]
            elif self.val == Quantity.zpmdom[1]:    #same for zpmdom and zpdom
                posvals = [Quantity.zpmdom[0], Quantity.zpmdom[1]]
            elif self.val == Quantity.zpmdom[2]:
                posvals = [Quantity.zpmdom[1]]

        elif self.delta == Quantity.deltadom[1]:
            posvals = [self.val]
        elif self.delta == Quantity.deltadom[2]:
            if self.val == Quantity.zpmdom[0]:      #same for zpmdom and zpdom
                posvals = [Quantity.zpmdom[1]]
            elif self.val == Quantity.zpmdom[1]:    #same for zpmdom and zpdom
                posvals = [Quantity.zpmdom[1], Quantity.zpmdom[2]]
            elif self.val == Quantity.zpmdom[2]:
                posvals = [self.val]
        return posvals

    def getNextDelta(self, rels):
        signs = []
        for (relType, qt_a) in rels:
            val = qt_a.val
            delta = qt_a.delta
            if relType == 'i+':
                if val != Quantity.zpmdom[0]:
                    signs.append(1)
            if relType == 'i-':
                if val != Quantity.zpmdom[0]:
                    signs.append(-1)
            if relType == 'p+':
                if delta != Quantity.deltadom[1]:
                    signs.append(1)
            if relType == 'p-':
                if delta != Quantity.deltadom[1]:
                    signs.append(-1)
        if Quantity.deltadom[2] in signs and Quantity.deltadom[0] in signs:
            raise ValueError('Shit is AMBIGU!')
        new_delta = self.delta
        if Quantity.deltadom[2] in signs:
            if new_delta != Quantity.deltadom[2]:
                new_delta += 1
        if Quantity.deltadom[0] in signs:
            if new_delta != Quantity.deltadom[0]:
                new_delta -= 1
        return new_delta
