import dataclasses
from PySide2 import QtGui
import typing


RED_BACKGROUND = QtGui.QColor(255, 150, 150)
GREEN_BACKGROUND = QtGui.QColor(150, 255, 150)
BLUE_BACKGROUND = QtGui.QColor(200, 200, 255)
WHITE_BACKGROUND = QtGui.QColor(255, 255, 255)


@dataclasses.dataclass
class TimeInput:
    disabled: bool = False


@dataclasses.dataclass
class Button:
    disabled: bool = False
    text: str = ''
    bind: typing.Callable = None

    def connect(self, f):
        self.bind = f
        return f


@dataclasses.dataclass
class MenuItem:
    disabled: bool = True


@dataclasses.dataclass
class View:
    """
    Describes the appearance of the main window in various 'views'. Used to set the static values of widget parameters.

    Each views is a constant instance.
    """
    status: str = ''
    name_box: TimeInput = TimeInput()

    target_input: TimeInput = TimeInput()
    work_input: TimeInput = TimeInput()
    rest_input: TimeInput = TimeInput()

    startstop_button: Button = Button()
    modify_button: Button = Button()

    background_colour: QtGui.QColor = WHITE_BACKGROUND

    open_action: MenuItem = MenuItem()
    save_action: MenuItem = MenuItem()


READY = View(status='Ready',
             name_box=TimeInput(disabled=False),
             target_input=TimeInput(disabled=True),
             work_input=TimeInput(disabled=False),
             rest_input=TimeInput(disabled=False),
             startstop_button=Button(disabled=False, text='Start'),
             modify_button=Button(disabled=False, text='New Target'),
             background_colour=WHITE_BACKGROUND,
             save_action=MenuItem(disabled=False),
             open_action=MenuItem(disabled=False))


WORKING = View(status='Working',
               name_box=TimeInput(disabled=True),
               target_input=TimeInput(disabled=True),
               work_input=TimeInput(disabled=True),
               rest_input=TimeInput(disabled=True),
               startstop_button=Button(disabled=False, text='Stop'),
               modify_button=Button(disabled=False, text='Pause'),
               background_colour=RED_BACKGROUND)

RESTING = dataclasses.replace(WORKING,
                              status='Resting',
                              background_colour=GREEN_BACKGROUND)

PAUSED = dataclasses.replace(WORKING,
                             status='Paused',
                             background_colour=BLUE_BACKGROUND,
                             startstop_button=Button(disabled=True, text='Stop'),
                             modify_button=Button(disabled=False, text='Unpause'))

NEW_TARGET = dataclasses.replace(READY,
                                 status='Enter New Target',
                                 startstop_button=Button(disabled=True, text='Start'),
                                 modify_button=Button(disabled=False, text='Set Target'),
                                 target_input=TimeInput(disabled=False),
                                 work_input=TimeInput(disabled=True),
                                 rest_input=TimeInput(disabled=True))

DONE = dataclasses.replace(READY,
                           status='Done')
