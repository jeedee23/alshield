# Allshield FreeCAD projectregels

Lees 01_OVERDRACHT_COPILOT.md en 02_TESTPLAN.md voordat je code of geometrie wijzigt.

- Werkomgeving: lokale FreeCAD/FreeCADCmd en deze workspace. Verifieer versies en paden; neem geen installatiepad aan.
- Eerst baseline 02 native testen, dan corrigeren en uitbreiden. Het bestaande screenshotprobleem is nog niet bewezen opgelost in native FreeCAD.
- V3 is geen bron voor code, coordinaten of defaults. Het nieuwe model is JSON-gestuurd.
- Geen magnetron/microwave, geen machinefootprint en geen placeholder. De gebruiker importeert zijn eigen machine.
- Oorsprong: staal-/gridkruising 21/A. +X naar as 1, +Y naar M, +Z omhoog. Een as is niet automatisch een muurvlak of volledig portaal.
- Geen uniform staalraster gokken; lokale assen van A en M afzonderlijk behouden.
- Componenten krijgen stabiele IDs en echte parent/child-relaties. Roof > Ceiling > Sandwich_Ceiling blijft behouden.
- Hergebruik identieke vormen via links; Component_Library buiten Building en standaard onzichtbaar. Controleer effectieve wereldtransformaties, niet alleen lokale Shape-data.
- Onbekende waarden blijven onopgelost. Primair bronbewijs, bronrevisie en geometrische betekenis bewaren. Een PDF-meting is niet automatisch as-built.
- Contouren niet met willekeurige dikte tot staal-solids maken. Voorkom dubbel genereren uit meerdere aanzichten.
- Dakonderzijde en dakbovenzijde zijn volgens de huidige broninterpretatie hetzelfde 132/164-sandwichdak, geen twee isolatiedaken.
- Bronnen en baseline-archief niet wijzigen. Niet publiceren of naar remote pushen zonder expliciete toestemming.
- Gebruikersdocumenten niet wissen, sluiten of overschrijven. Testen in nieuwe documenten/kopieen en unieke outputmappen.
- Rapporteer static, native, GUI en inhoudelijke broncontrole afzonderlijk. Geen ontbrekende testruns als PASS presenteren. Echte logs en screenshots bewaren.
