# QEMU, OVMF and Secure Boot

## Description and usage

Script to generate an OVMF variables ("VARS") file with default Secure
Boot keys enrolled.  (And verify that it works.)

Simplest working invocation of the script is:

    $ ./ovmf-vars-generator output-VARS.fd

But, a more tedious variant where you can invoke the script with custom
paths and URLs:

    $ ./ovmf-vars-generator \
        --ovmf-binary /usr/share/edk2/ovmf/OVMF_CODE.secboot.fd \
        --uefi-shell-iso /usr/share/edk2/ovmf/UefiShell.iso \
        --ovmf-template-vars /usr/share/edk2/ovmf/OVMF_VARS.fd \
        --fedora-version 27 \
        --kernel-path /tmp/qosb.kernel \
        --kernel-url https://download.fedoraproject.org/pub/fedora/linux/releases/27/Everything/x86_64/os/images/pxeboot/vmlinuz \
        another-output-VARS.fd


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


## What certificates and keys are enrolled?

The following certificates and keys are enrolled by the tool:

  - As *Platform Key*, and as one of the two *Key Exchange Keys* that we
    set up, the `EnrollDefaultKeys.efi` binary on both Fedora and RHEL,
    uses the same digital certificate called `Red Hat Secure Boot
    (PK/KEK key 1)/emailAddress=secalert@redhat.com`, and Red Hat's
    Product Security team has the private key for it.

  - The certificate that is enrolled as the second *Key Exchange Key* is
    called `Microsoft Corporation KEK CA 2011`. Updates to the
    authenticated dbx (basically, "blacklist") variable, periodically
    released at http://www.uefi.org/revocationlistfile , are signed such
    that the signature chain ends in this certificate. The update can be
    installed in the guest Linux OS with the `dbxtool` utility.

  - Then, the authenticated `db` variable gets the following two
    cetificates: `Microsoft Windows Production PCA 2011` (for accepting
    Windows 8, Windows Server 2012 R2, etc boot loaders), and `Microsoft
    Corporation UEFI CA 2011` (for verifying the `shim` binary, and PCI
    expansion ROMs).
