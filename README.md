# Incus simplestreams generator

A simple tool to create simplestreams streams for Incus or LXD images.


## Features

- Supports containers and VM images.
- Supports os-, version-, arch- and variant-based `requirements` definitions.
- Reuses already-computed SHA256 fingerprints.


## Limitations

- Does not support image diffs.


## Usage

```
usage: simplestreams.py [-Nh] [-i srcdir] [rootdir]
```

So-called "simplestreams" are basically JSON files describing Incus images
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
cp incus.tar.xz $destdir
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
incus remote add my-remote https://example.com/some-path-maybe --protocol simplestreams
incus image ls my-remote:
incus launch my-remote:some/alias
```

### Requirements

Incus images may have `requirements` properties that specify how it
will treat certain images. These properties may be set using
`simplestreams.py` by dropping a `.requirements` file into the
hierarchy. Any image in a directory or sub-directory where such a file
is located will be automatically added to the index. For example:

```
cd images/windows/
cat>.requirements<<__EOF__
{
  "secureboot": "false"
}
__EOF__
```

https://linuxcontainers.org/incus/docs/main/image-handling/#special-image-properties


## Supporting Incus or LXD

Incus renamed a few keys when it forked LXD. The main differences are:

- the rename of `lxd.tar.xz` tarballs to `incus.tar.xz`;
- renaming of the `lxd_requirements` key to `requirements`.

As of writing, there are no differences between `lxd.tar.xz` and
`incus.tar.xz` files, nor for `lxd_requirements` and `requirements`
dictionaries. As such, they can be used interchangeably. `simplestreams.py`
checks for both files and copies over the metadata to make the entries
usable by both Incus and LXD (`images.linuxcontainers.org` does this too).

In summary, if `incus.tar.xz` and `lxd.tar.xz` exists, both are treated
individually, but if only one or the other exists, its metadata is copied
over to the other. For requirements, both files must exist. A symlink can
be used if both sets are identical.

If you'd like an existing hierarchy to support Incus, simply removing the
`.items.json` cache files and regenerate the streams.

```
find /path/to/hier/ -name .items.json -exec rm -f {} \;
python3 simplestreams.py /path/to/hier/
```
