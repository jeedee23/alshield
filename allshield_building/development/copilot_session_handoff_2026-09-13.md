# Slk handoff - 2026-09-13

## Assignment

- Machine: `slk` (verified from the local hostname).
- Active write directory: `allshield_building/`.
- Read-only shared sources: `shared/`.
- No commit, staging, source, baseline, reference, or user-document change was made.

## Changed Files

- `development/create_new_media_evidence_ledger.py`
  - Creates a traceable evidence-only ledger from a successful shared-media review.
  - Requires every one of the 30 images and 6 videos to remain represented.
  - Rejects source records that would become eligible for geometry from visual evidence alone.
- `development/audit_axis20_source_readiness.py`
  - Verifies the existing shared A11/as-20 source, literal member labels and baseline source projection.
  - Produces an evidence-only readiness result which permits only four directly associated IPE500 primary members and blocks additional solids without a member-to-path and endpoint mapping.
- `development/steel_catalog_axis_20_draft.json`
  - Defines only the directly source-mapped A11/as-20 IPE500 marks `30`, `29`, `21` and `25`, with stable IDs `A11_20_30`, `A11_20_29`, `A11_20_21` and `A11_20_25`.
  - Retains literal labels, source path indices, calibrated vector-derived centrelines and profile orientation; all other as-20 labels are explicitly excluded.
- `development/allshield_axis_20.py`
  - Builds the four approved Axis-20 members as visible `App::Link` objects from hidden nominal IPE500 prototypes in `Component_Library`.
  - Preserves `Structure > Portal_Frames > Frame_Axis_20 > Axis20_IPE500_Primary` parentage and validates effective world geometry.
- `development/static_check_axis_20.py` and `development/native_test_axis_20.py`
  - Validate the scoped source contract and the native FreeCAD build respectively.
- `development/GUI_Build_Axis20_ColourReview.FCMacro`
  - Prepares a fresh full-FreeCAD GUI review with a screenshot and colour-roundtrip report for the four Axis-20 links.
  - It closes only its own new test document and GUI session after saving review artefacts.
- `development/test_gui_runner_sentinel.py`
  - Focused unittest target for FreeCAD's configured `--run-test` GUI route.
  - On execution, it would write an isolated JSON artifact that asserts `App.GuiUp`, `FreeCADGui` import, and an active GUI view before any model-review code runs.
- `outputs/a11_axis20_source_review_20260913_140023_372715/render_manifest.json`
  - Corrected the reviewed view from as-20 to as-8; the output-folder name is retained as an auditable initial naming error.

## Validation

- Static baseline: `FAIL` only for pre-existing hash mismatches in `allshield_building_reference_v0_2.json` and `allshield_roof_window_source_evidence_v0_3.json`. No source file is missing or changed.
- Native baseline: `PASS` with `C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe`, FreeCAD 1.1.3, embedded Python 3.11.14 and OCCT 7.8.1.
  - Output: `outputs/native_20260913_132119_228218/`.
  - `WORK.FCStd`: 141 geometry instances, save/reopen and 100-mm negative-shift detection passed.
  - `PANELS.FCStd`: 358 geometry instances, save/reopen and 100-mm negative-shift detection passed.
- Shared September-media review: `PASS_REVIEW_ARTIFACTS_CREATED`.
  - Output: `outputs/new_media_review_20260913_132137_539108/`.
  - 30 images and 6 decodable videos; 72 sampled video frames.
- Media evidence ledger: `PASS_EVIDENCE_LEDGER_CREATED`.
  - Output: `outputs/new_media_evidence_ledger_20260913_132325_923209/new_media_evidence_ledger.json`.
  - No geometry created and no shared source modified.
- Axis-20 static contract: `PASS_STATIC_AXIS20_ONLY`.
  - Verified the four-member catalogue against the shared A11 PDF hash and protected baseline hashes.
- Axis-20 source readiness: `PASS_SOURCE_READINESS_AUDIT_PARTIAL_GEOMETRY_APPROVED`.
  - Output: `outputs/axis20_source_readiness_20260913_141044_390984/axis20_source_readiness.json`.
  - Verified the shared A11 PDF hash, the 77-line `Section_A11_Axis_20` source projection and 18 expected literal labels.
  - Permitted `A11_20_30`, `A11_20_29`, `A11_20_21` and `A11_20_25` only, because their external IPE500 contour pairs provide an unambiguous label-to-vector-path association.
- Axis-20 native build: `PASS` with FreeCAD 1.1.3.
  - Output: `outputs/native_20260913_140926_581092/Axis20_WORK.FCStd`.
  - 480 objects, four Axis-20 IPE500 members, save/reopen and 100-mm negative-shift detection passed.
  - World-bounds error is 0.0 mm for every approved Axis-20 member; no secondary as-20 steel was created.
- Axis-20 GUI review: `NOT_RUN_UNVERIFIED`.
  - `GUI_Build_Axis20_ColourReview.FCMacro` compiled and `FreeCAD.exe` was verified locally, but no terminating GUI-session result or `gui_axis20_*` artefacts were observable from this automated host.
  - A configured GUI-runner sentinel was prepared using `FreeCAD.exe --python-path <development> --run-test test_gui_runner_sentinel.GuiRunnerSentinel.test_runner_writes_sentinel`, based on the FreeCAD test-runner source. The host produced no process result and did not create even the isolated `outputs/freecad_gui_runner_runtime/` directory, so the command did not reach FreeCAD or the sentinel's first filesystem action.
  - No GUI screenshot, manual visual review, as-built verification or fabrication verification is claimed.

## Source Evidence

The shared September media visibly confirms roof sandwich-panel undersides, vertical exterior sandwich panels, steel and diagonal bracing, high window frame layers, a horizontal wire cable support, and a separate vertical access/bridge structure. It does not establish absolute grid coordinates, elevations, profile sizes, exact member marks, window correspondence, or roof-panel seam phase.

## Required Manual Sources Before New Geometry

The shared A11 page 1 was rendered locally at 288 DPI in `outputs/a11_page_review_20260913_132522_451025/`. Together with the existing approved source catalog, it is sufficient evidence for the already-modelled six Axis-8 members; no manual A11/as-8 crop is required.

The existing A11/as-20 PDF now supports the four primary IPE500 solids `30`, `29`, `21` and `25`, but no additional as-20 members. The remaining baseline projection lacks a source-controlled member-to-path and endpoint mapping. See `outputs/axis20_source_readiness_*/axis20_source_readiness.json`.

1. Additional A11/as-20 steel beyond marks `30`, `29`, `21` and `25`: a structural-member schedule keyed to A11/as-20 marks, a native CAD/DWG export with member IDs, or an annotated A11/as-20 elevation that connects each remaining member label to its vector path and endpoints.
2. Cable support: measured plan or two field photos tied independently to grid references, with tray width, elevation, endpoints and support locations.
3. Window solids: confirmed facade/grid ID for each pictured window plus section or field dimensions for outer frame, inner frame, glazing and reveals.
4. Roof segmentation: panel-layout drawing or field measurement fixing one roof-panel seam and one steeldeck rib to two grid axes or a roof edge.

## Open Model Work

- The baseline already contains lightweight facade panel envelopes in `PANELS`; roof remains a sandwich volume and zero-thickness steeldeck envelope until panel/rib phase is sourced.
- Extend remaining primary/intermediate/secondary steel only from source-labelled member paths; Axis-20 marks `30`, `29`, `21` and `25` are now present as nominal IPE500 solids.
- Keep the DN900 zone non-cutting pending field/installer approval.
- Do not model the excluded microwave or a substitute footprint.