from EVSPModel import EVSP, Duty, Schedule
from ALNS import initialize

import pandas as pd
from gurobipy import GRB, Model, quicksum
from gurobipy import *

import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['STSong']
plt.rcParams['figure.dpi'] = 120
plt.rcParams['xtick.labelsize'] = 'large'
plt.rcParams['ytick.labelsize'] = 'large'


"""
@author: Chen Qiuzi
"""


class Gurobi4EVSP():

    """
    Gurobi solver for EVSP with functions of create, solve and pass solution to Schedule functions.
    """

    def __init__(self, evsp:EVSP):
        """
        Input an EVSP to pass params.
        """
        self.evsp = evsp
        self.model = Model()

    def createModel(self):
        """
        Create gurobi model with vars, constraints and obj.
        """
        print("--- Start Creating")
        
        # --- create sets ---
        
        K = self.evsp.K  # vehicle set
        D = set(['o', 'd'])  # depot node
        T = self.evsp.T  # trip node
        F = self.evsp.F  # recharging trip node
        N = D.union(T, F)  # node set
        A = self.evsp.A  # arc set

        if self.evsp.nonlinear_charge == True:
            B_k = {k:list(range(0,self.evsp.m_k[k])) for k in K}  # break point set
        R = self.evsp.R  # time division set, time range: 5:00-2:00(+24:00), 21 hours, 1260 mins
        I = self.evsp.I  # time division indicator set

        # ----------------------- create variables --------------------
        
        x_kij = self.model.addVars(K, A.union(I), vtype=GRB.BINARY, name='x_kij')  # decision variables
        y_ki = self.model.addVars(K, N, lb=0, ub=max(self.evsp.E_k.values()), vtype=GRB.CONTINUOUS, name='y_ki')  # remain battery energy / kWh
        s_f  =self.model.addVars(F, lb=0, ub=max(self.evsp.s_r.values()), vtype=GRB.CONTINUOUS, name='s_f')  # start time of recharging trip / min
        # q_kf_0 = self.model.addVars(K, F, lb=0, ub=1, vtype=GRB.CONTINUOUS, name='q_kf_0')  # start SoC of recharging trip
        y_kf_1 = self.model.addVars(K, F, lb=0, ub=1, vtype=GRB.CONTINUOUS, name='q_kf_1')  # end SoC of recharging trip
        
        if self.evsp.nonlinear_charge == True:           
            ## start & end time of recharging trip / min
            c_kf_0 = self.model.addVars(K, F, vtype=GRB.CONTINUOUS, name='c_kf_0')
            c_kf_1 = self.model.addVars(K, F, vtype=GRB.CONTINUOUS, name='c_kf_1')
            
            ## 充电函数阶段表征参数
            w_kfb_0 = self.model.addVars(K, F, B_k[1][1:], vtype=GRB.BINARY, name='w_kfb_0')
            w_kfb_1 = self.model.addVars(K, F, B_k[1][1:], vtype=GRB.BINARY, name='w_kfb_1')

            ## 充电函数系数lambda
            lamb_kfb_0 = self.model.addVars(K, F, B_k[1], vtype=GRB.CONTINUOUS, name='lamb_kfb_0')
            lamb_kfb_1 = self.model.addVars(K, F, B_k[1], vtype=GRB.CONTINUOUS, name='lamb_kfb_1')
    
        else:
            # min constraint vars
            u_kf_1 = self.model.addVars(K, F, vtype=GRB.BINARY, name='u_kf_1')
            u_kf_2 = self.model.addVars(K, F, vtype=GRB.BINARY, name='u_kf_2')


        # ---------------------------------- add constraints --------------------------------------------
        
        ## network flow feasibility
        ## (1)
        for i in T:
            delta1_i = [(i,j) for j in N if (i,j) in A]  # 从i出发的弧
            self.model.addConstr(
                sum(x_kij[k,i,j] for k in K for (i,j) in delta1_i) == 1
            )
        ## (2)
        for f in F:
            delta1_f = [(f,j) for j in N if (f,j) in A]  # 从f出发的弧
            self.model.addConstr(
                sum(x_kij[k,f,j] for k in K for (f,j) in delta1_f) <= 1
            )
        ## (3)
        for i in T.union(F):
            for k in K:
                delta0_i = [(j,i) for j in N if (j,i) in A]  # 到达i的弧
                delta1_i = [(i,j) for j in N if (i,j) in A]  # 从i出发的弧
                self.model.addConstr(
                    sum(x_kij[k,i,j] for (i,j) in delta1_i) - sum(x_kij[k,j,i] for (j,i) in delta0_i) == 0
                )
        ## (4)
        for f in F:
            for k in K:
                delta0_f = [(i,f) for i in N if (i,f) in A]  # 到达f的弧
                # delta1_f = [(f,j) for j in N if (f,j) in A]  # 从f出发的弧
                self.model.addConstr(
                    sum(x_kij[k,f,r] for r in R if (f,r) in I) - sum(x_kij[k,i,f] for (i,f) in delta0_f) == 0
                )
        ## (5)
        for k in K:
            delta0_d = [(i,'d') for i in N if (i,'d') in A]  # 到达d的弧（返场）
            delta1_o = [('o',j) for j in N if ('o',j) in A]  # 从o出发的弧（出场）
            self.model.addConstr(
                sum(x_kij[k,i,j] for (i,j) in delta1_o) - sum(x_kij[k,i,j] for (i,j) in delta0_d) == 0
            )
        
        ## timetable constraints
        M = 1000000  # 足够大的数
        ## (6)
        for i in T:
            delta1_i = [(i,j) for j in T if (i,j) in A]  # 从i出发的弧，不加F是因为在A中i可连接的f均符合时间约束
            for (i,j) in delta1_i:
                self.model.addConstr(
                    self.evsp.s_i[i] + self.evsp.t_i[i] + self.evsp.t_ij[(i,j)] - M*(1-sum(x_kij[k,i,j] for k in K)) <= self.evsp.s_i[j]
                )
        ## (7)
        for f in F:
            T_ = [j for j in T if (f,j) in A]  # 与f有连接的j
            for j in T_:
                self.model.addConstr(
                    s_f[f] + self.evsp.U*self.evsp.delta + self.evsp.t_ij[(f,j)] - M*(1-sum(x_kij[k,f,j] for k in K)) <= self.evsp.s_i[j]
                )
        ## (8)
        for f in F:
            R_ = [r for r in R if (f,r) in I]  # 与f有连接的r
            self.model.addConstr(
                s_f[f] - sum(sum((self.evsp.s_r[r]*x_kij[k,f,r]) for r in R_) for k in K) == 0
            )
        ## energy constraints
        ## (9)
        for i in T.union(set(['o'])):
            delta1_i = [(i,j) for j in T.union(F) if (i,j) in A]  # 从i出发的弧
            for (i,j) in delta1_i:
                for k in K:
                    self.model.addConstr(
                        y_ki[k,i] - self.evsp.e_ki[k][i] - self.evsp.e_kij[k][(i,j)] + M*(1-sum(x_kij[k,i,j] for k in K)) >= y_ki[k,j]
                    )
        ## (10)
        for f in F:
            T_ = [j for j in T if (f,j) in A]  # 与f有连接的j
            for j in T_:
                for k in K:
                    self.model.addConstr(
                        y_kf_1[k,f] - self.evsp.e_kij[k][(f,j)] + M*(1-sum(x_kij[k,f,j] for k in K)) >= y_ki[k,j]
                    )
        ## (11)
        for i in T.union(F):
            for k in K:
                self.model.addConstr(
                    y_ki[k,i] >= self.evsp.batteryLB*self.evsp.E_k[k]
                )
                self.model.addConstr(
                    y_ki[k,i] <= self.evsp.batteryUB*self.evsp.E_k[k]
                )
        ## (12)
        for k in K:
            self.model.addConstr(
                y_ki[k,'o'] == self.evsp.E_k[k]
            )

        ## nonlinear constraints
        for f in F:
            delta1_f = [(f,j) for j in N if (f,j) in A]  # 充电行程f出场弧
            delta0_f = [(i,f) for i in N if (i,f) in A]  # 充电行程f入场弧
            for k in K:
        #         if self.evsp.nonlinear_charge == True:
        #             ## (14)
        #             self.model.addConstr(
        #                 q_kf_0[k,f] <= q_kf_1[k,f]
        #             )
        #             ## (15)
        #             self.model.addConstr(
        #                 c_kf_1[k,f] - c_kf_0[k,f] == self.evsp.U*self.evsp.delta * sum(x_kij[k,f,j] for (f,j) in delta0_f)
        #             )
        #             ## (16)
        #             self.model.addConstr(
        #                 q_kf_0[k,f]  == sum(lamb_kfb_0[k,f,b]*self.evsp.a_kb[k][b] for b in B_k[k])
        #             )
        #             ## (17)
        #             self.model.addConstr(
        #                 c_kf_0[k,f] == sum(lamb_kfb_0[k,f,b]*self.evsp.c_kb[k][b] for b in B_k[k])
        #             )
        #             ## (18)
        #             self.model.addConstr(
        #                 sum(lamb_kfb_0[k,f,b] for b in B_k[k]) == sum(w_kfb_0[k,f,b] for b in B_k[k][1:])
        #             )
        #             ## (19)
        #             self.model.addConstr(
        #                 sum(w_kfb_0[k,f,b] for b in B_k[k][1:]) == sum(x_kij[k,f,j] for (f,j) in delta0_f)
        #             )
        #             ## (20)
        #             self.model.addConstr(
        #                 lamb_kfb_0[k,f,0] <= w_kfb_0[k,f,1]
        #             )
        #             ## (21)
        #             for b in B_k[k][1:-1]:
        #                 self.model.addConstr(
        #                     lamb_kfb_0[k,f,b] <= (w_kfb_0[k,f,b] + w_kfb_0[k,f,b+1])
        #                 )
        #             ## (22)
        #             self.model.addConstr(
        #                 lamb_kfb_0[k,f,B_k[k][-1]] <= w_kfb_0[k,f,B_k[k][-1]]
        #             )
        #             ## (23)
        #             self.model.addConstr(
        #                 q_kf_1[k,f]  == sum(lamb_kfb_1[k,f,b]*self.evsp.a_kb[k][b] for b in B_k[k])
        #             )
        #             ## (24)
        #             self.model.addConstr(
        #                 c_kf_1[k,f] == sum(lamb_kfb_1[k,f,b]*self.evsp.c_kb[k][b] for b in B_k[k])
        #             )
        #             ## (25)
        #             self.model.addConstr(
        #                 sum(lamb_kfb_1[k,f,b] for b in B_k[k]) == sum(w_kfb_1[k,f,b] for b in B_k[k][1:])
        #             )
        #             ## (26)
        #             self.model.addConstr(
        #                 sum(w_kfb_1[k,f,b] for b in B_k[k][1:]) == sum(x_kij[k,f,j] for (f,j) in delta0_f)
        #             )
        #             ## (27)
        #             self.model.addConstr(
        #                 lamb_kfb_1[k,f,0] <= w_kfb_1[k,f,1]
        #             )
        #             ## (28)
        #             for b in B_k[k][1:-1]:
        #                 self.model.addConstr(
        #                     lamb_kfb_1[k,f,b] <= (w_kfb_1[k,f,b] + w_kfb_1[k,f,b+1])
        #                 )
        #             ## (29)
        #             self.model.addConstr(
        #                 lamb_kfb_1[k,f,B_k[k][-1]] <= w_kfb_1[k,f,B_k[k][-1]]
                #     )
                # else:
                ## (14)
                M = 10000
                ## (13-1)
                self.model.addConstr(
                    y_kf_1[k,f] <= y_ki[k,f] + self.evsp.U * self.evsp.delta * self.evsp.v_k[k]
                )
                ## (13-2)
                self.model.addConstr(
                    y_kf_1[k,f] <= 1
                )
                ## (13-3)
                self.model.addConstr(
                    y_kf_1[k,f] >= y_ki[k,f] + self.evsp.U * self.evsp.delta * self.evsp.v_k[k] * self.evsp.E_k[k] - (1 - u_kf_1[k,f])*M
                )
                ## (13-4)
                self.model.addConstr(
                    y_kf_1[k,f] >= 1 - (1 - u_kf_2[k,f])*M
                )
                ## (14-5)
                self.model.addConstr(
                    u_kf_1[k,f] + u_kf_2[k,f] >= 1
                )

        ## recharging station capacity constraints
        ## (30)
        for r in R:
            for k in K:
                F_ = [f for f in F if (f,r) in I] # 与r有连接的indicator
                R_ = ["r%d"%(int(r[1:])-u) for u in range(self.evsp.U) if int(r[1:])-u > 0]
                self.model.addConstr(
                    sum(sum(x_kij[k,f,r_] for f in [f for f in F if (f,r_) in I]) for r_ in R_) <= self.evsp.C_r[r]
                )

    # ----------------------- objective funtion --------------------------------
    
        ## 购车成本
        delta1_o = [('o',j) for j in T if ('o',j) in A]
        purchase_cost = quicksum(quicksum(self.evsp.c_k[k]*x_kij[k,i,j] for (i,j) in delta1_o) for k in K)
        
        ## 能耗成本
        electric_cost = quicksum(quicksum((y_kf_1[k,f]-y_ki[k,f])*self.evsp.c_e[r]*x_kij[k,f,r] for (f,r) in I) for k in K)\
                      + quicksum(quicksum((self.evsp.E_k[k] - (y_ki[k,i] - self.evsp.e_ki[k][i] - self.evsp.e_kij[k][(i,'d')]))*max(self.evsp.c_e.values())*x_kij[k,i,'d'] for i in T) for k in K)

        ## 时间成本
        time_cost = quicksum(quicksum((self.evsp.t_i[i]+self.evsp.t_ij[i,j])*self.evsp.c_t*x_kij[k,i,j] for (i,j) in A if i in T) for k in K)

        ## 目标函数
        self.model.setObjective(purchase_cost + electric_cost + time_cost, 
                        GRB.MINIMIZE)
        # model.setObjectiveN(purchase_cost, index=0, priority=1, weight=1)
        # model.setObjectiveN(electric_cost, index=1, priority=1, weight=1)
        # model.setObjectiveN(time_cost, index=1, priority=1, weight=1)
        # model.Sense()
        print("--- Finish Creating")

    def initVarByGreedy(self):
        """
        Input initial solution to Gurobi model.
        """
        schedule = initialize(self.evsp)
        
        self.model.NumStart = 1
        self.model.params.StartNumber = 0
        self.model.update()
    
        for duty in schedule.schedule:
            k = duty.K
            for p in range(len(duty.S)-1):
                i = duty.S[p]
                j = duty.S[p+1]
                self.model.getVarByName("x_kij[%s,%s,%s]"%(k,i,j)).Start = 1
                # if i == 'o':
                #     self.model.getVarByName("x_kij[%s,o,%s]"%(k,j)).Start = 1
                # elif j == 'd':
                #     self.model.getVarByName("x_kij[%s,%s,d]"%(k,i)).Start = 1
                if i in self.evsp.F:
                    r = duty.R[i]
                    self.model.getVarByName("x_kij[%s,%s,%s]"%(k,i,r)).Start = 1
                    self.model.getVarByName("s_f[%s]"%i).Start = self.evsp.s_r[r]
        del schedule

    # def initVarByRead(self, solFile):
    #     """
    #     Input initial solution to Gurobi model.
    #     """
    #     self.model.NumStart = 1
    #     self.model.params.StartNumber = 0
    #     self.model.update()
    #     self.model.read(solFile)


    def solve(self, timeLimit=10*60, printLog=True, MIPGap=0.001, MIPFocus=0):
        """
        Use gurobi solver to solve EVSP.
        """
        self.model.setParam('TimeLimit', timeLimit)
        self.model.setParam('OutputFlag', printLog)
        self.model.setParam('MIPGap', MIPGap)
        self.model.setParam('MIPFocus', MIPFocus)
        self.model.optimize()
    
    def outputSchedule(self):
        """
        Update solution to a Schedule objective.
        """
        schedule = Schedule(self.evsp,[],{})  # new Schedule
        vehicleIndex = 0
        for k in self.evsp.K:
            for j in self.evsp.T:
                Xkoj = self.model.getVarByName("x_kij[%s,o,%s]"%(k,j))
                if Xkoj.X == 1:
                    vehicleIndex += 1
                    S = self.findS(k, j)
                    R = self.findR(k, S)
                    duty = Duty(self.evsp, k, S, R)
                    schedule.addDuty(duty)
        return schedule

    def findS(self,k,j):
        # get nodes that belong to the same trip start with j
        # sets reset
        trips = ['o', j]
        a = j
        while True:
            if a == 'd':
                break
            for b in self.evsp.T.union(self.evsp.F, set(['d'])):
                if (a,b) in self.evsp.A:
                    Xkab = self.model.getVarByName("x_kij[%s,%s,%s]"%(k,a,b))
                    if Xkab.X == 1:  # if the connection a-b equal to 1
                        trips.append(b)
                        a = b
        return trips

    def findR(self, k, S):
        """
        Find R dict of a trips.
        """
        R = {}
        F = [node for node in S[1:-1] if type(node)==str]
        for f in F:
            for r in [r for r in self.evsp.R if (f,r) in self.evsp.I]:
                Xkfr = self.model.getVarByName("x_kij[%s,%s,%s]"%(k,f,r))
                if Xkfr.X == 1:
                    R[f] = r
        return R

