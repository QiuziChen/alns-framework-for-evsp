from EVSPModel.EVSPClass import EVSP


"""
@author: Chen Qiuzi
"""


def calCharge(evsp:EVSP, k, y0):
    """
    Calculate charging volume of one recharging activity.
    """
    if evsp.chargingFuncType == 'linear':
        return min(evsp.E_k[k] - y0, evsp.v_k[k] * evsp.U * evsp.delta)
    else:
        E = evsp.E_k[k]
        a_b = evsp.a_kb[k]  # soc of break points / 1
        c_b = evsp.c_kb[k]  # time of break points / min
        B = evsp.B_k[k]  # set of break points
        a0 = y0/E  # origin soc

        if a0 < 0:  # energy infeasible condition
            rate = [(a_b[i+1]-a_b[i])/(c_b[i+1]-c_b[i]) for i in B[:-1]]
            c_ = a0 / rate[0]  # time to charge to 0%
            c1 = evsp.U * evsp.delta - c_
            if c1 <= 0:
                return evsp.U * evsp.delta * rate[0]
            else:
                interval = [i for i in B[:-1] if c_b[i]<= c1 <c_b[i+1]][0]
                a1 = (c1 - c_b[interval]) * rate[interval] + a_b[interval]
                return (a1 - a0) * E  # kWh
        else:
            if a0 in a_b:
                c0 = [c_b[i] for i in B if a_b[i]==a0][0]  # origin time
            else:
                rate = [(a_b[i+1]-a_b[i])/(c_b[i+1]-c_b[i]) for i in B[:-1]]
                interval = [i for i in B[:-1] if a_b[i]<= a0 <a_b[i+1]][0]
                c0 = (a0 - a_b[interval]) / rate[interval] + c_b[interval]
            c1 = c0 + evsp.U * evsp.delta
            interval = [i for i in B[:-1] if c_b[i]<= c1 <c_b[i+1]][0]
            a1 = (c1 - c_b[interval]) * rate[interval] + a_b[interval]
            return (a1 - a0) * E  # kWh
