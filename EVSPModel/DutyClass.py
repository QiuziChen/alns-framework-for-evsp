from EVSPModel.EVSPClass import EVSP
from EVSPModel.Calculations import calCharge

from copy import deepcopy


"""
@author: Chen Qiuzi
"""


class Duty():

    """
    A duty is schedule for a single vehicle.
    It contains information of its vehicle type, trip chain and charging time assignment.
    A feasible duty should not violate the energy constraint.
    """
    
    __slots__ = ['K','S','R','vehicleCost','timeCost','chargingCost','totalCost','evsp']


    def __init__(self, evsp:EVSP, type=1, tripChain=[], chargingTime={}) -> None:
        """
        evsp: EVSP model storing data of nodes, arcs and params
        type: vehicle type
        tripChain: trip chain, list
        chargingTime: charging time assignment, dict
        """
        self.K = type  # vehicle type
        self.S = tripChain  # trip chain
        self.R = chargingTime  # charging time of charging events in the trip chain
        self.vehicleCost = 0  # initial vehicle cost
        self.timeCost = 0  # initial time-related cost
        self.chargingCost = 0  # initial charging cost
        self.totalCost = 0  # initial total cost
        self.evsp = evsp

    def __deepcopy__(self, memodict={}):
        """
        For deepcopy.
        """
        info = Duty(self.evsp)
        info.K = deepcopy(self.K)
        info.S = [i for i in self.S]
        info.R = {f:r for f,r in self.R.items()}
        return info

    def checkEnergyFeasibility(self):
        """
        Return True if a duty can meet the energy constraint, else False.
        """
        feasibility = True

        y = self.evsp.E_k[self.K]  # remaining energy at the beginning of each node
        for i, s in enumerate(self.S[:-1]):
            
            if s in self.evsp.F:
                chargeVolume = calCharge(self.evsp, self.K, y)
                y = y + chargeVolume - self.evsp.e_kij[self.K][(s,self.S[i+1])]
            else:
                y = y - self.evsp.e_ki[self.K][s] - self.evsp.e_kij[self.K][(s,self.S[i+1])]

            if y < self.evsp.batteryLB * self.evsp.E_k[self.K]:  # if battery level less than the safe level
                feasibility = False
                break
        return feasibility
    
    def calCost(self):
        """
        Calculate the cost of a duty.
        """
        self.vehicleCost = 0  # initialize whenever a new cost calculation procedure is performed
        self.timeCost = 0
        self.chargingCost = 0
        self.totalCost = 0
        
        # time and charging cost
        y = self.evsp.E_k[self.K]
        for i,s in enumerate(self.S[:-1]):

            # time cost
            self.timeCost += (self.evsp.t_ij[(s, self.S[i+1])] + self.evsp.t_i[s]) * self.evsp.c_t
            if s in self.evsp.F:
                # charging cost
                chargeVolume = calCharge(self.evsp, self.K, y)
                self.chargingCost += chargeVolume * self.evsp.c_e[self.R[s]] 
                y = y + chargeVolume - self.evsp.e_kij[self.K][(s,self.S[i+1])]
            else:
                y = y - self.evsp.e_ki[self.K][s] - self.evsp.e_kij[self.K][(s,self.S[i+1])]
        
        # charged to full after daily operation
        self.chargingCost += (self.evsp.E_k[self.K] - y) * min(self.evsp.c_e.values())
        
        # vehicle cost
        if self.evsp.calVehCost == True:
            self.vehicleCost = self.evsp.c_k[self.K]
        if self.evsp.calTimeCost == False:
            self.timeCost == 0
        if self.evsp.calElecCost == False:
            self.chargingCost = 0

        self.totalCost = self.vehicleCost + self.timeCost + self.chargingCost 
            
        return self.totalCost
