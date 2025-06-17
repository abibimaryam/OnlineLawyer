import subprocess
import sys


def main():
    django_process = subprocess.Popen([sys.executable, 'manage.py', 'runserver'])
    from telegram_bot.bot import run_bot
    run_bot()


if __name__ == '__main__':
    main()