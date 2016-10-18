"""
    This file is part of WorkCycler.
    WorkCycler is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    WorkCycler is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with WorkCycler.  If not, see <http://www.gnu.org/licenses/>.
    
"""

import sys
from PySide import QtGui, QtCore

import threading
import time


DEFAULT_WORK_TIME = QtCore.QTime(0, 45, 0)
DEFAULT_REST_TIME = QtCore.QTime(0, 20, 0)
DEFAULT_TARGET_TIME = QtCore.QTime(3, 0, 0)
SEGMENT_NUM = 100

RED_BACKGROUND = QtGui.QColor(255, 150, 150)
GREEN_BACKGROUND = QtGui.QColor(150, 255, 150)
BLUE_BACKGROUND = QtGui.QColor(200, 200, 255)

WHITE_BACKGROUND = QtGui.QColor(255, 255, 255)

START_ALARM_PATH = "./Alarm1.wav"
END_ALARM_PATH = "./Alarm2.wav"

def QTime_to_secs(time):
    return QtCore.QTime(0, 0, 0).secsTo(time)


class Window(QtGui.QWidget):
    
    def __init__(self):
        super(Window, self).__init__()
        
        self.work_time = 0
        self.rest_time = 0
        
        self.been_paused = False
        self.next_rest_time = 0
        
        self.big_time = 0
        self.big_time_remaining = 0
        
        self.is_working = True
        self.big_time_set = False       
        
        self.initUI()
        
        self.cycle_thread = DoCycleThread(500)
        
        self.cycle_thread.started_sig.connect(self.started)
        self.cycle_thread.paused_sig.connect(self.paused)
        self.cycle_thread.update_sig.connect(self.update)
        self.cycle_thread.done_sig.connect(self.done)
        
        
        self.work_input.selectAll()
        
    def initUI(self):
        
        vbox = QtGui.QVBoxLayout()        
        self.setLayout(vbox)
                
        
        hbox0 = QtGui.QHBoxLayout()
        hbox0.addStretch(1)
        
        big_time_label = QtGui.QLabel("Work Time Target HH:MM:SS")
        hbox0.addWidget(big_time_label)
        
        hbox0.addStretch(1)
        
        vbox.addLayout(hbox0)
        
        self.big_time_input = QtGui.QTimeEdit(self, displayFormat="hh:mm:ss")
        self.big_time_input.setTime(DEFAULT_TARGET_TIME)
        
        vbox.addWidget(self.big_time_input)
        
        self.big_progress_bar = QtGui.QProgressBar(self)#, invertedAppearance=True)
        self.big_progress_bar.setTextVisible(False)
        vbox.addWidget(self.big_progress_bar)                                
        
        hbox1 = QtGui.QHBoxLayout()
        
        hbox1.addStretch(2)
        
        work_time_label = QtGui.QLabel("Work Time MM:SS")
        self.work_input = QtGui.QTimeEdit(self, displayFormat="mm:ss")
        self.work_input.setTime(DEFAULT_WORK_TIME)
        hbox1.addWidget(work_time_label)
        hbox1.addWidget(self.work_input)
                
        rest_time_label = QtGui.QLabel("Rest Time MM:SS")
        self.rest_input = QtGui.QTimeEdit(self, displayFormat="mm:ss")
        self.rest_input.setTime(DEFAULT_REST_TIME)        
        hbox1.addWidget(rest_time_label)
        hbox1.addWidget(self.rest_input)
        
        hbox1.addStretch(1)
                
        vbox.addLayout(hbox1)
                
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addStretch(1)
        
        self.btn = QtGui.QPushButton('Start', self)
        self.btn.clicked.connect(self.start_cycle)
        self.pause_button = QtGui.QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.pause)
        
        hbox2.addWidget(self.btn)
        hbox2.addWidget(self.pause_button)
                
        loop_label = QtGui.QLabel("Loop around?")
        self.loop = QtGui.QCheckBox(self)
        self.loop.setToolTip("loop?")
        
        hbox2.addWidget(loop_label)
        hbox2.addWidget(self.loop)
        hbox2.addStretch(1)
        
        vbox.addLayout(hbox2)
        
        self.progress_bar = QtGui.QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        vbox.addWidget(self.progress_bar)
        
        
        self.message_box = QtGui.QLineEdit("", self, readOnly=True)
        self.message_box.setAlignment(QtCore.Qt.AlignHCenter)
        vbox.addWidget(self.message_box)
       
        self.setWindowTitle('Work Cycler')    
        self.show()
        
    def _update_button(self, button, text, bind):
        button.setText(text)
        button.clicked.disconnect()
        button.clicked.connect(bind)
    
    def _set_fill(self, colour):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), colour)
        self.setPalette(palette)
    
    def _fill_red(self):
        self._set_fill(RED_BACKGROUND)
    
    def _fill_green(self):
        self._set_fill(GREEN_BACKGROUND)
        
    def _alert(self):
        alert = None
        if self.is_working:
            alert = QtGui.QSound(END_ALARM_PATH)
            message = "Woop working time is over :D"
        else:
            alert = QtGui.QSound(START_ALARM_PATH)
            message = "Unfortunately it's time to get back to work"
        alert.setLoops(4)        
        alert.play()
        if self.loop.isChecked():
            while not alert.isFinished() and self.loop.isChecked():
                time.sleep(0.1)
        else:
            wait = QtGui.QMessageBox.information(self, "Alert", message)
        alert.stop()
        
        #QtGui.QApplication.beep()          
        QtGui.QApplication.alert(self)        
        QtGui.QApplication.setActiveWindow(self)
        
    def start_cycle(self):
        
        self.work_time = QTime_to_secs(self.work_input.time())
        self.rest_time = QTime_to_secs(self.rest_input.time())

        self.next_rest_time = self.rest_time
        
        self.been_paused = False
        self.set_target()
       
        print("work time", self.work_time, "rest time", self.rest_time)
        self.work_input.setDisabled(True)
        self.rest_input.setDisabled(True)
        
        self.start_timer(self.work_time)
        
        return True
    
    def start_timer(self, time):
        self.cycle_thread.time = time
        self.cycle_thread.start()
        
    def started(self):
        if self.is_working:
            self.message_box.setText("Working time")            
            self._fill_red()
            self.pause_button.setDisabled(False)
        else:
            self.message_box.setText("Resting time")
            self.pause_button.setDisabled(True)
            self._fill_green()
        self._update_button(self.btn, "Stop", self.interupt)
        self.big_time_input.setEnabled(False)
        
    def paused(self, increment):
        self.next_rest_time += -increment
        if self.next_rest_time < 0:
            self.next_rest_time = 0
        self.been_paused = True
        
    def update(self, value, increment):
        self.progress_bar.setValue(value)
        if self.is_working:
            self.big_time_remaining += -increment
            self.big_progress_bar.setValue(((self.big_time - self.big_time_remaining) / self.big_time) * 100)
            if self.big_time_remaining <= 0:
                self.big_progress_bar.setValue(100)
                self._alert()
                self.interupt()
        print("update", value)
    
    def done(self):
        print("loop complete")
        self._alert()
        if self.is_working:
            print("starting break cycle")
            self.is_working = False
            self.start_timer(self.next_rest_time)
            return True
        if self.loop.isChecked():
            print("looping around")
            self.is_working = True
            self.start_timer(self.work_time)
            return True
        print("finished")
        self.reset()
        
    def interupt(self):
        print("recieved interupt")
        self.loop.setCheckState(QtCore.Qt.CheckState(False))
        self.cycle_thread.terminate()
        self.reset()
    
    def reset(self):
        print("reseting")
        self.work_input.setDisabled(False)
        self.rest_input.setDisabled(False)
        self.pause_button.setDisabled(False)
        
        self.progress_bar.setValue(0)
        self.is_working = True        
        
        self.message_box.setText("")
        
        self._update_button(self.btn, "Start", self.start_cycle)
        self._update_button(self.pause_button, "New Target", self.enable_big_time)
        
        self._set_fill(WHITE_BACKGROUND)
        
    def big_reset(self):
        pass
    
    def pause(self):
        self.cycle_thread.pause = True
        self._set_fill(BLUE_BACKGROUND)        
        self.message_box.setText("Paused")
        self._update_button(self.pause_button, "Unpause", self.unpause)
        
    def unpause(self):        
        self.cycle_thread.pause = False
        if self.is_working:
            self._fill_red()
            self.message_box.setText("Working Time")
        else:
            self._fill_green()
            self.message_box.setText("Resting Time")
        self._update_button(self.pause_button, "Pause", self.pause)
        
    def enable_big_time(self):
        self.btn.setDisabled(True)
        self.big_time_input.setDisabled(False)
        self._update_button(self.pause_button, "Set Target", self.set_target)
    
    def set_target(self):
        new_big_time = QTime_to_secs(self.big_time_input.time())
        print(new_big_time, self.big_time)
        if new_big_time != self.big_time:
            self.big_time = new_big_time
            self.big_time_remaining = self.big_time
            self.big_time_set = True
        self.btn.setDisabled(False)
        self._update_button(self.pause_button, "Pause", self.pause)
        
class DoCycleThread(QtCore.QThread):    
    
    started_sig = QtCore.Signal()
    paused_sig = QtCore.Signal(float)
    update_sig = QtCore.Signal((float, float))
    done_sig = QtCore.Signal()
    
    def __init__(self, time):
        super(DoCycleThread, self).__init__()
        self.time = time
        self.pause = False
        
    def run(self):
        print("run ... run from inside the thread")
        self.started_sig.emit()
        self.update_sig.emit(0, 0)
        increment = self.time / SEGMENT_NUM
        for x in range(1, SEGMENT_NUM + 1):
            while self.pause:
                time.sleep(0.75)
                self.paused_sig.emit(0.75)
            time.sleep(increment)
            self.update_sig.emit((float(x) * (100 / SEGMENT_NUM)), increment)
        self.done_sig.emit()
        

def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
