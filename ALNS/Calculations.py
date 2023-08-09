from EVSPModel import Duty, Schedule, EVSP
from EVSPModel.Calculations import calCharge

import random


"""
@author: Chen Qiuzi
This Python file includes several calculation functions for operators.
X-Pos: get a trip & position to insert according to specific principle.
X-ChargingTime: find a charging time for charging activity according to certain principle.
find-X: search for position or vehicle type.
"""


def randomPos(evsp:EVSP, tripBank:list, schedule:Schedule):
    """
    Find trip & position to insert randomly.
    """
    trip, dutyIndex, pos = None, -1, -1
    tripPool = [i for i in tripBank]

    while tripPool:
        trip = random.choice(tripPool)  # select a trip randomly
        dutyIndex, pos = findPosInSchedule(evsp, schedule, trip)
        if pos == -1:
            tripPool.remove(trip)
            continue
        else:
            break
    return trip, dutyIndex, pos


# def minCostPos(evsp:EVSP, tripBank:list, schedule:Schedule):
#     """
#     Find trip & position to insert with min cost.
#     """
#     trip, dutyIndex, pos = None, -1, -1
#     tripPool = [i for i in tripBank]

#     while tripPool:
#         trip = random.choice(tripPool)  # select a trip randomly
#         dutyIndex, pos = findPosInSchedule(evsp, schedule, trip)
#         if pos == -1:
#             tripPool.remove(trip)
#             continue
#         else:
#             break
#     return trip, dutyIndex, pos


def findPosInSchedule(evsp:EVSP, schedule:Schedule, trip:int):
    """
    Find one position to insert in a schedule randomly.
    Return (dutyIndex, pos).
    """
    dutyIndexPool = list(range(len(schedule.schedule)))
    dutyIndex, pos = -1, -1

    while dutyIndexPool:
        dutyIndex = random.choice(dutyIndexPool)
        duty = schedule.schedule[dutyIndex]
        pos = findPosInDuty(evsp, duty, trip)
        if pos == -1:
            dutyIndexPool.remove(dutyIndex)
            continue
        else:
            break
    return (dutyIndex, pos)


def findPosInDuty(evsp:EVSP, duty:Duty, trip:int):
    """
    Find position to insert in the duty.
    One duty only has one position for one trip.
    Consider time feasibility.
    """
    pos = -1
    for index, _trip in enumerate(duty.S[:-1]):
        trip_ = duty.S[index+1]  # trip/node before & after
        
        if (_trip,trip) not in evsp.A:  # no pos to insert
            break
        elif (trip, trip_) in evsp.A:
            pos = index + 1
            break
        elif trip_ == 'd':
            pos = index + 1
            break
        # if (((_trip, trip) in evsp.A) and ((trip, trip_) in evsp.A)):  #  and (evsp.s_i[_trip]+evsp.t_i[_trip]+evsp.t_ij[(_trip,trip)]<=evsp.s_i[trip]) and (evsp.s_i[trip]+evsp.t_i[trip]+evsp.t_ij[(trip,trip_)]<=evsp.s_i[trip_])
        #     pos = index + 1
        #     break
        # elif ((trip, _trip) in evsp.A):
        #     break
        # elif (trip_ == 'd') and ((_trip, trip) in evsp.A):
        #     pos = index + 1
        #     break
        
    return pos


def greedyChargingTime(evsp:EVSP, schedule:Schedule, trip1:int, trip2:int):
    """
    Find an available charging time division between trip1 & trip2.
    Return None if cannot insert charging node.
    """
    r = None
    if ("f%d"%trip1,trip2) not in evsp.A:
        return r
    else:
        possibleR = []
        if trip2 == 'd':
            possibleR = [r for r in evsp.R if (evsp.s_r[r]>=evsp.s_i[trip1]+evsp.t_i[trip1]+evsp.t_ij[(trip1,"f%d"%trip1)])]
        else:
            possibleR = [r for r in evsp.R if ((evsp.s_r[r]>=evsp.s_i[trip1]+evsp.t_i[trip1]+evsp.t_ij[(trip1,"f%d"%trip1)]) and (evsp.s_r[r]+evsp.U*evsp.delta+evsp.t_ij[("f%d"%trip1,trip2)]<=evsp.s_i[trip2]))]
    
        # assignFlag = 0  # flag param, =1 if assignment finished
        # minCost = float("inf")
        availableR = {}
        for r_ in possibleR:
            num = calVehNumList(evsp, schedule, r_)
            if (max(num) < evsp.stationCap):
                availableR[r_] = evsp.c_e[r_]
        if len(availableR) != 0:
            r = min(availableR, key=availableR.get)
        else:
            r = random.choice(possibleR)  # choose one randomly
        #     if (max(num) < evsp.capacity) and (evsp.c_e[r_] < minCost):  # considering capacity
        #         minCost = evsp.c_e[r_]
        #         r = r_
        #         assignFlag = 1
        # if assignFlag == 0:  # no available time division
        #     r = random.choice(possibleR)  # choose one randomly
    return r


def randomChargingTime(evsp:EVSP, trip1, trip2):
    """
    Find an available charging time division randomly between trip1 & trip2.
    Not consider capacity in order to reduce calculation.
    """
    r = None

    if ("f%d"%trip1,trip2) not in evsp.A:
        return r
    else:
        possibleR = []
        if trip2 == 'd':
            possibleR = [r for r in evsp.R if (evsp.s_r[r]>=evsp.s_i[trip1]+evsp.t_i[trip1]+evsp.t_ij[(trip1,"f%d"%trip1)])]
        elif ("f%d"%trip1, trip2) in evsp.A:
            possibleR = [r for r in evsp.R if ((evsp.s_r[r]>=evsp.s_i[trip1]+evsp.t_i[trip1]+evsp.t_ij[(trip1,"f%d"%trip1)]) and (evsp.s_r[r]+evsp.U*evsp.delta+evsp.t_ij[("f%d"%trip1,trip2)]<=evsp.s_i[trip2]))]
        
        r = random.choice(possibleR)  # choose the nearest
        return r


def nearestChargingTime(evsp:EVSP, trip1, trip2):
    """
    Find the nearest charging time division between trip1 & trip2.
    Not consider capacity in order to reduce calculation.
    """
    r = None

    if ("f%d"%trip1,trip2) not in evsp.A:
        return r
    else:
        possibleR = []
        if trip2 == 'd':
            possibleR = [r for r in evsp.R if (evsp.s_r[r]>=evsp.s_i[trip1]+evsp.t_i[trip1]+evsp.t_ij[(trip1,"f%d"%trip1)])]
        elif ("f%d"%trip1, trip2) in evsp.A:
            possibleR = [r for r in evsp.R if ((evsp.s_r[r]>=evsp.s_i[trip1]+evsp.t_i[trip1]+evsp.t_ij[(trip1,"f%d"%trip1)]) and (evsp.s_r[r]+evsp.U*evsp.delta+evsp.t_ij[("f%d"%trip1,trip2)]<=evsp.s_i[trip2]))]
      
        r = possibleR[0]  # choose the nearest
        return r


def findBestVehType(evsp:EVSP, duty:Duty):
    """
    Find a best veh type leading to the least cost for a duty. 
    """
    if len(evsp.K) == 1:
        return evsp.K[0]
    else:
        cost = {}
        for k in evsp.K:
            duty_ = Duty(evsp, k, duty.S, duty.R)
            cost[k] = duty_.calCost() if duty_.checkEnergyFeasibility() else float("inf")
        return min(cost, key=cost.get)


def calVehNumList(evsp:EVSP, schedule:Schedule, r:str):
    """
    Calculate the number of vehicle still in charging station of division r.
    """
    numList = []
    for u in range(evsp.U):  # 0, 1, 2...
        index = int(r[1:])+u  # index of r to check capacity, if r=r3, then index=3,4,5...
        num_before = 0
        for u in range(evsp.U):
            index_before = index-u  # index of r when vehicle still charging
            if index_before > 0:  # considering r1, r2...
                num_before += sum(map(('r%d'%(index_before)).__eq__, schedule.R.values()))
        numList.append(num_before)
    return numList

def calSOC(evsp:EVSP, duty:Duty, pos:int):
    """
    Calculate SOC after finishing trip whose position equal to pos in schedule.
    """
    k = duty.K
    y = evsp.E_k[k]  # battery level at the beginning of a node
    trips = duty.S
    for i, s in enumerate(trips[:pos]):
        if s in evsp.F:  # charging node
            y = y + calCharge(evsp, k, y) - evsp.e_kij[k][(s,trips[i+1])]
        else:
            y = y - evsp.e_ki[k][s] - evsp.e_kij[k][(s,trips[i+1])]
    return y / evsp.E_k[k]