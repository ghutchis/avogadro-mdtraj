#  This source file is part of the Avogadro project.
#  This source code is released under the 3-Clause BSD License, (see "LICENSE").

"""Avogadro plugin for reading MDTraj trajectory files."""

import argparse
import json
import os
import sys
import tempfile


def main():
    # Avogadro calls the plugin as:
    #   avogadro-mdtraj <identifier> [--read] [--write] [--lang <locale>] [--debug]
    # with a JSON payload on stdin. For file-mode formats, the payload is:
    #   {"operation": "read", "filename": "/path/to/file.h5"}
    parser = argparse.ArgumentParser()
    parser.add_argument("feature")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--read", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    try:
        avo_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"avogadro-mdtraj: failed to parse JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    if args.debug:
        print(f"avogadro-mdtraj: feature={args.feature} input={avo_input}",
              file=sys.stderr)

    output = None
    try:
        match args.feature:
            case "mdtraj-hdf5":
                if args.read:
                    filename = avo_input.get("filename")
                    if not filename:
                        print("avogadro-mdtraj: no 'filename' in input payload",
                              file=sys.stderr)
                        sys.exit(1)
                    output = read_hdf5(filename, debug=args.debug)
    except Exception as e:
        import traceback
        print(f"avogadro-mdtraj: error in feature '{args.feature}': {e}",
              file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    if output is not None:
        print(output, end="")
    else:
        print(f"avogadro-mdtraj: no output produced for feature='{args.feature}'",
              file=sys.stderr)
        sys.exit(1)


def read_hdf5(filename, debug=False):
    import mdtraj as md

    if debug:
        print(f"avogadro-mdtraj: loading '{filename}'", file=sys.stderr)

    trajectory = md.load(filename)

    if debug:
        print(f"avogadro-mdtraj: loaded {trajectory.n_frames} frames, "
              f"{trajectory.n_atoms} atoms", file=sys.stderr)

    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        trajectory.save_pdb(tmp_path)
        with open(tmp_path, "r") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)
