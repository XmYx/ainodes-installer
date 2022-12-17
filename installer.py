import importlib
import os
import subprocess
import sys

import pkg_resources
subprocess.run(["pip", "install", "pyside6"])
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel



python = sys.executable
index_url = os.environ.get('INDEX_URL', "")



from PySide6 import QtWidgets, QtGui
dir_repos = "ainodes-pyside/src"

def run_pip(args, desc=None):
    index_url_line = f' --index-url {index_url}' if index_url != '' else ''
    return run(f'"{python}" -m pip {args} --prefer-binary{index_url_line}', desc=f"Installing {desc}", errdesc=f"Couldn't install {desc}")


def is_installed(package):
    try:
        spec = importlib.util.find_spec(package)
    except ModuleNotFoundError:
        return False

    return spec is not None

def repo_dir(name):
    return os.path.join(dir_repos, name)

def run(command, desc=None, errdesc=None):
    if desc is not None:
        print(desc)

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    if result.returncode != 0:

        message = f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}
stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout)>0 else '<empty>'}
stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr)>0 else '<empty>'}
"""
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")

git = os.environ.get('GIT', "git")
def git_clone(url, dir, name, commithash=None):
    # TODO clone into temporary dir and move if successful

    if os.path.exists(dir):
        #sys.path.append(os.path.join(os.getcwd(),dir))
        if commithash is None:
            return

        current_hash = run(f'"{git}" -C {dir} rev-parse HEAD', None, f"Couldn't determine {name}'s hash: {commithash}").strip()
        if current_hash == commithash:
            return

        run(f'"{git}" -C {dir} fetch', f"Fetching updates for {name}...", f"Couldn't fetch {name}")
        run(f'"{git}" -C {dir} checkout {commithash}', f"Checking out commit for {name} with hash: {commithash}...", f"Couldn't checkout commit {commithash} for {name}")
        return

    run(f'"{git}" clone "{url}" "{dir}"', f"Cloning {name} into {dir}...", f"Couldn't clone {name}")

    if commithash is not None:
        run(f'"{git}" -C {dir} checkout {commithash}', None, "Couldn't checkout {name}'s hash: {commithash}")

def create_venv(venv_path):
    subprocess.run(["python", "-m", "virtualenv", "--python=python3.10", venv_path])


def is_package_installed(package_name):
    try:
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False

def activate_venv(venv_path):
    activate_this = os.path.join(venv_path, "Scripts", "activate.bat")
    subprocess.run([activate_this])
    print(is_package_installed("k-diffusion"))
    python = "test_venv/Scripts/python.exe"
    print(subprocess.run([python, "--version"]))

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.installButton = QtWidgets.QPushButton('Install All', self)
        self.installButton.clicked.connect(self.installPackages)

        self.runButton = QtWidgets.QPushButton('Run aiNodes', self)
        self.runButton.clicked.connect(self.run_aiNodes)
        # Create a layout to hold the list widget and button
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.packageList)
        layout.addWidget(self.installButton)
        layout.addWidget(self.runButton)

    def initUI(self):
        # Create a list widget to display the packages
        self.packageList = QtWidgets.QListWidget(self)
        self.install_buttons = {}
        # Read the requirements.txt file and add each package to the list widget
        with open('requirements_versions.txt', 'r') as f:
            for line in f:
                package = line.strip()
                item = QtWidgets.QListWidgetItem()
                #print(package.split('==')[0])
                # Check if the package is installed and set the item's color accordingly
                #if self.isPackageInstalled(package.split('==')[0]):
                #    item.setForeground(QtGui.QColor('green'))
                #else:
                #    item.setForeground(QtGui.QColor('red'))


                widget = QWidget()
                layout = QHBoxLayout()
                widget.setLayout(layout)
                label = QLabel(package)
                button = QPushButton("Install")
                button.setMaximumWidth(200)
                button.clicked.connect(self.install_package)
                self.install_buttons[button] = package

                layout.addWidget(label)
                item.setSizeHint(widget.sizeHint())

                if is_package_installed(package.split('==')[0]):
                    item.setForeground(QtGui.QColor('green'))
                    button.setText("Reinstall")
                    layout.addWidget(button)
                else:
                    item.setForeground(QtGui.QColor('red'))
                    layout.addWidget(button)


                self.packageList.addItem(item)
                self.packageList.setItemWidget(item, widget)

        # Create a button to install all the packages
    def install_package(self):
        python = "python"
        button = self.sender()
        requirement = self.install_buttons[button]
        if 'torch' in requirement:
            torch_command = os.environ.get('TORCH_COMMAND',
                                           "pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117")

            run(f'{torch_command}', "Installing torch and torchvision", "Couldn't install torch")
        elif 'xformers' in requirement:
            subprocess.run(["pip", "install", "xformers-0.0.15.dev0+4601d9d.d20221216-cp310-cp310-win_amd64.whl"])
        else:
            subprocess.run(["pip", "install", requirement])
        reinitUI()
    def run_aiNodes(self):
        print(f"Launching SD UI")
        #launch = 'frontend/main_app.py'
        #exec(open(launch).read(), {'__file__': launch})

        sys.path.append('ainodes-pyside')
        import frontend.startup
        frontend.startup.run_app()

    def isPackageInstalled(self, package):
        """Returns True if the given package is installed, False otherwise."""
        installed = subprocess.run(["pip", "freeze"], capture_output=True)
        return installed
    def installPackages(self):
        """Installs all the packages listed in the requirements.txt file."""
        subprocess.run(['pip', 'install', "--extra-index-url", "https://download.pytorch.org/whl/cu117", '-r', 'requirements.txt'])

        gfpgan_package = os.environ.get('GFPGAN_PACKAGE', "git+https://github.com/TencentARC/GFPGAN.git@8d2447a2d918f8eba5a4a01463fd48e45126a379")
        clip_package = os.environ.get('CLIP_PACKAGE', "git+https://github.com/openai/CLIP.git@d50d76daa670286dd6cacf3bcd80b5e4823fc8e1")
        deepdanbooru_package = os.environ.get('DEEPDANBOORU_PACKAGE', "git+https://github.com/KichangKim/DeepDanbooru.git@d91a2963bf87c6a770d74894667e9ffa9f6de7ff")

        xformers_windows_package = os.environ.get('XFORMERS_WINDOWS_PACKAGE', 'https://github.com/C43H66N12O12S2/stable-diffusion-webui/releases/download/f/xformers-0.0.14.dev0-cp310-cp310-win_amd64.whl')

        stable_diffusion_repo = os.environ.get('STABLE_DIFFUSION_REPO', "https://github.com/CompVis/stable-diffusion.git")
        taming_transformers_repo = os.environ.get('TAMING_REANSFORMERS_REPO', "https://github.com/CompVis/taming-transformers.git")
        k_diffusion_repo = os.environ.get('K_DIFFUSION_REPO', 'https://github.com/crowsonkb/k-diffusion.git')
        codeformer_repo = os.environ.get('CODEFORMET_REPO', 'https://github.com/sczhou/CodeFormer.git')
        blip_repo = os.environ.get('BLIP_REPO', 'https://github.com/salesforce/BLIP.git')

        real_esrgan_repo = os.environ.get('REAL_ESRGAN_REPO', "https://github.com/xinntao/Real-ESRGAN.git")
        adabins_repo = os.environ.get('ADABINS_REPO', "https://github.com/osi1880vr/AdaBins.git")
        midas_repo = os.environ.get('MIDAS_REPO', 'https://github.com/isl-org/MiDaS.git')
        pytorch_lite_repo = os.environ.get('PYTORCH_LITE_REPO', 'https://github.com/osi1880vr/pytorch3d-lite.git')
        impro_aesthetic_repo = os.environ.get('IMPRO_AESTHETIC_REPO', 'https://github.com/christophschuhmann/improved-aesthetic-predictor.git')
        volta_ml_repo = os.environ.get('VOLTA_ML_REPO', 'https://github.com/VoltaML/voltaML-fast-stable-diffusion.git')

        stable_diffusion_commit_hash = os.environ.get('STABLE_DIFFUSION_COMMIT_HASH', "69ae4b35e0a0f6ee1af8bb9a5d0016ccb27e36dc")
        taming_transformers_commit_hash = os.environ.get('TAMING_TRANSFORMERS_COMMIT_HASH', "24268930bf1dce879235a7fddd0b2355b84d7ea6")
        k_diffusion_commit_hash = os.environ.get('K_DIFFUSION_COMMIT_HASH', "5b3af030dd83e0297272d861c19477735d0317ec")
        codeformer_commit_hash = os.environ.get('CODEFORMER_COMMIT_HASH', "c5b4593074ba6214284d6acd5f1719b6c5d739af")
        blip_commit_hash = os.environ.get('BLIP_COMMIT_HASH', "48211a1594f1321b00f14c9f7a5b4813144b2fb9")
        volta_ml_hash = os.environ.get('VOLTA_ML__HASH', "303d5f8df54f58987818722226a6398a9aed8aa6")

        real_esrgan_commit_hash = os.environ.get('REAL_ESRGAN_COMMIT_HASH', "5ca1078535923d485892caee7d7804380bfc87fd")
        adabins_commit_hash = os.environ.get('ADABINS_COMMIT_HASH', "4524615236f5f486381fac2f9c624f20dedf324f")
        midas_commit_hash = os.environ.get('MIDAS_COMMIT_HASH', "66882994a432727317267145dc3c2e47ec78c38a")
        pytorch_litet_hash = os.environ.get('PYTORCH_LITE_COMMIT_HASH', "4070975c1d6e4de7c87848a53b603f6b29711e55")
        impro_aesthetic_hash = os.environ.get('IMPRO_AESTHETIC_COMMIT_HASH', "fe88a163f4661b4ddabba0751ff645e2e620746e")
        git_clone(taming_transformers_repo, repo_dir('taming-transformers'), "Taming Transformers", taming_transformers_commit_hash)
        git_clone(k_diffusion_repo, repo_dir('k-diffusion'), "K-diffusion", k_diffusion_commit_hash)
        git_clone(codeformer_repo, repo_dir('CodeFormer'), "CodeFormer", codeformer_commit_hash)
        git_clone(blip_repo, repo_dir('BLIP'), "BLIP", blip_commit_hash)

        git_clone(real_esrgan_repo, repo_dir('realesrgan'), "Real ESRGAN", real_esrgan_commit_hash)
        git_clone(adabins_repo, repo_dir('AdaBins'), "AdaBins", adabins_commit_hash)
        git_clone(midas_repo, repo_dir('MiDaS'), "MiDaS", midas_commit_hash)
        git_clone(pytorch_lite_repo, repo_dir('pytorch3d-lite'), "pytorch3d-lite", pytorch_litet_hash)
        git_clone(impro_aesthetic_repo, repo_dir('improved-aesthetic-predictor'), "improved-aesthetic-predictor", impro_aesthetic_hash)
        #git_clone(volta_ml_repo, repo_dir('volta-ml'), "volta-ml", volta_ml_hash)

        if not is_installed("lpips"):
            run_pip(f"install -r {os.path.join(repo_dir('CodeFormer'), 'requirements.txt')}", "requirements for CodeFormer")


def reinitUI():
    global window
    #window.destroy()
    #window = MainWindow()
    #window.show()
    window.layout().removeWidget(window.packageList)
    window.initUI()
    window.layout().addWidget(window.packageList)

if __name__ == '__main__':
    global window
    #create_venv('test_venv')
    #activate_venv('test_venv')
    app = QtWidgets.QApplication()
    window = MainWindow()
    window.show()
    app.exec_()
