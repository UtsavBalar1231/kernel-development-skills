#!/bin/bash
# Build wrapper for the Acme SoC tree (fixture stub).
set -euo pipefail
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
O=out
FRAGMENTS="arch/arm64/configs/acme-evb.config"

case "${1:-}" in
kconfig)
	make O="$O" acme_defconfig
	scripts/kconfig/merge_config.sh -m -O "$O" "$O/.config" $FRAGMENTS
	make O="$O" olddefconfig
	;;
kernel)
	make O="$O" -j"$(nproc)" Image modules dtbs
	;;
dtbs-check)
	make O="$O" CHECK_DTBS=y acme/acme-soc-evb.dtb
	;;
*)
	echo "usage: $0 {kconfig|kernel|dtbs-check}" >&2
	exit 2
	;;
esac
