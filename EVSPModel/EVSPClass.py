import pandas as pd


"""
@author: Chen Qiuzi
"""


class EVSP():

    """
    An EVSP object is used to store timetables and network params.
    Network params include data of nodes, arcs, vehicles and charging stations.
    """

    def __init__(
        self,
        timetable:pd.DataFrame, 
        calVehCost=True, # model param, whether to calculate vehicle cost
        calElecCost=True, # model param, whether to calculate electricity cost
        calLaborCost=True, # model param, whether to calculate labor cost
        batteryLB=0.2, # vehicle param, lower bound of battery level
        batteryUB=1.0, # vehicle param, upper bound of battery level 
        stationCap=-1, # model param, charging station capacity
        delta=10, # operating param, minimum time interval / min
        U=3, # operating param, number of delta in a fixed charging duration
        lineChange=True, # operating param, whether line change activities are allowed for BEBs
    ):
        """
        0 [timetable]
        timetable: DataFrame with columns=['ID','Route','StartTime','StartTimeMin','TravelTimeMin','Consumption']
        
        1 [model param]
        calVehCost: [model param] whether to calculate vehicle cost, default=True
        calElecCost: [model param] whether to calculate electricity cost, default=True
        calLaborCost: [model param] whether to calculate labor cost, default=True

        2 [vehicle param]
        batteryLB: [vehicle param] lower bound of battery level, default=0.2
        batteryUB: [vehicle param] upper bound of battery level, default=1.0

        3 [operating param]
        stationCap: [model param] charging station capacity, default=-1 means capacity constraints are not considered
        delta: [operating param] minimum time interval, default=10(min)
        U: [operating param] number of delta in a fixed charging duration, default=3 (delta=10, U=3 means the fixed charging duration=30min)
        lineChange: [operating param] whether line change activities are allowed for BEBs, default=True
        """
        
        self.timetable = timetable
        self.stationCap = stationCap
        self.calVehCost = calVehCost
        self.calElecCost = calElecCost
        self.calLaborCost = calLaborCost
        self.batteryLB = batteryLB
        self.batteryUB = batteryUB
        self.delta = delta
        self.U = U
        self.lineChange = lineChange

    def setVehTypes(
            self,
            k_num,
            E_k:dict,
            capRelatedCons=False,
            benchCap=220,
            consIncRate=0.000297,
    ):
        """
        Set vehicle types information.
        k_num: number of vehicle types
        E_k: battery capacity of each type, dict, indices should be integer start from 1
        capRelatedCons: whether to adjust energy consumption according to battery capacity
        benchCap: if adjust consumption, a benchmark capacity should be set
        consIncRate: assuming a linear relationship between energy consumption and battery capaicty, the coefficient or increasing rate should be set
        """
        self.k_num = k_num

        if list(E_k.keys())[0] != 1:
            raise KeyError("Indices of vehicle types should be integers beginning at 1.")
        elif len(E_k.keys()) != k_num:
            raise ValueError("Length of E_k should be equal to k_num.")
        else:
            self.E_k = E_k

        self.capRelatedCons = capRelatedCons
        self.benchCap = benchCap
        self.consIncRate = consIncRate

    def setCosts(self):
        """
        Set costs value.
        """
        pass

    def setChargingFunc(self, func):
        """
        Set charging function.
        """
        pass


    def plotChargingFunc(self):
        """
        Plot charging curve.
        """
        pass


    def createModel(self):

        # --- basic data ---
        
        self.k_num = k_num  # number of vehicle types
        self.K = list(range(1, self.k_num+1))  # set of vehicle types
        self.E_k = {1: 100, 2: 170, 3: 258}  # battery capacity
        self.batteryLB = batteryLB  # lower bound of safe battery level [0,1]
        self.batteryUB = batteryUB  # upper bound of safe battery level [0,1]
        self.delta = delta  # time interval for recharging time division
        self.U = U  # fixed number of unit intervals to recharge

        # --- trip data ---
        
        self.timetable = timetable  # timetable
        self.n = self.timetable.shape[0]  # trip number
        self.T = set(list(range(1, self.n+1)))  # set of trip nodes
        self.F = set(['f%d'% i for i in range(1, self.n+1)])
        ## start time of trips
        self.s_i = {i:self.timetable.StartTimeMin.iloc[i-1] for i in range(1, self.n+1)}  
        self.s_i['o'] = 0
        self.s_i['d'] = 24 * 60
        ## travel time of trips
        self.t_i = {i:self.timetable.TravelTimeMin.iloc[i-1] for i in range(1, self.n+1)}
        for f in self.F:
            self.t_i[f] = 0
        self.t_i['o'] = 0
        ## set of arcs
        self.lineChange = lineChange
        if self.lineChange == True:
            self.A = [('o', j) for j in self.T] \
                    + [(i, j) for i in self.T for j in self.T if (self.s_i[i]+self.t_i[i]<=self.s_i[j])] \
                    + [(i, f) for i in self.T for f in self.F if i==int(f[1:])] \
                    + [(i, j) for i in self.T for j in ['d']] \
                    + [(f, j) for f in self.F for j in self.T if (self.s_i[int(f[1:])]+self.t_i[int(f[1:])]+(self.U*self.delta)<=self.s_i[j])]
            self.A = set(self.A)
        else:
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
        if capRelatedCons == False:
            self.e_ki = {k:{i:self.timetable.Consumption.iloc[i-1] for i in range(1, self.n+1)} for k in range(1, self.k_num+1)}  # energy consumption of trips
            for k in self.K:
                self.e_ki[k]['o'] = 0
                # self.e_ki[k]['d'] = 0
        else:
            consIncRate = 0.000297
            benchCap = 220
            self.e_ki = {k:{i:(self.timetable.Consumption.iloc[i-1] + (self.E_k[k] - benchCap) * consIncRate * self.timetable.Distance.iloc[i-1])
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
        
        # --- piecewise linear function ---

        self.L = L
        if self.L == True:
            self.c_kb = {1:[0, 80, 100, 150, 300], 2:[0, 136, 170, 255, 400], 3:[0, 206.4, 258, 387, 500]}  # charging time for break point
            self.a_kb = {1:[0.0, 0.8, 0.9, 1.0, 1.0], 2:[0.0, 0.8, 0.9, 1.0, 1.0], 3:[0.0, 0.8, 0.9, 1.0, 1.0]}  # SOC for break point
            self.m_k = {k: len(self.c_kb[k]) for k in self.K}  # number of break point
            self.B_k = {k:list(range(0,self.m_k[k])) for k in self.K}  # break point set
        else:
            self.v_k = {1: cPower/60, 2: cPower/60, 3: cPower/60}  # # linear charging rate, kWh/min
            

        # ---time division parameters---

        ## set of time division
        self.R = ['r%d'% i for i in range(1, 1260//self.delta-1)]  # time range: 5:00-2:00(+24:00), 21 hours, 1260 mins
        self.s_r = {r:(int(r[1:])-1)*10+300 for r in self.R}  # start time of time division
        self.capacity = capacity
        self.C_r = {r:self.capacity for r in self.R}  # station capacity of recharging time division
        ## set of time division indicators
        self.I = set([(f,r) for f in self.F for r in self.R if self.s_i[int(f[1:])]+self.t_i[int(f[1:])]+self.t_ij[(int(f[1:]), f)]<=self.s_r[r]])

        ## remove infeasible arcs
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
        self.c_k = {1: 804.7, 2: 907.56, 3: 1039.14}  # purchase cost CNY/d
        self.c_e = {}  # unit electricity cost

        ## time of use
        # for r in self.R:
        #     if (0<=self.s_r[r]<480) or (self.s_r[r]>=1440):
        #         self.c_e[r] = 0.3155  # CNY/kWh
        #     else:
        #         self.c_e[r] = 0.6465  # CNY/kWh
        
        for r in self.R:
            self.c_e[r] = 0.6414  # CNY/kWh

        self.calLaborCost = calLaborCost
        self.c_t = 0.5  # unit time cost, CNY/min


    def printParams(self):
        """
        Print parameters of EVSP. 
        """
        print("--- EVSP Parameters")
        print("Number of Trips:", self.n)
        print("Number of Vehicle Types:", self.k_num)
        print("Battery Capacity:", self.E_k)
        print("Safe Battery Level:", self.batteryLB)
        print("Station Capacity:", self.capacity)
        print("Allow Line Change:", self.lineChange)
        print("Charging Function:", "non-linear" if self.L else "linear")
        print("Time Interval:", self.delta)
        print("Recharging Time:", self.delta*self.U)