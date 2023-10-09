#!/bin/sh
set -eu

PROGBASE=$(d=$(dirname -- "${0}"); cd "${d}" && pwd)

tmpdir=$(mktemp -d)
cleanup() {
	rm -rf "${tmpdir}"
}
trap cleanup EXIT INT QUIT TERM


check() {
	mkdir "${tmpdir}/images"
	python3 "${PROGBASE}/../simplestreams.py" -N -i "${tmpdir}" "${tmpdir}/images"
	python3 "${PROGBASE}/../simplestreams.py" -N "${tmpdir}"
	cat "${tmpdir}/streams/v1/images.json" | python3 -mjson.tool --indent 2
}


printf '=> Testing lxd-only image\n'
cp "${PROGBASE}/files/root.tar.xz" "${PROGBASE}/files/lxd.tar.xz" "${tmpdir}"
check

printf '=> Testing incus-only image\n'
rm -rf "${tmpdir}"/*
cp "${PROGBASE}/files/root.tar.xz" "${PROGBASE}/files/incus.tar.xz" "${tmpdir}"
check

printf '=> Testing individual images\n'
rm -rf "${tmpdir}"/*
cp "${PROGBASE}/files"/* "${tmpdir}"
check
