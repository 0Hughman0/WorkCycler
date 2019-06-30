# WorkCycler
A simple program for working using the Pomodoro technique, or any other work and rest cycle for that matter!
Also serving as an example PySide2 application.

# Usage:

* Set how long you want to be working in total at the top.
* Set how long you want your segments of working time to be on the left.
* Set how long you want your resting periods to be on the right.
* Check the box if you want each cycle to automatically loop round.
* Press start!

Additional Features:
* Save and open previous cycles to keep track of old tasks.
* Set work_cycler as your default app to open `.todo` files.

Differing pop-ups and alarms will sound when it's time to stop and start working.

# Installation:

Windows:

* Simply copy the .exe found in the dist folder! (Tested Windows 10)

Other OS's or with Python

* Clone this repository to your desired location
* In your terminal of choice navigate to the WorkCycler folder
* Use pipenv to setup your environment with `pipenv install`
* Then simply run WorkCycler with `pipenv run work_cycler.pyw`

You can also make your own binary using something like pyinstaller, see `buildbin.bat` for recommended arguments.
