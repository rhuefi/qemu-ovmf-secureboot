#!/bin/python
# Copyright (C) 2017 Red Hat
# Authors:
# - Patrick Uiterwijk <puiterwijk@redhat.com>
# - Kashyap Chamarthy <kchamart@redhat.com>
#
# Licensed under MIT License, for full text see LICENSE
#
# Purpose: Launch a QEMU guest and enroll ithe UEFI keys into an OVMF
#          variables ("VARS") file.  Then boot a Linux kernel and initrd
#          with QEMU.  Finally, perform a check to verify if Secure Boot
#          is enabled.

from __future__ import print_function

import argparse
import os
import shutil
import string
import subprocess


def strip_special(line):
    return ''.join([c for c in line if c in string.printable])


def generate_qemu_cmd(args, readonly, *extra_args):
    return [
        args.qemu_binary,
        '-machine', 'q35,smm=on,accel=kvm',
        '-display', 'none',
        '-no-user-config',
        '-nodefaults',
        '-m', '256',
        '-smp', '2,sockets=2,cores=1,threads=1',
        '-chardev', 'pty,id=charserial1',
        '-device', 'isa-serial,chardev=charserial1,id=serial1',
        '-global', 'driver=cfi.pflash01,property=secure,value=on',
        '-drive',
        'file=%s,if=pflash,format=raw,unit=0,readonly=on' % (
            args.ovmf_binary),
        '-drive',
        'file=%s,if=pflash,format=raw,unit=1,readonly=%s' % (
            args.output, 'on' if readonly else 'off'),
        '-object', 'rng-random,id=objrng0,filename=/dev/urandom',
        '-device', 'virtio-rng-pci,rng=objrng0,id=rng0',
        '-serial', 'stdio'] + list(extra_args)


def download(url, target, verbose):
    if os.path.exists(target):
        return
    import requests
    if verbose:
        print('Downloading %s to %s' % (url, target))
    r = requests.get(url, stream=True)
    with open(target, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def enroll_keys(args):
    shutil.copy(args.ovmf_template_vars, args.output)

    cmd = generate_qemu_cmd(
        args,
        False,
        '-drive',
        'file=%s,format=raw,if=none,media=cdrom,id=drive-virtio-disk1,'
        'readonly=on' % args.uefi_shell_iso,
        '-device',
        'virtio-blk-pci,scsi=off,drive=drive-virtio-disk1,id=virtio-disk1,'
        'bootindex=1')
    p = subprocess.Popen(cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    # Wait until the UEFI shell starts (first line is printed)
    read = p.stdout.readline()
    if args.print_output:
        print(strip_special(read), end='')
    # Send the escape char to enter the UEFI shell early
    p.stdin.write(chr(27))
    # And then run the following three commands from the UEFI shell:
    # change into the first file system device; install the default
    # keys and certificates, and reboot
    p.stdin.write(b'fs0:\r\n')
    p.stdin.write(b'EnrollDefaultKeys.efi\r\n')
    p.stdin.write(b'reset\r\n')
    while True:
        read = p.stdout.readline()
        if args.print_output:
            print('OUT: %s' % strip_special(read), end='')
        if 'info: success' in read:
            break
    p.kill()
    if args.print_output:
        print(strip_special(p.stdout.read()), end='')


def test_keys(args):
    kernel = '/tmp/qemu-kernel'
    initrd = '/tmp/qemu-initrd'

    download(args.kernel_url, kernel, args.verbose)
    download(args.initrd_url, initrd, args.verbose)

    cmd = generate_qemu_cmd(
        args,
        True,
        '-append', 'console=tty0 console=ttyS0,115200n8',
        '-kernel', kernel,
        '-initrd', initrd)
    p = subprocess.Popen(cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    while True:
        read = p.stdout.readline()
        if args.print_output:
            print('OUT: %s' % strip_special(read), end='')
        if 'Secure boot disabled' in read:
            raise Exception('Secure boot was disabled')
        elif 'Secure boot enabled and kernel locked down' in read:
            if args.verbose:
                print('Confirmed: Secure Boot enabled!')
            break
    p.kill()
    if args.print_output:
        print(strip_special(p.stdout.read()), end='')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', help='Filename for output vars file')
    parser.add_argument('--force', help='Overwrite existing output file',
                        action='store_true')
    parser.add_argument('--print-output', help='Print the QEMU guest output',
                        action='store_true')
    parser.add_argument('--verbose', '-v', help='Print status',
                        action='store_true')
    parser.add_argument('--qemu-binary', help='QEMU binary path',
                        default='/usr/bin/qemu-system-x86_64')
    parser.add_argument('--ovmf-binary', help='OVMF secureboot code file',
                        default='/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd')
    parser.add_argument('--ovmf-template-vars', help='OVMF empty vars file',
                        default='/usr/share/edk2/ovmf/OVMF_VARS.fd')
    parser.add_argument('--uefi-shell-iso', help='Path to uefi shell iso',
                        default='/usr/share/edk2/ovmf/UefiShell.iso')
    parser.add_argument('--fedora-version',
                        help='Fedora version to get kernel/initrd for checking',
                        default='27')
    parser.add_argument('--kernel-url', help='Kernel URL',
                        default='https://download.fedoraproject.org/pub/fedora'
                                '/linux/releases/%(version)s/Everything/x86_64'
                                '/os/images/pxeboot/vmlinuz')
    parser.add_argument('--initrd-url', help='Initrd URL',
                        default='https://download.fedoraproject.org/pub/fedora'
                                '/linux/releases/%(version)s/Everything/x86_64'
                                '/os/images/pxeboot/initrd.img')
    args = parser.parse_args()
    args.kernel_url = args.kernel_url % {'version': args.fedora_version}
    args.initrd_url = args.initrd_url % {'version': args.fedora_version}
    return args


def main():
    args = parse_args()
    if os.path.exists(args.output) and not args.force:
        raise Exception('%s already exists' % args.output)
    enroll_keys(args)
    test_keys(args)
    if args.verbose:
        print('Created and verified %s' % args.output)


if __name__ == '__main__':
    main()
