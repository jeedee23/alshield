# AllShield AHU - TM Technics BOM and RFQ dossier

## Status and purpose

This file defines the procurement package for TM Technics. It is based only on the supplied documents below; it is not a fabrication drawing, a final routing design, or an instruction to infer missing geometry.

The selected route is **B**: prepare a part-by-part BOM/RFQ dossier from the explicitly supplied assembly STEP, separately supplied subassembly STEPs, dimensioned screenshots, and this source register. Do not generate Fusion drawings as the first deliverable.

The complete AHU assembly STEP has **not** yet been provided or identified. Do not derive a final quantity, length, transition, plenum, flange, damper, penetration, or support from unrelated reference STEP files.

## Source documents read

| Source | Date/revision | What it establishes | What it does not establish |
|---|---|---|---|
| `TM tecnics pre-offer.pdf` | Offer S04874, 2026-08-05 | Preliminary material categories, nominal duct sizes, surface-area pricing, provisional isolation, lifting, engineering and installation pricing | Final routing, individual segment lengths, elbow orientation, transition geometry, support locations, interfaces, or final scope |
| `AllShield - TM Technics Work Scope.pdf` | Draft rev. 0.1, 2026-09-01 | Required building interfaces, prefabrication principle, platform/site scope and exclusions | Final 3D arrangement, positions, connection points, selected equipment, final BOM, drawing issue, or fabrication dimensions |

The work-scope document says that MEAM will provide a BOM in the format already used by TM Technics. This dossier is intended to become that input.

## Decision: use a controlled STEP-to-BOM package

Use the later-provided full assembly STEP as the geometry index and the subassembly STEPs as procurement references. For every BOM row, retain the source file and an item ID. A TM Technics quotation must never depend only on a visual screenshot or a generic name embedded in STEP metadata.

The package sent for quotation should contain:

1. One **read-only released assembly STEP** with a versioned filename.
2. One STEP for every separately orderable or fabricated subassembly, including plenums and custom transitions.
3. A BOM in the table format below, with a stable `AHU-` item ID that also appears in the model and screenshots.
4. One annotated isometric screenshot for the whole system and one screenshot per subassembly. Each screenshot must identify item IDs, connection IDs, view direction, and units in mm.
5. A short interface schedule: machine, upperdeck, building roof, wall intake and on-site connection interfaces.
6. An open-items list. Unknown information must remain `UNRESOLVED`; it must not be converted into a nominal dimension or counted as an order item.

Fusion drawing automation is a possible later phase only for items where TM Technics requests a fabrication drawing after reviewing the BOM/STEP package. It is not needed to request a first complete quotation.

## Preliminary offer evidence - do not use as final take-off

The following values are transcribed as commercial evidence from offer S04874. The offer uses square metres for the rectangular ducts and bends, so it is not an item-by-item fabrication BOM.

### Inlet material stated in the offer

| Offer items | Description | Quantity stated | BOM interpretation |
|---|---|---:|---|
| 10 to 12 | Spiro duct, $\varnothing500$ | 3 x 7 m | 21 m total only; individual run IDs and couplers are not stated |
| 13 | Spiro bend, 90 degrees, $\varnothing500$ | 1 each | Bend radius, orientation and connection type are not stated |
| 14 | Spiro duct, $\varnothing500$ | 6 m | 6 m only; route is not stated |
| 15 | Reducer, $\varnothing500$ to $\varnothing710$ | 1 each | Length and eccentricity are not stated |
| 16 | Spiro duct, $\varnothing710$ | 6 m | 6 m only; route is not stated |
| 17 | Reducer, $\varnothing710$ to $\varnothing800$ | 1 each | Length and eccentricity are not stated |
| 18 | Spiro duct, $\varnothing900$ | 15 m | 15 m only; route and connection are not stated |

**Open RFQ question `RFQ-01`:** the sequence explicitly lists a transition from $\varnothing710$ to $\varnothing800$ and then 15 m of $\varnothing900$ duct. No $\varnothing800$ to $\varnothing900$ transition is listed. Confirm whether this is an omitted transition, a nominal-size notation issue, or a separate interface item.

### Outlet material stated in the offer

| Offer items | Description | Quantity stated | BOM interpretation |
|---|---|---:|---|
| 19 to 22 | Rectangular 90-degree bend, 880 x 220 mm | 6.52 m2 | Surface area only; four individual bends are implied by the item range but their geometry/orientation must be confirmed |
| 23 to 26 | Rectangular duct, 880 x 220 mm | 52.80 m2 | Surface area only; segmentation and lengths must come from the model |
| 27 | Rectangular 90-degree bend, 880 x 220 mm | 1.63 m2 | Surface area only; geometry/orientation unresolved |
| 28 | Rectangular duct, 880 x 220 mm | 9.90 m2 | Surface area only; segmentation and length unresolved |
| 29 | Rectangular transition, L = 1000 mm | 2.80 m2 | End sizes and eccentricity unresolved |
| 30 | Rectangular duct, 880 x 440 mm | 11.90 m2 | Surface area only; segmentation and length unresolved |
| 31 | Rectangular transition, L = 1000 mm | 3.10 m2 | End sizes and eccentricity unresolved |
| 32 | Rectangular duct, 880 x 660 mm | 13.90 m2 | Surface area only; segmentation and length unresolved |
| 33 | Rectangular transition, L = 1000 mm | 3.50 m2 | End sizes and eccentricity unresolved |
| 34 | Rectangular duct, 880 x 880 mm | 52.80 m2 | Surface area only; segmentation and length unresolved |

The likely area-derived lengths must **not** be used as ordering lengths. They do not establish fabrication segmentation, bend development, flange allowance, or transition geometry.

### Preliminary commercial scope to clarify

| Subject | Offer/work-scope evidence | Required clarification |
|---|---|---|
| Internal insulation | Offer contains 160 m2 of 13-mm damp-tight internal insulation | Map isolation exactly to BOM item IDs, faces, joints and interface exclusions |
| Supports | Offer contains one lump-sum galvanized hanging/fixing-material item | Issue a support schedule with item IDs, load responsibility, fixed points and building connection requirements |
| Mechanical installation | Offer contains installation and engineering lines; its "Niet inbegrepen" note says placing named materials is excluded | `RFQ-02`: obtain a written scope clarification before using the offer as an installation price |
| Electrical | Work scope explicitly excludes electrical installation | Keep sensors as mechanical placement only unless a later written scope revision says otherwise |
| Site work | Work scope assumes two people for about one to three working days | Treat as an assumption contingent on issued 3D/BOM and access prerequisites, not as a commitment |

## Required BOM schema

One row represents one orderable part or an explicit fabrication assembly. Do not group different dimensions, orientations or connection types into a single row merely because their material category is the same.

| BOM ID | Parent assembly | Description | Qty | Nominal internal size | Fabrication length / angle | Material and thickness | Connection at end A | Connection at end B | Insulation | STEP source | Screenshot | Status |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| AHU-000 | - | Reserved example only; not an order item | - | - | - | - | - | - | - | - | - | UNRESOLVED |

The following fields are mandatory where applicable:

- rectangular: clear width x height, length, bend throat/radius, orientation, and whether a transition is concentric or eccentric;
- round: nominal diameter, length, bend radius/angle, reducer end diameters, and orientation;
- plenum: all connection faces, clear internal dimensions, plate thickness, access requirements, drain requirements and support points;
- flanges/connections: flange standard/profile, outside dimensions, bolt pattern, gasket/seal responsibility, mating component and access clearance;
- roof/wall interfaces: interface ID, penetration size, grid/world position supplied by the building coordination model, weathering scope and installer responsibility;
- supports: hanger type, quantity, spacing, load basis, fixing substrate and responsibility;
- every physical part: quantity, status and a versioned source reference.

## Interface and scope register

| Interface ID | Required by work scope | Current status | Required released input |
|---|---|---|---|
| IF-ROOF-01 to IF-ROOF-03 | Three DN1000 roof penetrations, each with anti-bird grille | UNRESOLVED | Centre positions, penetration/collar detail, roof build-up, flashing responsibility and which outlet is humid process air |
| IF-ROOF-EXH-01 | Humid process-air exhaust needs condensate collection and a single central drain point | UNRESOLVED | Drain diameter/material, fall, discharge route, cleanability, freeze protection responsibility and interface to roof outlet |
| IF-WALL-INTAKE-01 | Wall penetration in an existing window opening; suspended horizontal duct to machine connection point | UNRESOLVED | Window opening survey, final penetration detail, intake louvre/weather detail, duct end geometry, support and machine connection ID |
| IF-MACHINE-01 | Machine/platform flanges to be prepared at MEAM | UNRESOLVED | Released machine interface schedule from MEAM; do not invent or model a machine footprint |
| IF-PLATFORM-01 | Ducts, transitions, bypasses, dampers, sensors, chillers, coils and recuperators prepared on/around upperdeck | UNRESOLVED | Released upperdeck 3D assembly with actual selected equipment or explicitly approved fabrication dummies |
| IF-SITE-01 | Final positioning and mechanical connections at AllShield | UNRESOLVED | Rigging/access plan, connection sequence, installer responsibility matrix and approved final installation drawing |

## Release procedure

1. Johan identifies the exact released full-assembly STEP and each subassembly STEP. Record filename, SHA-256, source owner and date in the BOM dossier.
2. Extract the assembly hierarchy and visible physical components without assigning missing dimensions from names alone.
3. Create the first BOM using the schema above. Every row must be traceable to a STEP object, a screenshot callout, or an explicit document source.
4. Reconcile the BOM against the offer as a commercial comparison only. Record differences, including `RFQ-01` and `RFQ-02`.
5. Send the STEP set, annotated screenshots, BOM, interface register and open-items list to TM Technics for technical review and quotation.
6. Only after TM Technics identifies the drawings they require, decide whether to produce a Fusion drawing export for those selected parts.
7. Preserve the submitted package in a versioned `outputs/` subfolder below `allshield_AHU/`; do not overwrite the source PDFs or a previous submission.

## Acceptance gate before quotation

Do not label the dossier `READY_FOR_QUOTATION` until every ordered row has a quantity, nominal dimensions, connection definition, source reference, status and responsibility. A final check must also confirm:

- all three DN1000 roof interfaces are represented, including anti-bird grilles;
- the humid exhaust condensate/drain arrangement is explicitly represented;
- the wall-intake interface is tied to a surveyed existing window opening and machine connection;
- electrical work is excluded or explicitly added by a written revision;
- support and insulation scope are mapped to specific BOM items;
- no machine geometry, placeholder, assumed material thickness, or invented route has been introduced.

Until then the correct status is **BOM DRAFT - TECHNICAL REVIEW REQUIRED**.