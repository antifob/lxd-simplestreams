# LXD simplestreams generator

A simple tool to create simplestreams streams for LXD images.


## Features

- Supports LXD containers and VM images.
- Supports product-, release- and arch-based `lxd_requirements` definitions.
- Reuses already-computed SHA256 fingerprints.


## Limitations

- Does not yet support image diffs.


## Usage

```
# place the image files in their location
version=$(TZ= date +%Y%m%d_%H:%M)
destdir=images/os/version/arch/variant/$version

mkdir -p $destdir
cp lxd.tar.xz $destdir
# for virtual machines
cp disk.qcow2 $destdir
# for containers (root.squashfs is optional)
cp root.tar.xz $destdir
cp root.squashfs $destdir

# generate and print images.json
python3 simplestreams.py

# generate and write images.json and index.json
python3 simplestreams.py -w
```

Then, simply serve the directory containing `images/` and `streams/`
using an HTTPS server.

```
lxc remote add my-remote https://example.com/some-path-maybe
lxc image ls my-remote:
lxc launch my-remote:some/alias
```
