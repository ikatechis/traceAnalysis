# -*- coding: utf-8 -*-
"""
Created on Tue May 28 12:05:13 2019

@author: iason
"""
import numpy as np
import sys

#sys.path.append('../traceAnalysis - Ivo')
import pandas as pd
import os
import matplotlib.pyplot as plt
import traceAnalysisCode as analysis

os.chdir(os.path.dirname(os.path.abspath(__file__)))
#mainPath = './traces'
mainPath = './simulations'
exp = analysis.Experiment(mainPath, 0.1)
file = exp.files[0]
df = file.importExcel()
mol = file.molecules[2]
time = np.arange(0,len(mol.I(0))*exp.exposure_time, exp.exposure_time)

dwelltimes = []

for mol in file.molecules:
    if mol.steps is not None:
        print(mol.index)
        times = mol.steps.time.sort_values().values
        if times.size % 2 != 0:
            continue
        times1 = times.reshape((int(times.size/2), 2))
        dwells = np.diff(times1, axis=1).flatten()
        dwelltimes.append(dwells)
dwelltimes = np.concatenate(dwelltimes).ravel()

#
plt.hist(dwelltimes, bins=20, density=True)
time = np.arange(0, 20, 0.1)
tau = np.average(dwelltimes)
exp = 1/tau*np.exp(-time/tau)
plt.plot(time, exp)
plt.title(f'tau = {tau:.1f} s')





#for d in dwells:
#    if times[0] <0.1 and d == dwells[0]:
#        dwells_l.append(d)
#    if times[-1] >= 299.7 and d == dwells[-1]:
#        dwells_r.append(d)
#    else:
#        dwells_m.append(d)
## calculate tau_on
##times = np.insert(times, 0, 0)
#tau_on = np.append(np.insert(times, 0, 0), 300)
#tau_on = np.diff(times)[::2]
#
#for i, t in enumerate(tau_on):
#    if i == 0 and t > 0.1:
#        tau_on_l.append(t)
#    if i == (len(tau_on) -1) and t > 0.3:
#        dwells_r.append(t)
#    else:
#        tau_on_m.append(t)

