<h1>An ALNS Framework for EVSP</h1>

This project provides an Adaptive Large Neighborhood Search (ALNS) framework for (single depot & charging station) electric vehicle scheduling problem (EVSP).

The package requirements, data structure and details of algorithm design will be introduced below. A simple tutorial will help you better understand how to use the framework to solve EVSP and extend it by designing your own destroy and repair operators.

---

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
    - [2.1.1 `EVSPClass`](#211-evspclass)
    - [2.1.2 `DutyClass`](#212-dutyclass)
    - [2.1.3 `ScheduleClass`](#213-scheduleclass)
  - [2.2 Algorithm components](#22-algorithm-components)
- [3 Tutorial](#3-tutorial)
  - [3.1 Input data](#31-input-data)
  - [3.2 Create model](#32-create-model)
  - [3.3 Solve](#33-solve)
  - [3.4 Develop your own operators](#34-develop-your-own-operators)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

---

# 1 Background knowledge

## 1.1 EVSP

### 1.1.1 Problem Description

### 1.1.2 Assumptions

1. **Fixed charging duration**: the charging duration of each charging event is assumed fixed for the ease of formulation and calculation. Note that the duration is not directly defined as one parameter, but defined by param `delta` and `U`, which means the minimum time interval and the number of interval in a fixed charging duration, respectively.

2. **Fixed charging power**:

### 1.1.3 Notations

## 1.2 ALNS

---

# 2 Structure of the framework

## 2.1 Data structure

### 2.1.1 `EVSPClass`

### 2.1.2 `DutyClass`

### 2.1.3 `ScheduleClass`

## 2.2 Algorithm components

---

# 3 Tutorial

## 3.1 Input data

## 3.2 Create model

## 3.3 Solve

## 3.4 Develop your own operators

