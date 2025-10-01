#!/bin/python3
import sys

if len(sys.argv) < 2:
    print("Usage: python solver.py <payload>")
    sys.exit(1)

I = sys.argv[1]

print(f"FLAG: COMPFEST17{{{I}}}")