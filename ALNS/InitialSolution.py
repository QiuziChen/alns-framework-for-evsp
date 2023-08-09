from EVSPModel import Duty, Schedule, EVSP
from EVSPModel.Calculations import calCharge


"""
@author: Chen Qiuzi
"""


def initialize(evsp:EVSP):
    """
    Provide initialize feasible solution using greedy heuristic.
    """
    k0 = max(evsp.E_k, key=evsp.E_k.get)  # initial veh_type has the largest capacity
    T = [i for i in evsp.T]  # temp trip set
    newSchedule = Schedule(evsp, [], {})  # dict, veh_no:[type:int, schedule:list, time division:dict]
    S = []  # trip chain list of single duty
    R = {}  # time division dict for charging nodes

    while T:
        # initialization
        T = list(filter(lambda x: x not in S, T)) # update T
        if not T:
            break
        i = 'o'
        Y = [evsp.E_k[k0]]  # initial battery level
        S = [i]
        while 1:
            j = search_trip(evsp, i, T, R)  # search the nearest trip
            if j == None:  # end of a schedule
                if i in evsp.F:
                    S.remove(i)
                # if i not in evsp.F:
                #     S.append('f%d'%i)  # link with charging node
                #     # Y.append(Y[-1] - evsp.e_ki[k0][i] - evsp.e_kij[k0][(i,'f%d'%i)])  # update energy level of fi
                #     i = 'f%d'%i
                #     R = choose_r(evsp, i, R)
                S.append('d')
                if evsp.k_num == 1:
                    kb = k0
                else:
                    kb = choose_k(evsp, S, R)  # choose an optimal veh type
                newSchedule.schedule.append(Duty(evsp, kb, S, {k:R[k] for k in S[1:-1] if type(k)==str}))
                break
            elif energy_violate(evsp, k0, Y, i, j) == True:
                S.append('f%d'%i)
                Y.append(Y[-1] - evsp.e_ki[k0][i] - evsp.e_kij[k0][(i,j)])  # update energy level of fi
                i = 'f%d'%i
                R = choose_r(evsp,i,R)
                continue
            else:
                S.append(j)
                if i in evsp.F:
                    Y.append(Y[-1] + calCharge(evsp, k0, Y[-1]) - evsp.e_kij[k0][(i,j)])  # if i is charging trip
                else:
                    Y.append(Y[-1] - evsp.e_ki[k0][i] - evsp.e_kij[k0][(i,j)])  # update Y of tj
                i = j
                continue

    # update solution
    newSchedule.R = R
    
    return newSchedule


def initialize_nightCharge(evsp:EVSP):
    """
    Provide initialize feasible solution using greedy heuristic for <night time charge only> mode.
    """
    k0 = max(evsp.E_k, key=evsp.E_k.get)  # initial veh_type
    T = [i for i in evsp.T]  # temp trip set
    newSchedule = Schedule(evsp, [], {})  # dict, veh_no:[type:int, schedule:list, time division:dict]
    S = []  # schedule list
    R = {}  # time division dict for charging nodes

    while T:
        # initialization
        T = list(filter(lambda x: x not in S, T)) # update T
        if not T:
            break
        i = 'o'
        Y = [evsp.E_k[k0]]  # initial battery level
        S = [i]
        while 1:
            j = search_trip(evsp, i, T, R)  # search the nearest trip
            if j == None or energy_violate(evsp, k0, Y, i, j):  # end of a schedule
                # if i in evsp.F:
                #     S.remove(i)
                # if i not in evsp.F:
                #     S.append('f%d'%i)  # link with charging node
                #     # Y.append(Y[-1] - evsp.e_ki[k0][i] - evsp.e_kij[k0][(i,'f%d'%i)])  # update energy level of fi
                #     i = 'f%d'%i
                #     R = choose_r(evsp, i, R)
                S.append('d')
                if evsp.k_num == 1:
                    kb = k0
                else:
                    kb = choose_k(evsp, S, R)  # choose an optimal veh type
                newSchedule.schedule.append(Duty(evsp, kb, S, {k:R[k] for k in S[1:-1] if type(k)==str}))
                break
            else:
                S.append(j)
                if i in evsp.F:
                    Y.append(Y[-1] + calCharge(evsp, k0, Y[-1]) - evsp.e_kij[k0][(i,j)])  # if i is charging trip
                else:
                    Y.append(Y[-1] - evsp.e_ki[k0][i] - evsp.e_kij[k0][(i,j)])  # update Y of tj
                i = j
                continue

    # update solution
    newSchedule.R = R
    
    return newSchedule


def search_trip(evsp, i, T, R):
    """
    i: current node index
    T: set of remain trips
    R: dict of charging division assignment
    return: nearest linkable trip
    considering: time compatibility
    """
    j = None
    if not T:
        return None
    elif i in evsp.T:
        for t in T:
            if ((i, t) in evsp.A):  # cause trips are sorted assendingly
                j = t
                break
    elif i in evsp.F:
        for t in T:
            if ((i, t) in evsp.A):
                j = t
                break
    elif i == 'o':
        j = T[0]
    return j
    
    # j = None
    # if i=='o':  # first trip of a schedule
    #     return T[0]
    # elif not T:  # available trips set empty
    #     return None
    # elif i in evsp.F:  # charging trip node
    #     for t in T:
    #         if ((i, t) in evsp.A) and (evsp.s_i[t] >= evsp.s_r[R[i]] + evsp.U * evsp.delta + evsp.t_ij[(i,t)]):
    #             j = t
    #             break
    # else:  # trip node
    #     for t in T:
    #         if ((i, t) in evsp.A) and (evsp.s_i[t] >= evsp.s_i[i] + evsp.t_i[i] + evsp.t_ij[(i,t)]):  # cause trips are sorted assendingly
    #             j = t
    #             break
    # return j

def choose_r(evsp, f, R):
    """
    i: current node index
    R: dict of charging division assignment
    return: new R with the nearest available time division
    considering: time & capacity
    """
    i = int(f[1:])
    for r in [r for r in evsp.R if (f,r) in evsp.I]:
        num = []  # number of vehicle in the station before r when i is charging
        for u in range(evsp.U):  # 0, 1, 2...
            index = int(r[1:])+u  # index of r to check capacity, if r=r3, then index=3,4,5...
            num_before = 0
            for u in range(evsp.U):
                index_before = index-u  # index of r when vehicle still charging
                if index_before > 0:  # considering r1, r2...
                    num_before += sum(map(('r%d'%(index_before)).__eq__, R.values()))
            num.append(num_before)
        if  (max(num) < evsp.stationCap):  # considering capacity
            R[f] = r
            break
        
    return R

def choose_k(evsp, S, R):
    """
    S: list of schedule
    R: dict of recharging time division
    return: type k leading to min cost
    """
    cost = {}
    for k in evsp.K:
        duty = Duty(evsp,k,S,R)
        cost[k] = duty.calCost() if duty.checkEnergyFeasibility() else float("inf")
    return min(cost, key=cost.get)  # minimum cost k    

def energy_violate(evsp, k, Y, i, j):
    """
    return True if able to complete trip j after trip i
    """
    if i in evsp.F:
        if (Y[-1] + calCharge(evsp, k, Y[-1]) - evsp.e_kij[k][(i,j)]) < evsp.batteryLB * evsp.E_k[k]:
            return True
        else:
            return False
    else:  # i is trip node
        if (Y[-1] - evsp.e_ki[k][i] - evsp.e_kij[k][(i,j)] - evsp.e_ki[k][j]) < evsp.batteryLB * evsp.E_k[k]:  # safe energy level
            return True
        else:
            return False
