import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""
@author: Chen Qiuzi
"""


class EVSP():

    """
    An EVSP object is used to store the timetable and network params.
    Network params include data of nodes, arcs, vehicles and charging stations.
    """

    def __init__(
        self,
        timetable:pd.DataFrame, 
        batteryLB=0.2, # vehicle param, lower bound of battery level
        batteryUB=1.0, # vehicle param, upper bound of battery level 
        stationCap=-1, # model param, charging station capacity
        delta=10, # operating param, minimum time interval / min
        U=3, # operating param, number of delta in a fixed charging duration
        lineChange=True, # operating param, whether line change activities are allowed for BEBs
    ):
        """
        [timetable]
        timetable: DataFrame with columns=['ID','Route','StartTime','StartTimeMin','TravelTimeMin','Consumption']
        
        [operating param]
        batteryLB: lower bound of battery level, default=0.2
        batteryUB: upper bound of battery level, default=1.0
        stationCap: charging station capacity, default=-1 means capacity constraints are not considered
        delta: minimum time interval, default=10(min)
        U: number of delta in a fixed charging duration, default=3 (delta=10, U=3 means the fixed charging duration=30min)
        lineChange: whether line change activities are allowed for BEBs, default=True
        """
        
        self.timetable = timetable
        self.stationCap = stationCap
        self.batteryLB = batteryLB
        self.batteryUB = batteryUB
        self.delta = delta
        self.U = U
        self.lineChange = lineChange


    def setVehTypes(
            self,
            E_k={1: 100, 2: 170, 3: 258},  # kWh
            capRelatedCons=False,
            benchCap=220,
            consIncRate=0.000297,  # kWh·km^-1 / kWh
    ):
        """
        Set vehicle types information.
        E_k: battery capacity of each type, dict, indices should be integer start from 1
        capRelatedCons: whether to adjust energy consumption according to battery capacity
        benchCap: if adjust consumption, a benchmark capacity should be set
        consIncRate: assuming a linear relationship between energy consumption and battery capaicty, the coefficient or increasing rate should be set
        """
        self.k_num = len(E_k.keys())  # number of vehicle types
        self.K = list(range(1, self.k_num+1))  # set of vehicle types

        if list(E_k.keys())[0] != 1 or not isinstance(list(E_k.keys())[0], int):
            raise KeyError("Indices of vehicle types should be integers beginning at 1.")
        else:
            self.E_k = E_k

        self.capRelatedCons = capRelatedCons
        self.benchCap = benchCap
        self.consIncRate = consIncRate


    def setCosts(
            self,
            calVehCost=True, # whether to calculate vehicle cost
            calElecCost=True, # whether to calculate electricity cost
            calTimeCost=True, # whether to calculate time-related cost
            ToU=False,  # whether to consider time-of-use electricity cost
            c_k={1: 804.7, 2: 907.56, 3: 1039.14},  # vehicle depreciation cost
            c_e=0.6414,  # electricity cost
            c_t=0.5,  # labor/time-related cost
    ):
        """
        Set costs value.
        calVehCost: whether to calculate vehicle cost
        calElecCost: whether to calculate electricity cost
        calTimeCost: whether to calculate time-related cost
        ToU: whether to consider time-of-use electricity cost
        c_k: vehicle cost, should be dict, independent to time (/veh)
        c_e: electricity cost, should be dict if ToU, else a fixed num (/kWh)
        c_t: labor cost, a fixed num (/min) 
        """
        if calVehCost or calElecCost or calElecCost:
            self.calVehCost = calVehCost
            self.calElecCost = calElecCost
            self.calTimeCost = calTimeCost
        else:
            raise ValueError("At least one cost item should be considered.")
        
        # electricity cost
        self.ToU = ToU
        if self.ToU:
            if type(c_e) != dict:
                raise TypeError("c_e should be a dict if ToU policy is adopted.")
            else:
                self.c_e = c_e  # still need key (r) transform.
        else:
            self.c_e = c_e

        # vehicle cost
        if len(list(c_k.keys())) != self.k_num:
            raise KeyError("Length of c_k should be equal to the number of vehicle types k_num")
        else:
            self.c_k = c_k

        # time-related cost
        self.c_t = c_t


    def setChargingFunc(
            self,
            chargingFuncType='linear',
            chargingRate={1: 1, 2: 1, 3: 1},
            breakpoint_time={1:[0, 80, 100, 150, 300], 2:[0, 136, 170, 255, 400], 3:[0, 206.4, 258, 387, 500]},
            breakpoint_soc={1:[0.0, 0.8, 0.9, 1.0, 1.0], 2:[0.0, 0.8, 0.9, 1.0, 1.0], 3:[0.0, 0.8, 0.9, 1.0, 1.0]},
    ):
        """
        Set charging function.
        chargingFuncType: type of charging function, {'linear', 'piecewise'}
        chargingRate: dict, charging rate in the linear charging fucntion for each vehicle type, kWh/min 
        breakpoint_time: dict, charging time of breakpoints, min
        breakpoint_soc: dict, soc of breakpoints
        """
        self.chargingFuncType = chargingFuncType
        if self.chargingFuncType == 'linear':
            self.v_k = chargingRate
        elif self.chargingFuncType == 'piecewise':
            self.c_kb = breakpoint_time
            self.a_kb = breakpoint_soc
            self.m_k = {k: len(self.c_kb[k]) for k in self.K}  # number of break point
            self.B_k = {k:list(range(0,self.m_k[k])) for k in self.K}  # break point set
        else:
            raise ValueError("Charging function type should be either linear or piecewise.")


    def plotChargingFunc(self):
        """
        Plot charging curve.
        """
        if self.chargingFuncType == 'linear':
            fig, ax = plt.subplots(1,1,figsize=(6,4))
            ax.set_xlabel("Time", weight="bold")
            ax.set_ylabel("SOC", weight="bold")
            ax.grid(linestyle=':')

            for k in evsp.K:
                E = evsp.E_k[k]  # kWh
                y = np.array([0, 100])
                x = y / 100 * E / evsp.v_k[k]
                ax.plot(x, y, label="Veh Type: %d(%.1f kWh)" % (k, evsp.E_k[k]))
                ax.scatter(x, y)
                ax.text(x[-1], y[-1], "(%d,%d)" % (x[-1], y[-1]), horizontalalignment='center')
            plt.legend()
            plt.show()

        elif self.chargingFuncType == 'piecewise':
            fig, ax = plt.subplots(1,1,figsize=(6,4))
            ax.set_xlabel("Time", weight="bold")
            ax.set_ylabel("SOC", weight="bold")
            ax.grid(linestyle=':')

            for k in evsp.K:
                E = evsp.E_k[k]  # kWh
                x = np.array(evsp.c_kb[k][:-1])
                y = np.array(evsp.a_kb[k][:-1]) * 100
                ax.plot(x, y, label="Veh Type: %d(%.1f kWh)" % (k, evsp.E_k[k]))
                ax.scatter(x, y)
                ax.text(x[-1], y[-1], "(%d,%d)" % (x[-1], y[-1]), horizontalalignment='center')
            plt.legend()
            plt.show()
        else:
            raise ValueError("Charging function type should be either linear or piecewise.")


    def createModel(self):

        """
        Create model parameters according to previous input info.
        Note that all sets are defined as varType 'set' to accelerate calculations.
        """

        # --- sets ---
        
        self.n = self.timetable.shape[0]  # trip number
        self.T = set(list(range(1, self.n+1)))  # set of trip nodes
        self.F = set(['f%d'% i for i in range(1, self.n+1)])  # set of recharging event nodes     
       
        # --- nodes ---

        ## start time of trips
        self.s_i = {i:self.timetable.StartTimeMin.iloc[i-1] for i in range(1, self.n+1)}  
        self.s_i['o'] = 0
        self.s_i['d'] = 24 * 60
        
        ## travel time of trips
        self.t_i = {i:self.timetable.TravelTimeMin.iloc[i-1] for i in range(1, self.n+1)}
        for f in self.F:
            self.t_i[f] = 0
        self.t_i['o'] = 0

        # ---arcs---

        ## set of arcs
        if self.lineChange == True:  # allowing line change activity of EBs
            self.A = [('o', j) for j in self.T] \
                    + [(i, j) for i in self.T for j in self.T if (self.s_i[i]+self.t_i[i]<=self.s_i[j])] \
                    + [(i, f) for i in self.T for f in self.F if i==int(f[1:])] \
                    + [(i, j) for i in self.T for j in ['d']] \
                    + [(f, j) for f in self.F for j in self.T if (self.s_i[int(f[1:])]+self.t_i[int(f[1:])]+(self.U*self.delta)<=self.s_i[j])]
            self.A = set(self.A)
        else:  # not allowing line change, that is an EB can only perform tasks of one route
            self.A = [('o', j) for j in self.T] \
                    + [(i, j) for i in self.T for j in self.T if (self.timetable.Route.iloc[i-1]==self.timetable.Route.iloc[j-1]) and (self.s_i[i]+self.t_i[i]<=self.s_i[j])] \
                    + [(i, f) for i in self.T for f in self.F if i==int(f[1:])] \
                    + [(i, j) for i in self.T for j in ['d']] \
                    + [(f, j) for f in self.F for j in self.T if (self.timetable.Route.iloc[int(f[1:])-1]==self.timetable.Route.iloc[j-1]) and (self.s_i[int(f[1:])]+self.t_i[int(f[1:])]+(self.U*self.delta)<=self.s_i[j])]
            self.A = set(self.A)

        ## travel time of deadhead trips
        self.t_ij = {arc:None for arc in self.A}
        for i, j in self.A:
            if i == 'o':  # depart arc
                self.t_ij[(i,j)] = 0  # min
            if i in self.T:
                if j in self.T:  # trip-trip arc
                    self.t_ij[(i,j)] = 2  # min
                if j in self.F:  # recharging deadhead arc
                    self.t_ij[(i,j)] = 3
                if j in ['d']:  # return arc
                    self.t_ij[(i,j)] = 3
            if i in self.F:
                if j in self.T:  # depart arc
                    self.t_ij[(i,j)] = 2
        for f in self.F:  # for temporary schedule cost calculation
            self.t_ij[(f,'d')] = 0
        
        ## energy consumption of trips
        if self.capRelatedCons == False:
            self.e_ki = {k:{i:self.timetable.Consumption.iloc[i-1] for i in range(1, self.n+1)} for k in range(1, self.k_num+1)}  # energy consumption of trips
            for k in self.K:
                self.e_ki[k]['o'] = 0
                # self.e_ki[k]['d'] = 0
        else:
            self.e_ki = {k:{i:(self.timetable.Consumption.iloc[i-1] + (self.E_k[k] - self.benchCap) * self.consIncRate * self.timetable.Distance.iloc[i-1])
                        for i in range(1, self.n+1)} for k in range(1, self.k_num+1)}  # energy consumption of trips
            for k in self.K:
                self.e_ki[k]['o'] = 0
        
        ## consumption of deadhead trips
        self.e_kij = {k:{arc:None for arc in self.A} for k in self.K}
        for k in self.K:
            for i, j in self.A:
                if i == 'o':  # depart arc
                    self.e_kij[k][(i,j)] = 0.0  # kWh
                if i in self.T:
                    if j in self.T:  # trip-trip arc
                        self.e_kij[k][(i,j)] = 0.05  # kWh
                    if j in self.F:  # recharging deadhead arc
                        self.e_kij[k][(i,j)] = 0.05  # kWh
                if i in self.F:
                    if j in ['d']:  # return arc
                        self.e_kij[k][(i,j)] = 0  # kWh
                    if j in self.T:  # depart arc
                        self.e_kij[k][(i,j)] = 0.05  # kWh
            for i in self.T:  # for temporary schedule cost calculation
                self.e_kij[k][(i,'d')] = 0.05  # kWh 
       
        # ---time division parameters---

        ## set of time division
        self.R = ['r%d'% i for i in range(1, 1260//self.delta-1)]  # time range: 5:00-2:00(+24:00), 21 hours, 1260 mins
        self.s_r = {r:(int(r[1:])-1)*10+300 for r in self.R}  # start time of time division
        self.C_r = {r:self.stationCap for r in self.R}  # station capacity of recharging time division
        ## set of time division indicators
        self.I = set([(f,r) for f in self.F for r in self.R if self.s_i[int(f[1:])]+self.t_i[int(f[1:])]+self.t_ij[(int(f[1:]), f)]<=self.s_r[r]])

        # ---remove infeasible arcs---

        for i in self.T:
            for j in self.T:
                if ((i,j) in self.A) and (self.s_i[i]+self.t_i[i]+self.t_ij[(i,j)]>self.s_i[j]):
                    self.A.remove((i,j))
        for f in self.F:
            for j in self.T:
                if (f,j) in self.A:
                    possibleR = [r for r in self.R if ((self.s_r[r]>=self.s_i[int(f[1:])]+self.t_i[int(f[1:])]+self.t_ij[(int(f[1:]),f)]) and (self.s_r[r]+self.U*self.delta+self.t_ij[(f,j)]<=self.s_i[j]))]
                    if len(possibleR)==0:
                        self.A.remove((f,j))

        # --- cost ---
        
        self.c_e = {}  # unit electricity cost
        ## time of use
        if self.ToU:
            """
            Time-of-use policy is not yet available.
            """
            pass
        else:
            for r in self.R:
                self.c_e[r] = self.c_e  # /kWh


    def printParams(self):
        """
        Print parameters of EVSP. 
        """
        print("--- EVSP Parameters ---", "\n",
              "Number of Trips:", self.n, "\n",
              "Number of Vehicle Types:", self.k_num, "\n",
              "Battery Capacity:", self.E_k, "\n",
              "Safe Range of Battery Level:", self.batteryLB, self.batteryUB, "\n",
              "Station Capacity:", "not considered" if self.stationCap==-1 else self.stationCap, "\n",
              "Allow Line Change:", self.lineChange, "\n",
              "Charging Function:", self.chargingFuncType, "\n",
              "Time Interval:", self.delta, "\n",
              "Fixed Recharging Time:", self.delta*self.U,
              )


if __name__ == '__main__':
    
    timetable = pd.read_excel('Data\T275_Ave.xlsx')
    
    # initialize an evsp object
    evsp = EVSP(timetable)
    evsp.setVehTypes()
    evsp.setCosts()
    evsp.setChargingFunc(chargingFuncType='piecewise')
    evsp.createModel()
    evsp.printParams()
    