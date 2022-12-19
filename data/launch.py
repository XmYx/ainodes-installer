import os, sys
import subprocess

from platform import platform
# Determine the location of the executable

def create_venv(venv_path):
    subprocess.run(["pythonw", "-m", "virtualenv", "--python=python3.10", venv_path])


def activate_venv(venv_path):
    activate_this = os.path.join(venv_path, "Scripts", "activate.bat")
    subprocess.run([activate_this])
    #exec(open(activate_this).read(), {'__file__': activate_this})

if __name__ == "__main__":
    subprocess.run(["pip", "install", "-q", "virtualenv"])
    print(os.path.exists("test_venv"))
    if os.path.exists("test_venv") == False:
        create_venv("test_venv")
        subprocess.run(["git", "clone", "https://github.com/XmYx/ainodes-pyside"])
    try:
        subprocess.run(["git", "pull"])
    except:
        pass

    if 'Windows' in platform():
        python = "test_venv/Scripts/pythonw.exe"
        activate_this = os.path.join(os.path.dirname(os.path.abspath(__file__)) + "/test_venv/Scripts/activate_this.py")
    else:
        python = "test_venv/bin/python"
        activate_this = "test_venv/bin/activate_this.py"

    exec(open(activate_this).read(), {'__file__': activate_this})
    subprocess.run([python, "data/installer.py"])