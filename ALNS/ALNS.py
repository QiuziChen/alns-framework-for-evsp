from EVSPModel import EVSP
from .InitialSolution import initialize, initialize_nightCharge
from .WeightsManagement import Weights
from .RemoveOperators import randomRemoval, timeRelatedRemoval, neighborRemoval
from .InsertOperators import randomInsert, greedyInsert

import math
import random
import numpy as np
from tqdm import tqdm
from copy import deepcopy
from timeit import default_timer as timer

import matplotlib
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 100
plt.rcParams['xtick.labelsize'] = 'large'
plt.rcParams['ytick.labelsize'] = 'large'


"""
@author: Chen Qiuzi
"""

_reject = 0
_accept = 1
_better = 2
_optimal = 3


class ALNS():

    """
    ALNS is first proposed in "An adaptive large neighborhood search heuristic for the pickup and
    delivery problem with time windows, 2016" by Ropke and Pisinger. 
    
    It's the extention of Large Neighborhood Search(LNS) with multiple destroy & repair methods.
    """

    def __init__(
        self,
        evsp:EVSP,
        iterMax=15000,
        nMax=10,
        nMin=1,
        T0=100,
        alpha=0.9997,
        r=0.5,
        enePenalty=700,
        capPenalty=700,
        chargeProb = 0.9,
        segLength=100,
        terminate=True,
        terminateLength=2000,
        printLog=True,
    ):
        """
        iterMax: maximum iteration
        nMax, nMin: maximun & minimum number of trips to remove
        T0: initial temperature
        alpha: cooling rate of temperature (0,1)
        r: reaction factor when update weights (0,1)
        enePenalty, capPenalty: penalty when violating capacity and energy constraints
        chargeProb: probability of charging insertion for random insertion
        segLength: segment length for updating weights
        terminateLength: length of iteration to check improvement
        nightCharge: decision var of <night time charge only> mode
        ALNS class use <Weights> class to manage operators.
        """
        self.evsp = evsp
        self.iterMax = iterMax
        self.T0 = T0
        self.nMax = nMax
        self.nMin = nMin
        self.alpha = alpha
        self.enePenalty = enePenalty
        self.capPenalty = capPenalty
        self.chargeProb = chargeProb
        self.segLength = segLength
        self.terminate=terminate
        if self.terminate is True:
            self.terminateLength = terminateLength
        else:
            self.terminateLength = self.iterMax

        self.printLog = printLog
        self.nightCharge = evsp.nightCharge
        if self.nightCharge:
            self.chargeProb = 0

        self.removeOperators = {
            1: randomRemoval,
            2: timeRelatedRemoval,
            3: neighborRemoval
        }

        # self.insertOperators = {
        #     1: greedyInsert
        # }
        self.insertOperators = {
            1: randomInsert,
            2: greedyInsert
        }

        self.weights = Weights(r, self.removeOperators, self.insertOperators)
        
        self.bestSchedule = None
        self.bestCost = 0
        self.historyCurrentCost = []
        self.historyBestCost = []

        self.runTime = 0
        self.totalIter = 0


    def solve(self):
        """
        Solve EVSP using ALNS.
        """
        if self.printLog is True:
            print("--- ALNS Starts")
        tic = timer()

        # initialize
        if self.nightCharge:
            self.bestSchedule = initialize_nightCharge(self.evsp)
        else:
            self.bestSchedule = initialize(self.evsp)
        self.bestCost = self.bestSchedule.calCost()
        currentSchedule = deepcopy(self.bestSchedule)
        currentCost = deepcopy(self.bestCost)

        # params
        T = self.T0

        # iteration
        # for iter in tqdm(range(self.iterMax), desc='Iteration', ncols=60):
        for iter in range(self.iterMax):

            removeOp = self.weights.selectRemoveOperator()
            insertOp = self.weights.selectInsertOperator()

            # remove and insert
            num2remove = random.randint(self.nMin, self.nMax)          
            tripBank, removedSchedule = removeOp(self.evsp, currentSchedule, num2remove)
            newCost, newSchedule, isFeasible = insertOp(self.evsp, tripBank, removedSchedule, self.enePenalty, self.capPenalty, self.chargeProb)
            
            # acceptance
            result = _reject
            if isFeasible and (newCost < self.bestCost):
                result = _optimal  # optimal
                self.bestSchedule, self.bestCost = newSchedule, newCost
                currentSchedule, currentCost = newSchedule, newCost
            elif newCost < currentCost:
                result = _better  # better
                currentSchedule, currentCost = newSchedule, newCost
            elif ((self.bestCost - newCost)/T < 709) and (math.exp((self.bestCost - newCost) / T) >= random.random()):  # Simulated Anealing
                result = _accept  # accept
                currentSchedule, currentCost = newSchedule, newCost
            else:
                pass

            # update params
            self.historyCurrentCost.append(currentCost)
            self.historyBestCost.append(self.bestCost)
            self.weights.updateTimeAndScores(result)
            T = T * self.alpha

            # update weights
            if (iter+1) % self.segLength == 0:
                self.weights.updateWeights()    

                # no improvement termination
                if self.terminate is False:
                    pass
                else:
                    if ((iter+1) >= self.terminateLength) and (self.historyBestCost[-1] == self.historyBestCost[-self.terminateLength]):
                        self.totalIter = iter + 1
                        if self.printLog is True:
                            print("--- Terminate at %d Iteration"%(iter+1))
                        break

        toc = timer()
        self.runTime = toc - tic
        if self.totalIter == 0:
            self.totalIter = self.iterMax
        
        self.bestSchedule.updateR()

        if self.printLog is True:
            print("--- Solve Time: %.2f sec"%(toc-tic))
            print("--- Best Cost: %.2f yuan"%(self.bestCost))
            print("--- Number of Buses: %d" %(len(self.bestSchedule.schedule)))
            print("--- Number of Charging Trips: %d" %(len(self.bestSchedule.R)))
            # print("--- Energy Feasibility: %s"%(self.bestSchedule.checkEnergyFeasibility()))
            # print("--- Capacity Feasibility: %s"%(self.bestSchedule.checkCapacityFeasibility()))
            print("--- ALNS Finished")


    # def recordSchedule(self, schedule:Schedule):
    #     """
    #     Record history duties for post-optimization.
    #     Duties should be energy-feasible.
    #     """
    #     for duty in schedule.schedule:
    #         if duty.checkEnergyFeasibility():
    #             self.historyDuty.append(duty)


    def plotWeights(self):
        """
        Display history weights of operators.
        """
        lineStyle = {1:'k-', 2:'k--', 3:'k-.', 4:'k:'}
        fig, ax = plt.subplots(2,1, figsize=(14,8))
        for k,v in self.weights.historyWeightR.items():
            ax[0].plot(v, lineStyle[k], label=self.weights.removeOperators[k].__name__)
        ax[0].legend(fontsize=15, loc=1)
        for k,v in self.weights.historyWeightI.items():
            ax[1].plot(v, lineStyle[k], label=self.weights.insertOperators[k].__name__)
        ax[1].legend(fontsize=15, loc=1)

        for ax_ in ax:
            ticks = np.arange(0, self.totalIter//self.segLength+1, 10)
            ax_.set_xlim(0, self.totalIter//self.segLength)
            ax_.set_xticks(ticks)
            ax_.set_xticklabels(ticks*self.segLength)
        
        fig.supylabel("Weights of Operators", fontsize=20, x=0.08)
        fig.supxlabel("Iteration Number", fontsize=20, y=0.03)
        plt.show()


    def plotEvaluation(self):
        """
        Display history cost change.
        """
        fig, ax = plt.subplots(1,1,figsize=(14,6))
        ax.plot(self.historyCurrentCost, 'k--', label="Current Cost / yuan")
        ax.plot(self.historyBestCost, 'k-', label="Best Cost / yuan")
        # ax.set_xticks(list(range(1, len(self.historyBestCost)+1), 100))
        ax.set_xlim(1, len(self.historyBestCost))
        ax.set_ylabel("Cost Evaluation", fontsize=20)
        ax.set_xlabel("Iteration Number", fontsize=20)

        plt.legend(fontsize=20, loc=1)
        plt.grid(zorder=0)
        plt.show()
        
        
    