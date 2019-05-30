# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 19:25:17 2016

@author: ikatechis
"""

import numpy as np
import matplotlib.pyplot as plt
from os import listdir
import os
from scipy import signal

def make_differences(trace, Ndif=2):
    differences = np.zeros((Ndif, len(trace)))
    for nd in range(Ndif):
        for i, s in enumerate(trace):
            if i < len(trace)-nd-1:
                differences[nd, i+nd] = trace[i+nd+1] - trace[i]  # the first row will remain zeros
    return differences


def stepfinder(trace, threshold=100, include_start=True,
               include_end=True, max_steps=20):
    trace = np.copy(trace)
    if include_start:
        trace[0] = 0
        trace[1] = 0
    if include_end:
        trace[-1] = 0
        trace[-2] = 0

    start_frames = []
    stop_frames = []
    for i in range(trace.size):
        if i < len(trace)-2:
            dif1 = trace[i+1] - trace[i]
            dif2 = trace[i+2] - trace[i]

            if dif1 > threshold and dif2 > threshold\
                                and trace[i] < threshold:
                for j in range(i, len(trace)):
                    if j < len(trace)-2:
                        dif1 = trace[j+1] - trace[j]
                        dif2 = trace[j+2] - trace[j]


                        if dif1 < -threshold and dif2 < -threshold\
                                    and trace[j+2] < trace[i] + 0.33*trace[j]:
                            start_frames.append(i-1)
                            stop_frames.append(j-1)
                            break

    if not include_end and len(start_frames) == len(stop_frames) + 1: # if the
            start_frames = start_frames[:-1] # exclude the last start_frame

    if len(start_frames) != len(stop_frames):  # sometimes 2 consecutive frames both satisfy the threshold condition for very big jumps
        start_temp = np.copy(start_frames)
        stop_temp = np.copy(stop_frames)
        for i, start in enumerate(start_temp):
            if  start_temp[i] - start_temp[i-1] == 1:
                start_frames.remove(start)
        for i, stop in enumerate(stop_temp):
            if  stop_temp[i] - stop_temp[i-1] == 1:
                stop_frames.remove(stop)

    if len(start_frames) != len(stop_frames): # if the problem remains
        print ("something is wrong")
        print ("start frames: "+str(start_frames))
        print ("stop frames: "+str(stop_frames))
        return {"start_frames": start_frames, "stop_frames": stop_frames}

    elif len(start_frames) > max_steps:
        print ("Found more steps than the limit of "+str(max_steps))
        return {"start_frames": start_frames, "stop_frames": stop_frames}
    else:
#        print "steps found: " + str(len(start_frames))
        res={ "start_frames": start_frames,
             "stop_frames": stop_frames,
             "threshold": threshold}
        return res


def plot_steps(trace="red", exposure_time=0.1, steps={},
               name="molecule_0", display_plot=False,
               save_plot=True, save_folder="./saved_plots"):

    Nframes = trace.size
    time = np.linspace(0, Nframes*exposure_time, Nframes)
    if not display_plot:
        plt.ioff()
    plt.figure(name, figsize=(10, 4))


    if "start_times" in steps.keys():
        start_times = steps["start_times"]
        stop_times = steps["stop_times"]
        for start, stop in zip(start_times, stop_times):
            plt.axvline(start, c="green", lw=2, ls="-.")
            plt.axvline(stop, c="red", lw=1, ls="--")
    plt.plot(time, trace, "k", lw=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Counts")
    plt.xlim((min(time), max(time)))
    plt.tight_layout()
    if save_plot:
        if save_folder not in listdir("."):
            os.mkdir(save_folder)
        plt.savefig("./"+save_folder+"/"+name)
        if not display_plot:
            plt.close()
            plt.pause(0.001)
    plt.ion()



#read_selected = True
#thresholds = [100]
#differences = ["2"]
#
#
#os.chdir("G:/TIRF Data/collected")
#
#if read_selected:
#    dirs = []
#    for path, subdirs, files in os.walk("."):
#
#        for name in subdirs:
#            if "selected" in name:
#                dirs.append(os.path.join(path, name))
#
#if not read_selected:
#    dirs = []
#    for d in os.listdir("."):
#        dirs.append(os.path.abspath(d))
#
#for d in dirs:
#    os.chdir(d)
#    for thres in thresholds:
#        for Ndif in differences:
#            threshold = thres
#            if read_selected:
#                os.chdir("..")
#                name = d[d.find("hel"):]
#                dwell_times = analyzer(name, threshold, read_selected=read_selected, Ndif=Ndif)
#                plt.figure("Dwell-times histogram - "+name)
#                plt.hist(dwell_times, bins=30)
#                plt.savefig("./dwell_times_threshold_"+str(threshold)+"_selected_"+Ndif+"dif_{}".format(name))
#                plt.close()
#
#            if not read_selected:
#                names = [n[:n.find(".traces")] for n in os.listdir(".") if ".traces" in n]
#                for name in names:
#                    dwell_times = analyzer(name, threshold, read_selected=read_selected, Ndif=Ndif)
#
#                    plt.figure("Dwell-times histogram - "+name)
#                    plt.hist(dwell_times, bins=30)
#                    plt.savefig("./dwell_times_threshold_"+str(threshold)+"_selected_"+Ndif+"dif_{}".format(name))
#                    plt.close()
#    os.chdir("..")


#
#    for i in range(len(acceptor)):
#    plt.figure(data["names"][i])
#    plt.plot(time, acceptor[i])
#    plt.show()


#trace = acceptor[0]
#plt.figure("Trace")
#plt.plot(trace)
#trace_filt = signal.savgol_filter(trace, 11, 2)
#plt.plot(trace_filt)
#plt.figure()
#plt.hist(trace, bins=100)

#def check_differences(trace, threshold, Ndif=4):
#    for i, t in enumerate(trace):
#        if i <= len(trace) - Ndif+1:
#            dif = [trace[i+j] - t for j in range(1,Ndif+1)]
#            b_up = []
#            b_down = []
#            for d in dif:
#                if d > threshold and t < threshold:
#                    b_up.append(True)
#                elif d < -threshold:
#                    b.append(False)
#
#            if all(b):
#                print "step at "+str(i)
#                print dif
#                print b