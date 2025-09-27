#!/usr/bin/env python3
# exploit.py
# Requires: pwntools
# pip install pwntools

from pwn import *
import re
import time
import sys

if len(sys.argv) < 2:
    print(f'Usage: {sys.argv[0]} <host> <port>')
    sys.exit(1)
HOST = sys.argv[1]
PORT = 40005

# ====== CONFIG ======
SAMPLES = 200         # jumlah sampel talk untuk dikumpulkan (tingkatkan jika perlu)
TARGET_MENU = '3'     # 1 = alice-you, 2 = bob-you, 3 = alice-bob (default target)
# ====================

# helper: parse lucky numbers line
def parse_lucky(text):
    m = re.search(r'Your lucky numbers:\s*\(([^)]+)\)', text)
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split(',')]
    return parts

def read_until_menu_prompt(io, timeout=2.0):
    """Try to sync until a menu prompt '>' appears or until timeout"""
    try:
        # many servers show '> ' as prompt; try to read until that
        data = io.recvuntil(b'> ', timeout=timeout)
        return data.decode(errors='ignore')
    except EOFError:
        return ''
    except Exception:
        # fallback: read whatever is available
        try:
            data = io.recv(timeout=0.5)
            return data.decode(errors='ignore')
        except Exception:
            return ''

def collect_samples(io, menu_choice: bytes, samples: int):
    collected = []
    for i in range(samples):
        try:
            # send menu choice (as bytes)
            io.sendline(menu_choice)
        except Exception as e:
            log.warn(f'sendline failed: {e}')
            break

        # After choosing "talk", the server will print a number then ask "more? (y/n): "
        # We'll read lines until we find a line that contains an integer.
        try:
            # wait up to short time for the number line
            line = io.recvline(timeout=3).decode().strip()
        except Exception:
            log.warn('timeout waiting for number line; trying a bit more...')
            try:
                line = io.recvline(timeout=2).decode().strip()
            except Exception:
                log.warn('still no line; aborting collection loop')
                break

        # skip blank lines, try to find a numeric line
        attempts = 0
        while (line == '' or not re.match(r'^\d+$', line)) and attempts < 5:
            try:
                line = io.recvline(timeout=1).decode().strip()
            except Exception:
                break
            attempts += 1

        if not re.match(r'^\d+$', line):
            log.warn(f'Could not parse numeric line, got: {repr(line)}')
            # try to resync: read until menu prompt and continue
            read_until_menu_prompt(io, timeout=1)
            break

        try:
            val = int(line)
            collected.append(val)
        except Exception as e:
            log.warn(f'parse int failed for line={line}: {e}')
            break

        # respond 'y' to continue sampling, or 'n' on last sample
        try:
            if i < samples - 1:
                io.sendline(b'y')
            else:
                io.sendline(b'n')
        except Exception as e:
            log.warn(f'failed to send more? response: {e}')
            break

        # small delay to avoid flooding
        time.sleep(0.01)

        # After sending 'n' at the end of a talk session, the menu should reappear.
        # read a little to keep sync but don't block too long
        if i == samples - 1:
            read_until_menu_prompt(io, timeout=1)

    return collected

def reconstruct_upper(collected):
    acc = 0
    for v in collected:
        acc |= v
    return acc

def main():
    io = remote(HOST, PORT, timeout=10)
    # read initial banner (a few lines)
    try:
        banner = io.recvrepeat(timeout=1).decode(errors='ignore')
    except Exception:
        banner = ''
    # try parse lucky numbers
    parsed = parse_lucky(banner)
    if parsed:
        g, p, you_secret, alice_pub, bob_pub = parsed
        log.info('Parsed lucky numbers:')
        log.info(f'g = {g}')
        log.info(f'p = {p}')
        log.info(f'you.secret = {you_secret}')
        log.info(f'alice.public = {alice_pub}')
        log.info(f'bob.public = {bob_pub}')
    else:
        log.warn('Could not parse lucky numbers from initial banner.')

    log.info(f'Collecting up to {SAMPLES} samples from talk(menu {TARGET_MENU}) ...')
    samples = collect_samples(io, TARGET_MENU, SAMPLES)
    log.success(f'Collected {len(samples)} samples.')

    if len(samples) == 0:
        log.warn('No samples collected; exiting.')
        io.close()
        return

    upper = reconstruct_upper(samples)
    log.success('Reconstructed OR of all outputs (upper half mask):')
    log.info(f'upper (hex) = {upper:x}')
    log.info(f'upper (bitlen) = {upper.bit_length()}')

    candidate = (upper << 256)
    log.info('Trying to submit candidate secret with lower bits = 0 ...')

    # choose menu 7 (Flag)
    try:
        io.sendline(b'7')
        # wait for 'secret:' prompt or similar
        io.recvuntil(b'secret:', timeout=2)
        io.sendline(str(candidate).encode())
        # read a bit of response
        resp = io.recvrepeat(timeout=2).decode(errors='ignore')
        print('--- server response after submitting candidate ---')
        print(resp)
    except Exception as e:
        log.warn(f'Error while submitting candidate: {e}')

    # save samples for offline analysis
    with open('samples.txt', 'w') as f:
        for s in samples:
            f.write(str(s) + '\n')
    log.info('Saved samples to samples.txt')

    io.close()

if __name__ == '__main__':
    main()