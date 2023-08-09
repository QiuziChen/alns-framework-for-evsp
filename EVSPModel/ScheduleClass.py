from copy import deepcopy
from EVSPModel.DutyClass import Duty
from EVSPModel.EVSPClass import EVSP
from EVSPModel.Calculations import calCharge

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


"""
@author: Chen Qiuzi
"""


class Schedule():
    """
    A schedule is an object which contains a series of vehicles with their service trips and
    charging activities scheduled according to a given timetable.

    A schedule has these attributes:
        schedule: a list containts several duties
        cost: total cost of all the duties
        energy feasibility: True if the energy constraints are satisfied, else False
        capacity feasibility: True if the charging station capacity constraints are satisfied, else False
    """

    __slots__ = ['schedule','R','vehicleCost','timeCost','chargingCost','totalCost','evsp']

    def __init__(self, evsp:EVSP, schedule=[], R={}):
        """
        evsp: EVSP model
        schedule: initial schedule, list of duties
        R: initial charging time assignment, list of time divisions r
        """
        self.schedule = schedule  # list of duties
        self.R = R  # charging time assignment
        self.vehicleCost = 0
        self.timeCost = 0
        self.chargingCost = 0
        self.totalCost = 0
        self.evsp = evsp


    def __deepcopy__(self, memodict={}):
        """
        For deepcopy.
        """
        info = Schedule(self.evsp, [], {})
        for duty in self.schedule:
            duty_ = deepcopy(duty)
            info.schedule.append(duty_)
        info.R = {f:r for f,r in self.R.items()}
        return info


    def addDuty(self, duty:Duty):
        """
        Add a duty to schedule and update R.
        """
        self.schedule.append(duty)
        for f,r in duty.R.items():
            self.R[f] = r
    

    def delDuty(self, duty:Duty):
        """
        Delete a duty from the schedule and update R.
        """
        r2Remove = duty.R.keys()
        for f in r2Remove:
            r_ = self.R.pop(f)

        self.schedule.remove(duty)
    

    def sortDuty(self):
        """
        Sort duties by start time of first trip.
        """
        newS = []
        startT = {}  # duty : start time of the first trip
        for duty in self.schedule:
            startT[duty] = self.evsp.s_i[duty.S[1]]
        # sort by start time
        startT = sorted(startT.items(), key=lambda d: d[1])
        for k,v in startT:
            newS.append(k)
        self.schedule = newS
    

    def updateR(self):
        """
        Update R list.
        """
        self.R = {}
        for duty in self.schedule:
            for f,r in duty.R.items():
                self.R[f] = r
    

    def addR(self, f, r):
        """
        Add f-r to R list.
        """
        self.R[f] = r
    

    def delR(self, f):
        """
        Delete f-r in R list.
        """
        r_ = self.R.pop(f)


    def checkEnergyFeasibility(self):
        """
        Return True if the energy constraints are satisfied, else False
        """
        for duty in self.schedule:
            if duty.checkEnergyFeasibility() == False:
                return False
        return True
    

    def checkCapacityFeasibility(self):
        """
        Return True if the capacity constraints are satisfied, else Flase.
        """
        feasibility = True
        if self.evsp.stationCap < 0:
            return feasibility
        else:
            for r in set(self.R.values()):
                num = []  # number of vehicle in the station before r when i is charging
                for u in range(self.evsp.U):  # 0, 1, 2...
                    index = int(r[1:])+u  # index of r to check capacity, if r=r3, then index=3,4,5...
                    num_before = 0
                    for u in range(self.evsp.U):
                        index_before = index-u  # index of r when vehicle is still being charged
                        if index_before > 0:  # considering r1, r2...
                            num_before += sum(map(('r%d'%(index_before)).__eq__, self.R.values()))
                    num.append(num_before)
                if (max(num) > self.evsp.stationCap):
                    feasibility = False
            return feasibility


    def calCost(self):
        """
        Calculate schedule cost of all the duties.
        """
        self.totalCost = 0
        self.vehicleCost = 0
        self.timeCost = 0
        self.chargingCost = 0
        
        for duty in self.schedule:
            self.totalCost += duty.calCost()
            if self.evsp.calVehCost == True:
                self.vehicleCost += duty.vehicleCost
            if self.evsp.calTimeCost == True:
                self.timeCost += duty.timeCost
            if self.evsp.calElecCost == True:
                self.chargingCost += duty.chargingCost
        
        return self.totalCost


    def printTimetable(self):
        """
        Print out a table(DataFrame) of the schedule.
        """
        self.sortDuty()
        df = pd.DataFrame(columns=['Vehicle Type', 'Trip Chain', 'Charging Time'])
        for duty in self.schedule:
            df.loc[len(df.index)] = [duty.K, duty.S, duty.R]
        print(df)


    # --- Plot ---


    def plotTimetable(self):
        """
        Display timetable & schedule in form of Gantt Chart.
        """
        fig, ax = plt.subplots(1,1,figsize=(16,8))
        vehType = {1:'A',2:'B',3:'C',4:'D',5:'E',6:'F'}
        index = 0
        self.sortDuty()
        for duty in self.schedule:
            index += 1
            K = duty.K
            for node in duty.S[1:-1]:
                if type(node)==int:  # trip node
                    start_t = self.evsp.s_i[node]  # start time
                    duration = self.evsp.t_i[node]  # duration
                    ax.barh(index, duration, left=start_t, color='silver', zorder=1)
                    ax.text(start_t, index, 'T%d'%node, ha='left', va= 'center',fontsize=10, zorder=2)
                else:  # recharging trip node
                    start_t = self.evsp.s_r[duty.R[node]]  # start time
                    duration = self.evsp.U*self.evsp.delta  # duration
                    ax.barh(index, duration, left=start_t, color='lightgreen', zorder=1)
                    ax.text(start_t, index, 'F%s'%node[1:], ha='left', va='center',fontsize=10, zorder=2)
        # axis setting
        ax.set_xticks(list(range(300,1620, 60)))
        ax.set_xlim(300, 1560)
        ax.set_xticklabels(['%d:00'%i for i in list(range(5,24))+[0,1,2]])
        ax.set_yticks(list(range(1, len(self.schedule)+1)))
        ax.set_yticklabels(['Bus%d (%s)'%(i+1, vehType[self.schedule[i].K]) for i in range(len(self.schedule))])
        ax.set_ylabel("Bus  Number", fontsize=20)

        plt.title("EBs Schedule", fontsize=20)
        legend_elements = [
            Patch(facecolor='silver', label='Service trip'),
            Patch(facecolor='lightgreen', label='Charging event')
        ]
        ax.legend(handles=legend_elements, loc=4, shadow=True, fontsize='x-large')
        plt.grid(zorder=0)
        plt.show()
        pass


    def costBar(self):
        """
        Display the cost composition of a schedule.
        """
        _cost = self.calCost()
        fig, ax = plt.subplots(1,1,figsize=(6,6))
        costs = [round(self.vehicleCost,1), round(self.chargingCost,1), round(self.timeCost,1)]
        labels = ['Purchase Cost', 'Electricity Cost', 'Time-related Cost']
        ax.bar(labels, costs, width=0.8,color='gray', zorder=10)
        ax.set_ylabel("Cost / CNY", fontsize=20)
        for a,b in zip(labels, costs):
            plt.text(a,b,b,ha='center', va='bottom')
        plt.grid(True, alpha=0.6, zorder=0)
        plt.show()


    def chargingPowerPlot(self):
        """
        Display charging power at station in form of plot.
        """
        # calculate charging volume of each charging activity "f"
        chargingV = {}
        for duty in self.schedule:
            k = duty.K
            y = self.evsp.E_k[k]  # initial battery volume
            for i in range(len(duty.S)-1):
                if duty.S[i] in self.evsp.F:
                    chargeVolume = calCharge(self.evsp, k, y)
                    chargingV[duty.S[i]] = chargeVolume
                    y = y + chargeVolume - self.evsp.e_kij[k][(duty.S[i],duty.S[i+1])]
                else:
                    y = y - self.evsp.e_ki[k][duty.S[i]] - self.evsp.e_kij[k][(duty.S[i],duty.S[i+1])]
    
        # calculate charging volume of each r
        cons_rate, start_t = [], []
        interval = self.evsp.U * self.evsp.delta
        for t in list(range(300, 1620, interval)):  # 5:00 - 1:30
            start_t.append(t)
            cons = 0
            for r in [r for r in self.evsp.R if t<=self.evsp.s_r[r]<t+interval]:
                for f in [f for f in self.R.keys() if self.R[f] == r]:
                    cons += chargingV[f]
            cons_rate.append(cons/interval)
        # plot
        fig, ax = plt.subplots(1,1,figsize=(14,6))
        ax.plot(start_t, cons_rate, 'k^-', label="Energy Consumption per Minute")
        ax.set_xticks(list(range(300,1620, 60)))
        ax.set_xlim(300, 1560)
        ax.set_xticklabels(['%d:00'%i for i in list(range(5,24))+[0,1,2]])
        ax.set_ylabel("Electricity Consumption per Minute / kW·h", fontsize=20)

        plt.legend(fontsize=20, loc=2)
        plt.grid(zorder=0)
        plt.show()


    def chargerUsagePlot(self):
        """
        Vehicle number - time division plot.
        """
        fig, ax = plt.subplots(1,1,figsize=(14,6))
        veh_in, start_t = [], []  # vehicle in station
        for r in self.evsp.R:
            start_t.append(self.evsp.s_r[r])
            num = 0
            for u in range(self.evsp.U):
                index = int(r[1:])-u  # index of r when still charging
                num += sum(map(('r%d'%(index)).__eq__, self.R.values()))
            veh_in.append(num)

        ax.plot(start_t, veh_in, 'ko-', label="Number of Buses in Station")
        ax.set_xticks(list(range(300,1620, 60)))
        ax.set_xlim(300, 1560)
        ax.set_xticklabels(['%d:00'%i for i in list(range(5,24))+[0,1,2]])
        ax.set_ylabel("Number of Buses", fontsize=20)

        plt.legend(fontsize=20, loc=2)
        plt.grid(zorder=0)
        plt.show()