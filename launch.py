import os
import subprocess
subprocess.run(["pip", "install", "-q", "virtualenv"])
from platform import platform

def create_venv(venv_path):
    subprocess.run(["python", "-m", "virtualenv", "--python=python3.10", venv_path])


def activate_venv(venv_path):
    activate_this = os.path.join(venv_path, "Scripts", "activate.bat")
    subprocess.run([activate_this])
    #exec(open(activate_this).read(), {'__file__': activate_this})

if __name__ == "__main__":
    if not os.path.exists("test_venv"):
        create_venv("test_venv")
        subprocess.run(["git", "clone", "https://github.com/XmYx/ainodes-pyside"])
    if 'Windows' in platform():
        python = "test_venv/Scripts/python.exe"
    else:
        python = "test_venv/bin/python"
    activate_this = "test_venv/Scripts/activate_this.py"
    exec(open(activate_this).read(), {'__file__': activate_this})
    subprocess.run([python, "installer.py"])