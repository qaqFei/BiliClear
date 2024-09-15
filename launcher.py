import tkinter as tk
from tkinter import messagebox
import subprocess
import platform


# 判断操作系统，并返回适当的终端命令
def open_new_terminal(command):
    system = platform.system()
    if system == "Windows":
        # Windows 下使用 start 命令
        subprocess.Popen(["start", "cmd", "/k", command], shell=True)
    elif system == "Darwin":
        # macOS 使用 osascript 启动新终端
        subprocess.Popen(
            ["osascript", "-e", f'tell application "Terminal" to do script "{command}"']
        )
    elif system == "Linux":
        # Linux 下使用 gnome-terminal 或者 x-terminal-emulator
        subprocess.Popen(
            ["gnome-terminal", "--", "bash", "-c", f"{command}; exec bash"]
        )


# 启动 QT GUI 版本
def run_qt_gui():
    messagebox.showinfo("启动 QT GUI", "正在启动 QT GUI...")
    open_new_terminal("python ./biliclear_gui_qt.py")


# 启动 WebUI 版本
def run_webui():
    messagebox.showinfo("启动 WebUI", "正在启动 WebUI...")
    open_new_terminal("python ./biliclear_gui_webui.py")


# 启动命令行版本
def run_command_line():
    messagebox.showinfo("启动命令行", "正在启动命令行版本...")
    open_new_terminal("python ./biliclear.py")


# 创建主界面
app = tk.Tk()
app.title("Biliclear 启动器")

# 添加提示标签
label = tk.Label(app, text="请选择你想要运行的版本:")
label.pack(pady=10)

# 创建按钮
qt_button = tk.Button(
    app, text="启动 QT GUI (功能更完善)", width=30, command=run_qt_gui
)
qt_button.pack(pady=5)

webui_button = tk.Button(
    app, text="启动 WebUI (适配更及时)", width=30, command=run_webui
)
webui_button.pack(pady=5)

cli_button = tk.Button(
    app, text="启动命令行 (性能最好)", width=30, command=run_command_line
)
cli_button.pack(pady=5)

# 启动 Tkinter 循环
app.mainloop()
