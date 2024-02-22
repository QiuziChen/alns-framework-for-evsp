<h1>An ALNS Framework for EVSP</h1>

This project provides an **Adaptive Large Neighborhood Search (ALNS)** framework for (single depot & charging station) **electric vehicle scheduling problem (EVSP)**.

Data structure and details of algorithm design will be introduced below. A simple tutorial will help you better understand how to use the framework to solve EVSP.

# Table of Contents

- [Table of Contents](#table-of-contents)
- [1 Background knowledge](#1-background-knowledge)
  - [1.1 EVSP](#11-evsp)
    - [1.1.1 Problem Description](#111-problem-description)
    - [1.1.2 Assumptions](#112-assumptions)
  - [1.2 ALNS](#12-alns)
- [2 Structure of the framework](#2-structure-of-the-framework)
  - [2.1 Data structure](#21-data-structure)
    - [2.1.1 `EVSP`](#211-evsp)
    - [2.1.2 `Duty`](#212-duty)
    - [2.1.3 `Schedule`](#213-schedule)
  - [2.2 Algorithm components](#22-algorithm-components)
    - [2.2.1 `ALNS`](#221-alns)
    - [2.2.2 `InitialSolution`](#222-initialsolution)
    - [2.2.3 `WeightsManagement`](#223-weightsmanagement)
    - [2.2.4 `RemoveOperators`](#224-removeoperators)
    - [2.2.5 `InsertOperators`](#225-insertoperators)
- [3 Tutorial](#3-tutorial)
  - [3.1 Input data](#31-input-data)
  - [3.2 Solve](#32-solve)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

---

# 1 Background knowledge

> Detailed information and explanation of the model and algorithm can be found in my article: <https://doi.org/10.1016/j.trd.2023.103724>.

## 1.1 EVSP

### 1.1.1 Problem Description

We consider a single-depot bus network with one charging station and multiple types of BEBs. At the beginning of the operation, vehicles are dispatched from the depot to terminals for the day’s service. After finishing all tasks, they return to the depot to park and get charged. During the operation, vehicles are allowed to dwell or park at terminals between service tasks and get recharged at the charging station, which is integrated into the terminal. The EVSP aims to find the optimal vehicle schedule, charging plan and fleet composition of the network.

### 1.1.2 Assumptions

1. **Single depot & charging station**: Vehicles are charged at the same charging station during operation, which is reasonable because we only consider the single depot operation mode.

2. **Fixed charging duration**: The charging duration of each charging event is assumed fixed for the ease of formulation and calculation. Note that the duration is not directly defined as one parameter, but defined by param `delta` and `U`, which means the minimum time interval and the number of interval in a fixed charging duration, respectively.

3. **Fully night charging**: Vehicles will be fully charged at the depot after finishing all tasks for the day to ensure that vehicles have enough power for the next day’s operation. Charging resources at the depot are assumed sufficient.

## 1.2 ALNS

The ALNS algorithm [(Ropke & Pisinger, 2006)](https://doi.org/10.1287/trsc.1050.0135), which is widely used for varied kinds of vehicle routing problems (VRP) with high efficiency, is employed to solve the EVSP. The ALNS explores the neighborhood by **destroying** and **repairing** the current solution to increase the search range of the search space, and improve the probability of obtaining a better solution. A **greedy insertion algorithm** is used to construct initial solutions. A **roulette wheel selection** and an **adaptive weight adjustment method** are employed for operator selection, and the **simulated annealing** algorithm is used as the acceptance criteria. The algorithm terminates when $n$ iterations are executed, or $n'$ iterations occur without improvements.

# 2 Structure of the framework

## 2.1 Data structure

The framework uses three class to store the data of an EVSP, including

- `EVSP`: containing timetable and network parameters of an EVSP.
- `Duty`: containing information of a trip chain (a schedule of one single bus).
- `Schedule`: containing information of the schedule of the day.

### 2.1.1 `EVSP`

An EVSP object is used to initialize and store the *timetable* and *network params*. Users should first initialize an EVSP object with the timetale and operating params. Then use functions to input other information.

- `__init__()`: initialize function, including the following attributes:
  - `timetable`: start time, travel time and energy consumption of each trip
  - `batteryLB`: lower safe bound of battery remaining level (0.0-1.0)
  - `stationCap`: number of chargers in the station
  - `delta`: time interval
  - `U`: the number of interval in a fixed charging duration
  - `lineChange`: whether linechange is allowed, which means a bus can serve several lines in a day

- `setVehTypes()`: Set vehicle types info, including battery capacity dict `E_k`. If users want to consider capacity-related consumptions, then set `capRelatedCons=True`, define bench capacity `benchCap` and consumption increasing rate `consIncRate` ($kWh\cdot km^{-1} / kWh$). Note that this consideration is based on the assumption that energy consumption rate of different veh types is linearly related to battery capaicty. A default value is provided referring to existing study.
- `setCosts()`: Set costs, including vehicle cost `c_k`, electricity cost `c_e` and labor (time-related) cost `c_t`. The labor or time-related cost is assume fixed.  *Time-of-Use policy is not yet available.*
- `setChargingFunc()`: Set charging functions. Either linear or piecewise linear functions are acceptable.
- `createModel()`: Create model including sets, nodes, arcs and time division params.
- `plotChargingFunc()`: Plot charging function curve according to the input.
- `printParams()`: Display model parameters.

### 2.1.2 `Duty`

A Duty object storage the schedule of a single bus including trip nodes, charging events, and charging time assignment.

- `__init__()`: A Duty object is initialized with the following parameters:
  - `evsp`
  - `type`: vehicle type
  - `tripChain`
  - `chargingTime`
- `checkEnergyFeasibility()`: Return True if a duty can meet the energy constraint.
- `calCost()`: Calculate the cost of a duty.

### 2.1.3 `Schedule`

A Schedule object consists of a series of vehicles with their service trips and charging activities scheduled according to a given timetable.

- `__init__()`: A Schedule object is initialized with the following parameters:
  - `evsp`
  - `schedule`: initial schedule, a list of duties (or empty list)
  - `R`: initial charging time assignment, a list of time divisions
- `addDuty`, `delDuty`, `sortDuty`
- `addR`, `delR`, `updateR`
- `checkEnergyFeasibility`
- `checkCapacityFeasibility`
- `calCost`: Calculate the cost of a schedule.
- `printTimetable`: Print timetable as in the form of dataframe.
- `plotTimetable`: Plot timetable as an image.
- `costBar`: Return a barplot of each item of cost.
- `chargingPowerPlot`: Display the variation of charging power at the station.
- `chargingUsagePlot`: Display the variation of the number of buses in the charging station.

## 2.2 Algorithm components

### 2.2.1 `ALNS`

An `ALNS` object stores the parameters and results of the algorithm, and all the components are aggregated into it.

- `__init__()`:
  - `evsp`: an `EVSP` object.
  - `iterMax`: the maximum iteration number.
  - `nMax`: the maximum number of trips to remove in one iteration.
  - `nMin`: the minimum number of trips to remove in one iteration.
  - `T0`: initial temperature of simulated annealing.
  - `alpha`: cooling rate of the temperature (0,1).
  - `r`: reaction factor when update weights (0,1).
  - `enePenalty`: penalty when violating energy constraints.
  - `capPenalty`: penalty when violating capacity constraints.
  - `chargeProb`: probability of charging insertion for random insertion.
  - `segLength`: segment length for updating weights.
  - `terminate`: whether to terminate when no improvement.
  - `terminateLength`: length of iteration to check improvement.
  - `printLog`: whether to print solving log.
- `solve`: Aggregate all components to perform the solving procedure.
- `plotWeights`: Display historical variation of weights of different operators.
- `plotEvaluation`: Display historical cost variation.

### 2.2.2 `InitialSolution`

The `InitialSolution` profile contains two initialization methods:

- `initialize`: Provide initlaized feasible solution using greedy heuristic.
- `initialize_nighCharge`: Provide initlaized feasible solution for night charging mode in which buses are not allowed to get charged during daytime.

### 2.2.3 `WeightsManagement`

A `Weights` object is used to store the scores and weights of remove operators and insert operators, and select operators using roulette wheel.

### 2.2.4 `RemoveOperators`

Three remove operators are provided:

- `randomRemoval`
- `timeRelatedRemoval`
- `neighborRemoval`

### 2.2.5 `InsertOperators`

Three insert operators are provided:

- `randomInsert`
- `greedyInsert`

# 3 Tutorial

## 3.1 Input data

```python
import pandas as pd
from EVSPModel import EVSP

# read timetable
timetable = pd.read_excel('Data\T275_Ave.xlsx')

# initialize evsp object
evsp = EVSP(timetable)

# set parameters
evsp.setVehTypes()
evsp.setCosts()
evsp.setChargingFunc()

# create model
evsp.createModel()
```

Using the above code can initalize an `EVSP` object with the default parameters. However, all the parameters including operation, network and vehicle parameters can be self-defined. The parameters and charging function can be display by the following code.

```python
evsp.printParams()
```

```python
evsp.plotChargingFunc()
```

![chargingFunc](figures/plot%20charging%20func-linear.png)

## 3.2 Solve

The solving procedure is quite simple.

```python
alns = ALNS(evsp)
alns.solve()
```

Functions for displaying the results are also provided.

```python
alns.plotWeights()
```

![weights](figures/plot%20weights.png)

```python
alns.plotEvaluation()
```

![evaluation](figures/plot%20evaluation.png)

```python
bestS = alns.bestSchedule  # the best schedule stored in the ALNS object
bestS.plotTimetable()
```

![schedule](figures/plot%20schedule.png)

```python
bestS.costBar()
```

![costbar](figures/cost%20bar.png)

```python
bestS.chargerUsagePlot()
```

![charger usage](figures/charger%20usage.png)

```python
bestS.chargingPowerPlot()
```

![charging power](figures/charging%20power.png)
