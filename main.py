
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from enum import Enum
from SequencePlotter import *



ui,_ = loadUiType(os.path.join(os.path.dirname(__file__),'mainwindow.ui'))


class MagnetizationVectorChannels(Enum):
    Mx = 0
    My = 1
    Mz = 2


class ImagePropertyChannels(Enum):
    PD = 0
    T1 = 1
    T2 = 2
    T2_Star = 3



class MainWindow(QtWidgets.QMainWindow, ui):


    def __init__(self, parent = None):
        super().__init__()
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.ifPSDPlotter = False

        self.phantomFigure = plt.figure()
        self.phantomFigure.set_facecolor('black')
        self.phantomFigureAx = self.phantomFigure.add_subplot(111)
        self.pulseSequenceFigure, self.pulseSequenceFigureAx = plt.subplots(5, 1)
        self.pulseSequenceFigure.set_facecolor('white')
        self.KSpaceFigure = plt.figure()
        self.KSpaceFigure.set_facecolor('black')
        self.KSpaceFigureAx = self.KSpaceFigure.add_subplot(111)
        self.port1Figure = plt.figure()
        self.port1Figure.set_facecolor('black')
        self.port1FigureAx = self.port1Figure.add_subplot(111)
        self.port2Figure = plt.figure()
        self.port2Figure.set_facecolor('black')
        self.port2FigureAx = self.port2Figure.add_subplot(111)

        self.DrawNewFigure(self.phantomFigure, self.phantomFigureAx, np.zeros((100, 100)), self.phantomGridLayout)
        self.DrawNewFigure(self.KSpaceFigure, self.KSpaceFigureAx, np.zeros((100, 100)), self.kSpaceGridLayout)
        self.DrawNewFigure(self.port1Figure, self.port1FigureAx, np.zeros((100, 100)), self.port1GridLayout)
        self.DrawNewFigure(self.port2Figure, self.port2FigureAx, np.zeros((100, 100)), self.port2GridLayout)

        self.openPhantomAction.triggered.connect(self.OpenPhantom)
        self.viewPDAction.triggered.connect(lambda: self.ChangeImageProperty(ImagePropertyChannels.PD.value, "Proton Density"))
        self.viewT1Action.triggered.connect(lambda: self.ChangeImageProperty(ImagePropertyChannels.T1.value, "T1 Property"))
        self.viewT2Action.triggered.connect(lambda: self.ChangeImageProperty(ImagePropertyChannels.T2.value, "T2 Property"))
        self.viewT2StarAction.triggered.connect(lambda: self.ChangeImageProperty(ImagePropertyChannels.T2_Star.value, "T2* Property"))
        self.phantomFigure.canvas.mpl_connect('motion_notify_event', self.HoverOnPhantomImage)

        self.openPSDAction.triggered.connect(self.OpenPSD)
        self.outputPortNumber = 1
        self.viewOnPort1Action.triggered.connect(lambda: self.ChooseOutputPort(1))
        self.viewOnPort2Action.triggered.connect(lambda: self.ChooseOutputPort(2))
        self.runPushButton.clicked.connect(self.ApplyPulseSequence)


    def OpenPSD(self):

        if self.ifPSDPlotter:
            self.PSDGridLayout.removeWidget(self.PSDCanvas)
            self.PSDCanvas.deleteLater()

        self.PSDPlotter = self.ReadJsonGetSequence()
        self.PSDCanvas = FigureCanvas(self.PSDPlotter.fig)
        self.PSDGridLayout.addWidget(self.PSDCanvas)          
        self.ifPSDPlotter =True
        

    def OpenPhantom(self):  

        self.filename = QFileDialog.getOpenFileName(
        None, 'Open the .npy file', './', filter="NumPy files (*.npy)")

        path = self.filename[0]
        if path:
            self.MRIPhantomForHover, self.MRIPhantom = np.zeros_like(np.load(path), dtype=np.uint64), np.zeros_like(np.load(path), dtype=np.uint8)
            self.MRIPhantomForHover, self.MRIPhantom = np.load(path), np.load(path)
        else: return
     
        self.imagePropertyLabel.setText("Proton Density")
        self.DrawNewFigure(self.phantomFigure, self.phantomFigureAx, self.MRIPhantom[:, :, ImagePropertyChannels.PD.value], self.phantomGridLayout)

    
    def ChangeImageProperty(self, channelNumber, propertyName):

        self.DrawNewFigure(self.phantomFigure, self.phantomFigureAx, self.MRIPhantom[:, :, channelNumber], self.phantomGridLayout)
        self.imagePropertyLabel.setText(propertyName)


    def HoverOnPhantomImage(self, event):

        x, y= event.xdata, event.ydata
        if x is None or y is None: return
       
        pd = self.MRIPhantomForHover[int(y), int(x), 0]
        t1 = self.MRIPhantomForHover[int(y), int(x), 1]
        t2 = self.MRIPhantomForHover[int(y), int(x), 2]
        t2_star = self.MRIPhantomForHover[int(y), int(x), 3]

        self.hovered_PD_value.setText(str(pd))
        self.hovered_T1_value.setText(str(t1))
        self.hovered_T2_value.setText(str(t2))
        self.hovered_T2Star_value.setText(str(t2_star))


    def ReadJsonGetSequence(self):
        plotter = SequencePlotter(self.pulseSequenceFigure, self.pulseSequenceFigureAx)
        self.JSONData = plotter.readJson()
        plotter.plot()
        self.PSDLabel.setText(self.JSONData["Sequence Name"])
        return plotter
        
        
    def DrawNewFigure(self, figureToBeDrawOn, ax, imageToDraw, figureGridLayout):

        ax.clear()
        ax.imshow(imageToDraw, cmap='gray')
        ax.axis('off')
        figureToBeDrawOn.canvas.draw()
        figureToBeDrawOn.canvas.flush_events()
        figureCanvas = FigureCanvas(figureToBeDrawOn)
        figureCanvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        figureCanvas.updateGeometry()
        figureGridLayout.addWidget(figureCanvas, 0, 0, 1, 1)
        figureToBeDrawOn.tight_layout()


    def ApplyPulseSequence(self):
        self.SortSequence()
        self.RunSequence()


    def ChooseOutputPort(self, portNumber): self.outputPortNumber = portNumber


    def SortSequence(self):

        self.sequenceElements = []
        for element in self.JSONData["Sequence"]:

            if "RF" in element:
                RFElement = RF(element["RF"]["Flip Angle"], element["RF"]["Start Time"], element["RF"]["End Time"], element["RF"]["Is Alternating"])
                self.sequenceElements.append(RFElement)

            elif "Gradient" in element:
                if (element["Gradient"]["Orientation"] != "Z")  and (element["Gradient"]["Functionality"] != " "):
                    gradientElement = Gradient(element["Gradient"]["Start Amplitude Polarity"], element["Gradient"]["End Amplitude Polarity"], element["Gradient"]["Start Time"], element["Gradient"]["End Time"], element["Gradient"]["Is Alternating"], element["Gradient"]["Orientation"], element["Gradient"]["Functionality"])
                    self.sequenceElements.append(gradientElement)

        orientationDict = {"RF": -1, "Y": 0, "X": 1}
        self.sequenceElements.sort(key=lambda obj: (obj.startPoint, orientationDict[obj.orientation]))


    def RunSequence(self):

        self.rowSize, self.columnSize, __ = self.MRIPhantom.shape
        magnetization_vector = np.zeros((self.rowSize, self.columnSize, 3))
        magnetization_vector[:, :, MagnetizationVectorChannels.Mz.value] = self.MRIPhantom[:, :, ImagePropertyChannels.PD.value]
        self.rowIncrementalPhase, self.columnIncrementalPhase = 360 / self.rowSize, 360 / self.columnSize

        self.kSpace = np.zeros((self.rowSize, self.columnSize), dtype=np.complex_)
        self.centeredKSpace = False
        refocusingPulseApplied = False

        TE = self.JSONData["Time Parameters"]["TE"]
        TR = self.JSONData["Time Parameters"]["TR"]

        for iterationNumber in range(self.rowSize):

            for element in self.sequenceElements:

                if type(element) == RF:
                    if element.flipAngle == 180:
                        refocusingPulseApplied = True
                        magnetization_vector = self.ApplyDecayRecovery(TE / 2, magnetization_vector)
                    magnetization_vector = self.ApplyRF(magnetization_vector, element.flipAngle)

                elif type(element) == Gradient:
                    if (element.isAlternating == False) and (TE > element.startPoint and TE < element.endPoint):
                        isReadoutGradient = True
                        if refocusingPulseApplied: magnetization_vector = self.ApplyDecayRecovery(TE / 2, magnetization_vector)
                        else: magnetization_vector = self.ApplyDecayRecovery(TE, magnetization_vector)
                    else: isReadoutGradient = False
                    magnetization_vector = self.ApplyGradient(magnetization_vector, iterationNumber, element.isAlternating, element.orientation, element.startAmplitudePolarity, element.endAmplitudePolarity, isReadoutGradient, element.functionality)

            magnetization_vector = self.ApplyDecayRecovery(TR - TE, magnetization_vector)
            self.DisplayImageAndKSpace()
            time.sleep(0.01)


    def ApplyRF(self, magnetization_vector, flipAngle):

        FA = np.radians(flipAngle)
        rotX = np.matrix([[1, 0, 0],
                          [0, math.cos(FA), math.sin(FA)],
                          [0, -math.sin(FA), math.cos(FA)]])

        for rowIndex in range(self.rowSize):
            for columnIndex in range(self.columnSize):
                magnetization_vector[rowIndex, columnIndex] = np.dot(rotX, magnetization_vector[rowIndex, columnIndex])

        return magnetization_vector
    

    def ApplyGradient(self, magnetization_vector, iterationNumber, isAlternating, orientation, startPolarity, endPolarity, isReadoutGradient, functionality):

        if isAlternating:

            if (startPolarity == "Positive" and endPolarity == 'Zero') or (startPolarity == "Positive" and endPolarity == 'Negative'): newIterationNumber = -iterationNumber
            else: newIterationNumber = iterationNumber

            newMagnetizationVector = np.zeros((self.rowSize, self.columnSize, 3))
            newMagnetizationVector[:, :, 2] = magnetization_vector[:, :, 2]

            for sliceColumnIndex in range(self.columnSize):
                for sliceRowIndex in range(self.rowSize):

                    phaseY = self.rowIncrementalPhase * newIterationNumber * sliceRowIndex

                    phaseY = np.radians(phaseY)
                    rotZ = np.matrix([[math.cos(phaseY), -math.sin(phaseY), 0],
                                      [math.sin(phaseY), math.cos(phaseY), 0],
                                      [0, 0, 1]])

                    newMagnetizationVector[sliceRowIndex, sliceColumnIndex] = np.dot(rotZ, magnetization_vector[sliceRowIndex, sliceColumnIndex])

            return newMagnetizationVector


        elif not isAlternating:
            
            for KSpaceColumnIndex in range(self.columnSize):

                if (startPolarity == "Zero" and endPolarity == 'Negative'): newKSpaceColumnIndex = -KSpaceColumnIndex
                else: newKSpaceColumnIndex = KSpaceColumnIndex

                newMagnetizationVector = np.zeros((self.rowSize, self.columnSize, 3))
                newMagnetizationVector[:, :, 2] = magnetization_vector[:, :, 2]

                for sliceRowIndex in range(self.rowSize):
                    for sliceColumnIndex in range(self.columnSize):

                        if functionality == 'Spoiler': phaseX = ((0.5 * 360)/self.columnSize) * newKSpaceColumnIndex * sliceColumnIndex

                        # calculating current xphase to be applied on slice
                        phaseX = self.columnIncrementalPhase * newKSpaceColumnIndex * sliceColumnIndex

                        phaseX = np.radians(phaseX)
                        rotZ = np.matrix([[math.cos(phaseX), -math.sin(phaseX), 0],
                                          [math.sin(phaseX), math.cos(phaseX), 0],
                                          [0, 0, 1]])

                        newMagnetizationVector[sliceRowIndex, sliceColumnIndex] = np.dot(rotZ, magnetization_vector[sliceRowIndex, sliceColumnIndex])

                if isReadoutGradient: self.Readout(iterationNumber, KSpaceColumnIndex, newMagnetizationVector)
            
            return newMagnetizationVector
        

    def Readout(self, KSpaceRowIndex, KSpaceColumnIndex, magnetizationVector):

        realComponent = np.sum(magnetizationVector[:, :, MagnetizationVectorChannels.My.value])
        imaginaryComponent = np.sum(magnetizationVector[:, :, MagnetizationVectorChannels.Mx.value])
        self.kSpace[KSpaceRowIndex, KSpaceColumnIndex] = complex(realComponent, imaginaryComponent)


    def DisplayImageAndKSpace(self):

        self.DrawNewFigure(self.KSpaceFigure, self.KSpaceFigureAx, 0.2 * np.abs(self.kSpace), self.kSpaceGridLayout)

        inverseImage = np.fft.ifft2(self.kSpace)
        inverseImage = np.round(np.abs(inverseImage))

        if self.outputPortNumber == 1: self.DrawNewFigure(self.port1Figure, self.port1FigureAx, inverseImage, self.port1GridLayout)
        elif self.outputPortNumber == 2: self.DrawNewFigure(self.port2Figure, self.port2FigureAx, inverseImage, self.port2GridLayout)


    def ApplyDecayRecovery(self, time, magnetization_vector):

        newMagnetizationVector = np.zeros((self.rowSize, self.columnSize, 3))
        newMagnetizationVector[:, :, 2] = magnetization_vector[:, :, 2]

        for rowIndex in range(self.rowSize):
            for columnIndex in range(self.columnSize):

                intermediateDecayRecoveryMatrix = np.array([[np.exp(-time / self.MRIPhantom[rowIndex, columnIndex, ImagePropertyChannels.T2_Star.value]), 0, 0],
                                                            [0, np.exp(-time / self.MRIPhantom[rowIndex, columnIndex, ImagePropertyChannels.T2_Star.value]), 0],
                                                            [0, 0, np.exp(-time / self.MRIPhantom[rowIndex, columnIndex, ImagePropertyChannels.T1.value])]])
                
                newMagnetizationVector[rowIndex, columnIndex] = np.dot(intermediateDecayRecoveryMatrix,
                                                                       magnetization_vector[rowIndex, columnIndex]) + np.array([0,
                                                                                                                                0,
                                                                                                                                self.MRIPhantom[rowIndex, columnIndex, ImagePropertyChannels.PD.value] * (1 - np.exp(-time / self.MRIPhantom[rowIndex, columnIndex, ImagePropertyChannels.T1.value]))])
        return newMagnetizationVector


        
      

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())