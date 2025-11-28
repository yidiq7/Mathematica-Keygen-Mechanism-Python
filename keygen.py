#!/usr/bin/env python3
"""
Wolfram Keygen & Auto-Activation Script

Usage:
    python keygen.py          Interactive mode - enter MathID manually
    python keygen.py -a       Auto-activation mode
    python keygen.py --auto   Auto-activation mode 
"""
import pexpect
import re
import signal
import argparse
import random
import string
import time
import sys
from datetime import datetime, timedelta


class MathPass:
    HASH_CODE_1 = 0b1000001011100001
    HASH_CODE_2 = 0b1000001100100101
    hash_value = 24816

    def __init__(self, math_id: str):
        self.math_id = math_id
        self.activation_key = self.random_activation_key()
        self.password = ''

    @staticmethod
    def hasher(hasher_code: int, hash_val: int, byte: int) -> int:
        for _ in range(8):
            bit = byte & 1
            if hash_val % 2 == bit:
                hash_val >>= 1
            else:
                hash_val >>= 1
                hash_val ^= hasher_code
            byte >>= 1
        return hash_val

    @staticmethod
    def split_hex(hex_val: int) -> list:
        n = int(hex_val * 99999.0 / 0xFFFF)
        slices = []
        for _ in range(5):
            slices.append(n % 10)
            n //= 10
        return slices

    @staticmethod
    def encoding_hash(n1: int) -> int:
        import math
        n1 = int(n1 * 99999.0 / 0xFFFF)
        n1_01 = n1 % 100
        n1 -= n1_01
        n1_2 = n1 % 1000
        n1 -= n1_2
        n1 += n1_01 * 10 + n1_2 // 100
        temp = math.ceil(n1 * 65535.0 / 99999)
        return MathPass.hasher(
            MathPass.HASH_CODE_2,
            MathPass.hasher(MathPass.HASH_CODE_2, 0, temp & 0xFF),
            temp >> 8
        )

    @staticmethod
    def find_magic_char(hasher_code: int, hash_val: int, target: int) -> int:
        for c1 in range(256):
            for c2 in range(256):
                if MathPass.hasher(hasher_code, MathPass.hasher(hasher_code, hash_val, c1), c2) == target:
                    return c1 | (c2 << 8)
        return 0

    @staticmethod
    def encoding_characters(hasher_code: int, hash_val: int, characters: list) -> int:
        for char in characters:
            hash_val = MathPass.hasher(hasher_code, hash_val, char)
        return MathPass.find_magic_char(hasher_code, hash_val, 0xA5B6)

    @staticmethod
    def construct_password(n1: int, n2: int) -> str:
        n1str = MathPass.split_hex(n1)[::-1]
        n2str = MathPass.split_hex(n2)[::-1]
        return (f"{n2str[3]}{n1str[3]}{n1str[1]}{n1str[0]}-"
                f"{n2str[4]}{n1str[2]}{n2str[0]}-"
                f"{n2str[2]}{n1str[4]}{n2str[1]}")

    @staticmethod
    def random_fill(fmt: str) -> str:
        result = []
        for c in fmt:
            if c == 'x':
                result.append(str(random.randint(0, 9)))
            elif c == 'a':
                result.append(random.choice(string.ascii_uppercase))
            elif c == 'b':
                if random.random() > 0.722:
                    result.append(str(random.randint(0, 9)))
                else:
                    result.append(random.choice(string.ascii_uppercase))
            else:
                result.append(c)
        return ''.join(result)

    @staticmethod
    def random_activation_key() -> str:
        return MathPass.random_fill('xxxx-xxxx-aaaaaa')

    @staticmethod
    def get_date_after(days: int) -> str:
        date = datetime.now() + timedelta(days=days)
        return date.strftime('%Y%m%d')

    def generate_password(self, math_num: str = '800001', expire_date: str = None) -> bool:
        if expire_date is None:
            expire_date = self.get_date_after(999)
        s = f"{self.math_id}@{expire_date}${math_num}&{self.activation_key}"
        characters = [ord(c) for c in reversed(s)]
        hash_val = MathPass.hash_value
        n0 = self.encoding_characters(self.HASH_CODE_1, hash_val, characters)
        n1 = (n0 + 0x72FA) % 65536
        hash_val = self.encoding_hash(n1)
        n2 = self.encoding_characters(self.HASH_CODE_2, hash_val, characters)
        self.password = f"{self.construct_password(n1, n2)}::{math_num}:{expire_date}"
        return True


def check_format(fmt: str, s: str) -> bool:
    if len(fmt) != len(s):
        return False
    for i, fc in enumerate(fmt):
        if fc == 'x':
            if not s[i].isdigit():
                return False
        elif fc == 'a':
            if not s[i].isupper():
                return False
        elif fc == 'b':
            if not (s[i].isdigit() or s[i].isupper()):
                return False
        else:
            if fc != s[i]:
                return False
    return True


def interactive_mode():
    """Interactive mode: manually enter MathID and get credentials."""
    math_id = input("Enter Math ID (format: xxxx-xxxxx-xxxxx): ").strip()
    
    if not check_format('xxxx-xxxxx-xxxxx', math_id):
        print("Invalid Math ID format. Should be xxxx-xxxxx-xxxxx")
        return

    mp = MathPass(math_id)
    mp.generate_password()

    print(f"\nMath ID:        {mp.math_id}")
    print(f"Activation Key: {mp.activation_key}")
    print(f"Password:       {mp.password}")


def auto_activate():
    """Auto-activation mode: fully automated Wolfram activation."""
    try:
        import pexpect
    except ImportError:
        print("[-] Error: pexpect is required for auto-activation mode.")
        print("    Install it with: pip install pexpect")
        return False

    print("[*] Starting Wolfram activation process...")
    
    # Spawn wolfram process
    child = pexpect.spawn('wolfram', encoding='utf-8', timeout=60)
    child.logfile = None  # Set to sys.stdout for debugging
    
    print("[*] Waiting for Wolfram to start...")
    time.sleep(3)
    
    # Send Ctrl+C twice to cancel license server connection
    print("[*] Sending Ctrl+C to cancel license server lookup...")
    child.sendintr()  # Ctrl+C
    time.sleep(0.5)
    child.sendintr()  # Ctrl+C again
    
    # Wait for Web Activation prompt and skip it
    # If already activated, we'll see "In[1]:=" prompt instead
    print("[*] Waiting for Web Activation prompt...")
    index = child.expect([
        r'skip Web Activation',  # 0: Needs activation
        r'In\[\d+\]:=',          # 1: Already activated (Wolfram prompt)
        pexpect.TIMEOUT          # 2: Timeout
    ], timeout=30)
    
    if index == 1:
        print("[+] Wolfram is already activated!")
        print("[*] Exiting...")
        child.sendeof()  # Ctrl+D to exit
        child.expect(pexpect.EOF, timeout=10)
        child.close()
        return True
    elif index == 2:
        print("[-] Timeout waiting for prompt. Exiting...")
        child.close(force=True)
        return False
    
    # index == 0: Needs activation, continue
    child.sendline('')  # Press return to skip
    
    # Wait for and extract MathID
    print("[*] Looking for MathID...")
    child.expect(r'MathID:\s*(\d{4}-\d{5}-\d{5})', timeout=30)
    math_id = child.match.group(1)
    print(f"[+] Found MathID: {math_id}")
    
    # Generate credentials
    print("[*] Generating activation credentials...")
    mp = MathPass(math_id)
    mp.generate_password()
    print(f"[+] Activation Key: {mp.activation_key}")
    print(f"[+] Password: {mp.password}")
    
    # Wait for activation key prompt
    child.expect(r'Enter your Activation key', timeout=30)
    print("[*] Entering activation key...")
    child.sendline(mp.activation_key)
    
    # Wait for password prompt
    child.expect(r'Enter your password', timeout=30)
    print("[*] Entering password...")
    child.sendline(mp.password)
    
    # Wait for password file creation confirmation
    print("[*] Waiting for password file creation...")
    child.expect(r'Creating password file entry in:', timeout=30)
    child.expect(r'\.Wolfram/Licensing/mathpass', timeout=10)
    
    time.sleep(1)
    child.sendline('')  # Press return
    
    time.sleep(1)
    
    child.expect(r'In\[d+\]:=', timeout=30)
    # Send Ctrl+D to exit
    print("[*] Exiting Wolfram...")
    child.sendeof()  # Ctrl+D
    
    # Wait for process to end
    child.expect(pexpect.EOF, timeout=10)
    child.close()
    
    print("[+] Wolfram activation completed successfully!")
    print(f"[+] License file created at: ~/.Wolfram/Licensing/mathpass")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Wolfram Keygen & Auto-Activation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python keygen.py          Interactive mode - enter MathID manually
  python keygen.py -a       Auto-activation mode
  python keygen.py --auto   Auto-activation mode
        '''
    )
    parser.add_argument(
        '-a', '--auto',
        action='store_true',
        help='Run in auto-activation mode'
    )
    
    args = parser.parse_args()
    
    if args.auto:
        try:
            auto_activate()
        except Exception as e:
            print(f"[-] Error during auto-activation: {e}")
            raise
    else:
        interactive_mode()


if __name__ == '__main__':
    main()
