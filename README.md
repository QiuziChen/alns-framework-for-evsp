<h1>An ALNS Framework for EVSP</h1>

This project provides an **Adaptive Large Neighborhood Search (ALNS)** framework for (single depot & charging station) **electric vehicle scheduling problem (EVSP)**.

Package requirements, data structure and details of algorithm design will be introduced below. A simple tutorial will help you better understand how to use the framework to solve EVSP and extend it by designing your own destroy and repair operators.

# Table of Contents

- [Table of Contents](#table-of-contents)
- [1 Background knowledge](#1-background-knowledge)
  - [1.1 EVSP](#11-evsp)
    - [1.1.1 Problem Description](#111-problem-description)
    - [1.1.2 Assumptions](#112-assumptions)
    - [1.1.3 Notations](#113-notations)
  - [1.2 ALNS](#12-alns)
- [2 Structure of the framework](#2-structure-of-the-framework)
  - [2.1 Data structure](#21-data-structure)
    - [2.1.1 `EVSP`](#211-evsp)
    - [2.1.2 `Duty`](#212-duty)
    - [2.1.3 `Schedule`](#213-schedule)
  - [2.2 Algorithm components](#22-algorithm-components)
- [3 Tutorial](#3-tutorial)
  - [3.1 Input data](#31-input-data)
  - [3.2 Create model](#32-create-model)
  - [3.3 Solve](#33-solve)
  - [3.4 Develop your own operators](#34-develop-your-own-operators)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

# 1 Background knowledge

> Detailed information and explanation of the model and algorithm can be found in my article <https://doi.org/10.1016/j.trd.2023.103724>.

## 1.1 EVSP

### 1.1.1 Problem Description

### 1.1.2 Assumptions

1. **Single depot & charging station**: Vehicles are charged at the same charging station during operation, which is reasonable because we only consider the single depot operation mode.

2. **Fixed charging duration**: The charging duration of each charging event is assumed fixed for the ease of formulation and calculation. Note that the duration is not directly defined as one parameter, but defined by param `delta` and `U`, which means the minimum time interval and the number of interval in a fixed charging duration, respectively.

3. **Fully night charging**: Vehicles will be fully charged at the depot after finishing all tasks for the day to ensure that vehicles have enough power for the next day’s operation. Charging resources at the depot are assumed sufficient.

### 1.1.3 Notations

## 1.2 ALNS

# 2 Structure of the framework

## 2.1 Data structure

### 2.1.1 `EVSP`

An EVSP object is used to initialize and store the *timetable* and *network params*. Users should first initialize an EVSP object with the timetale and operating params. Then use functions to input other information.

- `__init__()`: Initialize function, including the following attributes:
  - `timetable`
  - `batteryLB`
  - `batteryUB`
  - `stationCap`
  - `delta`
  - `U`
  - `lineChange`

- `setVehTypes()`: Set vehicle types info, including battery capacity dict `E_k`. If users want to consider capacity-related consumptions, then set `capRelatedCons=True`, define bench capacity `benchCap` and consumption increasing rate `consIncRate` ($kWh\cdot km^{-1} / kWh$). Note that this consideration is based on the assumption that energy consumption rate of different veh types is linearly related to battery capaicty. A default value is provided referring to existing study.
- `setCosts()`: Set costs, including vehicle cost `c_k`, electricity cost `c_e` and labor (time-related) cost `c_t`. The labor or time-related cost is assume fixed.  *Time-of-Use policy is not yet available.*
- `setChargingFunc()`: Set charging functions. Either linear or piecewise linear functions are acceptable.
- `createModel()`: Create model including sets, nodes, arcs and time division params.
- `plotChargingFunc()`: Plot charging function curve according to the input.
- `printParams()`: Display model parameters.

### 2.1.2 `Duty`

### 2.1.3 `Schedule`

## 2.2 Algorithm components

# 3 Tutorial

## 3.1 Input data

## 3.2 Create model

## 3.3 Solve

## 3.4 Develop your own operators

