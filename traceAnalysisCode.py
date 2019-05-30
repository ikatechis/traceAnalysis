# -*- coding: utf-8 -*-
"""
Created on Fri Sep 14 15:24:46 2018

@author: ivoseverins
"""

import os
import re # Regular expressions
import warnings
import numpy as np
np.seterr(divide='ignore', invalid='ignore')
import pandas as pd
import matplotlib.pyplot as plt
import itertools
from threshold_analysis_v2 import stepfinder
# Use the following instead of: import matplotlib as mpl
#from matplotlib import use
#use('WXAgg')
import pickle

class Experiment:
    def __init__(self, mainPath, exposure_time=None):
        self.name = os.path.basename(mainPath)
        self.mainPath = mainPath
        self.files = list()
        self.Ncolours = 2
        self.exposure_time = exposure_time

        os.chdir(mainPath)

        self.addAllFilesInMainPath()

    @property
    def molecules(self):
        return [molecule for file in self.files for molecule in file.molecules]

    @property
    def selectedFiles(self):
        return [file for file in self.files if file.isSelected]
    @property
    def selectedMoleculesInSelectedFiles(self):
        return [molecule for file in self.selectedFiles for molecule in file.selectedMolecules]
    @property
    def selectedMoleculesInAllFiles(self):
        return [molecule for file in self.files for molecule in file.selectedMolecules]

    def addAllFilesInMainPath(self):
        # Only works/tested for files in the main folder for now

        for root, dirs, fileNames in os.walk('.', topdown=False):

            for fileName in fileNames:
                    print(root)
                    print(fileName)

                    self.addFile(root, fileName)

            for name in dirs:
                warnings.warn('Import of files in subfolders does not work properly yet')
                print(os.path.join(root, name))

    def addFile(self, relativePath, fileName):
        fileNameSearch = re.search('(hel[0-9]*)(.*\..*)', fileName)

        if fileNameSearch:
            name, extension = fileNameSearch.groups()

            fullPath = os.path.join(relativePath, name)

            # Test whether file is already in experiment
            for file in self.files:
                if file.fullPath == fullPath:
                    foundFile = file
                    break
            else:
                foundFile = None

            # If not found: add file and extension, or if the file is already there then add the extention to it.
            # If the file and extension are already imported, display a warning message.
            if not foundFile:
                self.files.append(File(relativePath, name, self, self.exposure_time))
                self.files[-1].addExtension(extension)
            else:
                if extension not in foundFile.extensions:
                    foundFile.addExtension(extension)
                else:
                    warnings.warn(fullPath + extension + ' already imported')
        else:
            warnings.warn('FileName ' + fileName + ' not added, filename should contain hel...')


    def histogram(self, axis = None, fileSelection = False, moleculeSelection = False, makeFit = False):
        #files = [file for file in exp.files if file.isSelected]
        #files = self.files

        if (fileSelection & moleculeSelection):
            histogram([molecule for file in self.selectedFiles for molecule in file.selectedMolecules], axis, makeFit)
        elif (fileSelection & (not moleculeSelection)):
            histogram([molecule for file in self.selectedFiles for molecule in file.molecules], axis, makeFit)
        elif ((not fileSelection) & moleculeSelection):
            histogram([molecule for file in self.files for molecule in file.selectedMolecules], axis, makeFit)
        else:
            histogram([molecule for file in self.files for molecule in file.molecules], axis, makeFit)


    def select(self):
        for molecule in self.molecules:
            molecule.plot()
            input("Press enter to continue")

class File:
    def __init__(self, relativePath, name, experiment, exposure_time):
        self.relativePath = relativePath
        self.name = name
        self.extensions = list()
        self.experiment = experiment
        self.molecules = list()
        self.exposure_time = exposure_time  #Here the exposure time is given but it should be found from the log file if possible

        self.isSelected = False

    @property
    def fullPath(self):
        return os.path.join(self.relativePath, self.name)

    @property
    def coordinates(self):
        return np.concatenate([[molecule.coordinates[0, :]
                                for molecule in self.molecules]])

    @property
    def selectedMolecules(self):
        return [molecule for molecule in self.molecules if molecule.isSelected]

    def addExtension(self, extension):
        self.extensions.append(extension)
        print(extension)
        importFunctions = {'.pks'        : self.importPksFile,
                           '.traces'     : self.importTracesFile,
                           '.sim'       : self.importSimFile
                           }

        importFunctions.get(extension, print)()
#        if extension == '.pks':
            #self.importPksFile()

    def importPksFile(self):
        print()
        # Background value stored in pks file is not imported yet
        Ncolours = self.experiment.Ncolours
        pks = np.genfromtxt(self.name + '.pks', delimiter='      ')
        Ntraces = np.shape(pks)[0]

        if not self.molecules:
            for molecule in range(0, Ntraces, Ncolours):
                self.addMolecule()

#        for trace in range(0, Ntraces, Ncolours):
#            coordinates = pks[trace:(trace+Ncolours),1:3]
#            self.addMolecule(coordinates)

        for i, molecule in enumerate(self.molecules):
            molecule.coordinates = pks[(i*Ncolours):((i+1)*Ncolours), 1:3]

    def importTracesFile(self):
        Ncolours = self.experiment.Ncolours
        file = open(self.name + '.traces', 'r')
        self.Nframes = np.fromfile(file, dtype=np.int32, count=1).item()
        Ntraces = np.fromfile(file, dtype=np.int16, count=1).item()
        if not self.molecules:
            for molecule in range(0, Ntraces, Ncolours):
                self.addMolecule()

        rawData = np.fromfile(file, dtype=np.int16, count=self.Nframes * Ntraces)
        orderedData = np.reshape(rawData.ravel(), (Ncolours, Ntraces//Ncolours, self.Nframes), order = 'F')

        for i, molecule in enumerate(self.molecules):
            molecule.intensity = orderedData[:,i,:]
        file.close()

    def importSimFile(self):
        file = open(self.name + '.sim', 'rb')
        self.data = pickle.load(file)
        red, green  = self.data['red'], self.data['green']
        Ntraces = red.shape[0]
        self.Nframes = red.shape[1]

        if not self.molecules:
            for molecule in range(0, Ntraces):
                self.addMolecule()

        for i, molecule in enumerate(self.molecules):
            molecule.intensity = np.vstack((green[i], red[i]))
        file.close()

    def addMolecule(self):
        self.molecules.append(Molecule(self))
        self.molecules[-1].index = len(self.molecules)  # this is the molecule number

    def histogram(self):
        histogram(self.molecules)

    def importExcel(self, filename=None):
        if filename is None:
            filename = self.name+'_steps_data.xlsx'
        try:
            steps_data = pd.read_excel(filename, index_col=[0,1],
                                            dtype={'kon':np.str})       # reads from the 1st excel sheet of the file
        except FileNotFoundError:
            return
        molecules = steps_data.index.unique(0)
        indices = [int(m.split()[-1]) for m in molecules]
        for mol in self.molecules:
            if mol.index not in indices:
                continue
            mol.steps = steps_data.loc[f'mol {mol.index}']
            k = [int(i) for i in mol.steps.kon[0]]
            mol.kon_boolean = np.array(k).astype(bool).reshape((3,3))


class Molecule:

    def __init__(self, file):
        self.file = file
        self.index = None
        self.coordinates = None
        self.intensity = None

        self.isSelected = False

        self.steps = None  #Defined in other classes as: pd.DataFrame(columns=['frame', 'trace', 'state', 'method','thres'])
        self.kon_boolean = None  # 3x3 matrix that is indicates whether the kon will be calculated from the beginning, in-between molecules or for the end only

    def I(self, emission, Ioff=0):
        return self.intensity[emission, :] - Ioff

    def E(self, Imin=0, alpha=0):  # alpha correction is not implemented yet, this is just a reminder
        red = np.copy(self.I(1))
        green = self.I(0)
        np.putmask(red, red<Imin, 0)  # the mask makes all elements of acceptor that are below the Imin zero, for E caclulation
        return (red - alpha*green) / (green + red - alpha*green)

    def plot(self):
        plt.plot(self.intensity[0,:], 'g')
        plt.plot(self.intensity[1,:], 'r')
        plt.show()

    @property
    def find_steps(self):
        return stepfinder


def histogram(input, axis, makeFit = False):
    if not input: return None
    if not axis: axis = plt.gca()
    #    if not isinstance(input,list): input = [input]
#
#    molecules = list()
#
#    for i in input:
#        if isinstance(i, Molecule):
#            molecules.append(i)
#        else:
#            molecules.append(i.molecules)
    molecules = input
    data = np.concatenate([molecule.E() for molecule in molecules])
    axis.hist(data,100, range = (0,1))

    if makeFit:
        fit_hist(data, axis)


def fit_hist(data, axis):

    hist, bin_edges = np.histogram(data,100, range = (0,1))
    bin_centers = (bin_edges[0:-1]+bin_edges[1:])/2

    #plt.plot(bin_centers,hist)

    from scipy.signal import butter
    from scipy.signal import filtfilt
    b, a = butter(2, 0.2, 'low')
    output_signal = filtfilt(b, a, hist)
    plt.plot(bin_centers, output_signal)

    from scipy.signal import find_peaks
    peaks, properties = find_peaks(output_signal, prominence=5, width=7) #prominence=1
    plt.plot(bin_centers[peaks], hist[peaks], "x")


    def func(x, a, b, c, d, e, f):
        return a * np.exp(-(x-b)**2/(2*c**2)) + d * np.exp(-(x-e)**2/(2*f**2))

    from scipy.optimize import curve_fit
    popt, pcov = curve_fit(func, bin_centers, hist, method = 'trf',
                           p0 = [hist[peaks[0]],bin_centers[peaks[0]],0.1,hist[peaks[1]],bin_centers[peaks[1]],0.1], bounds = (0,[np.inf,1,1,np.inf,1,1]))

    axis.plot(bin_centers,func(bin_centers, *popt))
    #plt.plot(bin_centers,func(bin_centers, 10000,0.18,0.1,5000,0.5,0.2))

#uniqueFileNames = list(set([re.search('hel[0-9]*',fileName).group() for fileName in fileNames]))

"""

for root, dirs, files in os.walk('..', topdown=False):
	for name in files:
		print(os.path.join(root, name))
		print(root)
		print(name)

	for name in dirs:
		print(os.path.join(root, name))



for root, dirs, files in os.walk('..', topdown=False):
	print(files)

"""
