# Bronnenregister - meegeleverd en ontbrekend

De negen PDF-bestanden hieronder zijn in dit pakket opgenomen. Enkele lokale bestandsnamen zijn verkort; de oorspronkelijke Library-/uploadnamen staan ernaast. De oorspronkelijke PDF-bytes zijn niet aangepast. SHA-256-controles staan in `verification/source_registry.json` en `MANIFEST_SHA256.json`.

## Primaire tekeningen en fotobatch

| Bestand in `sources/pdf/` | Oorspronkelijke naam | Relevantie | Pagina's om eerst te bekijken |
|---|---|---|---|
| `20260522 ter Aar Indeling totaal (002).pdf` | 20260522 ter Aar Indeling totaal (002).pdf | Volledige layout en kalibratiematen 6060/2800/5200; overige apparatuur en openingen. | 1 |
| `20260730_maatvoering.pdf` | 20260730 maatvoering indeling fabriek totaal ter Aar nav gesprek Rody(1).pdf | Aanvullende layout/maatvoering na gesprek Rody; bronverschillen expliciet vergelijken. | 1 |
| `44449_Logivast_07maart2025(1).pdf` | 44449_Logivast_07maart2025(1).pdf | Architectuur: materiaal-/laagopbouw en details. Oudere situatie niet blind boven actuele inrichting laten gelden. | 6-8; detailblad 8 |
| `Hardeman_tekeningenset.pdf` | Tekeningenset plantekenaar_Hardeman.pdf | Aanvullende plantekenaarset; de paginabeelden bekijken waar de native tekstextractie onvoldoende is. | zie PDF |
| `a03_ovz-a.pdf` | a03_ovz-a(1).pdf | Staal fase A: bronmarkeringen, profielen, partiele as 6 en andere doorsneden. | 1 |
| `a11_ovz-b.pdf` | a11_ovz-b_gezien_geen_opm(1).pdf | Staal fase B: profielen, specifieke portalen, wandregels en verbanden. | 1 |
| `c04a_gevels.pdf` | c04a_gevels_opmTS(1).pdf | Gevelaanzichten, maatkettingen, zichtbare dak-/gevelgeometrie; revisie 24-07-2025. | 1 |
| `c05a_binnen.pdf` | c05a_binnen(1).pdf | Binnenaanzichten en exacte maatkettingen; niet automatisch bewijs van huidige volledige scheidingswanden. | 1 |
| `photos allshield inside 2026_09_05_@_12-37-16.pdf` | photos allshield inside 2026_09_05_@_12-37-16.pdf | Fotobatch binnen/buiten: plafond, gevelpanelen, plint, raam-/deurdetails en staal. Geen zelfstandige metrische opname. | 1-5 |

## Aanvullende beelden

`sources/images/USER_FAILURE_SCREENSHOT.png` is Johans screenshot van de foutieve FreeCAD-weergave. Dit is werkelijk gebruikersbewijs, niet een door de generator geproduceerde preview.

`IMG-20260905-WA0015.jpg` toont het geveldetail. `plan_5200_PS_marked.png`, `kozijn_980x4000_label.png` en `plan_beams_1_2_3.png` zijn de aangeleverde planuitsneden. `c04_roof_profile_source.png` is een eerder gemaakte uitsnede van het bronprofiel, geen meting van het gebouw.

`sources/video/Untitled Project.mp4` is de verkleinde dronevideo. De opnamehoogte en perspectief vervormen zichtbare afstanden; niet als orthografische maatbron behandelen.

## Gegenereerde werkresultaten

`model/allshield_building_02.json` is de uitvoerbare invoer voor generator 02. `reference/allshield_building_reference_v0_2.json` en `reference/allshield_roof_window_source_evidence_v0_3.json` bewaren eerdere afleidingen en broninformatie. De v0.3 is aanvullend bewijs, geen zelfstandig compleet bouwrecept.

`reference/allshield_base_topview_v0_2.dxf` en de preview zijn afgeleide controles, niet de originele architectuur. `reference/Allshield_FreeCAD_Rebuild_01.zip` is alleen bedoeld voor regressie/foutreproductie. V3 is bewust niet opgenomen.

De oorspronkelijke `model/LEESMIJ_02.txt` en `model/VALIDATIE_02.json` beschrijven eerder uitgevoerde niet-native controles. Die documenten zijn ongewijzigd bewaard en gelden niet als bewijs van een geslaagde native run.

## Nog lokaal nodig

Het werkelijke problematische `.FCStd` uit Johans screenshot is NIET meegeleverd; alleen de screenshot is beschikbaar. Plaats een kopie in `user_inputs/` voor exacte foutreproductie. De generator kan zonder dat bestand alvast native getest worden.

De FreeCAD-installatie, lokale versiegegevens en lokale runtime-logs zijn eveneens niet in de ZIP opgenomen. FreeCAD-binaries, Python/OCCT-runtime en afhankelijkheden komen uit Johans eigen installatie, niet uit dit pakket.

## Bronverwerking

De bestanden in `sources/text/` bevatten alleen native PDF-tekst, per fysieke PDF-pagina gemarkeerd. Een lege of korte extractie betekent niet dat de PDF leeg is. Foto's, maat-hulplijnen, staalgeometrie en sommige teksten kunnen alleen in het paginabeeld/vectorpaden zichtbaar zijn. Geen tekst is met OCR bijgemaakt. Gebruik de bron-PDF voor iedere geometrische interpretatie.

De tooldocumentatie staat onderaan `02_TESTPLAN.md` en is duidelijk gescheiden van de projectbronnen.
