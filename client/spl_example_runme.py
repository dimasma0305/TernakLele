#!/usr/bin/env python3
import time
import sys
from time import sleep


if len(sys.argv) < 2:
    print(f'Usage: {sys.argv[0]} <host> <port>')
    sys.exit(1)

print("COMPFEST17{"+time.strftime("%Y%m%d%H%M%S")+"}", flush=True)
sleep(1)