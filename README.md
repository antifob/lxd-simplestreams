# LXD simplestreams generator

A simple tool to create simplestreams streams for LXD images.


## Limitations

- Does not yet support container images.
- Does not yet support image diffs.


## Usage

```
# place the image files in its location
version=$(TZ= date +%Y%m%d_%H:%M)
destdir=images/os/version/arch/variant/$version

mkdir -p $destdir
cp lxd.tar.xz $destdir
cp disk.qcow2 $destdir

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
