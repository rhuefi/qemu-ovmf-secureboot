# QEMU, OVMF and Secure Boot

Script to generate an OVMF variables ("VARS") file with default Secure
Boot keys enrolled.  (And verify that it works.)

Simplest working invocation of the script is:

    $ ./ovmf-vars-generator.py output_VARS-final.fd

But, a more tedious variant where you can invoke the script with custom
paths and URLs:

    $ ./ovmf-vars-generator.py \
        --ovmf-binary /usr/share/edk2/ovmf/OVMF_CODE.secboot.fd \
        --uefi-shell-iso /usr/share/edk2/ovmf/UefiShell.iso \
        --ovmf-template-vars /usr/share/edk2/ovmf/OVMF_VARS.fd \
        --fedora-version 27 \
        --kernel-url https://dl.fedoraproject.org/pub/fedora/linux/releases/27/Everything/x86_64/os/images/pxeboot/vmlinuz \
        --initrd-url https://dl.fedoraproject.org/pub/fedora/linux/releases/27/Everything/x86_64/os/images/pxeboot/initrd.img 2-output_VARS-final.fd \
        another-output_VARS-final.fd


This script does the following, in that order:

(1) Launches a QEMU guest with the UefiShell.iso as a CD-ROM.

(2) Automatically enrolls the cryptographic keys in the UEFI shell.

(3) Finally, downloads a Fedora Kernel and 'initrd' file and boots into
    it, & confirms Secure Boot is really applied.


Alternatively: You can also verify that Secure Boot is enabled properly
in a full virtual machine by explicitly running `dmesg`, and grepping
for "secure" string.  On a recent Fedora QEMU+KVM virtual machine, it
looks as follows:

    (fedora-vm)$ dmesg | grep -i secure
          [    0.000000] Secure boot enabled and kernel locked down
          [    3.261277] EFI: Loaded cert 'Fedora Secure Boot CA: fde32599c2d61db1bf5807335d7b20e4cd963b42' linked to '.builtin_trusted_keys'
