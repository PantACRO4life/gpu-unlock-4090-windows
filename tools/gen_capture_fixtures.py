#!/usr/bin/env python3
"""Generate tests/cap4_graph.h and tests/cap4_usb_paths.h from a probe capture.

Fixture handle = capture handle id + 1 (tests use H(id)). Edges are listed by
handle, in capture order. USB paths are the xHCI host and every handle below it.
"""
import json
import sys
from pathlib import Path

USB_HOST = bytes([2, 1, 12, 0, 0xd0, 0x41, 3, 10, 0, 0, 0, 0, 1, 1, 6, 0, 0, 0x14])
END = bytes([0x7f, 0xff, 4, 0])


def guid(raw):
    b = bytes.fromhex(raw)
    if len(b) != 16:
        raise SystemExit(f"bad GUID {raw}")
    d1, d2, d3 = int.from_bytes(b[0:4], "little"), int.from_bytes(b[4:6], "little"), int.from_bytes(b[6:8], "little")
    tail = ",".join(hex(x) for x in b[8:])
    return f"{{{d1:#x},{d2:#x},{d3:#x},{{{tail}}}}}"


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: gen_capture_fixtures.py CAPTURE.JSON TESTS_DIR")
    capture = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    platform = capture["platform"]
    if not platform["complete"] or len(platform["handles"]) != platform["handle_count"]:
        raise SystemExit("capture platform graph is incomplete")
    name = Path(sys.argv[1]).stem.upper()

    edges, paths = [], []
    for h in platform["handles"]:
        hid = h["id"] + 1
        for e in h["active_opens"]:
            edges.append(f"{{(EFI_HANDLE){hid},(EFI_HANDLE){e['agent'] + 1},(EFI_HANDLE){e['controller'] + 1},"
                         f"{guid(e['protocol'])},{int(e['attributes'], 16):#010x},{e['count']}}}")
        path = bytes.fromhex(h["path"]) if h["path"] else b""
        if path.startswith(USB_HOST) and path.endswith(END):
            if len(path) > 128:
                raise SystemExit(f"handle {h['id']} path longer than 128 bytes")
            paths.append(f"{{(EFI_HANDLE){hid},{{{','.join(hex(x) for x in path)}}}}}")
    if len(edges) != platform["edge_count"]:
        raise SystemExit(f"edge count {len(edges)} != {platform['edge_count']}")

    (out / "cap4_graph.h").write_text(
        f"/* {name} ownership graph; handles remapped to nonzero fixture IDs. */\n"
        "static const EDGE CapturedEdges[]={\n" + ",\n".join(edges) + "\n};\n", newline="\n")
    (out / "cap4_usb_paths.h").write_text(
        f"/* Captured {name} USB paths; no firmware binary data. */\n"
        "static const struct {EFI_HANDLE handle;UINT8 path[128];} CapturedUsbPaths[]={\n" + ",\n".join(paths) + "\n};\n",
        newline="\n")
    print(f"{len(edges)} edges, {len(paths)} USB paths")


if __name__ == "__main__":
    main()
