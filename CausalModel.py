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
                        if qt_a.val == qt_a_val and qt_b.val != qt_b_val:
                            valid = False
                        elif qt_a.val != qt_a_val and qt_b.val == qt_b_val:
                            valid = False
        return valid

    def getState(self):
        return list(itertools.chain(*[ent.qts for ent in self.ents]))

    def setState(self, vals):
        for val in vals:
            val[0].setValue(val[1])
            val[0].setDelta(val[2])

    def isSame(self, nextState, state):
        is_same = True 
        for i in range(len(nextState)):
            qt1 = nextState[i]
            qt2 = state[i]
            if qt1.val != qt2.val or qt1.delta != qt2.delta:
                is_same = False
        return is_same


    def generateStates(self, init_state):
        #if not(validState(init_state)): 
            #raise ValueError("Init state is not valid")
        state_tree  = [[init_state]]
        not_terminated = True
        count = 0
        while not_terminated:
            # de count mag eruit maar dan gaat hij wel forever door.. dus pas op!
            print(count, "-------------------------------------------")
            count +=1
            for branch in state_tree:
                nextStates, not_terminated = self.nextStates(branch[-1])
                # not_terminated checkt of hij ambigu is
                # en of de state hetzelfde is als de nieuwe state.. 
                # maar omdat hij de nieuwe state verkeerd in de list zet (zie hieronder + frustratie)
                # werkt het niet omdat de state elke keer anders is
                temp_state_tree = []
                for state in nextStates:
#FRUSTRATIE:
                    # het lijkt wel alsof hij bij de laatste state hem niet aan het einde maar er tussen zet..
                    # snap  niet waarom en ik wordt hier helemaal gek.. dus ga morgen weer hier een blik opwerpen
                    temp_state_tree.append(branch + [state])
            if count ==10:
                not_terminated = False
            state_tree = temp_state_tree
        return state_tree


    def nextStates(self,state):
        # Error catcher????
        nextStates = [[]]
        for qt in state:
            qt_rels = self.rels[qt.name]
            nextValues = qt.getNextValues()
            nextDelta = qt.getNextDelta(qt_rels) 
            nextDelta, ambiguous = qt.getNextDelta(qt_rels)
            if ambiguous: break
            #print(qt.name)
            #print("nextValues: {}".format(nextValues))
            #print("nextDelta: {}\n".format(nextDelta))
            nextStatesPerQt = []
            for nextValue in nextValues:
                qtcopy = deepcopy(qt)
                qtcopy.setDelta(nextDelta)
                qtcopy.setValue(nextValue)
                nextStatesPerQt.append(qtcopy)
            nextStates = [i+[j] for i in nextStates for j in nextStatesPerQt]
        if not(ambiguous):
            nonValidStates = []
            for nextState in nextStates:
                if not(self.checkValidVC(nextState)) or self.isSame(nextState, state):
                    nonValidStates.append(nextState)
            for nextState in nonValidStates:
                nextStates.remove(nextState)
        return nextStates, not(ambiguous)


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

# deze gebruiken we niet meer:
    #def increaseDelta(self):
        #return (self.delta + 1 in Quantity.deltadom)
    #def decreaseDelta(self):
        #return (self.delta - 1 in Quantity.deltadom)    

    
    def getNextValues(self):
        if self.delta == -1:      #check if derivative is negative
            if self.val == Quantity.zpmdom[2]:
                posvals = [self.val-1]
            elif self.val == Quantity.zpmdom[1]:
                posvals = [self.val-1, self.val]
                # self.setDelta(0) moet in bepaalde tak komen..
            else:
                self.setDelta(0)
                posvals = [self.val]
        elif self.delta == 0:    #check if derivative is zero
            posvals = [self.val]
        else:
            if self.val == Quantity.zpmdom[0]:
                posvals = [self.val+1]
            elif self.val == Quantity.zpmdom[1]:
                posvals = [self.val, self.val+1]
                # self.setDelta(0) moet in bepaalde tak komen..
            else:
                self.setDelta(0)
                posvals = [self.val]
        return posvals

    
    def getNextDelta(self, rels):
        ambiguous = False
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
            #raise ValueError('Shit is AMBIGU!')
            ambiguous = True
        new_delta = self.delta
        if 1 in signs:
            if new_delta != 1:
                new_delta += 1
        if -1 in signs:
            if new_delta != -1:
                new_delta -= 1
        return new_delta , ambiguous
