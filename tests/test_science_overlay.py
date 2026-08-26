from __future__ import annotations

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing

from Backend.Core.overlay.science import (
    ApparatusSpec,
    Atom,
    Bond,
    CircuitComponent,
    CircuitSpec,
    MoleculeSpec,
    RaySpec,
    apparatus_diagram,
    circuit_diagram,
    molecule_diagram,
    ray_diagram,
)


def test_science_diagrams_are_vector_and_deterministic() -> None:
    drawings = (
        apparatus_diagram(
            ApparatusSpec(
                vessels=("beaker", "measuring cylinder"),
                labels=("water bath", "gas collected"),
            )
        ),
        molecule_diagram(
            MoleculeSpec(
                atoms=(Atom("C", 0, 0), Atom("O", 1, 0), Atom("O", -1, 0)),
                bonds=(Bond(0, 1, 2), Bond(0, 2, 1)),
            )
        ),
        circuit_diagram(
            CircuitSpec(
                components=(
                    CircuitComponent("cell", "6 V"),
                    CircuitComponent("resistor", "12 Ω"),
                    CircuitComponent("ammeter", "A"),
                )
            )
        ),
        ray_diagram(
            RaySpec(object_distance=80, focal_length=30, image_distance=48)
        ),
    )

    assert all(isinstance(drawing, Drawing) for drawing in drawings)
    assert all(renderPDF.drawToString(drawing).startswith(b"%PDF-") for drawing in drawings)
    repeated = molecule_diagram(
        MoleculeSpec(
            atoms=(Atom("C", 0, 0), Atom("O", 1, 0), Atom("O", -1, 0)),
            bonds=(Bond(0, 1, 2), Bond(0, 2, 1)),
        )
    )
    assert _drawing_signature(drawings[1]) == _drawing_signature(repeated)


def test_science_diagrams_reject_invalid_geometry() -> None:
    invalid_bond = MoleculeSpec(
        atoms=(Atom("H", 0, 0),),
        bonds=(Bond(0, 2, 1),),
    )
    invalid_ray = RaySpec(object_distance=10, focal_length=0, image_distance=20)

    try:
        molecule_diagram(invalid_bond)
    except ValueError as error:
        assert "bond" in str(error)
    else:
        raise AssertionError("invalid bond was accepted")

    try:
        ray_diagram(invalid_ray)
    except ValueError as error:
        assert "focal length" in str(error)
    else:
        raise AssertionError("invalid focal length was accepted")


def _drawing_signature(drawing: Drawing) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
    return tuple(
        (
            type(shape).__name__,
            tuple(sorted((key, str(value)) for key, value in shape.getProperties().items())),
        )
        for shape in drawing.getContents()
    )
