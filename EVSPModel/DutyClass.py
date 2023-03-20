from EVSPModel.EVSPClass import EVSP
from EVSPModel.Calculations import calCharge

from copy import deepcopy


"""
@author: Chen Qiuzi
"""


class Duty():

    """
    A duty is schedule for a single vehicle which contains information of its vehicle type, trip chain 
    and charging time assignment.
    """
    
    __slots__ = ['K','S','R','vehicleCost','laborCost','chargingCost','totalCost','evsp']


    def __init__(self, evsp:EVSP, type=1, tripChain=[], chargingTime={}) -> None:
        """
        model: EVSP model storing data of nodes, arcs and params
        type: vehicle type
        tripChain: trip chain, list
        chargingTime: charging time assignment, dict
        cost: total cost including vehicle, labor and charging cost
        """
        self.K = type
        self.S = tripChain
        self.R = chargingTime
        self.vehicleCost = 0
        self.laborCost = 0
        self.chargingCost = 0
        self.totalCost = 0
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

        y = self.evsp.E_k[self.K]  # start energy of each node
        for i, s in enumerate(self.S[:-1]):
            
            if s in self.evsp.F:
                chargeVolume = calCharge(self.evsp, self.K, y)
                y = y + chargeVolume - self.evsp.e_kij[self.K][(s,self.S[i+1])]
            else:
                y = y - self.evsp.e_ki[self.K][s] - self.evsp.e_kij[self.K][(s,self.S[i+1])]

            if y < self.evsp.batteryLB * self.evsp.E_k[self.K]:  # if battery level less than safe level
                feasibility = False
                break
        return feasibility
    
    def calCost(self):
        """
        Calculate cost of a duty.
        """
        self.vehicleCost = 0
        self.laborCost = 0
        self.chargingCost = 0
        self.totalCost = 0

        # veh investemnt cost
        self.vehicleCost = self.evsp.c_k[self.K]
        
        y = self.evsp.E_k[self.K]
        for i,s in enumerate(self.S[:-1]):

            # labor cost
            self.laborCost += (self.evsp.t_ij[(s, self.S[i+1])] + self.evsp.t_i[s]) * self.evsp.c_t
            if s in self.evsp.F:
                # charging cost
                chargeVolume = calCharge(self.evsp, self.K, y)
                self.chargingCost += chargeVolume * self.evsp.c_e[self.R[s]] 
                y = y + chargeVolume - self.evsp.e_kij[self.K][(s,self.S[i+1])]
            else:
                y = y - self.evsp.e_ki[self.K][s] - self.evsp.e_kij[self.K][(s,self.S[i+1])]
        
        # charged to full after daily operation
        self.chargingCost += (self.evsp.E_k[self.K] - y) * max(self.evsp.c_e.values())
        
        if self.evsp.calLaborCost == True:
            self.totalCost = self.vehicleCost + self.laborCost + self.chargingCost 
        else:
            self.totalCost = self.vehicleCost + self.chargingCost  # self.laborCost + 
            
        return self.totalCost
