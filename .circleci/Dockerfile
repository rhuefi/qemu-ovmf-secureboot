FROM fedora:31
RUN dnf install -y git openssh \
	edk2-ovmf qemu-system-x86 \
	python2 python2-requests \
	python3 python3-requests
ADD https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/27/Everything/x86_64/os/images/pxeboot/vmlinuz .
