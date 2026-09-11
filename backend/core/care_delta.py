"""CareDelta: deterministic comparison of two extracted diagnostic reports."""
from __future__ import annotations

from backend.models.schemas import Biomarker, CareDelta, DeltaItem, ExtractedLabData


def _key(name: str) -> str:
    return " ".join(name.lower().replace("calculated", "").replace("ckd-epi 2021", "").split())


def _best_text(b: Biomarker) -> str | None:
    if b.qualitative_value:
        return b.qualitative_value
    return b.raw_value or (str(b.value) if b.value is not None else None)


def compare_lab_results(previous: ExtractedLabData, current: ExtractedLabData) -> CareDelta:
    prev = {_key(b.name): b for b in previous.biomarkers}
    curr = {_key(b.name): b for b in current.biomarkers}
    keys = list(dict.fromkeys([*prev.keys(), *curr.keys()]))

    items: list[DeltaItem] = []
    increased = decreased = unchanged = changed_qualitative = 0

    for key in keys:
        old = prev.get(key)
        new = curr.get(key)
        label = (new or old).name  # type: ignore[union-attr]

        if old is None:
            items.append(
                DeltaItem(
                    name=label,
                    current_value=new.value if new else None,
                    current_text=_best_text(new) if new else None,
                    unit=new.unit if new else None,
                    direction="new",
                )
            )
            continue
        if new is None:
            items.append(
                DeltaItem(
                    name=label,
                    previous_value=old.value,
                    previous_text=_best_text(old),
                    unit=old.unit,
                    direction="missing",
                )
            )
            continue

        if old.value is not None and new.value is not None:
            old_unit = (old.unit or "").strip().casefold()
            new_unit = (new.unit or "").strip().casefold()
            if not old_unit or not new_unit or old_unit != new_unit or any(s in (old.raw_value or "") + (new.raw_value or "") for s in ("<", ">", "≤", "≥")):
                items.append(
                    DeltaItem(
                        name=label,
                        previous_value=old.value,
                        current_value=new.value,
                        unit=f"{old.unit} → {new.unit}",
                        direction="not_comparable",
                    )
                )
                continue
            if abs(new.value - old.value) < 1e-9:
                direction = "unchanged"
                unchanged += 1
            elif new.value > old.value:
                direction = "increased"
                increased += 1
            else:
                direction = "decreased"
                decreased += 1
            pct = None
            if old.value != 0:
                pct = round(((new.value - old.value) / abs(old.value)) * 100, 1)
            items.append(
                DeltaItem(
                    name=label,
                    previous_value=old.value,
                    current_value=new.value,
                    unit=new.unit or old.unit,
                    direction=direction,
                    percent_change=pct,
                )
            )
        else:
            old_text = _best_text(old)
            new_text = _best_text(new)
            if old_text == new_text:
                direction = "unchanged"
                unchanged += 1
            else:
                direction = "changed"
                changed_qualitative += 1
            items.append(
                DeltaItem(
                    name=label,
                    previous_text=old_text,
                    current_text=new_text,
                    unit=new.unit or old.unit,
                    direction=direction,
                )
            )

    return CareDelta(
        items=items,
        increased=increased,
        decreased=decreased,
        unchanged=unchanged,
        changed_qualitative=changed_qualitative,
    )
