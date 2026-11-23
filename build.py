#!/usr/bin/env python3
"""Regenerate the compressed submission build (main.py) from engine.py.

The submitted tiny-chess-01 build is the engine source compressed with LZMA
(alone format, 16 KiB dictionary, lc=3, lp=0, pb=0), embedded as a latin-1
string literal that decompresses and execs at import. This script reproduces
an equivalent build: the output decompresses to exactly engine.py.

Usage: python3 build.py   (writes main.py next to this file)
"""

import lzma
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _escape(s):
    parts = []
    for i, ch in enumerate(s):
        if ch == "\\":
            parts.append("\\\\")
        elif ch == "'":
            parts.append("\\'")
        elif ch == "\n":
            parts.append("\\n")
        elif ch == "\r":
            parts.append("\\r")
        elif ch == "\t":
            parts.append("\\t")
        elif ch == "\x00":
            nxt = s[i + 1] if i + 1 < len(s) else ""
            # \0 before an octal digit would parse as an octal escape.
            parts.append("\\x00" if nxt in "01234567" else "\\0")
        else:
            parts.append(ch)
    return "".join(parts)


def build(src_path, out_path):
    with open(src_path, "rb") as f:
        src = f.read()
    blob = bytearray(
        lzma.compress(
            src,
            format=lzma.FORMAT_ALONE,
            filters=[
                {
                    "id": lzma.FILTER_LZMA1,
                    "dict_size": 1 << 14,
                    "lc": 3,
                    "lp": 0,
                    "pb": 0,
                }
            ],
        )
    )
    # Alone header: store the uncompressed size (bytes 5..13).
    blob[5:13] = len(src).to_bytes(8, "little")
    lit = _escape(bytes(blob).decode("latin-1"))
    out = "#coding:l1\nimport lzma;exec(lzma.decompress('" + lit + "'.encode('l1')))\n"
    with open(out_path, "wb") as f:
        f.write(out.encode("latin-1"))
    return out.encode("latin-1")


def verify(out_path, src_path):
    import ast

    tree = ast.parse(open(out_path, "rb").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "exec":
            payload = eval(
                compile(ast.Expression(node.args[0]), "<verify>", "eval"),
                {"lzma": lzma},
            )
            with open(src_path, "rb") as f:
                return payload == f.read()
    return False


if __name__ == "__main__":
    src_path = os.path.join(HERE, "engine.py")
    out_path = os.path.join(HERE, "main.py")
    blob = build(src_path, out_path)
    ok = verify(out_path, src_path)
    print("wrote %s (%d bytes), decompresses to engine.py: %s" % (out_path, len(blob), ok))
    raise SystemExit(0 if ok else 1)
