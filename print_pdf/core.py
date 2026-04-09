"""Core PDF processing logic for print preparation."""

import os
import subprocess
import tempfile

import fitz  # PyMuPDF

_PREVIEW_DIR = tempfile.gettempdir()

A4_WIDTH = 595.28  # points
A4_HEIGHT = 841.89  # points


def process_pdf(
    input_path: str,
    output_base: str = None,
    duplex: bool = False,
    page_numbers: bool = False,
    two_up: bool = False,
    landscape: bool = False,
    output_path: str = None,
    odd_path: str = None,
    even_path: str = None,
) -> list[str]:
    """Process a PDF file for printing. Returns list of output file paths.

    For non-duplex: provide output_path or output_base.
    For duplex: provide (odd_path, even_path) or output_base.
    """
    src = fitz.open(input_path)

    # Step 1: Determine output page size based on landscape option
    if landscape:
        sheet_width, sheet_height = A4_HEIGHT, A4_WIDTH
    else:
        sheet_width, sheet_height = A4_WIDTH, A4_HEIGHT

    # Step 2: If 2-up, place two source pages on one sheet
    if two_up:
        doc = _make_two_up(src, sheet_width, sheet_height, landscape)
    else:
        doc = _reformat_pages(src, sheet_width, sheet_height)

    # Step 3: Add page numbers if requested
    if page_numbers:
        _add_page_numbers(doc)

    # Step 4 & 5: Duplex splitting or single output
    if duplex:
        if odd_path and even_path:
            return _split_duplex(doc, odd_path=odd_path, even_path=even_path)
        elif output_base:
            return _split_duplex(doc, output_base=output_base)
        else:
            raise ValueError("For duplex, provide output_base or both odd_path and even_path")
    else:
        if output_path:
            out = output_path
        elif output_base:
            out = f"{output_base}.pdf"
        else:
            raise ValueError("Provide output_path or output_base")
        doc.save(out)
        doc.close()
        return [out]


def _reformat_pages(src: fitz.Document, width: float, height: float) -> fitz.Document:
    """Reformat source pages to fit the target page size."""
    doc = fitz.open()
    for i in range(len(src)):
        new_page = doc.new_page(width=width, height=height)
        src_page = src[i]
        src_rect = src_page.rect

        # Scale to fit within target page, centered
        scale_x = width / src_rect.width
        scale_y = height / src_rect.height
        scale = min(scale_x, scale_y)

        scaled_w = src_rect.width * scale
        scaled_h = src_rect.height * scale
        x_offset = (width - scaled_w) / 2
        y_offset = (height - scaled_h) / 2

        target_rect = fitz.Rect(x_offset, y_offset, x_offset + scaled_w, y_offset + scaled_h)
        new_page.show_pdf_page(target_rect, src, i)

    return doc


def _make_two_up(
    src: fitz.Document, sheet_width: float, sheet_height: float, landscape: bool
) -> fitz.Document:
    """Place two source pages on one sheet.

    If landscape: side by side. If portrait: one above the other.
    """
    doc = fitz.open()
    total = len(src)

    for i in range(0, total, 2):
        new_page = doc.new_page(width=sheet_width, height=sheet_height)

        if landscape:
            # Side by side
            half_w = sheet_width / 2
            slot_h = sheet_height
            slots = [
                fitz.Rect(0, 0, half_w, slot_h),
                fitz.Rect(half_w, 0, sheet_width, slot_h),
            ]
        else:
            # One above the other
            half_h = sheet_height / 2
            slot_w = sheet_width
            slots = [
                fitz.Rect(0, 0, slot_w, half_h),
                fitz.Rect(0, half_h, slot_w, sheet_height),
            ]

        for j, slot in enumerate(slots):
            page_idx = i + j
            if page_idx >= total:
                break
            src_page = src[page_idx]
            src_rect = src_page.rect

            # Scale source page to fit within the slot
            scale_x = slot.width / src_rect.width
            scale_y = slot.height / src_rect.height
            scale = min(scale_x, scale_y)

            scaled_w = src_rect.width * scale
            scaled_h = src_rect.height * scale
            x_off = slot.x0 + (slot.width - scaled_w) / 2
            y_off = slot.y0 + (slot.height - scaled_h) / 2

            target_rect = fitz.Rect(x_off, y_off, x_off + scaled_w, y_off + scaled_h)
            new_page.show_pdf_page(target_rect, src, page_idx)

    return doc


def _add_page_numbers(doc: fitz.Document) -> None:
    """Add page numbers at the bottom center of each page."""
    total = len(doc)
    for i in range(total):
        page = doc[i]
        rect = page.rect
        text = f"{i + 1} / {total}"
        font_size = 10
        text_width = fitz.get_text_length(text, fontsize=font_size)
        x = (rect.width - text_width) / 2
        y = rect.height - 15
        page.insert_text(
            fitz.Point(x, y),
            text,
            fontsize=font_size,
            color=(0.3, 0.3, 0.3),
        )


def _split_duplex(
    doc: fitz.Document,
    output_base: str = None,
    odd_path: str = None,
    even_path: str = None,
) -> list[str]:
    """Split document for manual duplex printing.

    - If page count is odd, add a blank page at the end
    - Reverse order of odd pages (1, 3, 5... becomes 5, 3, 1)
    - Save odd pages and even pages to separate files
    """
    if output_base:
        odd_path = f"{output_base}_odd.pdf"
        even_path = f"{output_base}_even.pdf"

    total = len(doc)

    # Pad to even number of pages
    if total % 2 != 0:
        last_page = doc[-1]
        doc.new_page(width=last_page.rect.width, height=last_page.rect.height)
        total = len(doc)

    # Collect odd (0-indexed: 0,2,4...) and even (0-indexed: 1,3,5...) page indices
    odd_indices = list(range(0, total, 2))   # pages 1,3,5... (0-indexed: 0,2,4...)
    even_indices = list(range(1, total, 2))  # pages 2,4,6... (0-indexed: 1,3,5...)

    # Reverse odd pages so they print in correct order for manual duplex
    odd_indices.reverse()

    odd_doc = fitz.open()
    for idx in odd_indices:
        odd_doc.insert_pdf(doc, from_page=idx, to_page=idx)
    odd_doc.save(odd_path)
    odd_doc.close()

    even_doc = fitz.open()
    for idx in even_indices:
        even_doc.insert_pdf(doc, from_page=idx, to_page=idx)
    even_doc.save(even_path)
    even_doc.close()

    doc.close()
    return [odd_path, even_path]


def _apply_page_range(src: fitz.Document, page_from: int, page_to: int) -> fitz.Document:
    """Return a document with only pages in [page_from, page_to] (1-indexed).

    Returns src unchanged if both are 0 or range covers all pages.
    """
    total = len(src)
    start = (page_from - 1) if page_from > 0 else 0
    end = (page_to - 1) if page_to > 0 else total - 1
    start = max(0, min(start, total - 1))
    end = max(start, min(end, total - 1))
    if start == 0 and end == total - 1:
        return src
    subset = fitz.open()
    subset.insert_pdf(src, from_page=start, to_page=end)
    src.close()
    return subset


def print_pdf_file(pdf_path: str) -> tuple[bool, str]:
    """Send a PDF file to the default printer using lp. Returns (ok, message)."""
    try:
        result = subprocess.run(
            ["lp", pdf_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip() or "Nieznany błąd drukowania"
    except FileNotFoundError:
        return False, "Polecenie 'lp' nie zostało znalezione. Zainstaluj CUPS."
    except subprocess.TimeoutExpired:
        return False, "Przekroczono czas oczekiwania na odpowiedź drukarki."


def prepare_preview_pdfs(
    input_path: str,
    page_numbers: bool = False,
    two_up: bool = False,
    landscape: bool = False,
    duplex: bool = False,
    page_from: int = 0,
    page_to: int = 0,
) -> dict[str, str]:
    """Generate processed PDF(s) in /tmp for preview. Returns {mode: path}.

    page_from/page_to are 1-indexed inclusive; 0 means no limit.
    """
    src = fitz.open(input_path)
    src = _apply_page_range(src, page_from, page_to)

    if landscape:
        sheet_width, sheet_height = A4_HEIGHT, A4_WIDTH
    else:
        sheet_width, sheet_height = A4_WIDTH, A4_HEIGHT

    if two_up:
        doc = _make_two_up(src, sheet_width, sheet_height, landscape)
    else:
        doc = _reformat_pages(src, sheet_width, sheet_height)

    if page_numbers:
        _add_page_numbers(doc)

    src.close()

    if duplex:
        odd_path = os.path.join(_PREVIEW_DIR, "print_pdf_preview_odd.pdf")
        even_path = os.path.join(_PREVIEW_DIR, "print_pdf_preview_even.pdf")
        _split_duplex(doc, odd_path=odd_path, even_path=even_path)
        return {"odd": odd_path, "even": even_path}
    else:
        out_path = os.path.join(_PREVIEW_DIR, "print_pdf_preview.pdf")
        doc.save(out_path)
        doc.close()
        return {"processed": out_path}


def render_page_from_pdf(
    pdf_path: str,
    page_index: int = 0,
    target_width: int = 400,
) -> tuple[bytes, int]:
    """Render a single page from a PDF file as PNG bytes. Returns (png, total)."""
    doc = fitz.open(pdf_path)
    total = len(doc)
    page_index = max(0, min(page_index, total - 1))
    page = doc[page_index]
    zoom = target_width / page.rect.width
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes, total


def create_test_pdf(output_path: str) -> str:
    """Create a 2-page test PDF with descriptive labels in each half."""
    doc = fitz.open()
    font_size = 36

    for page_num in range(1, 5):
        page = doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
        half_h = A4_HEIGHT / 2

        line_h = font_size * 1.4
        for label, y_mid in [
            (f"strona {page_num}, górna połowa", half_h / 2),
            (f"strona {page_num}, dolna połowa", half_h + half_h / 2),
        ]:
            rect = fitz.Rect(20, y_mid - line_h, A4_WIDTH - 20, y_mid + line_h)
            html = (
                f'<p style="text-align:center; font-family:sans-serif;'
                f'font-size:{font_size}px; color:#262626; margin:0;">'
                f'{label}</p>'
            )
            page.insert_htmlbox(rect, html)

        page.draw_line(
            fitz.Point(40, half_h),
            fitz.Point(A4_WIDTH - 40, half_h),
            color=(0.7, 0.7, 0.7),
            width=1,
        )

    doc.save(output_path)
    doc.close()
    return output_path


def render_preview(
    input_path: str,
    page_numbers: bool = False,
    two_up: bool = False,
    landscape: bool = False,
    duplex: bool = False,
    preview_mode: str = "processed",
    page_index: int = 0,
    target_width: int = 400,
) -> tuple[bytes, int]:
    """Render a preview of a processed page as PNG bytes.

    preview_mode: "input", "processed", "odd", or "even".
    Returns (png_bytes, total_pages).
    """
    src = fitz.open(input_path)

    if preview_mode == "input":
        total = len(src)
        page_index = max(0, min(page_index, total - 1))
        page = src[page_index]
        zoom = target_width / page.rect.width
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        src.close()
        return png_bytes, total

    if landscape:
        sheet_width, sheet_height = A4_HEIGHT, A4_WIDTH
    else:
        sheet_width, sheet_height = A4_WIDTH, A4_HEIGHT

    if two_up:
        doc = _make_two_up(src, sheet_width, sheet_height, landscape)
    else:
        doc = _reformat_pages(src, sheet_width, sheet_height)

    if page_numbers:
        _add_page_numbers(doc)

    if preview_mode in ("odd", "even") and duplex:
        total = len(doc)
        if total % 2 != 0:
            last_page = doc[-1]
            doc.new_page(width=last_page.rect.width, height=last_page.rect.height)
            total = len(doc)

        odd_indices = list(range(0, total, 2))
        even_indices = list(range(1, total, 2))
        odd_indices.reverse()

        indices = odd_indices if preview_mode == "odd" else even_indices
        total_for_mode = len(indices)
        page_index = max(0, min(page_index, total_for_mode - 1))
        page = doc[indices[page_index]]
    else:
        total_for_mode = len(doc)
        page_index = max(0, min(page_index, total_for_mode - 1))
        page = doc[page_index]

    zoom = target_width / page.rect.width
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")

    doc.close()
    src.close()

    return png_bytes, total_for_mode
