# QEMU, OVMF and Secure Boot

Script to generate an OVMF variables ("VARS") file with default Secure
Boot keys enrolled.  (And verify that it works.)

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
