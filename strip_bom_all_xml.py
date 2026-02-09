#!/usr/bin/env python3
"""
Strip BOM from all .xml files under a directory.
Usage: python strip_bom_all_xml.py [path]
"""
import os
import sys

# Common BOM signatures
BOMS = {
    b"\xef\xbb\bf": "UTF-8",
    b"\xff\xfe\x00\x00": "UTF-32-LE",
    b"\x00\x00\xfe\xff": "UTF-32-BE",
    b"\xff\xfe": "UTF-16-LE",
    b"\xfe\xff": "UTF-16-BE",
}

def detect_bom(data: bytes):
    for bom, name in BOMS.items():
        if data.startswith(bom):
            return bom, name
    return None, None


def strip_file(path: str):
    """Strip BOM and any leading bytes before first '<'.

    Returns (changed: bool, info: str or None).
    """
    with open(path, 'rb') as f:
        data = f.read()
    orig = data
    bom, name = detect_bom(data)
    if bom:
        data = data[len(bom):]

    # find first '<' byte (start of XML)
    idx = data.find(b'<')
    if idx == -1:
        return False, 'no_xml_start'

    if idx != 0:
        # trim leading garbage up to first '<'
        data = data[idx:]

    if data != orig:
        # overwrite file without BOM/leading garbage
        with open(path, 'wb') as f:
            f.write(data)
        desc = []
        if name:
            desc.append(name)
        if idx != 0:
            desc.append('trimmed')
        return True, ','.join(desc) if desc else 'modified'

    return False, None

def main(root: str = '.'):
    root = os.path.abspath(root)
    scanned = 0
    changed = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith('.xml'):
                scanned += 1
                p = os.path.join(dirpath, fn)
                ok, name = strip_file(p)
                if ok:
                    changed.append((p, name))

    print(f"Scanned {scanned} .xml files; stripped BOM from {len(changed)} files")
    for p, name in changed:
        print(p, ':', name)


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    main(path)
