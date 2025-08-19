import os

if __name__ == '__main__':
    os.system('rm -r dist')
    os.system('pyarmor-7 obfuscate --src="." --exclude venv -r main.py')
    os.system('cp requirements.txt dist')
