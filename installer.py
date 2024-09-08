import os
import subprocess
import time
import urllib.request
import zipfile
import platform
import shutil
import sys  # 导入 sys 模块
import tkinter as tk
from tkinter import messagebox  # 确保导入 messagebox


class InstallerApp:
    def __init__(self):
        # 启动安装流程
        self.start_installation()

    def log(self, message):
        """在控制台中输出日志"""
        print(message)  # 控制台输出日志

    def start_installation(self):
        # 启动安装程序
        self.log("启动安装程序...")

        # 第一步，检测并静默安装 Python
        self.log("检测并安装 Python...")
        self.check_and_install_python()

        # 第二步，直接下载项目压缩包
        self.log("开始下载项目压缩包...")
        self.download_zip()

    def check_and_install_python(self):
        try:
            # 检测 Python 是否安装
            subprocess.run(["python", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.log("Python 已安装。")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("未检测到 Python，正在自动安装...")
            self.silent_install_python()

    def silent_install_python(self):
        system = platform.system()
        try:
            if system == "Windows":
                arch = platform.machine()
                if arch == "AMD64":
                    python_url = "https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe"
                elif arch == "ARM64":
                    python_url = "https://www.python.org/ftp/python/3.12.6/python-3.12.6-arm64.exe"
                else:
                    python_url = "https://www.python.org/ftp/python/3.12.6/python-3.12.6.exe"

                # 下载安装包
                self.download_and_silent_install(python_url, "python_installer.exe")

                # 执行静默安装，确保添加到 PATH
                self.log("正在静默安装 Python 并添加到 PATH...")
                subprocess.run(["python_installer.exe", "/quiet", "InstallAllUsers=1", "PrependPath=1"], check=True)

            elif system == "Darwin":  # macOS
                python_url = "https://www.python.org/ftp/python/3.12.6/python-3.12.6-macos11.pkg"
                self.download_and_silent_install(python_url, "python_installer.pkg")
                subprocess.run(["sudo", "installer", "-pkg", "python_installer.pkg", "-target", "/", "-silent"],
                               check=True)

            elif system == "Linux":
                self.log("正在通过 apt-get 安装 Python...")
                subprocess.run(["sudo", "apt-get", "install", "-y", "python3"], check=True)

            self.log("Python 安装完成")
        except Exception as e:
            self.log(f"Python 安装失败: {str(e)}")
            sys.exit(1)

    def download_and_silent_install(self, url, filename):
        try:
            # 下载安装包
            self.log(f"正在下载 {filename}...")
            urllib.request.urlretrieve(url, filename)
        except Exception as e:
            self.log(f"下载 {filename} 失败: {str(e)}")
            sys.exit(1)

    def download_zip(self):
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "main.zip")
            self.log("正在下载项目压缩包...")
            urllib.request.urlretrieve("https://github.com/qaqFei/BiliClear/archive/refs/heads/main.zip", desktop_path)
            self.log("下载完成，正在解压...")
            extract_path = self.extract_zip(desktop_path)
            self.log("解压完成，等待3秒后安装依赖...")
            time.sleep(3)  # 等待 3 秒
            self.install_requirements(extract_path)
        except Exception as e:
            self.log(f"下载或解压项目失败: {str(e)}")
            sys.exit(1)

    def extract_zip(self, zip_path):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        extract_path = os.path.join(desktop_path, "BiliClear-main")  # 解压后的默认文件夹名称为 BiliClear-main

        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(desktop_path)

        return extract_path

    def install_requirements(self, path):
        try:
            # 切换到项目目录
            self.log(f"切换到目录: {path}")
            os.chdir(path)

            # 确保 requirements.txt 存在
            if not os.path.exists("requirements.txt"):
                raise FileNotFoundError("requirements.txt 文件未找到")

            # 显示即将执行的命令
            command = ["pip3", "install", "-r", "./requirements.txt"]
            self.log(f"即将执行命令: {' '.join(command)}")

            # 执行安装依赖
            subprocess.run(command, check=True)
            self.log("依赖安装成功")

            # 安装完成后启动 launcher.py（在单独窗口中运行）
            self.start_launcher(path)

        except Exception as e:
            self.log(f"依赖安装失败: {str(e)}")
            sys.exit(1)

    def start_launcher(self, path):
        """启动项目根目录下的 launcher.py 并在单独窗口中运行"""
        launcher_path = os.path.join(path, "launcher.py")
        if os.path.exists(launcher_path):
            self.log(f"启动 launcher.py: {launcher_path}")
            if platform.system() == "Windows":
                # Windows: 使用新的控制台窗口启动 launcher.py
                subprocess.Popen(["python", launcher_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # Linux/macOS: 使用独立的终端窗口
                subprocess.Popen(["x-terminal-emulator", "-e", f"python3 {launcher_path}"])
        else:
            self.log("launcher.py 未找到，无法启动")


if __name__ == "__main__":
    app = InstallerApp()
