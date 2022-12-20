import importlib
import os
import subprocess
import sys
import shutil
import pkg_resources



subprocess.run(["pip", "install", "-q", "pyside6"])
from PySide6.QtGui import QIcon
subprocess.run(["pip", "install", "-q", "huggingface-hub"])
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox, QLineEdit, QCheckBox
from huggingface_hub import hf_hub_download
python = sys.executable
index_url = os.environ.get('INDEX_URL', "")
from platform import platform
#print(platform())
os.makedirs('pip_cache', exist_ok=True)
os.putenv("PIP_CACHE_DIR", "pip_cache")



from PySide6 import QtWidgets, QtGui
dir_repos = "ainodes-pyside/src"




def create_windows_shortcut():
    if "ainodes-pyside" in os.getcwd():
        os.chdir("..")
    try:
        subprocess.run(["pip", "install", "-q", "pypiwin32"])
    except:
        pass
    try:
        subprocess.run(["pip", "install", "-q", "pywin32"])
    except:
        pass
    try:
        import win32com.client
    except:
        return
    # Set the path to the file or directory that you want to create a shortcut for

    target = os.path.join(os.getcwd(), "launch.exe")


    # Create the shortcut
    shell = win32com.client.Dispatch("WScript.Shell")

    # Get the path to the desktop folder
    shortcut_path = shell.SpecialFolders("Desktop")
    # Set the name and location for the shortcut
    shortcut_name = "aiNodes Launcher.lnk"
    if not os.path.exists(os.path.join(shortcut_path, shortcut_name)):
        #shortcut_path = r"C:\Users\Username\Desktop"
        shortcut = shell.CreateShortcut(os.path.join(shortcut_path, shortcut_name))

        # Set the shortcut's properties
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = os.path.join(os.getcwd(), "splash_2.ico")

        # Save the shortcut
        shortcut.Save()

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

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        #self.initUI()

        self.installButton = QtWidgets.QPushButton('Install / Update All', self)
        self.installButton.clicked.connect(self.installPackages)

        # Create a layout to hold the list widget and button
        layout = QtWidgets.QVBoxLayout(self)

        os.chdir("ainodes-pyside")
        self.setWindowTitle("aiNodes Launcher")
        self.setWindowIcon(QIcon("data/splash_2.ico"))
        # Fetch the list of branches
        output = subprocess.run(["git", "branch", "-a"], capture_output=True).stdout
        # Split the output into a list of branches
        branches = output.decode().strip().split("\n")
        #print(branches)
        # Create the QComboBox
        self.branch_select = QComboBox()

        # Populate the QComboBox with the list of branches
        x = 0
        for branch in branches:
            if "/" in branch and ">" not in branch:
                item = branch.split('/')[2]
                self.branch_select.addItem(item)
                if item == 'main':
                    self.branch_select.setCurrentIndex(x)
                x += 1
        os.chdir("..")

        self.token_label = QLabel("Enter Huggingface Token:")
        self.token_edit = QLineEdit()
        self.model_select = QComboBox()

        self.models = ("1.4", "1.5", "2.0 768", "2.1 768", "1.5 Inpaint", "2.0 Inpaint")
        self.model_select.addItems(self.models)
        self.model_download = QPushButton("Download Model")
        self.model_download.clicked.connect(self.download_hf_model)
        self.shortcut = QCheckBox("Create Desktop shortcut")
        #layout.addWidget(self.packageList)
        layout.addWidget(self.installButton)

        layout.addWidget(self.token_label)
        layout.addWidget(self.token_edit)
        layout.addWidget(self.model_select)
        layout.addWidget(self.model_download)

        layout.addWidget(self.branch_select)
        if "Windows" in platform():
            layout.addWidget(self.shortcut)
        if self.check_if_ainodes_can_start() == True:
            self.runButton = QtWidgets.QPushButton('Run aiNodes', self)
            self.runButton.clicked.connect(self.run_aiNodes)
            layout.addWidget(self.runButton)
        self.branch_select.currentIndexChanged.connect(self.update_ainodes)
    def check_if_ainodes_can_start(self):
        can_start = True
        with open('data/requirements.txt', 'r') as f:
            for line in f:
                package = line.strip()
                if not is_package_installed(package.split('==')[0]):
                    can_start = False
        return can_start

    def initUI(self):
        #Set Window title, icon, and stylesheet:

        # Create a list widget to display the packages
        self.packageList = QtWidgets.QListWidget(self)
        self.install_buttons = {}
        # Read the requirements.txt file and add each package to the list widget
        with open('data/requirements_versions.txt', 'r') as f:
            for line in f:
                package = line.strip()
                #print(package.split('==')[0])
                # Check if the package is installed and set the item's color accordingly
                #if self.isPackageInstalled(package.split('==')[0]):
                #    item.setForeground(QtGui.QColor('green'))
                #else:
                #    item.setForeground(QtGui.QColor('red'))

                item = QtWidgets.QListWidgetItem()
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
                    button.setStyleSheet("background-color: green")
                    layout.addWidget(button)
                elif package == 'ainodes':
                    button.setText("Update")
                    layout.addWidget(button)
                else:
                    item.setForeground(QtGui.QColor('red'))
                    button.setStyleSheet("background-color: red")
                    layout.addWidget(button)


                self.packageList.addItem(item)
                self.packageList.setItemWidget(item, widget)

        # Create a button to install all the packages

    def download_hf_model(self):
        if "ainodes-pyside" in os.getcwd():
            os.chdir("..")
        model = self.model_select.currentText()
        if model == "1.4":
            repo_id = "CompVis/stable-diffusion-v-1-4-original"
            filename = "sd-v1-4.ckpt"
        elif model == "1.5":
            repo_id = "runwayml/stable-diffusion-v1-5"
            filename = "v1-5-pruned-emaonly.ckpt"
        elif model == "1.5 Inpaint":
            repo_id = "runwayml/stable-diffusion-inpainting"
            filename = "sd-v1-5-inpaint.ckpt"
        elif model == "2.0 768":
            repo_id = "stabilityai/stable-diffusion-2"
            filename = "768-v-ema.ckpt"
        elif model == "2.0 Inpaint":
            repo_id = "stabilityai/stable-diffusion-2-inpainting"
            filename = "512-inpainting-ema.ckpt"
        elif model == "2.1 768":
            repo_id = "stabilityai/stable-diffusion-2-1"
            filename = "v2-1_768-ema-pruned.ckpt"

        destpath = os.path.join("ainodes-pyside/data/models", filename)
        if not os.path.exists(destpath):
            downloaded_model_path = hf_hub_download(repo_id=repo_id, filename=filename,
                                                    use_auth_token=self.token_edit.text(),
                                                    cache_dir='ainodes-pyside/data/models',
                                                    )
            shutil.copy(downloaded_model_path, destpath)
        else:
            print(f"{destpath} already exists")

    def install_package(self):
        if "ainodes-pyside" in os.getcwd():
            os.chdir("..")
        print(self.sender())
        python = "python"
        button = self.sender()
        requirement = self.install_buttons[button]
        if 'torch' in requirement:
            torch_command = os.environ.get('TORCH_COMMAND',
                                           "pip install torch==1.13.0+cu117 torchvision==0.14.0+cu117 --extra-index-url https://download.pytorch.org/whl/cu117")

            run(f'{torch_command}', "Installing torch and torchvision", "Couldn't install torch")
        elif 'xformers' in requirement:
            if 'Windows' in platform():
                subprocess.run(["pip", "install", "xformers-0.0.15.dev0+4601d9d.d20221216-cp310-cp310-win_amd64.whl"])
            else:
                subprocess.run(["pip", "install", "xformers"])
        elif 'ainodes' in requirement:
            if not os.path.exists("ainodes-pyside"):
                subprocess.run(["git", "clone", "https://github.com/XmYx/ainodes-pyside"])
            else:
                self.update_ainodes()
        else:
            subprocess.run(["pip", "install", requirement, "--upgrade"])

        print(self.install_buttons[button])
        selected_item = self.packageList.currentItem()

        # Replace the selected item with the new item
        self.packageList.takeItem(self.packageList.row(selected_item))
        item = QtWidgets.QListWidgetItem()
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        label = QLabel(requirement)
        button = QPushButton("Install")
        button.setMaximumWidth(200)
        button.clicked.connect(self.install_package)
        self.install_buttons[button] = requirement
        layout.addWidget(label)
        item.setSizeHint(widget.sizeHint())

        if is_package_installed(requirement.split('==')[0]):
            item.setForeground(QtGui.QColor('green'))
            button.setText("Reinstall")
            button.setStyleSheet("background-color: green")
            layout.addWidget(button)
        elif requirement == 'ainodes':
            button.setText("Update")
            layout.addWidget(button)
        else:
            item.setForeground(QtGui.QColor('red'))
            button.setStyleSheet("background-color: red")
            layout.addWidget(button)

        self.packageList.insertItem(self.packageList.row(selected_item), item)        #reinitUI()
    def run_aiNodes(self):
        print(f"Launching SD UI")
        #launch = 'frontend/main_app.py'
        #exec(open(launch).read(), {'__file__': launch})
        if "Windows" in platform():
            if self.shortcut.isChecked():
                create_windows_shortcut()
        sys.path.append('ainodes-pyside')

        import frontend.startup_new
        print(os.getcwd())
        if "ainodes-pyside" not in os.getcwd():
            os.chdir("ainodes-pyside")
        frontend.startup_new.run_app()

    def update_ainodes(self):
        if "ainodes-pyside" not in os.getcwd():
            os.chdir("ainodes-pyside")
        branch = self.branch_select.currentText()

        if '/' in branch:
            branch = branch.split('/')[2]
        elif '*' in branch:
            branch = branch.replace("* ", "")
        else:
            branch = branch
        subprocess.run(["git", "checkout", branch])
        # Run the git pull command
        subprocess.run(["git", "pull"])

        os.chdir("..")

    def isPackageInstalled(self, package):
        """Returns True if the given package is installed, False otherwise."""
        installed = subprocess.run(["pip", "freeze"], capture_output=True)
        return installed
    def installPackages(self):
        if "ainodes-pyside" in os.getcwd():
            os.chdir("..")

        """Installs all the packages listed in the requirements.txt file."""
        torch_command = os.environ.get('TORCH_COMMAND',
                                       "pip install torch==1.13.0+cu117 torchvision==0.14.0+cu117 --extra-index-url https://download.pytorch.org/whl/cu117")

        run(f'{torch_command}', "Installing torch and torchvision", "Couldn't install torch")

        subprocess.run(['pip', 'install', "--extra-index-url", "https://download.pytorch.org/whl/cu117", '-r', 'data/requirements.txt'])

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

        lavis_repo = os.environ.get('LAVIS_REPO', 'https://github.com/salesforce/LAVIS.git')
        lavis_commit_hash = os.environ.get('LAVIS_COMMIT_HASH', '8a261e309a413c2f426243151a450f9792283f67')
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
        git_clone(lavis_repo, repo_dir('lavis'), "lavis", lavis_commit_hash)
        #git_clone(volta_ml_repo, repo_dir('volta-ml'), "volta-ml", volta_ml_hash)

        if not is_installed("lpips"):
            run_pip(f"install -r {os.path.join(repo_dir('CodeFormer'), 'requirements.txt')}", "requirements for CodeFormer")
        if not is_installed("gfpgan"):
            run_pip(f"install {gfpgan_package}", "gfpgan")
            run_pip(f"install {gfpgan_package}", "gfpgan")

        if not is_installed("clip"):
            run_pip(f"install {clip_package}", "clip")
        if not is_installed("deepdanbooru"):
            run_pip(
                f"install {deepdanbooru_package}#egg=deepdanbooru[tensorflow] tensorflow==2.10.0 tensorflow-io==0.27.0",
                "deepdanbooru")

        try:
            if 'Windows' in platform():
                subprocess.run(["pip", "install", "data/xformers-0.0.15.dev0+4601d9d.d20221216-cp310-cp310-win_amd64.whl"])
            else:
                subprocess.run(["pip", "install", "xformers"])
        except:
            pass
        restart_app()
def reinitUI():
    global window
    #window.destroy()
    #window = MainWindow()
    #window.show()
    window.layout().removeWidget(window.packageList)
    window.initUI()
    window.layout().addWidget(window.packageList)

def restart_app():
    # Re-start the application
    activate_this = "launch.exe"
    app.closeAllWindows()
    subprocess.run([activate_this])


if __name__ == '__main__':
    #download_model()
    global window
    #create_venv('test_venv')
    #activate_venv('test_venv')
    app = QtWidgets.QApplication()
    window = MainWindow()
    sshFile="data/QTDark.stylesheet"
    with open(sshFile,"r") as fh:
        window.setStyleSheet(fh.read())


    window.show()

    print('''
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                   │
│                        xxxx                                        xx                             │
│                        xxxxxxx             xxx                     xx                             │
│                        xxxxxxxx           xxxx                     xx                             │
│                 x      xxxxxxxx           xxx                     xx                              │
│                xxx     xxxxxxxxx         xxx                      xx                              │
│                 x      xxxx xxxx         xxx                      xx      xxxx         xxxx       │
│                        xxxx  xxxx        xx                      xxx    xxxxxxxx    xxxxxxxxxx    │
│     xxxxxxx    xx      xxxx   xxxx      xxx   xxxx        xxx    xx    xxx    xxx  xxxx    xxx    │
│   xxx    xxx    x      xxxx    xxx      xx  xxxxxxxx    xxxxxxx  xx   xx       xx  xxx            │
│  xx       xx    x      xxxx     xxx    xxx xx     xx  xxx     xxxxx  xxx      xx   xxx   xxxx     │
│ xxx       xx    x     xxxxx      xxx   xxxxx       xx xx        xxx  xxxx    xxx    xxxxxxxxxx    │
│ xx         x   xxx    xxxxx       xxx  xx xx       xxxx         xxx xxxxxxxxxx        xxxx   xxx  │
│ xx        xxxx xxx  xxxxxxxx        xxxxx xx       xxxx        xxxx xx    xx                  xxx │
│ xxx      xxxxxxxxxxxxxx xxxx         xxxx xx      xxxxxx       xxx  xx         xx  xxx        xx  │
│  xxxxxxxxxx xxxx xxxx    xxx          xxx xxxxxxxxx   xxxxxxxxxxxx   xxx      xx    xxx     xxx   │
│     xxxx     xx   x        x          xx    xxxxx      xxxxxxxxx       xxxxxxxx      xxxxxxxxx    │
│                                                                                                   │
│                       Welcome to aiNodes, your Desktop AI Art Generator Suite                     │
│                         featuring Deforum Art Animation and Aesthetic Engine                      │
│                           Please use the launcher to install dependencies                         │
│                      and to update the application, download vanilla SD models                    │
│                                                                                                   │
│                      Please consider supporting the project via patreon at:                       │
│                                     www.patreon.com/ainodes                                       │
│                                     www.patreon.com/deforum                                       │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
    ''')

    app.exec()
