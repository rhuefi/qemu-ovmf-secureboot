# QEMU, OVMF and Secure Boot

## Description

`ovmf-vars-generator` is a script to generate OVMF variables ("VARS")
file with default Secure Boot keys enrolled in it.  And validate that it
works correctly.


## Prerequisite

To successfully generate a VARS file, we first need an X.509 certificate
from a given Linux distribution vendor, so that we can supply it as an
SMBIOS "OEM String" to QEMU (via `ovmf-vars-generator`).  Each Linux
distribution should provide an X.509 certificate, to be enrolled as
Secure Boot Platform Key in OVMF virtual machines.

For the sake of demonstration, let's create a self-signed CA (as
described here https://bugzilla.tianocore.org/show_bug.cgi?id=1747#c2):

  $> openssl req \
      -x509 \
      -newkey rsa:2048 \
      -outform PEM \
      -keyout PkKek1.private.key \
      -out PkKek1.pem

Fill out the details.  Then, "strip the header, footer; prepend the
application prefix" (borrowed from the same bug as above) from the
base64-encoded `PkKek1.pem` file:

    $> sed \
        -e 's/^-----BEGIN CERTIFICATE-----$/4e32566d-8e9e-4f52-81d3-5bb9715f9727:/' \
        -e '/^-----END CERTIFICATE-----$/d' \
        ./PkKek1.pem > PkKek1.oemstr

Now we're ready use the `PkKek1.oemstr` as an OEM Sting input for
`ovmf-vars-generator`.


## Invocation

The minimal invocation expects you to supply the OEM String and the name
of the output file:

    $> ./ovmf-vars-generator --oem-string "$(< PkKek1.oemstr)" \
        1_SB_VARS.fd
    INFO:root:Starting enrollment
    INFO:root:Performing enrollment
    INFO:root:Finished enrollment
    INFO:root:Grabbing test kernel
    INFO:root:Starting verification
    INFO:root:Performing verification
    INFO:root:Confirmed: Secure Boot is enabled
    INFO:root:Finished verification
    INFO:root:Created and verified output1_VARS.fd

Now the `output1_VARS.fd` file can be used, in combination with
OVMF_CODE.secboot.fd, to launch a QEMU/KVM guest with Secure Boot.

A longer command-line variant allows you to specify more details:

    $> ./ovmf-vars-generator \
        --ovmf-binary /usr/share/edk2/ovmf/OVMF_CODE.secboot.fd \
        --uefi-shell-iso /usr/share/edk2/ovmf/UefiShell.iso \
        --ovmf-template-vars /usr/share/edk2/ovmf/OVMF_VARS.fd \
        --fedora-version 33 \
        --kernel-path /tmp/qosb.kernel \
        --oem-string "$(< PkKek1.oemstr)" \
        --enable-kvm \
        2_SB_VARS.fd
    [...]

It is doing the following, in that order:

(1) Launches a QEMU guest with the UefiShell.iso as a CD-ROM.

(2) Automatically enrolls the cryptographic keys in the UEFI shell.

(3) Finally, downloads a Fedora kernel and 'initrd' file and boots into
    it, and confirms Secure Boot is really in effect.


Alternatively: You can also verify that Secure Boot is enabled properly
in a full virtual machine by explicitly running `dmesg`, and grepping
for the "secure" string.  On a recent Fedora (e.g. Fedora 33) QEMU/KVM
virtual machine, it looks as follows:

    (fedora-vm)$ dmesg | grep -i secure
          [    0.000000] secureboot: Secure boot enabled
          [    0.000000] Kernel is locked down from EFI Secure Boot mode; see man kernel_lockdown.7


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


## References

- https://bugzilla.tianocore.org/show_bug.cgi?id=1747 -- RFE: upstream
  EnrollDefaultKeys.efi to OvmfPkg
