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
            if (rel, qt_a.name) not in self.rels[qt_b.name]:
                self.rels[qt_b.name].append((rel, qt_a.name))     #key van dict is nu "ontvangende" quantity
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


    def getQts(self):
        return list(itertools.chain(*[ent.qts for ent in self.ents]))

    def getState(self):
        qts = self.getQts()
        return [(qt.name, qt.val, qt.delta) for qt in qts]

    def setState(self, vals):
        for val in vals:
            val[0].setValue(val[1])
            val[0].setDelta(val[2])
        """DIKKE ERROR"""

    def generateStates(self):
        if beginStateKlopt:
            while notTerminated():
                nextStates = self.nextStates()
                self.stateGraph.append(nextStates)

    def nextStates(self, prevstate):
        nextStates = []
        for (qt,val,delta) in prevstate:
            nextValues = qt.updateValue()
            nextDeltas = qt.updateDelta() #KAN AMBIGU ZIJN

        nextStates = combineNextValuesAndDeltas()
        for state in nextStates:
            if not checkValidCV(state):
                nextStates.flikkerEruit(state)

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
