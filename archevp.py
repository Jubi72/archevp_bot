#!bin/python

import time
from src.bot import Archebot
import argparse


def main():
    # Allow to set another config file
    p = argparse.ArgumentParser(description="Run the Archenhold bot to send changes of the vp to the user")
    p.add_argument("-f", default="autoexec.cfg", help="Config file (Default: autoexec.cfg)")

    args = p.parse_args()

    archevp = Archebot(args.f)
    lastUpdate = time.mktime(time.localtime())
    while True:
        archevp.response()
        if lastUpdate + 60 < time.mktime(time.localtime()):
            # "only" update the vp every minute
            lastUpdate = time.mktime(time.localtime())
            archevp.update()
            archevp.notifications()

        time.sleep(0.1) # be friendly to the cpu


if __name__ == "__main__":
    main()
