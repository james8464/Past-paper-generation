from __future__ import annotations

from dataclasses import dataclass

from Backend.Core.document_dsl.model import (
    DocumentSpec,
    LayoutBox,
    LayoutPage,
    LayoutPlan,
    Length,
    Size,
)
from Backend.Core.document_dsl.profiles import board_profile


class PaginationError(RuntimeError):
    pass


@dataclass
class Paginator:
    max_operations: int = 10_000

    def layout(self, spec: DocumentSpec) -> LayoutPlan:
        profile = board_profile(spec.profile_id)
        pages: list[LayoutPage] = []
        operations = 0
        for declared_page in spec.pages:
            pending = list(declared_page.components)
            boxes: list[LayoutBox] = []
            cursor_top = profile.content_frame.y.pt + profile.content_frame.height.pt
            while pending:
                operations += 1
                if operations > self.max_operations:
                    raise PaginationError("pagination watchdog detected no progress")
                component = pending.pop(0)
                available_height = cursor_top - profile.content_frame.y.pt
                available = Size(
                    profile.content_frame.width, Length(max(0, available_height))
                )
                measured = component.measure(profile, available)  # type: ignore[attr-defined]
                if measured.width.pt > available.width.pt + 0.01:
                    raise PaginationError(
                        f"component {type(component).__name__} cannot fit page width"
                    )
                if measured.height.pt <= available.height.pt + 0.01:
                    cursor_top -= measured.height.pt
                    boxes.append(
                        LayoutBox(
                            component=component,
                            x=profile.content_frame.x,
                            y=Length(cursor_top),
                            width=measured.width,
                            height=measured.height,
                        )
                    )
                    cursor_top -= profile.component_gap.pt
                    continue

                first, remainder = component.split(profile, available)  # type: ignore[attr-defined]
                if first is not None:
                    first_size = first.measure(profile, available)
                    signature_before = repr(component)
                    signature_after = repr(remainder)
                    if first_size.height.pt <= 0 or signature_after == signature_before:
                        raise PaginationError("component splitter made no progress")
                    cursor_top -= first_size.height.pt
                    boxes.append(
                        LayoutBox(
                            component=first,
                            x=profile.content_frame.x,
                            y=Length(cursor_top),
                            width=first_size.width,
                            height=first_size.height,
                        )
                    )
                    if remainder is not None:
                        pending.insert(0, remainder)
                elif not boxes:
                    raise PaginationError(
                        f"component {type(component).__name__} cannot fit an empty page"
                    )
                else:
                    pending.insert(0, component)

                pages.append(
                    LayoutPage(
                        number=len(pages) + 1,
                        role=declared_page.role,
                        boxes=tuple(boxes),
                        label=declared_page.label,
                    )
                )
                boxes = []
                cursor_top = (
                    profile.content_frame.y.pt + profile.content_frame.height.pt
                )

            pages.append(
                LayoutPage(
                    number=len(pages) + 1,
                    role=declared_page.role,
                    boxes=tuple(boxes),
                    label=declared_page.label,
                )
            )
        return LayoutPlan(
            profile=profile,
            role=spec.role,
            pages=tuple(pages),
            metadata=spec.metadata,
        )
