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

        # 第二步，询问用户是否安装 Git
        self.log("询问用户是否安装 Git...")
        self.ask_and_install_git()

    def check_and_install_python(self):
        try:
            # 检测 Python 是否安装
            subprocess.run(["python3", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

                self.download_and_silent_install(python_url, "python_installer.exe", "/quiet")

            elif system == "Darwin":  # macOS
                python_url = "https://www.python.org/ftp/python/3.12.6/python-3.12.6-macos11.pkg"
                self.download_and_silent_install(python_url, "python_installer.pkg", "-silent")

            elif system == "Linux":
                self.log("正在通过 apt-get 安装 Python...")
                subprocess.run(["sudo", "apt-get", "install", "-y", "python3"], check=True)

            self.log("Python 安装完成")
        except Exception as e:
            self.log(f"Python 安装失败: {str(e)}")
            exit(1)

    def download_and_silent_install(self, url, filename, silent_flag):
        try:
            # 下载安装包
            self.log(f"正在下载 {filename}...")
            urllib.request.urlretrieve(url, filename)

            # 静默安装
            self.log(f"正在静默安装 {filename}...")
            if platform.system() == "Windows":
                subprocess.run([filename, silent_flag], check=True)
            elif platform.system() == "Darwin":
                subprocess.run(["sudo", "installer", "-pkg", filename, "-target", "/", silent_flag], check=True)

            self.log(f"{filename} 安装完成")
        except Exception as e:
            self.log(f"下载或安装 {filename} 失败: {str(e)}")
            exit(1)

    def ask_and_install_git(self):
        # 询问用户是否安装 Git
        install_git = messagebox.askyesno("Git 安装提示", "是否安装 Git 以方便未来维护和升级项目？")
        if install_git:
            self.log("用户选择安装 Git，正在安装 Git...")
            self.silent_install_git()
        else:
            # 如果用户不安装 Git，直接下载压缩包
            self.log("用户选择不安装 Git，正在下载项目压缩包...")
            self.download_zip()

    def silent_install_git(self):
        system = platform.system()
        try:
            if system == "Windows":
                git_url = "https://github.com/git-for-windows/git/releases/download/v2.46.0.windows.1/Git-2.46.0-64-bit.exe"
                self.download_and_silent_install(git_url, "git_installer.exe", "/SILENT")
            elif system == "Darwin":  # macOS
                self.log("正在通过 Homebrew 安装 Git...")
                subprocess.run(['/bin/bash', '-c',
                                "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"])
                subprocess.run(['brew', 'install', 'git'], check=True)
            elif system == "Linux":
                self.log("正在通过 apt-get 安装 Git...")
                subprocess.run(["sudo", "apt-get", "install", "-y", "git"], check=True)

            self.log("Git 安装完成")
            self.clone_repo()
        except Exception as e:
            self.log(f"Git 安装失败: {str(e)}")
            exit(1)

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
            exit(1)

    def clone_repo(self):
        try:
            # 克隆 Git 项目到桌面
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            self.log("正在克隆项目到桌面...")
            os.chdir(desktop_path)
            subprocess.run(["git", "clone", "https://github.com/qaqFei/BiliClear.git"], check=True)
            self.log("项目克隆完成，等待3秒后安装依赖...")
            time.sleep(3)  # 等待 3 秒
            self.install_requirements(os.path.join(desktop_path, "BiliClear"))
        except Exception as e:
            self.log(f"克隆项目失败: {str(e)}")
            exit(1)

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

            # 显示即将执行的命令
            command = ["pip3", "install", "-r", "./requirements.txt"]
            self.log(f"即将执行命令: {' '.join(command)}")

            # 执行安装依赖
            subprocess.run(command, check=True)
            self.log("依赖安装成功")

            # 安装完成后启动 launcher.py
            self.start_launcher(path)

            # 删除安装包和压缩包
            self.cleanup_installation()

            # 自我删除
            self.self_delete()

        except Exception as e:
            self.log(f"依赖安装失败: {str(e)}")
            exit(1)

    def start_launcher(self, path):
        """启动项目根目录下的 launcher.py"""
        launcher_path = os.path.join(path, "launcher.py")
        if os.path.exists(launcher_path):
            self.log(f"启动 launcher.py: {launcher_path}")
            subprocess.Popen([sys.executable, launcher_path])
        else:
            self.log("launcher.py 未找到，无法启动")

    def cleanup_installation(self):
        """删除安装包和其他临时文件"""
        try:
            files_to_remove = [
                "python_installer.exe",
                "git_installer.exe",
                os.path.join(os.path.expanduser("~"), "Desktop", "main.zip")
            ]
            for file in files_to_remove:
                if os.path.exists(file):
                    self.log(f"删除文件: {file}")
                    os.remove(file)
            self.log("安装包和临时文件已删除")
        except Exception as e:
            self.log(f"删除文件时出错: {str(e)}")

    def self_delete(self):
        """自我删除"""
        try:
            current_script = sys.argv[0]
            self.log(f"自我删除: {current_script}")
            if platform.system() == "Windows":
                # Windows 不能立即删除运行中的文件，所以通过一个新进程延迟删除
                bat_script = f"""
                @echo off
                ping 127.0.0.1 -n 2 > nul
                del "{current_script}"
                """
                bat_path = os.path.join(os.path.expanduser("~"), "delete_self.bat")
                with open(bat_path, "w") as bat_file:
                    bat_file.write(bat_script)
                subprocess.Popen([bat_path], shell=True)
            else:
                os.remove(current_script)
        except Exception as e:
            self.log(f"自我删除失败: {str(e)}")


if __name__ == "__main__":
    app = InstallerApp()
