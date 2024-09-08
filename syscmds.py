import sys
from os import system

from compatible_getpass import getpass

def clearScreen():
    system("cls" if sys.platform == "win32" else "clear")

def pause():
    getpass("")