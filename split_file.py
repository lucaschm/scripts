#!/usr/bin/env python3
"""
Split a large text file into multiple smaller files.

A new output file is created whenever a line containing the specified split
marker is encountered. The matching line becomes the first line of the new file.

Lines before the first occurrence of the split marker are ignored.
"""

from pathlib import Path
import argparse
import sys


def split_file(input_file: Path, output_dir: Path, split_marker: str) -> int:
    """
    Split a text file into multiple files based on a marker line.

    Parameters
    ----------
    input_file : Path
        Path to the input text file.
    output_dir : Path
        Directory where the output files will be written.
    split_marker : str
        Text that marks the beginning of a new output file.

    Returns
    -------
    int
        Number of output files created.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    part = 0
    outfile = None

    try:
        with input_file.open("r", encoding="utf-8", errors="ignore") as infile:
            for line in infile:
                if split_marker in line:
                    if outfile is not None:
                        outfile.close()

                    part += 1
                    outfile = (
                        output_dir / f"part_{part:03d}.txt"
                    ).open("w", encoding="utf-8")

                if outfile is not None:
                    outfile.write(line)

    finally:
        if outfile is not None:
            outfile.close()

    return part


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Split a large text file into multiple smaller files. "
            "A new file is created whenever a line containing the specified "
            "split marker is encountered. The matching line becomes the first "
            "line of the new output file."
        ),
        epilog="Example:\n"
               "  python split_file.py log.txt output "
               "\"This is the beginning of a new file\"",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input log file.",
    )

    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where the split log files will be written.",
    )

    parser.add_argument(
        "split_marker",
        type=str,
        help="Text that marks the beginning of a new output file.",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    if not args.input_file.is_file():
        print(f"Error: Input file '{args.input_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    num_files = split_file(
        args.input_file,
        args.output_dir,
        args.split_marker,
    )

    print(f"Done. Created {num_files} output file(s) in '{args.output_dir}'.")


if __name__ == "__main__":
    main()