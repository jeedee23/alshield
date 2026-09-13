"""Fusion 360 script: export the active F3D component properties to TSV.

Install/run this file as a Fusion script. It reads the active design only and
writes one TSV named after the active F3D into subassembliesteps.
"""

import csv
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import adsk.core
import adsk.fusion


AHU_DIRECTORY = Path(r"D:\allshield_divers\repo\alshield\allshield_AHU")
OUTPUT_DIRECTORY = AHU_DIRECTORY / "ducting" / "subassembliesteps"
EXCEPTIONS_FILE = AHU_DIRECTORY / "tools" / "fusion_component_exceptions.json"
TSV_COLUMNS = [
    "schema",
    "generated_utc",
    "source_f3d_name",
    "source_fusion_data_id",
    "component_name",
    "component_part_number",
    "component_description",
    "component_entity_token",
    "occurrence_count",
    "occurrence_paths",
    "body_name",
    "body_entity_token",
    "body_count",
    "direct_subcomponent_count",
    "body_is_solid",
    "validation_status",
    "validation_details",
    "component_classification",
    "tm_bom_scope",
    "material_name",
    "appearance_name",
    "bbox_x_mm",
    "bbox_y_mm",
    "bbox_z_mm",
    "surface_area_mm2",
    "volume_mm3",
    "mass_kg",
    "density_kg_m3",
    "component_attributes_json",
    "body_attributes_json",
]


def _value_or_empty(value):
    return "" if value is None else value


def _attributes_json(entity):
    attributes = []
    for index in range(entity.attributes.count):
        attribute = entity.attributes.item(index)
        attributes.append({
            "group": attribute.groupName,
            "name": attribute.name,
            "value": attribute.value,
        })
    return json.dumps(attributes, ensure_ascii=True, sort_keys=True)


def _name_or_empty(item):
    return item.name if item is not None else ""


def _body_properties(body):
    bounds = body.boundingBox
    properties = body.physicalProperties
    material = body.material
    if material is None:
        material = body.parentComponent.material
    return {
        "body_name": body.name,
        "body_entity_token": body.entityToken,
        "body_is_solid": "YES" if body.isSolid else "NO",
        "material_name": _name_or_empty(material),
        "appearance_name": _name_or_empty(body.appearance),
        "bbox_x_mm": round(bounds.maxPoint.x - bounds.minPoint.x, 3) * 10.0,
        "bbox_y_mm": round(bounds.maxPoint.y - bounds.minPoint.y, 3) * 10.0,
        "bbox_z_mm": round(bounds.maxPoint.z - bounds.minPoint.z, 3) * 10.0,
        "surface_area_mm2": round(properties.area * 100.0, 3),
        "volume_mm3": round(properties.volume * 1000.0, 3),
        "mass_kg": round(properties.mass, 6),
        "density_kg_m3": round(properties.density * 1000000.0, 6),
        "body_attributes_json": _attributes_json(body),
    }


def _component_exception(component, exceptions):
    for exception in exceptions:
        if component.name == exception.get("component_name"):
            return exception
    return None


def _occurrence_component_names(occurrence_path):
    return [segment.rsplit(":", 1)[0] for segment in occurrence_path.split("+")]


def _purchased_parent_exception(component, occurrence_paths, exceptions):
    if not occurrence_paths:
        return None
    for exception in exceptions:
        parent_name = exception.get("component_name")
        if parent_name == component.name:
            continue
        if all(parent_name in _occurrence_component_names(path) for path in occurrence_paths):
            return exception
    return None


class ExportCancelled(Exception):
    pass


def _validation_failures(component):
    failures = []
    if component.bRepBodies.count != 1:
        failures.append("BODY_COUNT_{0}".format(component.bRepBodies.count))
    if component.occurrences.count != 0:
        failures.append("DIRECT_SUBCOMPONENTS_{0}".format(component.occurrences.count))
    if component.bRepBodies.count == 1 and not component.bRepBodies.item(0).isSolid:
        failures.append("BODY_NOT_SOLID")
    return failures


def _validation_status(component, is_root, exception, purchased_parent):
    if is_root:
        return "ROOT_ASSEMBLY", "Root assembly is not an orderable component.", "ROOT_ASSEMBLY", "NOT_AN_ORDER_ITEM"
    if exception is not None:
        return (
            exception["validation_status"],
            exception["reason"],
            exception["classification"],
            exception["tm_bom_scope"],
        )
    if purchased_parent is not None:
        return (
            "PURCHASED_PART_CHILD",
            "Child of purchased part {0}; excluded from TM Technics fabrication.".format(
                purchased_parent["component_name"]
            ),
            "PURCHASED_PART_CHILD",
            "MEAM_SUPPLY_EXCLUDED_FROM_TM_FABRICATION",
        )
    failures = _validation_failures(component)
    if failures:
        return "FAIL", "; ".join(failures), "FABRICATED_PART", "TM_FABRICATION_CANDIDATE"
    return "PASS", "Exactly one solid body and no direct subcomponents.", "FABRICATED_PART", "TM_FABRICATION_CANDIDATE"


def _occurrences_by_component(root_component):
    occurrences = {}
    for index in range(root_component.allOccurrences.count):
        occurrence = root_component.allOccurrences.item(index)
        occurrences.setdefault(occurrence.component.entityToken, []).append(occurrence.fullPathName)
    return occurrences


def _source_data_id(document):
    data_file = document.dataFile
    return data_file.id if data_file is not None else ""


def _exceptions():
    payload = json.loads(EXCEPTIONS_FILE.read_text(encoding="utf-8"))
    exceptions = payload.get("exceptions")
    if not isinstance(exceptions, list):
        raise ValueError("The Fusion component-exceptions file must contain an exceptions list.")
    for exception in exceptions:
        for field in ("component_name", "classification", "tm_bom_scope", "validation_status", "reason"):
            if not exception.get(field):
                raise ValueError("Fusion component exception is missing {0}.".format(field))
    return exceptions


def _write_exceptions(exceptions):
    payload = {
        "schema": "allshield.ahu.fusion-component-exceptions.v1",
        "exceptions": exceptions,
    }
    EXCEPTIONS_FILE.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _purchased_part_exception(component, failures):
    return {
        "component_name": component.name,
        "classification": "PURCHASED_PART_ASSEMBLY",
        "tm_bom_scope": "MEAM_SUPPLY_EXCLUDED_FROM_TM_FABRICATION",
        "validation_status": "PURCHASED_PART_EXCEPTION",
        "reason": (
            "Selected interactively as a purchased part during Fusion TSV export "
            "after validation: {0}."
        ).format("; ".join(failures)),
    }


def _prompt_for_purchased_part(ui, component, failures):
    answer = ui.messageBox(
        "{0} heeft subcomponenten en/of bodies ({1}).\n\n"
        "Kies Ja om dit specifieke onderdeel als koopdeel te markeren.\n"
        "Kies Nee of Annuleren om de export te annuleren; je kunt dan zelf "
        "de correcties uitvoeren.".format(component.name, "; ".join(failures)),
        "AllShield AHU-validatie",
        adsk.core.MessageBoxButtonTypes.YesNoCancelButtonType,
        adsk.core.MessageBoxIconTypes.QuestionIconType,
    )
    if answer == adsk.core.DialogResults.DialogYes:
        return _purchased_part_exception(component, failures)
    raise ExportCancelled(
        "Export geannuleerd. Geen TSV of koopdeeluitzonderingen zijn gewijzigd."
    )


def _model_stem(document_name):
    filename = Path(document_name).name
    return filename[:-4] if filename.lower().endswith(".f3d") else filename


def _row(component, occurrence_paths, document, is_root, exception, purchased_parent):
    status, details, classification, tm_bom_scope = _validation_status(
        component,
        is_root,
        exception,
        purchased_parent,
    )
    body_data = {}
    if component.bRepBodies.count == 1:
        body_data = _body_properties(component.bRepBodies.item(0))
    row = {
        "schema": "allshield.ahu.fusion-component-export.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_f3d_name": document.name,
        "source_fusion_data_id": _source_data_id(document),
        "component_name": component.name,
        "component_part_number": _value_or_empty(component.partNumber),
        "component_description": _value_or_empty(component.description),
        "component_entity_token": component.entityToken,
        "occurrence_count": len(occurrence_paths),
        "occurrence_paths": " | ".join(occurrence_paths),
        "body_count": component.bRepBodies.count,
        "direct_subcomponent_count": component.occurrences.count,
        "validation_status": status,
        "validation_details": details,
        "component_classification": classification,
        "tm_bom_scope": tm_bom_scope,
        "component_attributes_json": _attributes_json(component),
        "body_name": "",
        "body_entity_token": "",
        "body_is_solid": "",
        "material_name": "",
        "appearance_name": "",
        "bbox_x_mm": "",
        "bbox_y_mm": "",
        "bbox_z_mm": "",
        "surface_area_mm2": "",
        "volume_mm3": "",
        "mass_kg": "",
        "density_kg_m3": "",
        "body_attributes_json": "[]",
    }
    row.update(body_data)
    return row


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        document = app.activeDocument
        design = adsk.fusion.Design.cast(app.activeProduct)
        if document is None or design is None:
            raise RuntimeError("Open an F3D design before running this script.")

        root_component = design.rootComponent
        occurrences = _occurrences_by_component(root_component)
        exceptions = _exceptions()
        pending_exceptions = []
        rows = []
        for index in range(design.allComponents.count):
            component = design.allComponents.item(index)
            is_root = component == root_component
            occurrence_paths = occurrences.get(component.entityToken, [])
            current_exceptions = exceptions + pending_exceptions
            exception = _component_exception(component, current_exceptions)
            purchased_parent = _purchased_parent_exception(
                component,
                occurrence_paths,
                current_exceptions,
            )
            failures = _validation_failures(component)
            if not is_root and exception is None and purchased_parent is None and failures:
                exception = _prompt_for_purchased_part(ui, component, failures)
                pending_exceptions.append(exception)
            rows.append(_row(
                component,
                occurrence_paths,
                document,
                is_root,
                exception,
                purchased_parent,
            ))

        OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIRECTORY / (_model_stem(document.name) + ".tsv")
        if pending_exceptions:
            _write_exceptions(exceptions + pending_exceptions)
        with output_path.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)

        failures = [row for row in rows if row["validation_status"] == "FAIL"]
        ui.messageBox(
            "TSV geschreven: {0}\nComponenten: {1}\nValidatiefouten: {2}".format(
                output_path, len(rows) - 1, len(failures)
            ),
            "AllShield AHU Fusion-export",
        )
    except ExportCancelled as error:
        ui.messageBox(str(error), "AllShield AHU-validatie")
    except Exception:
        ui.messageBox(traceback.format_exc(), "AllShield AHU Fusion-export fout")


def stop(context):
    pass