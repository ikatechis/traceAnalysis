# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 23:12:58 2019

@author: iason
"""

import numpy as np
import sys

sys.path.append('../traceAnalysis - Ivo')
import traceAnalysisCode as analysis
import pandas as pd
import os
import itertools
import matplotlib.pyplot as plt
import matplotlib.widgets
import seaborn as sns
from cursor_matplotlib import SnaptoCursor
#plt.rcParams['toolbar'] = 'toolmanager'
#from matplotlib.backend_tools import ToolBase
#mainPath = r'D:\ivoseverins\SURFdrive\Promotie\Code\Python\traceAnalysis\twoColourExampleData\HJ A'


class Draw_lines(object):
    def __init__(self, fig, iplot_radio):
        self.lines = []
        self.fig = fig
        self.radio = iplot_radio  # The InteractivePlot instance

    def onclick(self, event):
        if self.fig.canvas.manager.toolbar.mode != '':  # self.fig.canvas.manager.toolmanager.active_toggle["default"] is not None:
            return
        if event.inaxes is None:
            return
        ax = event.inaxes
        if event.button == 1:
            if ax == self.fig.get_axes()[0] or ax == self.fig.get_axes()[1]:
                sel = self.radio.value_selected*(ax == self.fig.get_axes()[0])
                sel = sel + "E"*(ax == self.fig.get_axes()[1])
                l = ax.axvline(x=event.xdata, zorder=0, lw=0.65, label="man "+sel)
                self.lines.append(l)

        if event.button == 3 and self.lines != []:
            self.lines.pop().remove()
        self.fig.canvas.draw()

    def clear_all(self, event):
        while self.lines:
            self.lines.pop().remove()
        self.fig.canvas.draw()

class InteractivePlot(object):
    def __init__(self, file):
        self.file = file
        self.mol_indx = 0  #From which molecule to start the analysis
        #  See if there are saved analyzed molecules
        self.file.load_from_excel(filename=self.file.name+'_steps_data.xlsx')

    def plot_initialize(self):
        sns.set(style="dark")
        sns.set_color_codes()
        plt.style.use('dark_background')
        self.fig, self.axes = plt.subplots(2, 1, sharex=True, figsize=(10,5))
        self.fig.canvas.set_window_title(f'Dataset: {self.file.name}')

        plt.subplots_adjust(bottom=0.23)

        # Create the axes for the widgets
        self.rax = plt.axes([0.91, 0.65, 0.08, 0.15])

        self.axcheckfret = plt.axes([0.91, 0.35, 0.08, 0.08])
        self.axcorred = plt.axes([0.95, 0.6, 0.028, 0.06])
        self.axcorgreen = plt.axes([0.95, 0.53, 0.028, 0.06])
        self.axcorrfretI = plt.axes([0.95, 0.3, 0.028, 0.06])
        self.axthrsliders = [plt.axes([0.26, 0.072, 0.10, 0.03]),
                             plt.axes([0.26, 0.033, 0.10, 0.03])]
        # Create the buttons
        self.axthresb = plt.axes([0.1, 0.03, 0.13, 0.062])  # Button to calculate dwell times by thresholding
        self.axrejb = plt.axes([0.41, 0.03, 0.07, 0.062])   # Button to reject calculated dwell times by thresholding
        self.axclearb = plt.axes([0.51, 0.03, 0.11, 0.062]) # Button to clear the clicked points (clears vlines)
        self.axthrowb = plt.axes([0.64, 0.03, 0.11, 0.062]) # Button to throw away already calculated dwell times and de-select molecule
        self.axconclb = plt.axes([0.77, 0.03, 0.15, 0.062]) # Button to conlcude analysis by saving all the calculated steps and metadata

        self.axnextb = plt.axes([0.17, 0.90, 0.065, 0.062])  # Buttons to cycle through molecules
        self.axprevb = plt.axes([0.083, 0.90, 0.08, 0.062])
        [ax.set_frame_on(False) for ax in self.fig.get_axes()[2:]]
        #  Radiobutton to select red or green
        self.radio = matplotlib.widgets.RadioButtons(self.rax, ("red", "green"))
        self.radio.circles[0].set_color("r")
        for circle in self.radio.circles: # adjust radius here. The default is 0.05
            circle.set_radius(0.07)
        self.radio.on_clicked(self.radio_manage)

        #  Connect clicking to draw lines class
        self.draw = Draw_lines(self.fig, self.radio)
        self.fig.canvas.mpl_connect('button_press_event', self.draw.onclick)
        # Create the buttons with

        bp = {'color': 'black', 'hovercolor': 'gray'}
        self.bauto = matplotlib.widgets.Button(self.axthresb,'autoThreshold' , **bp)
        self.bauto.on_clicked(self.autoThreshold_plot)
        self.brejauto = matplotlib.widgets.Button(self.axrejb,'reject' , **bp)
        self.brejauto.on_clicked(self.auto_reject)
        self.bclear = matplotlib.widgets.Button(self.axclearb,'clear clicks' , **bp)
        self.bclear.on_clicked(self.draw.clear_all)
        self.bthrow = matplotlib.widgets.Button(self.axthrowb,'throw away' , **bp)
        self.bthrow.on_clicked(self.throw_away)
        self.bconcl = matplotlib.widgets.Button(self.axconclb,'conclude analysis' , **bp)
        self.bconcl.on_clicked(self.conclude_analysis)
        self.bnext = matplotlib.widgets.Button(self.axnextb,'Next' , **bp)
        self.bnext.on_clicked(self.save_molecule)
        self.bprev = matplotlib.widgets.Button(self.axprevb,'Previous' , **bp)
        self.bprev.on_clicked(self.save_molecule)

        #  A checkbutton for fret autothreshold dwell-time calculation
        self.checkbfret = matplotlib.widgets.CheckButtons(self.axcheckfret, ["E fret"],
                                                          actives=[False])
        self.checkbfret.rectangles[0].set_color("black")
        self.checkbfret.rectangles[0].set_height( 0.2)
        [line.remove() for line in self.checkbfret.lines[0]]
        self.checkbfret.on_clicked(self.check_fret)

        #  Entryboxes for offset corrections
        corrdict = {'initial': str(0), 'color':'k', 'hovercolor': "k", 'label_pad':.2}
        corrlabels = [r'$I_{R_{off}}$', r'$I_{G_{off}}$', r'$I_{min}$']
        corraxes = [self.axcorred, self.axcorgreen, self.axcorrfretI]
        self.correntries = [matplotlib.widgets.TextBox(ax, label, **corrdict)
                            for ax, label in zip(corraxes, corrlabels)]
        [entry.on_submit(lambda _: self.plot_molecule()) for entry in self.correntries]

        #  Sliders for assigning the threshold
        self.thrsliders = []
        self.thrsliders.append(matplotlib.widgets.Slider(self.axthrsliders[0], label=r"$I_R$", valmin=0,
                                                   valmax=500, valinit=100, valfmt="%i", color="r"))
        self.thrsliders.append(matplotlib.widgets.Slider(self.axthrsliders[1], label=r"$E$", valmin=0,
                                                    valfmt="%.2f", valinit=0.5, color="b", valmax=1.0))
        [slider.vline.remove() for slider in self.thrsliders]

        self.fig.show()

    def plot_molecule(self, draw_plot=True):
        #clear the appropriate axes first
        [ax.clear() for ax in self.fig.get_axes()[:2]]
        # find the current molecule instance
        self.mol = self.file.molecules[self.mol_indx]

        # Check if molecule is selected
        if self.mol.isSelected: self.select_molecule(toggle=False)
        #load saved steps
        self.load_from_Molecule()
        # load kon if existing or assign a False 3x3 boolean
        self.prev_mol = self.file.molecules[self.mol_indx - 1]
        if all(kon is None for kon in [self.mol.kon_boolean, self.prev_mol.kon_boolean]):

            self.kon = np.zeros((3,3), dtype=bool)
        elif self.mol.kon_boolean is  None:
            self.kon = np.copy(self.prev_mol.kon_boolean)  # if no kon is defined for current molecule
        else:
            self.kon = self.mol.kon_boolean
        # update the edge color from self.kon:
        self.load_edges(load_fret=True)

        self.axes[0].set_title(f"Molecule: {self.mol.index} /{len(self.file.molecules)}")
        self.Iroff, self.Igoff, self.Imin = [float(c.text) for c in self.correntries]

        self.red = self.mol.I(1, Ioff=self.Iroff)
        self.green = self.mol.I(0, Ioff=self.Igoff)
        self.fret = self.mol.E(Imin=self.Imin)
        self.exp_time = self.file.exposure_time
        self.time = np.arange(0,len(self.red)*self.exp_time, self.exp_time)

        if not draw_plot:
            return

        self.axes[0].plot(self.time, self.green, "g", lw=.75)
        self.axes[0].plot(self.time, self.red, "r", lw=.75)

        self.axes[1].plot(self.time, self.fret, "b", lw=.75)
        self.axes[1].set_ylim((0,1.1))
        self.axes[1].set_xlim((-10, self.time[-1]))
        self.axes[1].set_xlabel("time (s)")
        # vertical lines to indicate the threshold in the two axes
        self.slidel = [ax.axhline(0, lw=1, ls=":", zorder=3, visible=False) for ax in self.axes]
        #  Creat cursor particular to the molelcule and connect it to mouse movement event
        self.cursors = []
        self.cursors.append(SnaptoCursor(self.axes[0], self.time, self.red))
        self.cursors.append(SnaptoCursor(self.axes[0], self.time, self.green))
        self.cursors.append(SnaptoCursor(self.axes[1], self.time, self.fret))
        self.connect_events_to_canvas()

        self.fig.canvas.draw()

    def connect_events_to_canvas(self):
        self.fig.canvas.mpl_connect('key_press_event', self.key_bind)
        self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_cursor)
        for cursor in self.cursors:
            self.fig.canvas.mpl_connect('axes_leave_event', cursor.leave_axis)
        self.fig.canvas.mpl_connect('axes_leave_event',
             lambda _: [[self.slidel[i].set_visible(False), self.fig.canvas.draw()] for i in [0,1]])

    def key_bind(self, event):
        k = event.key
        if k == 'a': self.autoThreshold_plot(event, find_all=False)
        if k == 'ctrl+a': self.autoThreshold_plot(event, find_all=True)
        elif k in ['left', 'right']: self.save_molecule(event, move=True)
        elif k == 'z': self.auto_reject(event)
        elif k == 'c': self.draw.clear_all(event)
        elif k in [',', '.', '/']: self.select_edge(k)
        elif k == ' ': self.select_molecule(toggle=True)
        elif k == 'r': self.radio_manage('red')
        elif k == 'g': self.radio_manage('green')
        elif k == 'e': self.check_fret('E')
        elif k == 't': self.throw_away(event)

        self.fig.canvas.draw()

    def load_from_Molecule(self):
        if self.mol.steps is None:
            return
        else:
            s = self.mol.steps
            [self.axes[0].axvline(f, zorder=0, lw=0.65, label="saved r")
             for f in s.time[s.trace == 'red'].values]
            [self.axes[0].axvline(f, zorder=0, lw=0.65, label="saved g")
             for f in s.time[s.trace == 'green'].values]
            [self.axes[1].axvline(f, zorder=0, lw=0.65, label="saved E")
             for f in s.time[s.trace == 'E'].values]

    def select_molecule(self, toggle=True, deselect=False):
        if toggle:
            self.mol.isSelected = not self.mol.isSelected
        elif deselect:
             self.mol.isSelected = False
        else:
            self.mol.isSelected = True
        title = f'Molecule: {self.mol.index} /{len(self.file.molecules)}'
        title += '  selected'*(self.mol.isSelected)
        rgba = matplotlib.colors.to_rgba
        c = rgba('g')*self.mol.isSelected + rgba('w')*(not self.mol.isSelected)
        self.axes[0].set_title(title, color=c)
        self.fig.canvas.draw()

    def throw_away(self, event):
        if self.mol.steps is not None:
            self.mol.steps = None
            lines = self.axes[0].get_lines() + self.axes[1].get_lines()
            [l.remove() for l in lines if l.get_label().split()[0] in ['man', 'thres', 'saved']]
            self.select_molecule(toggle=False, deselect=True)
            self.fig.canvas.draw()


    def save_molecule(self, event=None, move=True, draw=True):
        #  Assume acceptance of auto matically found and manually selected dwell times
        lines = self.axes[0].get_lines() + self.axes[1].get_lines()
        lines = [l for l in lines if l.get_label().split()[0] in ["man", "thres"]]
        self.mol.kon_boolean = self.kon
        if lines:
            if len(lines) % 2 != 0:
                print(f'Found an odd number of steps. Molecule {self.mol.index} not added')
                return
            if self.mol.steps is None:
                self.mol.steps = pd.DataFrame(columns=['time', 'trace', 'state',
                                                       'method','thres'])
            self.mol.isSelected = True

            for l in lines:
                method = l.get_label().split()[0]
                thres = "N/A"*(method=='man') + str(self.thrsliders[0].val)*(method =='thres')

                d = {'time': l.get_xdata()[0], 'trace': l.get_label().split()[1],
                     'state': 1, 'method': method, 'thres': thres}

                self.mol.steps= self.mol.steps.append(d, ignore_index=True)
            self.mol.steps.drop_duplicates(inplace=True)
            kon = [f'{int(i)}' for i in self.mol.kon_boolean.flatten()]
            kon = ''.join(kon)
            if 'kon' not in self.mol.steps.columns:
                kon = pd.DataFrame.from_records([{"kon": kon}])
                self.mol.steps = pd.concat([self.mol.steps, kon], axis=1)
                self.mol.steps.fillna(value='')
            else:
                self.mol.steps.loc[0, 'kon'] = kon

        if move:
            if event.inaxes == self.axnextb or event.key in ['right']:
                if self.mol_indx > len(self.file.molecules):
                    self.mol_indx = 1
                else:
                    self.mol_indx += 1
            elif event.inaxes == self.axprevb or event.key in ['left']:
                self.mol_indx -= 1

            self.plot_molecule(draw_plot=draw)

    def conclude_analysis(self, event=None, save=True):
        # Save current molecule if it was analyzed
        self.save_molecule(move=False)
        # Concatenate all steps dataframes that are not None
        mol_data = [mol.steps for mol in self.file.molecules if mol.steps is not None]
        if not mol_data:
            print('no data to save')
            return
        keys = [f'mol {mol.index}' for mol in self.file.molecules if mol.steps is not None]
        steps_data = pd.concat(mol_data, keys=keys)
        if save:
            print("steps saved")
            writer = pd.ExcelWriter(f'{self.file.name}_steps_data.xlsx')
            steps_data.to_excel(writer, self.file.name)
            writer.save()


    def autoThreshold_plot(self, event=None, find_all=False):
        self.auto_reject()
        #  Find the steps for the checked buttons
        sel = self.radio.value_selected
        color = self.red*bool(sel == "red") + self.green*bool(sel == "green")  # Select red  or green
        steps = self.mol.find_steps(color, threshold=self.thrsliders[0].val)
        l_props = {"lw": 0.75, "zorder": 5, "label": "thres "+sel}
        [self.axes[0].axvline(s*self.exp_time, **l_props) for s in steps["start_frames"]]
        [self.axes[0].axvline(s*self.exp_time, ls="--", **l_props) for s in steps["stop_frames"]]
        if self.checkbfret.get_status()[0]:
            steps = self.mol.find_steps(self.fret, threshold=self.thrsliders[1].val)
            l_props = {"lw": 0.75, "zorder": 5, "label": "thres E"}
            [self.axes[1].axvline(s*self.exp_time, **l_props) for s in steps["start_frames"]]
            [self.axes[1].axvline(s*self.exp_time, ls="--", **l_props) for s in steps["stop_frames"]]
        self.fig.canvas.draw()
        if find_all:
            for mol in self.file.molecules:
                self.autoThreshold_plot(find_all=False)
                print(f'Analyzed mol {self.mol.index} /{len(self.file.molecules)}')
                e = matplotlib.backend_bases.KeyEvent('key_press_event', self.fig.canvas, 'right')
                if mol != self.file.molecules[-1]:
                    self.save_molecule(event=e, move=True, draw=False)
                elif mol == self.file.molecules[-1]:
                    self.conclude_analysis()
                    return

    def auto_reject(self, event=None):
        for ax in self.axes:
            lines = ax.get_lines()
            [l.remove() for l in lines if l.get_label().split()[0] == 'thres']
            self.fig.canvas.draw()

    def mouse_cursor(self, event):
        if not event.inaxes :
            self.fret_edge_lock = True
            return
        ax = event.inaxes
        if ax == self.axes[0]:
            self.fret_edge_lock = True
            self.fig.canvas.mpl_connect('motion_notify_event', self.cursors[0].mouse_move)
            self.fig.canvas.mpl_connect('motion_notify_event', self.cursors[1].mouse_move)

            rad = self.radio.value_selected
            i = ['red', 'green'].index(rad)
            t, I = self.cursors[i].ly.get_xdata(), self.cursors[i].lx.get_ydata()
            try:
                labels = [rf"t = {t:.1f}, $I_R$ = {I:.0f}", rf"t = {t:.1f}, $I_G$ = {I:.0f}"]
                self.cursors[i].txt.set_text(labels[i])
            except TypeError:
                pass
            self.fig.canvas.draw()

        elif ax == self.axes[1]:
            self.fret_edge_lock = False
            self.fig.canvas.mpl_connect('motion_notify_event', self.cursors[-1].mouse_move)
            t, E = self.cursors[-1].ly.get_xdata(), self.cursors[-1].lx.get_ydata()
            try:
                self.cursors[-1].txt.set_text(f"t = {t:.1f}, E = {E:.2f}")
            except TypeError:
                pass
            self.fig.canvas.draw()

        elif ax in self.axthrsliders:
            indx = int(ax == self.axthrsliders[1])  # gives 0 if ax is upper (I) plot, 1 if ax is lower (E) plot
            self.slidel[indx].set_ydata(self.thrsliders[indx].val)
            self.slidel[indx].set_visible(True)
            self.fig.canvas.draw()


    def radio_manage(self, label):
        def update_slider(color, label):
            s = self.thrsliders[0]
            s.poly.set_color(color); s.label.set(text=label)

        indx = int(label == 'green')  # 1 if green, 0 if red
        self.axes[0].get_lines()[not indx].set_zorder((not indx)+2)
        self.axes[0].get_lines()[indx].set_zorder(indx)
        self.radio.circles[indx].set_color(label[0])
        self.radio.circles[not indx].set_color("black")
        update_slider(label[0], r"$I_G$"*bool(indx)+r"$I_R$"*bool(not indx))
        # Check the edge colors and set to white if not selected color
        sel = self.radio.value_selected
        selcol = matplotlib.colors.to_rgba(sel[0])
        spcol = [self.axes[0].spines[s].get_edgecolor() for s in ['left','bottom','right']]
        if selcol not in spcol:
            [self.axes[0].spines[s].set_color('white') for s in ['left','bottom','right']]

        self.load_edges()

    def load_edges(self, load_fret=False):  # loads edge color from kon array
        sel = self.radio.value_selected
        kons = [self.kon[int(sel == 'green')]] ; colors = [sel[0]]
        if load_fret: kons.append(self.kon[2]) ;colors.append('blueviolet')

        for i, kon in enumerate(kons):
            selected_sides = list(itertools.compress(['left','bottom','right'], kon))
            unselected_sides = list(itertools.compress(['left','bottom','right'], np.invert(kon)))
            [self.axes[i].spines[s].set_color(colors[i]) for s in selected_sides]
            [self.axes[i].spines[s].set_color('white') for s in unselected_sides]

        self.fig.canvas.draw()

    def select_edge(self, key):
        if self.fret_edge_lock:
            ax = self.axes[0]
            sel = self.radio.value_selected[0]  # get the selected color of the radiobutton
        elif not self.fret_edge_lock:
            ax = self.axes[1]
            sel = 'blueviolet'  # this refers to the fret color

        side = 'left'*(key == ',')  + 'bottom'*(key == '.') + 'right'*(key == '/')

        spcolor = ax.spines[side].get_edgecolor()
        selcol, w = matplotlib.colors.to_rgba(sel), matplotlib.colors.to_rgba('white')
        c = selcol*(spcolor == w) + w*(spcolor == selcol)
        ax.spines[side].set_color(c)

        self.update_kon(sel, selcol, side, ax)

    def update_kon(self, sel=None, selcol=None, side=None, ax=None):
        i = ['r', 'g', 'blueviolet'].index(sel)  # These are the colors of the sides. blueviolet refers to fret
        j = ['left', 'bottom', 'right'].index(side)
        self.kon[i][j] = (ax.spines[side].get_edgecolor() == selcol)


    def check_fret(self, label):
        if self.checkbfret.get_status()[0]:
            self.checkbfret.rectangles[0].set_color("b")
        elif not self.checkbfret.get_status()[0]:
            self.checkbfret.rectangles[0].set_color("black")
        self.fig.canvas.draw()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
#mainPath = './traces'
mainPath = 'N:/tnw/BN/CMJ/Shared/Iasonas/20190517_cas9_sigma/#7.20_streptavidin_200pM_biot-DNA00_10nM-cas9-WT_G'
exp = analysis.Experiment(mainPath, 0.1)
i = InteractivePlot(exp.files[0])
i.plot_initialize()
i.plot_molecule()
#plt.show()


#self.fig.canvas.manager.toolmanager.add_tool('Next', NextTool)
#self.fig.canvas.manager.toolbar.add_tool('Next', 'foo')
#class NextTool(ToolBase, InteractivePlot):
#    '''Go to next molecule'''
#    default_keymap = 'enter, right'
#    description = 'Next Molecule 1'
#
#    def trigger(self, *args, **kwargs):
#        pass
#        InteractivePlot.__init__(InteractivePlot, self.file)
#        print(self.mol_indx
#              )
#        InteractivePlot.plot_setup(InteractivePlot)
#        print(InteractivePlot.mol)