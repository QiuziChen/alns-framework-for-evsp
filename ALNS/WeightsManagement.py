import random


"""
@author: Chen Qiuzi
"""


_reject = 0
_accept = 1
_better = 2
_optimal = 3

score2Add = {
    0: 0,
    1: 5,
    2: 15,
    3: 30
}


class Weights():

    """
    Weights of operators.
    A Weights object needs functions including
        initialize, 
        update scores, 
        update weights,
        select operators.
    """

    def __init__(
        self,
        r,
        removeOperators:dict,
        insertOperators:dict,
    ):
        """
        A Weights object can record selection state and weights.
        """
        self.r = r  # control param when update weights
        self.removeSelection = 0
        self.insertSelection = 0
        self.removeOperators = removeOperators
        self.insertOperators = insertOperators

        self.weightRemove = {i:1 for i in removeOperators.keys()}
        self.weightInsert = {i:1 for i in insertOperators.keys()}
        self.scoreRemove = {i:0 for i in removeOperators.keys()}
        self.scoreInsert = {i:0 for i in insertOperators.keys()}
        self.timeRemove = {i:0 for i in removeOperators.keys()}
        self.timeInsert = {i:0 for i in insertOperators.keys()}
        self.historyWeightR = {i:[1] for i in removeOperators.keys()}
        self.historyWeightI = {i:[1] for i in insertOperators.keys()}

    def updateTimeAndScores(self, result:int):
        """
        Update scores after each interation.
        """
        self.scoreRemove[self.removeSelection] += score2Add[result]
        self.scoreInsert[self.insertSelection] += score2Add[result]
        self.timeRemove[self.removeSelection] += 1
        self.timeInsert[self.insertSelection] += 1

    def updateWeights(self):
        """
        Update weights after each segment.
        """
        for i in self.weightRemove.keys():
            if self.timeRemove[i] == 0:
                self.historyWeightR[i].append(self.weightRemove[i])
            else:
                self.weightRemove[i] = self.weightRemove[i] * (1 - self.r) + self.r * (self.scoreRemove[i] / self.timeRemove[i])
                self.historyWeightR[i].append(self.weightRemove[i])
       
        for i in self.weightInsert.keys():
            if self.timeInsert[i] == 0:
                self.historyWeightI[i].append(self.weightInsert[i])
            else:
                self.weightInsert[i] = self.weightInsert[i] * (1 - self.r) + self.r * (self.scoreInsert[i] / self.timeInsert[i])
                self.historyWeightI[i].append(self.weightInsert[i])

        self.scoreRemove = {i:0 for i in self.removeOperators.keys()}
        self.scoreInsert = {i:0 for i in self.insertOperators.keys()}
        self.timeRemove = {i:0 for i in self.removeOperators.keys()}
        self.timeInsert = {i:0 for i in self.insertOperators.keys()}
    
    def selectRemoveOperator(self):
        """
        Select operators according to weights.
        """
        cumWeights = {i:sum([self.weightRemove[n] for n in self.weightRemove.keys() if n <= i]) for i in self.weightRemove.keys()}  # cumulative probability
        rouletteValue = random.uniform(0, max(cumWeights.values()))  # roulette wheel number
        for k in self.weightRemove.keys():
            if cumWeights[k] >= rouletteValue:
                operator = self.removeOperators[k]
                self.removeSelection = k
                break
        return operator
        
    def selectInsertOperator(self):
        """
        Select operators according to weights.
        """
        cumWeights = {i:sum([self.weightInsert[n] for n in self.weightInsert.keys() if n <= i]) for i in self.weightInsert.keys()}  # cumulative probability
        rouletteValue = random.uniform(0, max(cumWeights.values()))  # roulette wheel number
        for k in self.weightInsert.keys():
            if cumWeights[k] >= rouletteValue:
                operator = self.insertOperators[k]
                self.insertSelection = k
                break
        return operator
    