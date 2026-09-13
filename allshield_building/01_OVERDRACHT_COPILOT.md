# Technische overdracht - Allshield Ter Aar / FreeCAD

## 1. Opdracht en uitgangspunt

Johan Degraeve wil een bruikbaar, licht en brongebaseerd 3D-model van het Allshield-gebouw in Ter Aar, Nederland, voor installatiecoordinatie. Het model wordt volledig opnieuw gegenereerd vanuit JSON. Een oudere FreeCAD V3 mag hoogstens visueel vergeleken worden; geen oude scripts, aannames, standaardmaten of openingsposities overnemen.

**Magnetron/microwave: niet genereren, niet importeren, geen footprint en geen placeholder maken.** Johan plaatst zijn eigen machine. Andere bestaande apparatuur mag als expliciet onderbouwde referentie worden behouden; ontbrekende machinehoogtes niet verzinnen.

De gebruiker heeft herhaaldelijk gevraagd alleen te deduceren wat werkelijk uit de bronnen volgt. Een plausibel ogend model met niet-onderbouwde maten is niet acceptabel. Daarentegen is een zichtbaar als onvolledig gemarkeerd bronmodel wel een tussenstap, niet het eindresultaat.

## 2. Huidige bestanden en werkelijke status

Startpunt is `model/allshield_build.py`, byte-identiek aan `model/Allshield_Build.FCMacro`. De bijbehorende invoer is `model/allshield_building_02.json`, schema `allshield.freecad.build.v1`, eenheden mm. Deze bestanden zijn ongewijzigd uit het laatst geleverde pakket 02 gekopieerd. De handoff voegt documentatie en tests toe, geen nieuwe gebouwgeometrie.

De generator maakt een NIEUW document. Entry point voor tests:

```python
module.build_from_json(str(json_path), overrides={
    'detail_mode': 'WORK',
    'autosave': False,
    'validate_shapes': True,
})
```

Importeer de Python-module, roep deze functie aan met een expliciet pad en vermijd de GUI-bestandsdialoog van `main()` tijdens batchtests. De schakelwaarden bovenaan de macro worden door `main()` als overrides doorgegeven; import + `build_from_json` gebruikt de JSON-instellingen met de opgegeven overrides.

Er zijn 449 componentrecords, waarvan 366 geometrie bevatten over alle varianten. De standaard WORK-selectie bevat 141 geometrie-instanties; PANELS 358. Dat zijn GEEN 141 of 358 volledig uitgewerkte bouwonderdelen/solids: er zitten ook vlakken, lijnen en referenties bij. Het totale aantal documentobjecten is hoger door groepen en prototypes. Zie `verification/static_check.json` voor de hier opnieuw getelde aantallen.

Standaard: vloer en gevels aan; dak en plafond uit; staalbroncontouren en overige apparatuur-footprints aan; raster uit; extra volledige gevelaanzichten niet gegenereerd. WORK/PANELS selecteren verschillende gevelrepresentaties. Het dakprofiel wordt nog niet overal als corrugatie aangemaakt.

## 3. Eerst oplossen: native foutreproductie en display/linkcontrole

De gebruiker leverde `sources/images/USER_FAILURE_SCREENSHOT.png`: een losse, lange plint links buiten de hal, een wand die ver naar beneden doorloopt en veel staalcontouren.

De codegebaseerde diagnose voor pakket 01 was: `Component_Library` stond onder `Building`; een zichtbaarheidsschakeling kon de lokale bronvormen zelf tonen naast hun geplaatste App::Link-instanties. In de eerdere geometriecontrole liepen sommige lokale prototypes tot Y=-54660 mm of Z ongeveer -8380 mm. Dat past bij het beeld, maar is **niet native bevestigd in het echte document van Johan**. De groene vloer kan selectie/preselectie zijn; behandel die kleur niet als bewijs van een geometriefout.

Wijzigingen in pakket 02:

- `Component_Library` staat buiten de schakelbare `Building`-boom.
- Prototypes staan op de plaats van hun eerste echte exemplaar in plaats van los op lokale nul.
- Links gebruiken `LinkTransform=False` en expliciete `LinkPlacement`.
- `audit_world_geometry()` vergelijkt de effectieve `Part.getShape(obj)`-begrenzing met de JSON na recompute.
- De controlegrens van 0,01 mm is een NUMERIEKE consistentietolerantie, niet de nauwkeurigheid van het gebouw of de PDF.

Valideer deze maatregelen in native FreeCAD; neem niet aan dat een App::Link in iedere runtime precies zo werkt als een testdouble. Controleer ook opgeslagen/heropende bestanden en GUI-zichtbaarheid. Verplaats losse vormen nooit handmatig om de screenshot visueel te herstellen. Controleer eerst of het bronvormen, instanties, dubbele transformaties of verkeerd gelokaliseerde broncontouren zijn.

`model/Allshield_Herstel_Weergave_02.FCMacro` is uitsluitend voor bibliotheekorganisatie/zichtbaarheid. Voor foutonderzoek eerst een kopie van het ongewijzigde probleemdocument bewaren. De herstelmacro is geen vervanging voor het uitwerken van de staal-solids.

## 4. Bronnen en beslisregels

De leesbare bronindex staat in `03_BRONNENREGISTER.md`. Alle onderstaande bestanden zitten in het pakket.

Gebruik de tekeningen per functie: C4a voor gevels en dakniveaus, C5a voor maatkettingen, A3/A11 voor de staalonderdelen, de architectuurset voor expliciete laagopbouw en details, de layouttekeningen voor apparatuur/actuele inrichting, foto's en video voor zichtbare uitvoering en onderlinge ligging.

Een nieuwere bestandsdatum alleen bewijst niet dat ieder detail een oudere bron vervangt. Bronnen die hetzelfde oorspronkelijke CAD-model delen zijn ook niet automatisch onafhankelijke metingen. Bewaar conflicten met bron, pagina, objectidentiteit en revisie; verzoen ze niet stilzwijgend.

De gegenereerde JSON-bestanden zijn traceerbare werkresultaten, geen extra primaire bron. De eerdere claims '100% exact' betekenen hier niet dat PDF-geometrie automatisch een as-built opname is. Behoud onderscheid tussen geschreven maat, uitgelezen vectorgeometrie, visuele bevestiging en nog onopgeloste waarde.

PDF-teksten kunnen ongeordend zijn. Voor geometrie: bekijk de oorspronkelijke pagina/uitsnede en gebruik zo nodig native vectorpaden met PyMuPDF. `sources/text/` is alleen een index. Geen OCR tenzij echt noodzakelijk. Kalibreer elk document/aanzicht afzonderlijk. Gebruik nooit een screenshot-pixelschaal op een andere afbeelding of een geveltransformatie op een schuin dakvlak.

Let op: referentie v0.2 gebruikt de gecombineerde planschaal 71,537710643 mm/PDF-punt; het aanvullende v0.3-bewijs gebruikt voor een lokale controle uitsluitend de 5200-maat (71,507149515 mm/PDF-punt). Niet ongezien mengen of bestaande coordinaten met de andere factor herschalen. Bewaar kalibratie, gebruikte maat-hulplijnen en residualen.

## 5. Vastgelegde coordinaten en namen

Client-oorsprong: **staal-/gridkruising 21/A = (0,0,0)**; dit is NIET het binnenvlak van een gevel. +X loopt van as 21 naar as 1, +Y van A naar M, +Z omhoog. Conversie uit het oorspronkelijke tekeninggrid: `X_client = 65160 - X_source`, `Y_client = Y_source`, `Z_client = Z_source`.

De referentiemaat tussen as 1 en 21 is 65160 mm, tussen A en M 54160 mm. Gevelvlakken mogen daardoor niet automatisch op die assen worden geplaatst; hun offsets komen uit het betreffende detail.

Gemeenschappelijke X-stations vanaf de oorsprong:

| As | Client X (mm) |
|---|---:|
| 21 | 0 |
| 20 | 5150 |
| 18 | 10250 |
| 16 | 15350 |
| 14 | 20450 |
| 12 | 25550 |
| 11 | 30650 |
| 10 | 35750 |
| 9 | 40850 |
| 8 | 45950 |
| 7 | 51100 |
| 5 | 53750 |
| 3 | 59100 |
| 1 | 65160 |

Lokale afwijkingen: gevel A heeft as 2 op X=61050; in de M-maatketting staan as 4 op X=58940 en as 6 op X=52250. Een aanwezige maat-/referentieas bewijst op zichzelf GEEN volledige kolom/portaal over de hele gebouwbreedte. Verifieer het daadwerkelijke lid en de reikwijdte in A3/A11; plaats niet alle doorsneden dubbel op alle assen.

As 3 draagt in de vastgelegde broninterpretatie het hoofdspan A-E, as 4 F-M. As 6 is lokale/partiele constructie, niet een volledig hoofdportaal. Niet ineens een 5000-mm of 5100-mm raster over de hele hal genereren.

Dakreferenties: A-E=27830, E-F=160, F-M=26170 mm. Noklijnen Y=13915 en Y=41075 mm. C4a vermeldt dakreferentieniveaus +9550 en +10300 mm. A3/A11 vermelden staalniveaus +9165 en +9910; de staaltekeningen bevatten ook lokale nokverhogingen. Deze niveaus niet blind als hartlijnen van ieder staalprofiel gebruiken: toewijzing aan bovenkant/hart/onderkant moet uit de aanzichten volgen.

Stabiele, betekenisvolle IDs en echte parent/child-relaties behouden:

```text
Building
  Reference_System
  Structure
    Steel_Source_Sections
    Unresolved_Steel
  Envelope
    Floor
    Roof
      Ceiling
        Sandwich_Ceiling
      Roof_Cladding
        SteelDeck
    Facades
      Facade_A / Facade_M / Facade_1 / Facade_21
  Internal_Buildings
  Existing_Equipment
  Existing_Services
Component_Library  [afzonderlijk; verborgen; geen gebouwinstantie]
```

Voeg echte staalcomponenten later logisch toe, bijvoorbeeld `Structure/Portal_Frames/Frame_Axis_08/Beam_A_to_Ridge1`; behoud bronmarkering en profielnaam. Een onderdeel niet twee keer fysiek genereren omdat het in meerdere aanzichten voorkomt.

## 6. Paneel- en raamgegevens: latere bronvondsten zijn belangrijk

De architectuurset pagina 6 en detailblad pagina 8 noemt **100-mm PIRplus 1060WB-LL gevelpanelen**. De uitvoer-JSON bevat een nominale werkbreedte van 1060 mm. De vroegere gesprekshypothese 'alle gevelpanelen zijn 1000 mm' is dus geen geldige default. Controleer de expliciete paneelspecificatie en de getekende voegen; asafstand delen door een vermeend paneelaantal is onvoldoende.

Dezelfde bron noemt **dak-sandwichpanelen 132/164 mm**. Plafondonderzijde en geprofileerde dakbovenzijde zijn representaties van dezelfde sandwich-dakopbouw, niet twee los gestapelde isolatiedaken. De gevraagde boomstructuur scheidt weergave en onderdelen; deze scheiding mag geen dubbeltelling of fictieve tussenruimte veroorzaken.

De profielanalyse v0.3 beschrijft een nominale 32/1000D-vorm: 1000-mm werkbreedte, zes perioden van 166,666... mm, profielhoogte 32 mm, vlakke kroon 30 mm en vlak dal 86 mm. Dat is een bron-/catalogusmatch, geen bewijs van fabrikant, staaldikte, buigradius of positie van de eerste rib. Die laatste gegevens blijven expliciet onopgelost.

Architectuur pagina 6/8: plint 250 mm totale elementdikte, bovenzijde +1000 mm; vloer 200 mm met bovenkant Z=0. De ondergrond en funderingen zijn niet volledig gemodelleerd. De huidige onderste vloergrens Z=-200 mm is dus op zichzelf geen 'onder het gebouw gezakt' object.

Voor ramen: houd het lagere kozijn met bovenlicht, het hoge raam, de ruwe opening, buitenmaat kozijn en dagmaat uit elkaar. Het label 980x4000 betreft niet automatisch ieder hoge raam. In het aanvullende bewijs staan ook ongeveer 1073 mm voor de PS-opening en ongeveer 1100 mm voor een getekende buitencontour. De architectuurdetails geven voor hoge ramen niveaus +6500/+8000, maar de fysieke koppeling van type en locatie blijft te verantwoorden. Geen maten laten 'winnen' alleen omdat ze bij een eerder model passen.

## 7. Geometrie die nog ontbreekt

Neem de negen `unresolved`-records uit de actuele bouw-JSON als werkvoorraad:

| Onderwerp | Werk |
|---|---|
| STEEL_SOLIDS | Individuele profielen, dikten, orientaties, hoogtereferenties en aansluitingen koppelen; bronlijnen vervangen door echte solids. |
| STEEL_INTERMEDIATE_FRAMES | Niet-afzonderlijk getoonde portalen onderbouwen; niet kopieren puur op een regelmatig grid. |
| SECONDARY_STEEL | Gordingen, wandregels en windverbanden inclusief werkelijke trajecten catalogiseren. |
| ROOF_PHASE / CEILING_JOINTS | Beginpositie van ribben en paneelnaden aan het datum koppelen. |
| WINDOWS | Type-/locatiekoppeling, kozijn-, dag- en ruwe maten, diepte en zetwerk scheiden. |
| ARCHITECTURE_REVISION | Laagopbouw uit maart 2025 naast latere plannen en foto's houden. |
| INTERNAL_BLOCK | De echte huidige binnenbouw reconstrueren; geen oude volledige brandwanden over de hal invoegen. |
| ROOF_FLASHINGS | Nok, goot, rand en dalgoot uit brongegevens uitwerken. |

Een contour-samenstelling extruderen met een willekeurige dikte is geen legitieme manier om staal-solids te krijgen. Een negatieve test moet ook aantonen dat ontbrekende gegevens niet automatisch door defaults worden ingevuld.

## 8. Prestaties en implementatiegrenzen

Behoud een lichte WORK-stand. Gebruik herbruikbare vormen met App::Link waar geometrie EN materiaalrol gelijk zijn. Plaats ieder lid met eigen JSON-coordinaten. Een array is alleen passend waar herhaling van afstand en vorm aantoonbaar is. Maak ribben niet stuk voor stuk als duizenden features; detailzones zijn later beter dan overal de maximale detaillering.

Houd de bronvormen buiten `Building`, standaard onzichtbaar en niet selecteerbaar. Fuse niet het hele gebouw tot een grote boolean-solid. Geen dependencies tussen delen die bij elke kleine wijziging alles laten herberekenen. Onopgeloste delen als metadata/groepen behouden, niet als verzonnen geometrie.

De bestaande modes genereren dak- en plafondreferenties ook wanneer ze niet zichtbaar zijn. 'Verborgen' is niet hetzelfde als 'niet aangemaakt'. Maak een later expliciet generate/detail-beleid waar dat echt rekentijd bespaart, zonder de betekenis van de coordinaten te veranderen.

## 9. Gewenst eindresultaat van de overdracht

Eerst: native WORK en PANELS met behoud van bron-JSON, correcte wereldplaatsingen, verborgen bibliotheek, save/reopen-tests en echte FreeCAD-screenshots. Daarna: geverifieerde uitbreiding van de ontbrekende geometrie, met wijzigingslijst per bron.

Lever de gebruikte FreeCAD/Python/OCCT-versies, commando's, volledige logs, testsamenvattingen, screenshots, buildduur/bestandsgrootte en een nieuw `.FCStd` terug. Houd implementatiefouten, bronconflicten en modelonvolledigheid gescheiden. Een PASS van de meegeleverde tests betekent consistentie met deze JSON, niet dat de bron-JSON fysiek volledig en juist is.
