from PyQt5 import QtWidgets, QtGui, QtCore
import sys
from ChorusGUI.ChorusPB import Ui_MainWindow
from matplotlib.widgets import SpanSelector
import pandas as pd
import os
from random import sample

class DesMainWD(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):

        super(DesMainWD, self).__init__(parent)

        # self.nowchr = 'Chromosome'

        self.setupUi(self)

        self.dockWidget_OV.setVisible(False)

        self.actionLoad_probe.triggered.connect(self.loadProbe)

        self.pushButton_loadchr.clicked.connect(self.draw_graph)

        self.comboBox_selectchr.activated[str].connect(self.onActionvated)

        self.horizontalSlider_start.valueChanged['int'].connect(self.update_graph)

        self.horizontalSlider_end.valueChanged['int'].connect(self.update_graph)

        self.selectedregionlength = 0

        self.pushButton_addpb.clicked.connect(self.add_probes)

        self.pushButton_delete.clicked.connect(self.del_probes)

        self.pushButton_show.clicked.connect(self.draw_overview)

        self.pushButton_projectdir.clicked.connect(self.setProjetDir)

        self.pushButton_saveprobe.clicked.connect(self.saveProbe)

        self.sortedperkbcount = object()

    def loadProbe(self):

        probefile, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose Probe File:", filter="*.bed")

        self.probefile = probefile

        self.label_probefile.setText(self.probefile)

        self.label_filename.setText(self.probefile)

        #Load probe bed file as panda data format
        self.probes = pd.read_table(self.probefile, names=("Chr","Start","End","Seq"))

        self.probes.Chr = self.probes.Chr.astype(object)

        self.probes['Kb'] = (self.probes.Start/1000).astype('int')

        # self.probes.Mb = int(self.probes.Start/1000000)

        self.chrs = self.probes.Chr.unique().tolist()

        #Load Chr length
        self.loadLen()

        self.comboBox_selectchr.clear()

        if len(self.longchr) > 0:

            self.comboBox_selectchr.addItems(self.longchr)

        self.comboBox_selectchr.insertSeparator(len(self.longchr))

        if len(self.shortchr) > 0:

            self.comboBox_selectchr.addItems(self.shortchr)

        self.currentChr = self.comboBox_selectchr.currentText()

        # print(self.currentChr)

    def loadLen(self):

        lenfile, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose Chromosome Length File:", filter="*.len")

        self.lenfile = lenfile

        self.label_lenfile.setText(self.lenfile)

        self.chrlen = dict()

        self.chrlenkb = dict()

        lenfileio = open(self.lenfile,'r')

        self.longchr = list()

        self.shortchr = list()

        for l in lenfileio.readlines():

            chro, length = l.rstrip('\n').split('\t')

            length = int(length)

            if chro in self.chrs:

                self.chrlen[chro] = length

                self.chrlenkb[chro] = int(length/1000)

                if length >= 1000000:

                    self.longchr.append(chro)

                else:

                    self.shortchr.append(chro)

    def draw_graph(self):

        self.nowprobe = self.probes[self.probes.Chr == self.currentChr]

        self.perkbprobe = self.nowprobe.Kb.value_counts(sort=False)

        self.sortedperkbcount = pd.DataFrame(self.perkbprobe).sort_index()

        self.sortedperkbcount = self.sortedperkbcount.reindex(index=range(0, self.chrlenkb[self.currentChr]), fill_value=0)

        self.spinBox_end.setMaximum(self.chrlenkb[self.currentChr])

        self.horizontalSlider_end.setMaximum(self.chrlenkb[self.currentChr])

        self.spinBox_start.setMaximum(self.chrlenkb[self.currentChr])

        self.horizontalSlider_start.setMaximum(self.chrlenkb[self.currentChr])

        self.spinBox_start.setValue(0)

        self.spinBox_end.setValue(self.chrlenkb[self.currentChr])

        self.horizontalSlider_start.setValue(0)

        self.horizontalSlider_end.setValue(self.chrlenkb[self.currentChr])

        self.widget.canvas.ax1.clear()

        self.widget.canvas.ax2.clear()

        self.widget.canvas.ax1.plot(pd.rolling_mean(self.sortedperkbcount.Kb,100))

        self.widget.canvas.ax1.set_xlim(0, self.chrlenkb[self.currentChr])

        self.widget.canvas.ax1.set_title(self.currentChr)

        self.widget.canvas.line2, = self.widget.canvas.ax2.plot(self.sortedperkbcount.Kb)
        # self.widget.canvas.ax2.plot(self.sortedperkbcount.Kb)

        self.widget.canvas.ax2.set_xlim(0, self.chrlenkb[self.currentChr])

        self.widget.canvas.draw()


    def onActionvated(self, text):

        self.statusbar.showMessage(text)

        self.currentChr = text


    def update_graph(self):

        self.widget.canvas.ax2.clear()

        self.widget.canvas.ax2.plot(self.sortedperkbcount.Kb)

        self.widget.canvas.ax2.set_xlim(self.spinBox_start.value(), self.spinBox_end.value())

        self.widget.canvas.ax1.clear()

        self.widget.canvas.ax1.set_title(self.currentChr)

        self.widget.canvas.ax1.plot(pd.rolling_mean(self.sortedperkbcount.Kb,100))

        self.widget.canvas.ax1.axvspan(self.spinBox_start.value(), self.spinBox_end.value(), facecolor=self.comboBox_color.currentText(), alpha=0.5)

        self.widget.canvas.ax1.set_xlim(0, self.chrlenkb[self.currentChr])

        self.subplotprob = self.nowprobe[self.nowprobe.Kb > self.spinBox_start.value()]

        self.subplotprob = self.subplotprob[self.subplotprob.Kb < self.spinBox_end.value()]

        self.subplottotalprobe = len(self.subplotprob.index)

        self.horizontalSlider_start.setMaximum(self.spinBox_end.value()-1)

        self.horizontalSlider_end.setMinimum(self.spinBox_start.value()+1)

        self.label_totalpb.setText(str(self.subplottotalprobe))

        self.spinBox_pbnumber.setMaximum(self.subplottotalprobe)

        self.spinBox_pbnumber.setValue(self.subplottotalprobe)

        regionlength = self.horizontalSlider_end.value() - self.horizontalSlider_start.value() + 1

        self.selectedregionlength = regionlength

        mes = "Region Length: "+str(regionlength)+'kb'

        self.statusbar.showMessage(mes)

        self.widget.canvas.draw()

    def oneselect(self, xmins, xmaxs):

        xmins = int(xmins)

        xmaxs = int(xmaxs)

        self.widget.canvas.ax2.clear()

        self.widget.canvas.ax2.plot(self.sortedperkbcount.Kb)

        self.widget.canvas.ax2.set_xlim(xmins, xmaxs)

        self.spinBox_start.setValue(xmins)

        self.spinBox_end.setValue(xmaxs)

        self.subplotprob = self.nowprobe[self.nowprobe.Kb < xmaxs]

        self.subplotprob = self.subplotprob[self.subplotprob.Kb > xmins]

        self.spinBox_start.setValue(xmins)

        self.spinBox_end.setValue(xmaxs)

        self.subplottotalprobe = len(self.subplotprob.index)

        self.label_totalpb.setText(str(self.subplottotalprobe))

        self.horizontalSlider_start.setMaximum(self.spinBox_end.value()-1)

        self.horizontalSlider_end.setMinimum(self.spinBox_start.value()+1)

        self.spinBox_pbnumber.setMaximum(self.subplottotalprobe)

        self.spinBox_pbnumber.setValue(self.subplottotalprobe)

        # print(self.subplotprob)

        self.widget.canvas.ax1.clear()

        self.widget.canvas.ax1.set_title(self.currentChr)

        self.widget.canvas.ax1.plot(pd.rolling_mean(self.sortedperkbcount.Kb,100))

        self.widget.canvas.ax1.set_xlim(0, self.chrlenkb[self.currentChr])

        self.widget.canvas.ax1.axvspan(xmins, xmaxs, facecolor=self.comboBox_color.currentText(), alpha=0.5)

        regionlength = self.horizontalSlider_end.value() - self.horizontalSlider_start.value() + 1

        mes = "Region Length: "+str(regionlength)+'kb'

        self.selectedregionlength = regionlength

        self.statusbar.showMessage(mes)

        self.widget.canvas.draw()

    def add_probes(self):

        rowcount = self.tableWidget.rowCount()

        self.tableWidget.insertRow(rowcount)

        #probe density per kb
        pbd = round(self.spinBox_pbnumber.value()/self.selectedregionlength, 1)

        itchr = QtWidgets.QTableWidgetItem(self.currentChr)
        itstart = QtWidgets.QTableWidgetItem(self.spinBox_start.text())
        itend = QtWidgets.QTableWidgetItem(self.spinBox_end.text())
        itcolor = QtWidgets.QTableWidgetItem(self.comboBox_color.currentText())
        ittp = QtWidgets.QTableWidgetItem(self.label_totalpb.text())
        itsp = QtWidgets.QTableWidgetItem(self.spinBox_pbnumber.text())
        itrgl = QtWidgets.QTableWidgetItem(str(self.selectedregionlength))
        itpbd = QtWidgets.QTableWidgetItem(str(pbd))



        qcolor = QtGui.QColor(0,0,0)

        if self.comboBox_color.currentText() == 'green':
            qcolor = QtGui.QColor(0, 255,0)
        if self.comboBox_color.currentText() == 'red':
            qcolor = QtGui.QColor(255, 0,0)

        itcolor.setBackground(qcolor)

        self.tableWidget.setItem(rowcount, 0, itchr)
        self.tableWidget.setItem(rowcount, 1, itstart)
        self.tableWidget.setItem(rowcount, 2, itend)
        self.tableWidget.setItem(rowcount, 3, itcolor)
        self.tableWidget.setItem(rowcount, 4, ittp)
        self.tableWidget.setItem(rowcount, 5, itsp)
        self.tableWidget.setItem(rowcount, 6, itrgl)
        self.tableWidget.setItem(rowcount, 7, itpbd)

    def del_probes(self):

        nowItem = self.tableWidget.currentItem()

        nowit = nowItem.row()

        self.tableWidget.removeRow(nowit)


    def draw_overview(self):

        self.widget_OV.canvas.ax.clear()

        self.widget_OV.canvas.ax.plot(pd.rolling_mean(self.sortedperkbcount.Kb,100))

        rowcount = self.tableWidget.rowCount()

        self.dockWidget_OV.setVisible(True)

        self.widget_OV.canvas.ax.set_title(self.currentChr)

        self.widget_OV.canvas.ax.set_xlim(0, self.chrlenkb[self.currentChr])

        print("nowchr", self.currentChr)

        for i in range(rowcount):

            itchr = self.tableWidget.item(i, 0).text()

            if itchr == self.currentChr:
                itstart = int(self.tableWidget.item(i,1).text())
                itend = int(self.tableWidget.item(i,2).text())
                itcolor = self.tableWidget.item(i,3).text()

                print(itchr, itstart, itend, itcolor)
                self.widget_OV.canvas.ax.axvspan(itstart, itend, facecolor=itcolor, alpha=0.95)



        regionlength = self.horizontalSlider_end.value() - self.horizontalSlider_start.value() + 1

        self.selectedregionlength = regionlength

        mes = "Region Length: "+str(regionlength)+'kb'

        self.statusbar.showMessage(mes)

        self.widget_OV.canvas.draw()

    def setProjetDir(self):

        # options = QtWidgets.QFileDialog.DontResolveSymlinks | QtWidgets.QFileDialog.ShowDirsOnly

        projectdir = QtWidgets.QFileDialog.getExistingDirectory()

        if projectdir:

            self.projectdir = projectdir

            self.label_prodir.setText(self.projectdir)


    def saveProbe(self):

        rowcount = self.tableWidget.rowCount()

        if not self.label_prodir.text():

            self.setProjetDir()

        for i in range(rowcount):

            itchr = self.tableWidget.item(i,0).text()

            itstart = int(self.tableWidget.item(i,1).text())

            itend = int(self.tableWidget.item(i,2).text())

            itcolor = self.tableWidget.item(i,3).text()

            #choosed probe number
            itsp = int(self.tableWidget.item(i,5).text())

            print(itsp)

            nowprobes = self.probes[self.probes.Chr==itchr]

            nowprobes = nowprobes[nowprobes.Kb > itstart]

            nowprobes = nowprobes[nowprobes.Kb < itend]

            nowprobes = nowprobes.loc[sample(list(nowprobes.index), itsp)]

            nowprobes = nowprobes.drop('Kb', axis=1)

            outfilename = itcolor + '_' + itchr + '_' + str(itstart) + '_' + str(itend) + '.bed'

            absfile = os.path.join(self.projectdir, outfilename)

            nowprobes.to_csv(path_or_buf=absfile, sep='\t', index = False, index_label= False, header=False)

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    tb = DesMainWD()

    tb.show()

    span = SpanSelector(tb.widget.canvas.ax1, tb.oneselect, 'horizontal', useblit=True,
                                 rectprops=dict(alpha=0.3, facecolor='grey'))

    sys.exit(app.exec_())
