import itertools
from collections import defaultdict


class CausalModel(object):
    """docstring for CausalModel"""
    pos_rels = ['p+', 'p-','i+','i-']

    def __init__(self, name, ents=None, rels=None):
        self.name = name
        if ents is None:
            ents = []
        self.ents = ents
        self.qts = list(itertools.chain(*[ent.qts for ent in self.ents]))
        if rels is None:
            rels = defaultdict(list)
        self.rels = rels

    def addEntity(self, ent):
        if not isinstance(ent, Entity):
            raise TypeError("Only objects of type Entity can be added to \
                            the model")
        self.ents.append(ent)


    def addRel(self, qt_a, rel, qt_b):
        if rel in CausalModel.pos_rels and qt_a in self.qts and qt_a in self.qts:
            if (rel, qt_b.name) not in self.rels[qt_a.name]:
                self.rels[qt_a.name].append((rel, qt_b.name))
        else:
            raise ValueError("Either one of the quantities or the relationship \
                                is not defined")


class Entity(object):
    """docstring for Entity."""
    def __init__(self, name, qts=None):
        if qts is None:
            qts = []
        self.name = name
        self.qts = qts

    def addQuantity(self, qt):
        if not isinstance(qt, Quantity):
            raise TypeError("Only objects of type Quantity can be assigned to \
                            the entity")
        self.qts.append(qt)

class Quantity(object):
    """docstring for Quantity."""
    zpdom = [0,1]       #possible values for zero/positive domain
    zpmdom = [0,1,2]    #possible values for zero/positive/max domain

    def __init__(self, name, dom=None):
        if dom is None:
            self.dom = 'zpm'
        elif dom == 'zp':
            self.dom = 'zp'
        else:
            raise ValueError("The only possible quantity domains are 'zpm' and \
                            'zp'")
        self.val = None
        self.name = name

    def setValue(self, val):
        if self.dom == 'zp':
            if val in Quantity.zpdom:
                self.val = val
            else:
                raise ValueError("The only possible values for the domain 'zp' \
                                are 0 (zero) and 1 (positive)")
        else:
            if val in Quantity.zpmdom:
                self.val = val
            else:
                raise ValueError("The only possible values for the domain 'zpm'\
                                are 0 (zero) , 1 (positive) and 2 (max)")

    def increaseValue(self):
        if self.dom  == 'zpm':
            if self.val + 1 in Quantity.zpmdom:
                self.val += 1
                return True
            else:
                return False
        else:
            if self.val + 1 in Quantity.zpdom:
                self.val += 1
                return True
            else:
                return False


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
