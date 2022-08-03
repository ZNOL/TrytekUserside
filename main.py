#!/usr/bin/env python
# coding: utf-
import os
from config import *

base_path = os.path.abspath(os.path.dirname(__file__))


def write_pid_file(pid_nr):
    with open(os.path.join(base_path, 'main.pid'), 'w') as f:
        f.write(pid_nr)


def delete_pid_file():
    try:
        os.remove(os.path.join(base_path, 'main.pid'))
    except FileNotFoundError:
        pass


def check_parallel_process():
    file = os.path.join(base_path, 'main.pid')
    try:
        f = open(file)
    except Exception:
        return True
    else:
        with f:
            _pid = f.readline()
        try:
            os.kill(int(_pid), 0)
        except Exception:
            logging.warning("PID file was found but process with its PID not running. Removing PID file")
            delete_pid_file()
            return True
        else:
            logging.warning(f"A running parallel process with ID {_pid} is found. Exiting")
            exit(0)


check_parallel_process()


from src.messages import *
from src.commands import *


async def main():
    pid = os.getpid()
    write_pid_file(str(pid))
    logging.info(f'*** BOT was started. PID={pid}')

    me = await bot.get_me()
    logging.info(me.username)

    checker = asyncio.create_task(task_updater())
    trashman = asyncio.create_task(trash_cleaner())
    await checker
    await trashman

    await bot.start()
    await bot.run_until_disconnected()

    delete_pid_file()
    logging.info(f'*** BOT was stopped. PID={pid}')


with bot:
    bot.loop.run_until_complete(main())
