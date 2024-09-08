import os
import subprocess
import time
import urllib.request
import zipfile
import platform
import shutil
import sys

class InstallerApp:
    def __init__(self):
        self.temp_dir = os.path.join(os.path.expanduser("~"), "temp", "biliclear")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.project_name = "BiliClear-main"
        self.launcher_file = "launcher.py"
        self.python_installer = None
        self.system = platform.system()

        self.log(f"所有临时文件存放在: {self.temp_dir}")
        self.start_installation()

    def log(self, message):
        """在控制台中输出日志"""
        print(message)

    def start_installation(self):
        """启动安装程序"""
        self.log("启动安装程序...")
        self.check_and_install_python()
        self.download_and_extract_project()
        self.install_requirements()
        self.run_launcher()

    def check_and_install_python(self):
        """检测并安装 Python"""
        try:
            subprocess.run(["python", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.log("Python 已安装。")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("未检测到 Python，正在自动安装...")
            self.download_and_install_python()

    def download_and_install_python(self):
        """下载并静默安装 Python"""
        try:
            if self.system == "Windows":
                arch = platform.machine()
                if arch == "AMD64":
                    self.python_installer = "https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe"
                elif arch == "ARM64":
                    self.python_installer = "https://www.python.org/ftp/python/3.12.6/python-3.12.6-arm64.exe"
                else:
                    self.python_installer = "https://www.python.org/ftp/python/3.12.6/python-3.12.6.exe"

                python_path = os.path.join(self.temp_dir, "python_installer.exe")
                self.download_file(self.python_installer, python_path)
                subprocess.run([python_path, "/quiet", "InstallAllUsers=1", "PrependPath=1"], check=True)

            elif self.system == "Darwin":  # macOS
                self.python_installer = "https://www.python.org/ftp/python/3.12.6/python-3.12.6-macos11.pkg"
                python_path = os.path.join(self.temp_dir, "python_installer.pkg")
                self.download_file(self.python_installer, python_path)
                subprocess.run(["sudo", "installer", "-pkg", python_path, "-target", "/", "-silent"], check=True)

            elif self.system == "Linux":
                self.log("正在通过 apt-get 安装 Python...")
                subprocess.run(["sudo", "apt-get", "install", "-y", "python3"], check=True)

            self.log("Python 安装完成。")

        except Exception as e:
            self.log(f"Python 安装失败: {str(e)}")
            sys.exit(1)

    def download_and_extract_project(self):
        """下载并解压项目"""
        try:
            project_zip_url = "https://github.com/qaqFei/BiliClear/archive/refs/heads/main.zip"
            zip_path = os.path.join(self.temp_dir, "main.zip")
            self.log("正在下载项目压缩包...")
            self.download_file(project_zip_url, zip_path)
            self.log("下载完成，正在解压...")
            self.extract_zip(zip_path, self.desktop_path)
            self.log("解压完成，等待3秒后安装依赖...")
            time.sleep(3)
        except Exception as e:
            self.log(f"下载或解压项目失败: {str(e)}")
            sys.exit(1)

    def extract_zip(self, zip_path, extract_to):
        """解压 zip 文件"""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    def download_file(self, url, destination):
        """下载文件"""
        urllib.request.urlretrieve(url, destination)

    def install_requirements(self):
        """安装项目依赖"""
        project_path = os.path.join(self.desktop_path, self.project_name)
        requirements_file = os.path.join(project_path, "requirements.txt")

        try:
            self.log(f"切换到目录: {project_path}")
            os.chdir(project_path)

            if os.path.exists(requirements_file):
                command = ["pip3", "install", "-r", requirements_file]
                self.log(f"即将执行命令: {' '.join(command)}")
                subprocess.run(command, check=True)
                self.log("依赖安装成功")
            else:
                raise FileNotFoundError(f"{requirements_file} 文件未找到")
        except Exception as e:
            self.log(f"依赖安装失败: {str(e)}")
            sys.exit(1)

    def run_launcher(self):
        """运行项目中的 launcher.py"""
        launcher_path = os.path.join(self.desktop_path, self.project_name, self.launcher_file)

        try:
            if self.system == "Windows":
                self.log("正在启动 launcher.py...")
                subprocess.Popen(["python", launcher_path], creationflags=subprocess.CREATE_NEW_CONSOLE)

            elif self.system == "Darwin" or self.system == "Linux":
                self.log("正在启动 launcher.py...")
                subprocess.Popen(["python3", launcher_path])

            self.log("项目启动成功。")
        except Exception as e:
            self.log(f"启动项目失败: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    app = InstallerApp()
