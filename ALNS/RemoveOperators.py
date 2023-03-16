from EVSPModel import Schedule, EVSP

import random
import pandas as pd
from copy import deepcopy


"""
@author: Chen Qiuzi
"""


def randomRemoval(evsp:EVSP, schedule:Schedule, n:int):
    """
    Remove n trips from schedule randomly.
    """
    # removedSchedule
    removedSchedule = deepcopy(schedule)
    tripBank = random.sample(evsp.T, n)  # generate trip bank
    
    removeList = []
    for duty in removedSchedule.schedule:  # remove trips and charging
                
        chargingBank = list(set(['f%d'%i for i in tripBank if 'f%d'%i in duty.S]))
        duty.S = list(filter(lambda x: (x not in tripBank) and (x not in chargingBank), duty.S))
        for f in chargingBank:
            r_ = duty.R.pop(f)

        if len(duty.S) <= 4:  # duty too short
            tripBank.extend([i for i in duty.S[1:-1] if type(i)==int])
            removeList.append(duty)

    for duty in removeList:
        removedSchedule.delDuty(duty)

    return tripBank, removedSchedule


def timeRelatedRemoval(evsp:EVSP, schedule:Schedule, n:int):
    """
    Remove n trips from schedule according time relation.
    """
    # removedSchedule = schedule
    removedSchedule = deepcopy(schedule)
    tripBank = random.sample(evsp.T, 1)  # generate first random index
    while len(tripBank) < n:
        i = random.choice(tripBank)
        unremoved = list(set(evsp.T) - set(tripBank))  # trips unremoved
        correlation = {j:abs(evsp.s_i[i]-evsp.s_i[j])+abs(evsp.t_i[i]-evsp.t_i[j]) for j in unremoved}
        j = min(correlation, key=correlation.get)  # most related trip index
        tripBank.append(j)
    
    removeList = []
    for duty in removedSchedule.schedule:

        chargingBank = list(set(['f%d'%i for i in tripBank if 'f%d'%i in duty.S]))
        duty.S = list(filter(lambda x: (x not in tripBank) and (x not in chargingBank), duty.S))
        for f in chargingBank:
            r_ = duty.R.pop(f)

        if len(duty.S) <= 4:  # duty too short
            tripBank.extend([i for i in duty.S[1:-1] if type(i)==int])
            removeList.append(duty)
    for duty in removeList:
        removedSchedule.delDuty(duty)

    return tripBank, removedSchedule


def neighborRemoval(evsp:EVSP, schedule:Schedule, n:int):
    """
    Remove n trips from schedule according to neighbor relation.
    """
    
    removedSchedule = deepcopy(schedule)
    tempSchedule = deepcopy(schedule)
    tripBank = []

    for duty in tempSchedule.schedule:
        duty.S = list(filter(lambda x: (type(x)==int or len(x)<2), duty.S))  # remove charging nodes

    while len(tripBank) < n:
        unremoved = list(set(evsp.T) - set(tripBank))
        i = random.choice(unremoved)  # generate random trip i
        tripBank.append(i)
        for duty in tempSchedule.schedule:
            if i in duty.S:  # duty with trip i
                index = duty.S.index(i,1,-1)  # index of i in duty
                if (index-1 != 0) and (duty.S[index-1] not in tripBank):
                    tripBank.append(duty.S[index-1])
                if (index+1 != len(duty.S)-1) and (duty.S[index+1] not in tripBank):  # the penultimate one
                    tripBank.append(duty.S[index+1])
                break 

    removeList = []
    for duty in removedSchedule.schedule:
        
        chargingBank = list(set(['f%d'%i for i in tripBank if 'f%d'%i in duty.S]))
        duty.S = list(filter(lambda x: (x not in tripBank) and (x not in chargingBank), duty.S))
        for f in chargingBank:
            r_ = duty.R.pop(f)
        
        if len(duty.S) <= 4:  # duty too short
            tripBank.extend([i for i in duty.S[1:-1] if type(i)==int])
            removeList.append(duty)
    for duty in removeList:
        removedSchedule.delDuty(duty)
    
    return tripBank, removedSchedule
