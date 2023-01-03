#!/usr/bin/env python3
#
# Copyright 2022 Philippe Grégoire <git@pgregoire.xyz>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
# ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
#

import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile


FILES = {
    # filename, ftype, combined inner tag
    'disk.qcow2': ('disk-kvm.img', 'disk-kvm-img'),
    'lxd.tar.xz': ('lxd.tar.xz', None),
    'root.squashfs': ('root.squashfs', 'squashfs'),
    'root.tar.xz': ('root.tar.xz', 'rootxz'),
}


def sha256(p, h):
    with open(p, 'rb') as fp:
        h.update(fp.read())


def getfp(path):
    h = hashlib.sha256()
    sha256(path, h)
    return h.hexdigest()


def getcfp(path, file):
    h = hashlib.sha256()
    sha256(os.path.join(path, 'lxd.tar.xz'), h)
    sha256(os.path.join(path, file), h)
    return h.hexdigest()


def relpath(path):
    p = path[::]
    for _ in range(7):
        p = os.path.dirname(p)
    # return relative path to support subdir in URL
    return path[len(p)+1:]


def parse_items(path):
    if os.path.exists(os.path.join(path, '.items.json')):
        print('[>] Reusing existing items ({})'.format(relpath(path)), file=sys.stderr)
        with open(os.path.join(path, '.items.json'), 'r') as fp:
            return json.load(fp)
 
    r = {}

    g  = glob.glob(os.path.join(path, '*'))

    for i in g:
        b = os.path.basename(i)
        if b not in FILES:
            # ignore unknown files
            continue
        r[b] = {
            'ftype': FILES[b][0],
            'path': relpath(i),
            'size': os.path.getsize(i),
            'sha256': getfp(i),
        }

    for i in g:
        b = os.path.basename(i)
        if b not in FILES or FILES[b][1] is None:
            # ignore unknown files
            continue
        t = 'combined_{}_sha256'.format(FILES[b][1])
        r['lxd.tar.xz'][t] = getcfp(path, b)

    if 'combined_rootxz_sha256' in r['lxd.tar.xz']:
        r['lxd.tar.xz']['combined_sha256'] = r['lxd.tar.xz']['combined_rootxz_sha256']

    with open(os.path.join(path, '.items.json'), 'w') as fp:
        fp.write(json.dumps(r))

    return r


def parse_versions(path):
    r = {}

    for v in glob.glob(os.path.join(path, '*')):
        b = os.path.basename(v)
        if not re.match('^[0-9]{8}_[0-9]{2}:[0-9]{2}$', b):
            # FIXME will accept dates like '11111111_99:99'
            continue
        r[b] = {
            'items': parse_items(v),
        }

    return r


# Find and merge .lxd_requirements files located in dirs
def find_lxd_requirements(path):
    r = {}

    for i in range(4):
        f = os.path.join(path, '.lxd_requirements')
        if os.path.exists(f):
            with open(f, 'r') as fp:
                t = json.load(fp)
                r = {**t, **r}
        path = os.path.dirname(path)

    return r


def build_aliases(os, release, variant):
    a = ['/'.join([os, release, variant])]
    if 'default' == variant:
        a += ['/'.join([os, release])]
    return ','.join(a)


def parse_product(path):
    # RAND/$os/$release/$arch/$variant
    s = path.split(os.path.sep)

    return {
      'arch': s[-2],
      'os': s[-4],
      'variant': s[-1],
      'release': s[-3],
      'release_title': s[-3],
      'aliases': build_aliases(s[-4], s[-3], s[-1]),
      'lxd_requirements': find_lxd_requirements(path),
      'versions': parse_versions(path),
    }


def generate_images(rootdir):
    r = {
        'content_id': 'images',
        'datatype': 'image-downloads',
        'format': 'products:1.0',
        'products': {},
    }

    for p in glob.glob(os.path.join(rootdir, 'images', '*', '*', '*', '*')):
        s = p.split(os.path.sep)[-4:]

        r['products'][':'.join(s)] = parse_product(p)

    return r


def generate_index(images):
    return {
        'format': 'index:1.0',
        'index': {
            'images': {
                'datatype': 'image-downloads',
                'path': 'streams/v1/images.json',
                'format': 'products:1.0',
                'products': list(images['products'].keys()),
            }
        }
    }


def write_streams(rootdir, images):
    p = os.path.join(rootdir, 'streams', 'v1')

    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, 'images.json'), 'w') as fp:
        fp.write(json.dumps(images))

    index = generate_index(images)
    with open(os.path.join(p, 'index.json'), 'w') as fp:
        fp.write(json.dumps(index))


def make_hier(metadata, root):
    with tarfile.open(metadata, 'r:xz') as tar:
        with tar.extractfile('metadata.yaml') as fp:
            # assuming ascii, feel free to pr
            md = fp.read().decode()

    # crude parsing to minimize dependencies
    keys = {
      'architecture': None,
      'creation_date': None,
      'description': None,
      'os': None,
      'release': None,
      'variant': 'default',
    }

    for ln in md.split('\n'):
        ln = ln.strip()
        k = ln.split(':')[0]
        if k not in keys:
            continue
        keys[k] = ln.split(':')[1].strip()
        if 'architecture' == k:
            if 'x86_64' == keys[k]:
                keys[k] = 'amd64'

    for k in keys:
        if keys[k] is None:
            raise Exception('{} is not set'.format(k))

    root = os.path.join(root, keys['os'], keys['release'])
    root = os.path.join(root, keys['architecture'], keys['variant'])
    ts = datetime.datetime.utcfromtimestamp(int(keys['creation_date']))
    return os.path.join(root, ts.strftime('%Y%m%d_%H:%M'))


def mkdir(p, n):
    if n is True:
        print('mkdir {}'.format(p))
    else:
        os.makedirs(p)


def mv(f, t, n):
    if n is True:
        print('mv {} {}'.format(f, t))
    else:
        shutil.move(f, t)


def main():
    import getopt

    def usage(fp=sys.stdout):
        u = '{} [-Nh] [-i srcdir] [rootdir]'
        u = u.format(os.path.basename(sys.argv[0]))
        fp.write('usage: {}\n'.format(u))
        fp.flush()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'Nhi:')
    except getopt.GetoptError as e:
        sys.stderr.write('{}\n'.format(e))
        usage(fp=sys.stderr)
        return 1

    o_import = None
    o_nothing = True
    for k, v in opts:
        if '-N' == k:
            o_nothing = False
        if '-h' == k:
            usage()
            return 0
        if '-i' == k:
            o_import = v

    o_rootdir = os.getcwd()
    if 1 == len(args):
        o_rootdir = args[0]

    if o_import is None:
        i = generate_images(o_rootdir)
        if o_nothing is True:
            print(json.dumps(i))
        else:
            write_streams(o_rootdir, i)
    else:
        d = make_hier(os.path.join(o_import, 'lxd.tar.xz'), o_rootdir)
        mkdir(d, o_nothing)
        for f in glob.glob(os.path.join(o_import, '*')):
            b = os.path.basename(f)
            if b in FILES:
                mv(f, os.path.join(d, b), o_nothing)


if '__main__' == __name__:
    exit(main())
