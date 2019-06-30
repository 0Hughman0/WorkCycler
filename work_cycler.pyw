import sys
import time
import json
import dataclasses

from PySide2 import QtCore
from PySide2.QtWidgets import (QMainWindow, QWidget, QApplication,
                               QMenu, QAction,
                               QVBoxLayout, QHBoxLayout,
                               QLineEdit, QLabel, QTimeEdit, QProgressBar, QPushButton, QCheckBox, QMessageBox,
                               QFileDialog)

import config as conf
import views
import functools


def transition(f):
    """
    Wrap methods that transition the GUI from one view to another.

    Transition methods should return the view to transition to.
    """

    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        view = f(self, *args, **kwargs)
        if not isinstance(view, views.View):
            raise TypeError("Transitions should return a view to transition to!")
        self._update_view(view)
        return view

    return wrapped


def QTime_to_secs(time):
    return QtCore.QTime(0, 0, 0).secsTo(time)


def secs_to_QTime(secs):
    return QtCore.QTime(0, 0, 0).addSecs(secs)


@dataclasses.dataclass
class State:
    """
    Keeps track of values the user interacts with. Also facilitates saving a loading.
    """

    __savables__ = ['name', 'target_time', 'work_time', 'rest_time', 'target_progress']

    name: str = 'Name Me'

    work_time: float = conf.DEFAULT_WORK_TIME
    rest_time: float = conf.DEFAULT_REST_TIME

    progress: float = 0.0
    view: views.View = views.READY
    last_view: views.View = views.READY

    target_time: float = conf.DEFAULT_TARGET_TIME
    target_progress: float = 0.0

    @property
    def progressage(self):
        if self.view is views.WORKING:
            return 100 * self.progress / self.work_time
        elif self.view is views.RESTING:
            return 100 * self.progress / self.rest_time
        return 0.0

    @property
    def Qwork_time(self):
        return secs_to_QTime(self.work_time)

    @property
    def Qrest_time(self):
        return secs_to_QTime(self.rest_time)

    @property
    def Qtarget_time(self):
        return secs_to_QTime(self.target_time)

    @property
    def target_progressage(self):
        return 100 * self.target_progress / self.target_time

    def open(self, path):
        with open(path) as file:
            save_dict = json.load(file)
            for attr in self.__savables__:
                val = save_dict.get(attr)
                if val:
                    setattr(self, attr, val)

    def save(self, path):
        with open(path, 'w') as file:
            json.dump({attr: value for attr, value
                       in self.__dict__.items()
                       if attr in self.__savables__}, file)


class Window(QMainWindow):

    instance = None
    
    def __init__(self, argv):
        super(Window, self).__init__()
        self.state = State()

        if len(argv) > 1:
            try:
                self.state.open(argv[1])
            except (FileNotFoundError):
                self.state = State()

        Window.instance = self

        self.menu = self.menuBar()

        self.name_box = QLineEdit(self.state.name)

        self.big_progress_bar = QProgressBar(self)
        self.target_input = QTimeEdit(self, displayFormat="hh:mm:ss")
        self.work_input = QTimeEdit(self, displayFormat="mm:ss")
        self.rest_input = QTimeEdit(self, displayFormat="mm:ss")

        self.startstop_button = QPushButton('Start', self)
        self.modify_button = QPushButton("Pause", self)

        self.loop = QCheckBox(self)

        self.progress_bar = QProgressBar(self)

        self.message_box = QLineEdit("", self, readOnly=True)

        self._create_layout()

        self.cycle_thread = DoCycleThread(self.state,
                                          self._update_progress,
                                          self.done_work,
                                          self.done_rest,
                                          self.done_target)

        self._update_view(views.READY)

    def _create_layout(self):
        """
        Arrange all the bits within the GUI.
        """
        menu_bar = self.menuBar()
        file_menu = QMenu("File")
        menu_bar.addMenu(file_menu)

        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.open)
        file_menu.addAction(self.open_action)
        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.save)
        file_menu.addAction(self.save_action)

        space = QWidget()
        self.setCentralWidget(space)

        vbox = QVBoxLayout(space)
        space.setLayout(vbox)

        hbox0 = QHBoxLayout()
        hbox0.addWidget(self.name_box)
        
        vbox.addLayout(hbox0)
        hbox1 = QHBoxLayout()

        big_time_label = QLabel("Total Target HH:MM:SS")
        hbox1.addWidget(big_time_label)

        self.target_input.setTime(self.state.Qtarget_time)
        hbox1.addWidget(self.target_input)

        vbox.addLayout(hbox1)
        self.big_progress_bar.setTextVisible(False)
        vbox.addWidget(self.big_progress_bar)                                
        
        hbox2 = QHBoxLayout()
        hbox2.addStretch(2)
        
        work_time_label = QLabel("Work Length MM:SS")
        self.work_input.setTime(self.state.Qwork_time)
        hbox2.addWidget(work_time_label)
        hbox2.addWidget(self.work_input)

        rest_time_label = QLabel("Rest Length MM:SS")
        self.rest_input.setTime(self.state.Qrest_time)
        hbox2.addWidget(rest_time_label)
        hbox2.addWidget(self.rest_input)
        
        hbox2.addStretch(1)
        vbox.addLayout(hbox2)
                
        hbox3 = QHBoxLayout()
        hbox3.addStretch(1)

        hbox3.addWidget(self.startstop_button)
        hbox3.addWidget(self.modify_button)
                
        loop_label = QLabel("Loop around?")
        self.loop.setToolTip("loop?")
        
        hbox3.addWidget(loop_label)
        hbox3.addWidget(self.loop)
        hbox3.addStretch(1)
        
        vbox.addLayout(hbox3)
        
        self.progress_bar.setTextVisible(False)
        vbox.addWidget(self.progress_bar)

        self.message_box.setAlignment(QtCore.Qt.AlignHCenter)
        vbox.addWidget(self.message_box)

        self.work_input.selectAll()
       
        self.setWindowTitle('Work Cycler')
        self.show()

    def _update_view(self, view):
        """
        Transition to a new view
        """
        self.state.last_view = self.state.view
        self.state.view = view

        self.save_action.setDisabled(view.save_action.disabled)
        self.open_action.setDisabled(view.open_action.disabled)

        self.message_box.setText(view.status)
        self.name_box.setDisabled(view.name_box.disabled)

        self.target_input.setDisabled(view.target_input.disabled)
        self.work_input.setDisabled(view.work_input.disabled)
        self.rest_input.setDisabled(view.rest_input.disabled)

        self._update_button(self.startstop_button, view.startstop_button)
        self._update_button(self.modify_button, view.modify_button)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), view.background_colour)
        self.setPalette(palette)

    def _update_button(self, button, btn_view):
        button.setDisabled(btn_view.disabled)
        button.setText(btn_view.text)
        try:
            button.clicked.disconnect()
        except RuntimeError:
            pass
        """
        This bit is weird upsetting but necessary. The sexy (IMO) way of binding my buttons to Window's methods does so 
        before those methods are bound to an instance of Window. So the self parameter is not filled. For reasons
        that I don't understand, _update_button is not always called by the Window instance. This dirty workaround 
        ensures the correct instance is passed to binds. 
        """
        button.clicked.connect(lambda: btn_view.bind(Window.instance))  # <-

    def _alert(self, alert, message):
        QApplication.beep()
        QApplication.alert(self)
        QApplication.setActiveWindow(self)

        alert = conf.ALERTS[alert]
        alert.setLoops(4)
        alert.play()
        if not self.loop.isChecked():
            wait = QMessageBox.information(self, "Alert", message)
        alert.stop()

    def _update_progress(self):
        progress, prog_percent = self.state.progress, self.state.progressage
        self.progress_bar.setValue(prog_percent)
        self.progress_bar.setToolTip(f'{prog_percent:.1f}% ({self.state.progress / 60:.0f} min)')

        t_progress, t_prog_percent = self.state.target_progress, self.state.target_progressage
        self.big_progress_bar.setValue(t_prog_percent)
        self.big_progress_bar.setToolTip(f'{t_prog_percent:.1f}% ({t_progress / 60:.0f} min)')

    def _start_cycle(self, cycle):
        self.state.progress = 0.0
        self.state.view = cycle
        self.cycle_thread.start()

    """
    Callbacks ####################################
    """

    def save(self):
        self.state.name = self.name_box.text()
        filename, _ = QFileDialog.getSaveFileName(self,
                                                  "Save Cycle", "{}.todo".format(self.state.name),
                                                  filter='Todos (*.todo);; All files (*)')
        if filename:
            self.state.save(filename)

    def open(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Cyle", filter='Todos (*.todo);; All files (*)')
        if filename:
            self.state.open(filename)

        self.cycle_thread.terminate()

        self.name_box.setText(self.state.name)
        self.target_input.setTime(self.state.Qtarget_time)
        self.big_progress_bar.setValue(self.state.target_progressage)
        self.work_input.setTime(self.state.Qwork_time)
        self.rest_input.setTime(self.state.Qrest_time)
        self._update_progress()

    @views.READY.modify_button.connect
    @transition
    def new_target(self):
        return views.NEW_TARGET

    @views.READY.startstop_button.connect
    @transition
    def start(self):
        self.state.work_time = QTime_to_secs(self.work_input.time())
        self.state.rest_time = QTime_to_secs(self.rest_input.time())

        self._start_cycle(views.RESTING)
        return views.WORKING

    @views.WORKING.startstop_button.connect
    @views.RESTING.startstop_button.connect
    @views.PAUSED.startstop_button.connect
    @transition
    def stop(self):
        self.state.progress = 0.0
        self._update_progress()
        self.cycle_thread.terminate()
        return views.READY

    @views.WORKING.modify_button.connect
    @views.RESTING.modify_button.connect
    @transition
    def pause(self):
        return views.PAUSED

    @views.PAUSED.modify_button.connect
    @transition
    def unpause(self):
        return self.state.last_view

    @views.NEW_TARGET.modify_button.connect
    @transition
    def set_target(self):
        new_big_time = QTime_to_secs(self.target_input.time())
        if any((self.state.target_progress == 0.0,  # we're done
                new_big_time != self.state.target_time)):  # or we've changed target
            self.state.target_time = new_big_time
            self.state.target_progress = 0.0
            self._update_progress()
        return views.READY

    @transition
    def done_work(self):
        self._alert('happy', 'Work time is over :D') # params!
        self._start_cycle(views.RESTING)
        return views.RESTING

    @transition
    def done_rest(self):
        self._alert('sad', 'Time to get back to work D:')
        if self.loop.isChecked():
            self._start_cycle(views.WORKING)
            return views.WORKING
        else:
            return views.READY

    @transition
    def done_target(self):
        self._alert('happy', 'Woohoo target reached')
        self.state.progress = 0.0
        self.state.target_progress = 0.0
        return views.DONE


class DoCycleThread(QtCore.QThread):

    update_sig = QtCore.Signal()
    done_work_sig = QtCore.Signal()
    done_rest_sig = QtCore.Signal()
    done_target_sig = QtCore.Signal()
    
    def __init__(self, state, update, done_work, done_rest, done_target):
        super(DoCycleThread, self).__init__()
        self.state = state
        self.update_sig.connect(update)
        self.done_work_sig.connect(done_work)
        self.done_rest_sig.connect(done_rest)
        self.done_target_sig.connect(done_target)

    def run(self):
        while self.state.progressage <= 100.0:
            if self.state.target_progressage >= 100.0:
                self.done_target_sig.emit()
                break

            self.state.progress += conf.DELTA_T

            if self.state.view is views.WORKING:
                self.state.target_progress += conf.DELTA_T

            self.update_sig.emit()

            time.sleep(conf.DELTA_T)

            while self.state.view is views.PAUSED:
                time.sleep(conf.DELTA_T)
        else: # will only run if no break
            if self.state.view is views.WORKING:
                self.done_work_sig.emit()
            if self.state.view is views.RESTING:
                self.done_rest_sig.emit()


def main():
    app = QApplication(sys.argv)
    ex = Window(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
