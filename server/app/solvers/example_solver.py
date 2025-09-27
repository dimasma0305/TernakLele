#!/usr/bin/env python3

import random
import sys

if len(sys.argv) < 2:
    print(f'Usage: {sys.argv[0]} <target>')
    sys.exit(1)

ip = sys.argv[1]

print(f"Attacking target: {ip}")
print("Running example solver...")

# Simulate some work
import time
time.sleep(1)

# Generate some example flags that match the format from config
flag_format = r'[A-Z0-9]{31}='

# Generate a few example flags
for i in range(3):
    random.seed(i)
    flag = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=31)) + '='
    print(f"Found flag: {flag}", flush=True)

print("Solver completed successfully!")
