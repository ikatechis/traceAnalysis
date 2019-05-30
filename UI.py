# -*- coding: utf-8 -*-
"""
Created on Fri Sep 14 15:44:52 2018

@author: ivoseverins
"""

#!/usr/bin/env python
import wx
import wx.dataview
import wx.lib.agw.hypertreelist as HTL
import wx.lib.agw.aui as aui
import os
from traceAnalysisCode import Experiment

import matplotlib as mpl

#Use the following for plt on Mac, instead of: import matplotlib.pyplot as plt
#from matplotlib import use
#use('WXAgg')

from matplotlib import pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar


class HistogramPanel(wx.Frame):
    def __init__(self, title='Histogram', parent=None):
        wx.Frame.__init__(self, parent=parent, title=title)
        self.panel = PlotPanel(self)
        self.parent = parent
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self,event):
        self.parent.viewMenuShowHistogram.Check(False)
        self.Hide()

class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        
        wx.Frame.__init__(self, parent, title='Trace Analysis', size=(1200,700))

        #self.panel1 = wx.Panel(self, wx.ID_ANY, size = (200,200))
        #self.panel2 = wx.Panel(self, wx.ID_ANY, size = (200,200))
        
        # Status bar
        self.CreateStatusBar()
        
        # File menu in Menu bar
        fileMenu = wx.Menu()
        fileMenuOpen = fileMenu.Append(wx.ID_OPEN, "&Open", "Open directory")
        fileMenuAbout = fileMenu.Append(wx.ID_ABOUT, "&About")
        fileMenuExit = fileMenu.Append(wx.ID_EXIT, "&Exit")
        
        self.Bind(wx.EVT_MENU, self.OnOpen, fileMenuOpen)
        self.Bind(wx.EVT_MENU, self.OnAbout, fileMenuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, fileMenuExit)

        # View menu in Menu bar
        viewMenu = wx.Menu()
        self.viewMenuShowHistogram = viewMenu.AppendCheckItem(wx.ID_ANY,"&Show histogram", "Show histogram")

        self.Bind(wx.EVT_MENU, self.OnShowHistogram, self.viewMenuShowHistogram)

        # Menu bar        x
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu,"&File")
        menuBar.Append(viewMenu,"&View")
        self.SetMenuBar(menuBar)
        
        
        # HyperTreeList
        self.tree = HTL.HyperTreeList(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(200,300),
                                      HTL.TR_MULTIPLE)
        self.Bind(HTL.EVT_TREE_ITEM_CHECKED, self.Test)

        # TreeListCtrl
        #self.tree = wx.dataview.TreeListCtrl(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(200,300),
        #                                     wx.dataview.TL_CHECKBOX | wx.dataview.TL_MULTIPLE)
        #self.Bind(wx.dataview.EVT_TREELIST_ITEM_CHECKED, self.Test, self.tree)
        #self.Bind(wx.EVT_TREE_SEL_CHANGED, self.Test, self.tree)
        ##self.tree.Bind(wx.EVT_LEFT_DOWN, self.Test)
        #panel = TreePanel(self)
        
        
        self.histogram = HistogramPanel(parent=self)
        #self.histogram = PlotPanel(self)
        #self.histogram.figure.gca().plot([1, 2, 3, 4, 5], [2, 1, 4, 2, 3])
        #self.histogram.figure.gca().hist([1, 2, 3, 4, 5])
        
        #test = wx.Button(self, -1, 'Large button')
        #test = wx.Button(self, -1, 'Large button')
        #wx.Button(self.panel1, -1, 'Small button')
        #box = wx.BoxSizer(wx.HORIZONTAL)
        #box.Add(self.tree, 0,wx.EXPAND,0)
        #box.Add(self.plotter, 0,0,0)
        #box.Add(self.histogram,1,wx.EXPAND,0)
        
        #box.Add(wx.Button(self, -1, 'Small button'), 0, 0, 0)
        #box.Add(wx.Button(self, -1, 'Large button'), 0, 0, 0)
        #box.Add(self.tree, 1,0,0)
        #box.Add(self.panel2, 1,0,0)
        #self.SetSizerAndFit(box)
           
        self.Show(True)
        
        self.createTree(r'D:\ivoseverins\SURFdrive\Promotie\Code\Python\traceAnalysis\twoColourExampleData\HJ A')
        #self.createTree(r'D:\SURFdrive\Promotie\Code\Python\traceAnalysis\twoColourExampleData\HJ A')
        #self.createTree(r'/Users/ivoseverins/SURFdrive/Promotie/Code/Python/traceAnalysis/twoColourExampleData/HJ A')



    # File menu event handlers
    def OnOpen(self,event):
        self.experimentRoot = ''
        dlg = wx.DirDialog(self, "Choose a directory", self.experimentRoot)
        if dlg.ShowModal() == wx.ID_OK:
            self.createTree(dlg.GetPath())
#            self.experimentRoot = dlg.GetPath()
#            print(self.experimentRoot)
#            exp = Experiment(self.experimentRoot)
#            
#            self.tree.AppendColumn('Files')
#            self.experimentRoot = self.tree.AppendItem(self.tree.GetRootItem(),exp.name)
#            
#            for file in exp.files:
#                self.tree.AppendItem(self.experimentRoot, file.name)
#            
#            self.tree.Expand(self.experimentRoot)
    
    # Temporary function to automate data import
    def createTree(self, experimentRoot):
        self.experimentRoot = experimentRoot
        print(self.experimentRoot)
        self.experiment = Experiment(self.experimentRoot)
        
        
        self.experiment.histogram(self.histogram.panel.axis, fileSelection = True)
        
        self.tree.AddColumn('Files')
        self.tree.AddColumn('Molecules')
        self.experimentRoot = self.tree.AddRoot(self.experiment.name)
        
        for file in self.experiment.files:
            item = self.tree.AppendItem(self.experimentRoot, file.name, ct_type = 1, data = file)
            self.tree.SetItemText(item, 'test', 1)
        
        self.tree.Expand(self.experimentRoot)
    #### End of temporary function
    
    def OnAbout(self,event):
        dlg = wx.MessageDialog(self, 'Software for trace analysis', 'About Trace Analysis', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnExit(self,event):
        self.Close(True) # Close program

    def OnShowHistogram(self,event):
        if event.IsChecked(): self.histogram.Show()
        elif ~event.IsChecked(): self.histogram.Hide()
    
    # TreeListCtrl event handlers
    def Test(self, event):
        item = event.GetItem()
        #newItemCheckedState = bool(self.tree.GetCheckedState(item))
        newItemCheckedState = bool(item.IsChecked())
        #file = self.tree.GetItemData(item)
        file = self.tree.GetItemPyData(item)
        file.isSelected = newItemCheckedState


        # self.histogram.axis.clear()
        # self.experiment.histogram(self.histogram.axis, fileSelection = True)
        # self.histogram.canvas.draw()
        # self.histogram.canvas.Refresh()

        #print(self.h.IsShown())
        if self.histogram.IsShown():
            self.histogram.panel.axis.clear()
            self.experiment.histogram(self.histogram.panel.axis, fileSelection=True)
            self.histogram.panel.canvas.draw()
            self.histogram.panel.canvas.Refresh()




class PlotPanel(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, size = (500,500), **kwargs)
        self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2, 2))
        self.axis = self.figure.gca()
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
    
    

#class Plot(wx.Panel):
#    def __init__(self, parent, id=-1, dpi=None, **kwargs):
#        wx.Panel.__init__(self, parent, id=id, **kwargs)
#        self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2, 2))
#        #self.axis = self.figure.gca()
#        self.canvas = FigureCanvas(self, -1, self.figure)
#        self.toolbar = NavigationToolbar(self.canvas)
#        self.toolbar.Realize()
#
#        sizer = wx.BoxSizer(wx.VERTICAL)
#        sizer.Add(self.canvas, 1, wx.EXPAND)
#        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
#        self.SetSizer(sizer)


#class PlotNotebook(wx.Panel):
#    def __init__(self, parent, id=-1, size = (500,500)):
#        wx.Panel.__init__(self, parent, id=id, size=size)
#        self.nb = aui.AuiNotebook(self)
#        sizer = wx.BoxSizer()
#        sizer.Add(self.nb, 1, wx.EXPAND)
#        self.SetSizer(sizer)
#
#    def add(self, name="plot"):
#        page = Plot(self.nb)
#        self.nb.AddPage(page, name)
#        return page.figure
        
        
        
        

app = wx.App(False)
frame = MainFrame(None, "MainFrame")
app.MainLoop()

print('End')

del app


"""

class MyTree(wx.TreeCtrl):
    def __init__(self, parent, id, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        
class TreePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.tree = MyTree(self, wx.ID_ANY, wx.DefaultPosition, (300,200), wx.TR_HAS_BUTTONS)
        
        self.root = self.tree.AddRoot('Something goes here')
        self.tree.SetPyData(self.root, ('key', 'value'))
        self.tree.AppendItem(self.root, 'Operating Systems')
        self.tree.Expand(self.root)
        


"""