from EVSPModel import Duty, Schedule, EVSP
from .Calculations import randomPos
from .Calculations import randomChargingTime, greedyChargingTime, nearestChargingTime
from .Calculations import findBestVehType, calSOC

import random
from copy import deepcopy


"""
@author: Chen Qiuzi
"""


def randomInsert(evsp:EVSP, tripBank:list, schedule:Schedule, enePenalty, capPenalty, chargeProb):
    """
    Insert trips & charging randomly.
    Random insertion doesn't need to guarantee feasibility, but for diversification.
    1. Select a trip randomly.
    2. Insert it to a random position.
    3. Insert a charging node behind it randomly.(choose a random charging time division)
    4. Choose a random time division for the last charging node. (needn't last charging in beta version)
    5. If infeasible, add a penalty instead of reject it.
    """
    newCost = 0
    newSchedule = deepcopy(schedule)
    tripPool = [i for i in tripBank]
    
    # insert trips
    while tripPool:
        trip, dutyIndex, pos = randomPos(evsp, tripPool, newSchedule)
        if pos == -1:  # no pos to insert
            kran = random.choice(evsp.K)  # choose a new bus with random type
            duty = Duty(evsp, kran, ['o',trip,'d'],{})
            newSchedule.addDuty(duty)  # add a new Bus
        else:
            newSchedule.schedule[dutyIndex].S.insert(pos, trip)
            # insert charging node randomly
            if chargeProb >= random.uniform(0,1):
                trip_ = newSchedule.schedule[dutyIndex].S[pos+1]
                r = randomChargingTime(evsp, trip, trip_)  # choose a random charging time
                if r == None:
                    pass
                else:
                    newSchedule.schedule[dutyIndex].S.insert(pos+1, "f%d"%trip)
                    newSchedule.schedule[dutyIndex].R["f%d"%trip] = r
                    newSchedule.addR("f%d"%trip, r)
        tripPool.remove(trip)

    # insert the last charging nodes
    # newSchedule = randomChargingInsert(evsp, newSchedule)
    for duty in newSchedule.schedule:
        i = duty.S[-2]
        if i in evsp.F:
            duty.S.remove(i)
            r_ = duty.R.pop(i)
            newSchedule.delR(i)

    # calculate cost
    eneFeasible, capFeasible = True, True
    newCost = newSchedule.calCost()
    # add penalty
    if not newSchedule.checkCapacityFeasibility():
        newCost += capPenalty
        capFeasible = False
    if not newSchedule.checkEnergyFeasibility():
        newCost += enePenalty
        eneFeasible = False
    isFeasible = eneFeasible and capFeasible

    return newCost, newSchedule, isFeasible


def greedyInsert(evsp:EVSP, tripBank:list, schedule:Schedule, enePenalty, capPenalty, chargeProb):
    """
    Greedy insertion try to guarantee feasibility.
    1. Select a trip randomly.
    2. Insert it to a random position.
    3. Insert a charging node behind it randomly.(choose the nearest charging time division)
    4. Choose a greedy time division for the last charging node.
    5. If infeasible, add a penalty instead of reject it.
    """
    newCost = 0
    newSchedule = deepcopy(schedule)
    tripPool = [i for i in tripBank]
    
    # insert trips
    while tripPool:
        trip, dutyIndex, pos = randomPos(evsp, tripPool, newSchedule)
        if pos == -1:  # no pos to insert
            kran = random.choice(evsp.K)  # choose a new bus with random type
            duty = Duty(evsp, kran, ['o',trip,'d'],{})
            newSchedule.addDuty(duty)  # add a new Bus
        else:
            newSchedule.schedule[dutyIndex].S.insert(pos, trip)
            
            # # insert charging node greedily
            # if calSOC(evsp, newSchedule.schedule[dutyIndex], pos+1) < evsp.sigma:
            #     trip_ = newSchedule.schedule[dutyIndex].S[pos+1]
            #     r = greedyChargingTime(evsp, newSchedule, trip, trip_)  # choose the nearest charging time
            #     if r == None:
            #         pass
            #     else:
            #         newSchedule.schedule[dutyIndex].S.insert(pos+1, "f%d"%trip)
            #         newSchedule.schedule[dutyIndex].R["f%d"%trip] = r
            #         newSchedule.addR("f%d"%trip, r)

            # insert charging node randomly
            if chargeProb >= random.uniform(0,1):
                trip_ = newSchedule.schedule[dutyIndex].S[pos+1]
                r = greedyChargingTime(evsp, newSchedule, trip, trip_)  # choose the nearest charging time
                if r == None:
                    pass
                else:
                    newSchedule.schedule[dutyIndex].S.insert(pos+1, "f%d"%trip)
                    newSchedule.schedule[dutyIndex].R["f%d"%trip] = r
                    newSchedule.addR("f%d"%trip, r)
        
        tripPool.remove(trip)

    # insert the last charging nodes
    # newSchedule = greedyChargingInsert(evsp, newSchedule)
    for duty in newSchedule.schedule:
        i = duty.S[-2]
        if i in evsp.F:
            duty.S.remove(i)
            r_ = duty.R.pop(i)
            newSchedule.delR(i)
            
    # optimize veh type
    for duty in newSchedule.schedule:
        duty.K = findBestVehType(evsp, duty)

    # calculate cost
    eneFeasible, capFeasible = True, True
    newCost = newSchedule.calCost()
    # add penalty
    if not newSchedule.checkCapacityFeasibility():
        newCost += capPenalty
        capFeasible = False
    if not newSchedule.checkEnergyFeasibility():
        newCost += enePenalty
        eneFeasible = False
    isFeasible = eneFeasible and capFeasible

    return newCost, newSchedule, isFeasible


def randomChargingInsert(evsp:EVSP, schedule:Schedule):
    """
    Insert the last charging nodes randomly.
    """
    newSchedule = deepcopy(schedule)

    for duty in newSchedule.schedule:

        # insert the last charging node
        if duty.S[-2] in evsp.F:
            pass
        else:
            trip = duty.S[-2]
            duty.S.insert(-1, "f%d"%trip)
            duty.R["f%d"%trip] = randomChargingTime(evsp, trip, 'd')
            newSchedule.addR("f%d"%trip, duty.R["f%d"%trip])
    return newSchedule


def greedyChargingInsert(evsp:EVSP, schedule:Schedule):
    """
    Insert the last charging nodes to position with min cost.
    """
    newSchedule = deepcopy(schedule)

    for duty in newSchedule.schedule:
        
        # insert the last charging node
        if duty.S[-2] in evsp.F:
            pass
        else:
            trip = duty.S[-2]
            duty.S.insert(-1, "f%d"%trip)
            duty.R["f%d"%trip] = greedyChargingTime(evsp, newSchedule, trip, 'd')
            newSchedule.addR("f%d"%trip, duty.R["f%d"%trip])
    return newSchedule