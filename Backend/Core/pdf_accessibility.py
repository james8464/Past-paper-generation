from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pymupdf as fitz


def add_page_structure_tree(path: Path, *, language: str = "en-GB") -> None:
    """Attach a deterministic page-level structure tree and marked content.

    Each page is one ordered ``Sect`` element associated with an MCID. This
    preserves the renderer's deliberate content-stream order for assistive
    technology while leaving page geometry untouched.
    """

    path = Path(path)
    descriptor, staged_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tagged",
    )
    os.close(descriptor)
    staged = Path(staged_name)
    staged.unlink()
    try:
        with fitz.open(path) as document:
            catalog = document.pdf_catalog()
            if _has_structure_tree(document, catalog):
                return

            root_xref = _new_object(document)
            parent_tree_xref = _new_object(document)
            elements: list[int] = []
            for index, page in enumerate(document):
                content_xref = _new_object(document)
                content = page.read_contents()
                document.update_stream(
                    content_xref,
                    b"/P <</MCID 0>> BDC\n" + content + b"\nEMC\n",
                    compress=True,
                )
                document.xref_set_key(page.xref, "Contents", f"{content_xref} 0 R")
                document.xref_set_key(page.xref, "StructParents", str(index))
                document.xref_set_key(page.xref, "Tabs", "/S")

                element_xref = _new_object(document)
                document.update_object(
                    element_xref,
                    "<< /Type /StructElem /S /Sect "
                    f"/P {root_xref} 0 R /Pg {page.xref} 0 R /K 0 >>",
                )
                elements.append(element_xref)

            element_refs = " ".join(f"{xref} 0 R" for xref in elements)
            parent_entries = " ".join(
                f"{index} [ {xref} 0 R ]" for index, xref in enumerate(elements)
            )
            document.update_object(
                parent_tree_xref,
                f"<< /Nums [ {parent_entries} ] >>",
            )
            document.update_object(
                root_xref,
                "<< /Type /StructTreeRoot "
                f"/K [ {element_refs} ] /ParentTree {parent_tree_xref} 0 R "
                f"/ParentTreeNextKey {len(elements)} >>",
            )
            document.xref_set_key(catalog, "StructTreeRoot", f"{root_xref} 0 R")
            document.xref_set_key(catalog, "MarkInfo", "<< /Marked true >>")
            document.xref_set_key(catalog, "Lang", f"({language})")
            document.save(staged, garbage=4, deflate=True)
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def has_logical_page_order(document: fitz.Document, page: fitz.Page) -> bool:
    """Return whether a page is linked to marked content in a structure tree."""

    if not _has_structure_tree(document, document.pdf_catalog()):
        return False
    parent_kind, _parent_value = document.xref_get_key(page.xref, "StructParents")
    return parent_kind == "int" and b"/MCID" in page.read_contents()


def _has_structure_tree(document: fitz.Document, catalog: int) -> bool:
    return catalog > 0 and document.xref_get_key(catalog, "StructTreeRoot")[0] == "xref"


def _new_object(document: fitz.Document) -> int:
    xref = document.get_new_xref()
    document.update_object(xref, "<<>>")
    return xref
