"""
Launch the forked barracuda-fsh/pyobd GUI with G37/HT500 defaults.

Just runs ./pyobd_fork/pyobd.py with the cwd set so its asset paths
(icon, ELM image) resolve. Once the GUI opens:
    Settings → OBD-II → Port:  COM3
                       Baud:  38400
                       Fast:  False (BT-friendly)
    Connection menu → Connect

This is the polished alternative to the custom Dear PyGui dashboard
in main.py. Both work side by side; pick whichever you prefer.
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORK = os.path.join(HERE, "pyobd_fork")

if not os.path.isdir(FORK):
    print("pyobd_fork/ is missing. Did you `git pull`?", file=sys.stderr)
    sys.exit(1)

os.chdir(FORK)
sys.path.insert(0, FORK)
runpy.run_path(os.path.join(FORK, "pyobd.py"), run_name="__main__")
