import sys

if "--compatible-getpass" in sys.argv:
    getpass = input
else:
    from getpass import getpass