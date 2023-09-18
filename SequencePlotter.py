

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
import numpy as np
import json
from PyQt5.QtCore import QThread, QObject, pyqtSignal as Signal, pyqtSlot as Slot


imageSize = 5


class SequencePlotter(QWidget):

    def __init__(self, fig, axs):
        super().__init__()
        self.rf, self.gx, self.gy, self.gz = [], [], [], []
        self.fig, self.axs = fig, axs


    def PrepareAxes(self, ax_index, axesName):
        self.axs[ax_index].set_ylabel(axesName, fontsize=11)
        self.axs[ax_index].set_xlim(0, self.maxPoint + 1)
        self.axs[ax_index].set_xticks([])
        self.axs[ax_index].set_yticks([])
        self.axs[ax_index].spines['bottom'].set_visible(False)
        self.axs[ax_index].spines['left'].set_visible(False)
        self.axs[ax_index].spines['top'].set_visible(False)
        self.axs[ax_index].spines['right'].set_visible(False)


    def plotMain(self):

        self.fig, self.axs = plt.subplots(5, 1)

        for i in range(len(self.rf)): self.rf[i].plot(self.axs[0])
        for i in range(len(self.gz)): self.gz[i].plot(self.axs[1])
        for i in range(len(self.gy)): self.gy[i].plot(self.axs[2])
        for i in range(len(self.gx)): self.gx[i].plot(self.axs[3])
        self.readout.plot(self.axs[4])

        axesLabel = {0: "RF", 1: "Gz", 2: "Gy", 3: "Gx", 4: "Read Out"}
        for axesNumber in range(5): self.PrepareAxes(axesNumber, axesLabel[axesNumber])

        self.plotTE()


    def plotTE(self):
        center = (self.rf[0].startPoint + self.rf[0].endPoint) / 2.0
        self.axs[0].text(center + (self.TE - (center))/2, 5, "TE", ha='center', va='bottom', fontsize=11)
        self.axs[0].annotate('', xy=(center, 5), xytext=(self.TE, 5), arrowprops=dict(arrowstyle='<->', color='black'))


    def plot(self):
        self.plotMain()


    def readJson(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)

        if file_path:
            with open(file_path, "r") as f:
                self.data = json.load(f)
                sequence = self.data["Sequence"]

            for seq in sequence:
                if "RF" in seq:
                    self.rf.append(RF(seq["RF"]["Flip Angle"], seq["RF"]["Start Time"], seq["RF"]["End Time"], seq["RF"]["Is Alternating"]))
                elif "Gradient" in seq:
                    if seq['Gradient']['Orientation'] == 'X':
                        self.gx.append(Gradient(seq["Gradient"]["Start Amplitude Polarity"], seq["Gradient"]["End Amplitude Polarity"], seq["Gradient"]["Start Time"], seq["Gradient"]["End Time"], seq["Gradient"]["Is Alternating"], seq["Gradient"]["Orientation"], seq["Gradient"]["Functionality"]))
                    elif seq['Gradient']['Orientation'] == 'Y':
                        self.gy.append(Gradient(seq["Gradient"]["Start Amplitude Polarity"], seq["Gradient"]["End Amplitude Polarity"], seq["Gradient"]["Start Time"], seq["Gradient"]["End Time"], seq["Gradient"]["Is Alternating"], seq["Gradient"]["Orientation"], seq["Gradient"]["Functionality"]))
                    elif seq['Gradient']['Orientation'] == 'Z':
                        self.gz.append(Gradient(seq["Gradient"]["Start Amplitude Polarity"], seq["Gradient"]["End Amplitude Polarity"], seq["Gradient"]["Start Time"], seq["Gradient"]["End Time"], seq["Gradient"]["Is Alternating"], seq["Gradient"]["Orientation"], seq["Gradient"]["Functionality"]))

                    self.maxPoint = seq["Gradient"]["End Time"]
                
            self.TE, acquistionDuration = self.data["Time Parameters"]["TE"], self.data["Time Parameters"]["Aquisition Duration"]
            self.readout = RF(180, self.TE - (acquistionDuration//2), self.TE + (acquistionDuration//2), None)

        return self.data



class RF:

    def __init__(self, flipAngle, startPoint, endPoint, isAlternating):
        self.flipAngle = flipAngle
        self.amplitude = (flipAngle // 90)
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.isAlternating = isAlternating
        self.orientation = "RF"
    
    def sinc(self, timePoints):
        return np.sinc(4 * timePoints)

    def plot(self, ax):

        ax.axhline(y=0,color = 'black', linewidth=1)
        ax.set_ylim(-0.5, 8)

        center = (self.startPoint + self.endPoint) / 2.0
        time = np.linspace(self.startPoint, self.endPoint, 1000)
        y = self.sinc(time - center) * self.amplitude
        ax.plot(time, y, color='black')
        ax.fill_between(time, y, 0, color='black', alpha=0.2)
        if self.isAlternating != None:
            sign = '±' if self.isAlternating else '+'
            ax.text(center, self.amplitude + 0.5, "FA: " + sign +str(self.flipAngle), ha='center', va='bottom')



class Gradient:
     
    def __init__(self, startAmplitudePolarity, endAmplitudePolarity, startPoint, endPoint, isAlternating, orientation, functionality):
        self.startAmplitudePolarity = startAmplitudePolarity
        self.endAmplitudePolarity = endAmplitudePolarity
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.isAlternating = isAlternating
        self.orientation = orientation
        self.functionality = functionality
        self.AmplitudeAssignment()


    def AmplitudeAssignment(self):
        self.amplitude = []
        if self.isAlternating is False:
            if self.functionality == "Spoiler": self.amplitude.append(4)
            else:
                if self.endAmplitudePolarity == "Positive": self.amplitude.append(1)
                elif self.endAmplitudePolarity == "Negative": self.amplitude.append(-1)
        else:
            self.gradientSteps = int(np.floor(imageSize/2))
            if self.startAmplitudePolarity == "Positive":
                for i in range(self.gradientSteps, -self.gradientSteps-1, -1): self.amplitude.append(i)
            if self.startAmplitudePolarity == "Negative":
                for i in range(-self.gradientSteps, self.gradientSteps+1): self.amplitude.append(i)
            if self.startAmplitudePolarity == "Zero":
                for i in range(0, imageSize): self.amplitude.append(i)


    def plot(self, ax):
        ax.axhline(y=0,color = 'black', linewidth=1)
        for currentAmplitude in self.amplitude:
            ax.plot([self.startPoint, self.startPoint], [0, currentAmplitude], color='black', linewidth=2)
            ax.plot([self.endPoint, self.endPoint], [0, currentAmplitude], color='black', linewidth=2)
            ax.plot([self.startPoint, self.endPoint], [currentAmplitude, currentAmplitude], color='black', linewidth=2)
            ax.add_patch(plt.Rectangle((self.startPoint, 0), self.endPoint - self.startPoint, currentAmplitude, color='black', alpha=0.2))

        center = (self.startPoint + self.endPoint) / 2.0
        if len(self.amplitude) == 1 and self.amplitude[0] < 0: ax.text(center, 0, self.functionality, ha='center', va='bottom')
        else: ax.text(center, max(self.amplitude) + 0.5, self.functionality, ha='center', va='bottom')
    
        if (self.startAmplitudePolarity != "Zero") or (self.endAmplitudePolarity == "Negative"): ax.set_ylim(min(self.amplitude) - 1, 8)
        else:
            if (ax.get_ylim()[0] > 0) or (ax.get_ylim()[0] < 0 and ax.get_ylim()[0] > -1): ax.set_ylim(0, 8)

        if self.isAlternating: 
            if self.startAmplitudePolarity == "Zero": xy, xytext = (self.startPoint - 0.5, imageSize - 1), (self.startPoint - 0.5, 0)
            elif self.startAmplitudePolarity == "Positive": xy, xytext = (self.startPoint - 0.5, -self.gradientSteps), (self.startPoint - 0.5, self.gradientSteps)
            elif self.startAmplitudePolarity == "Negative": xy, xytext = (self.startPoint - 0.5, self.gradientSteps), (self.startPoint - 0.5, -self.gradientSteps)
            ax.annotate('', xy=xy, xytext=xytext, arrowprops=dict(arrowstyle='->', color='red'))
