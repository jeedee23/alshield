# Allshield - overdracht naar GitHub Copilot

Dit pakket bevat de bestaande generator **02**, de gebruikte JSON, de beschikbare brondocumenten en nieuwe starttests. Het is een overdracht voor lokaal testen en verder bouwen, **geen nieuw gevalideerd FreeCAD-model**.

## Gebruik

1. Pak de ZIP volledig uit en open deze hoofdmap als workspace in VS Code, op de computer waarop FreeCAD is geinstalleerd.
2. Open Copilot in een lokale Agent-sessie, met toestemming om de relevante terminalcommando's uit te voeren.
3. Plak de inhoud van `04_OPDRACHT_VOOR_COPILOT.txt`. Laat Copilot eerst `01_OVERDRACHT_COPILOT.md`, `02_TESTPLAN.md` en `03_BRONNENREGISTER.md` lezen.
4. Laat eerst de huidige fout onderzoeken en de oorspronkelijke generator 02 native testen. Laat daarna pas de ontbrekende staalgeometrie en details uitwerken.

Er hoeft voor deze overdracht niets naar een publieke GitHub-repository. Het pakket bevat projecttekeningen, foto's en een video; houd de workspace en eventuele repository binnen je toegestane werkomgeving.

## Wat zit erin?

| Map/bestand | Functie |
|---|---|
| `model/` | Ongewijzigde generator 02, uitvoerbare JSON, herstelmacro en eerdere validatienotities. |
| `tests/` | Statische controle, echte FreeCADCmd-test, launcher met timeout en een aparte GUI-testmacro. |
| `reference/` | Referentie-JSON v0.2, profielbewijs v0.3, DXF-topview en pakket 01 voor foutreproductie. |
| `sources/pdf/` | Negen beschikbare bron-PDF's, waaronder de staal-, gevel- en bouwkundige tekeningen. |
| `sources/images/` | Screenshot van het foute resultaat, geveldetaillering en gemarkeerde planuitsneden. |
| `sources/video/` | De aangeleverde verkleinde dronevideo. |
| `sources/text/` | Native tekstextracties per PDF-pagina; navigatiehulp, geen vervanging van tekeninggeometrie. |
| `.github/copilot-instructions.md` | Permanente projectregels voor de lokale Copilot-workspace. |
| `verification/` | Hier uitgevoerde statische controle en herkomst-/hashcontrole. Geen native FreeCAD-testrapport. |
| `user_inputs/` | Plaats hier zelf een kopie van jouw problematische `.FCStd` en lokale versiegegevens. |

## Wat moet jij nog lokaal toevoegen?

**Voor exacte reproductie van het screenshot:** sla een kopie van het document met de fout op als `.FCStd` in `user_inputs/`, liefst voordat je een herstelmacro uitvoert. De screenshot is al opgenomen, maar de feitelijke Visibility- en Link-eigenschappen van jouw document zijn daar niet uit af te lezen.

**Voor native testen:** de werkelijke paden naar `FreeCADCmd.exe` en de volledige FreeCAD-applicatie, plus de FreeCAD-versie. Copilot mag die installatie lokaal opzoeken. Een afzonderlijke STEP van de magnetron is niet nodig: die blijft buiten de generator.

## Wat ontbreekt nog aan het model?

De huidige uitvoer is een gebouwschil met bronreferenties. Het staal bestaat nog grotendeels uit geplaatste 2D-broncontouren; de volledige solids, secundaire staalonderdelen, binnenbouw en een aantal detailaansluitingen moeten nog worden uitgewerkt. Dat is precies onderdeel van deze overdracht.

De nieuwe tests zijn voorbereid en syntactisch gecontroleerd. **FreeCADCmd en de FreeCAD-GUI waren in de voorbereidingsomgeving niet beschikbaar.** Copilot moet de tests op jouw computer werkelijk uitvoeren en de resultaten vastleggen; een groene statische test is niet voldoende.
