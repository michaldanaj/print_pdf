"""Command-line interface for print-pdf."""

import argparse
import sys

from print_pdf.core import process_pdf


def main():
    parser = argparse.ArgumentParser(
        description="Prepare a PDF for printing (duplex, 2-up, page numbers, landscape)."
    )
    parser.add_argument("-i", required=True, help="Input PDF file")
    parser.add_argument("-o", required=True, help="Base name for output file(s) (without extension)")
    parser.add_argument("-d", action="store_true", help="Manual duplex: split into _odd.pdf and _even.pdf")
    parser.add_argument("-n", action="store_true", help="Add page numbers")
    parser.add_argument("-t", action="store_true", help="2 pages per sheet (2-up)")
    parser.add_argument("-l", action="store_true", help="Landscape orientation")

    args = parser.parse_args()

    try:
        outputs = process_pdf(
            input_path=args.i,
            output_base=args.o,
            duplex=args.d,
            page_numbers=args.n,
            two_up=args.t,
            landscape=args.l,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    for path in outputs:
        print(f"Created: {path}")


if __name__ == "__main__":
    main()
