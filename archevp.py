#!/usr/bin/python

import time
from src.bot import Archebot
import argparse


def main():
    # Allow to set another config file
    p = argparse.ArgumentParser(description="Run the Archenhold bot to send changes of the vp to the user")
    p.add_argument("-f", default="autoexec.cfg", help="Config file (Default: autoexec.cfg)")

    args = p.parse_args()

    archevp = Archebot(args.f)
    archevp.message_loop()
    while True:
        time.sleep(10)
        #TODO: send daily notifications


if __name__ == "__main__":
    main()
