from PySide2 import QtGui, QtMultimedia
import sys

if len(sys.argv) > 1 and '--dev' in sys.argv:
    DEBUG = True
else:
    DEBUG = False

DEFAULT_WORK_TIME = 25 * 60  # s
DEFAULT_REST_TIME = 5 * 60  # s
DEFAULT_TARGET_TIME = 3 * 60 * 60  # s

if DEBUG:
    DEFAULT_WORK_TIME = 3  # s
    DEFAULT_REST_TIME = 3  # s
    DEFAULT_TARGET_TIME = 10  # s

MIN_WORTH_SAVING = 30  # s

if DEBUG:
    MIN_WORTH_SAVING = 1  # s

RED_BACKGROUND = QtGui.QColor(255, 150, 150)
GREEN_BACKGROUND = QtGui.QColor(150, 255, 150)
BLUE_BACKGROUND = QtGui.QColor(200, 200, 255)
WHITE_BACKGROUND = QtGui.QColor(255, 255, 255)

START_ALARM_PATH = "start.wav"
END_ALARM_PATH = "end.wav"

ALERTS = {
    'happy': QtMultimedia.QSound(END_ALARM_PATH),
    'sad': QtMultimedia.QSound(START_ALARM_PATH)
}

DELTA_T = 0.01