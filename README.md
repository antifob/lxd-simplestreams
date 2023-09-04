# LXD simplestreams generator

A simple tool to create simplestreams streams for LXD images.


## Features

- Supports containers and VM images.
- Supports os-, version-, arch- and variant-based `lxd_requirements` definitions.
- Reuses already-computed SHA256 fingerprints.


## Limitations

- Does not support image diffs.


## Usage

```
usage: simplestreams.py [-Nh] [-i srcdir] [rootdir]
```

So-called "simplestreams" are basically JSON files describing LXD images
and meant to be served over HTTP/S. `simplestreams.py` is meant to
help you manage the images and indexes.

First, choose a directory that will be served by your HTTP/S server. On
Debian-based Linux distributions, HTTP servers' base directory is
`/var/www/html/` (you can use a sub-path if you want). `simplestreams.py`
will use the `images/` and `streams/` directories at that location.

Then, import images into the `images/` hierarchy either manually:

```
version=$(TZ= date +%Y%m%d_%H:%M)
destdir=/var/www/html/images/os/version/arch/variant/$version

# import files
mkdir -p $destdir
cp lxd.tar.xz $destdir
# for virtual machines
cp disk.qcow2 $destdir
# for containers
cp root.tar.xz $destdir
# optional, for when image diffing is supported
cp root.squashfs $destdir
```

or automatically:

```
python3 simplestreams.py -N -i . /var/www/html
```

Once files have been imported, generate the streams using:

```
python3 -N /var/www/html/
```

Finally, serve the directory containing `images/` and `streams/`
using an HTTP/S server.

```
lxc remote add my-remote https://example.com/some-path-maybe
lxc image ls my-remote:
lxc launch my-remote:some/alias
```

### Requirements

LXD images may have `requirements` properties that specify how LXD
will treat certain images. These properties may be set using
`simplestreams.py` by dropping a `.lxd_requirements` file into the
hierarchy. Any image in a directory or sub-directory where such a file
is located will be automatically added to the index. For example:

```
cd images/windows/
cat>.lxd_requirements<<__EOF__
{
  "secureboot": "false"
}
__EOF__
```

https://linuxcontainers.org/lxd/docs/latest/image-handling/#special-image-properties
