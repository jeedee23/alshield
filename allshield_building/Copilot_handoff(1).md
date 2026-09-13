# ALLSHIELD - Geconsolideerde Copilot-handoff

**Bestand:** `Copilot_handoff.md`  
**Documentrevisie:** MERGED-03, 2026-09-06  
**Project:** Allshield Ter Aar - gebouw, upperdeck, luchtbehandeling en installatiecoördinatie  
**Opdrachtgever / inhoudelijke beslisser:** Johan Degraeve  
**Toepassing:** GitHub Copilot; JSON-gestuurde FreeCAD-opbouw; samenhang met Fusion 360, P&ID en controls engineering.

> **Lees dit document eerst.** Het voegt de bestaande gebouw-/FreeCAD-overdracht, het complete AHU-overzicht en Johans laatste architectuurcorrectie samen. Het is een nieuwe leidende overdracht, geen nieuwe release van de generator, geen nieuwe uitvoer-JSON en geen bewijs van geslaagde native FreeCAD-tests.

De operationele informatie is hieronder samengevoegd. Oude, tegengestelde concepten zijn niet als tweede actuele instructie blijven staan. Waar de bronnen geen uitsluitsel geven, staat het punt expliciet open. De oorspronkelijke bronnen blijven bewaard voor herkomstcontrole.

## Leeswijzer

- **A - Opdracht, bronnenprioriteit en huidige softwarebasis.**
- **B - Vastgelegde gebouwgeometrie, modelstructuur en prestaties.**
- **C - Volledig AHU-overzicht, 28 onderdelen overeenkomstig de aangeleverde bron, met de nieuwe mengregeling verwerkt.**
- **D - Open punten, bronconflicten en verboden automatische invullingen.**
- **E - Uitvoervolgorde, native tests, aanvullende AHU-controles en oplevering.**
- **F - Bestanden, bronnenregister, hashes en korte startopdracht voor Copilot.**

---

# A. Opdracht en beslisregels

## A.1 De laatste architectuurcorrectie is leidend

**De twee louvre dampers zijn gekoppelde, analoog modulerende regelelementen voor de proceslucht-inlaattemperatuur. Het zijn geen twee losse aan/uit-kleppen en geen drie discrete seizoensstanden.** [U1]

Na het roll-up filter splitst dezelfde proces-toevoerlucht in twee parallelle paden:

1. **Cooling path:** door de chiller coil(s).
2. **Heat-recovery path:** door de electric heat resistor en daarna de procesluchtzijde van **recuperator 1**.

Beide paden komen samen aan het begin van de **main top duct**, net voor/boven de inlet fans van de microwave machine. De temperatuursensor **na deze samenvoeging** levert de regelwaarde. [U1]

> **The measured temperature and its hysteresis in the main top duct after the two air paths have recombined is the source of truth for inlet-air control.** [U1, letterlijk overgenomen]

De hallucht is uit deze proceslucht-inlaatregeling verwijderd. **Hallucht gebruikt uitsluitend recuperator 2:** hallucht aanzuigen, via de eigen zijde van recuperator 2 opwarmen, met een fan terug naar de hal. Dit is geen derde toevoerpad naar de machine en geen halluchtbijmenging in de main top duct. Proceslucht, hallucht en chiller-condensorlucht blijven afzonderlijke luchtcircuits. [U1; A1, secties 1 en 9]

Deze correctie verandert de AHU-topologie en regelbeschrijving. Ze geeft **geen toestemming om de gebouwcoördinaten te veranderen** en legt nog geen exacte posities van kleppen, sensoren of kanaalaansluitingen vast.

## A.2 Afbakening van het CAD-werk

Doel is een licht, controleerbaar en brongebaseerd model van het bestaande gebouw en de te coördineren installaties. Het gebouw wordt volledig opnieuw gegenereerd vanuit JSON. De oude V3 mag Johan zelf visueel vergelijken; geen V3-code, standaardmaten, aannames of geïnterpreteerde openingsposities inlezen. [H1, sectie 1]

**Magnetron/microwave niet genereren of automatisch importeren: geen volume, geen footprint, geen placeholder. Johan plaatst zijn eigen machine.** De machine mag in een functioneel lucht-/waterstroomschema worden benoemd als externe installatiegrens, maar dat is geen CAD-object. Aansluitingen op een gebruikersimport worden pas geometrisch vastgelegd wanneer daarvoor een echte referentie bestaat. Laat eigen machine-imports ongemoeid. [H1; U0]

Andere apparatuur mag alleen met onderbouwde geometrie worden toegevoegd. Een bekende, als voorlopig aangeduide leveranciers-envelop kan als herkenbare referentie dienen; een onbekende hoogte, dikte of positie wordt niet verzonnen om een compleet ogend model te maken. De dummy-regel uit het AHU-overzicht is ondergeschikt aan deze grens; zie C.25 en D.

Het eindresultaat is geen verzameling fraaie broncontouren. Voor relevante botsingscontrole zijn daadwerkelijk uitgewerkte solids, correcte plaatsingen en broncontrole nodig. Tot die tijd moet de onvolledigheid zichtbaar en toetsbaar blijven.

## A.3 Herkomst en voorrang per gegeven

| Code | Bron | Gebruik |
|---|---|---|
| **U1** | Johans laatste bericht bij deze merge: continue mengregeling, twee parallelle paden, regeling op temperatuur na mengen, hallucht uitsluitend via recuperator 2 | Leidende functionele correctie op het AHU-overzicht |
| **U0** | Eerdere expliciete projectafspraken in deze conversatie | Geen V3-hergebruik; geen magnetrongeometrie; vaste datum; logische children; geen gokwerk |
| **A1** | `ALLSHIELD_AHU_COMPLETE_OVERVIEW(1).md`, secties 1-28 | AHU-architectuur, componenten, richtwaarden, leveranciersconcepten en werkafbakening, behalve expliciet door U1 vervangen passages |
| **H1** | `Allshield_Overdracht_Copilot.md`; tevens `01_OVERDRACHT_COPILOT.md` in de laatste ZIP | Gebouwbasis, bronregels, beperkingen en implementatieafspraken |
| **H2** | `Allshield_GitHub_Copilot_Overdracht.zip`: testplan, bronnenregister, model, tests en projectinstructies | Laatste werkelijk geleverde pakketstructuur en testinterface |
| **H0** | Oudere `COPILOT_HANDOFF.md`, `SOURCES.md` en `00_START_HIER.md` uit `Allshield_Copilot_Handoff.zip` | Aanvullende overdrachtsdetails; oudere `app/`- en testpaden niet mengen met H2 |
| **G** | Oorspronkelijke bouw-/staal-/layouttekeningen en werkelijke beelden in H2 | Primaire geometrische controlebronnen; bladen/revisies blijven belangrijker dan een afgeleid JSON-resultaat |

Een latere tekst vervangt alleen wat hij daadwerkelijk corrigeert. U1 wijzigt bijvoorbeeld niet stilzwijgend alle kanaaldiameters, het volledige hydraulische schema of de volgorde van de warme uitlaatlucht door de twee recuperators.

Een nieuwere bestandsdatum bewijst op zichzelf geen inhoudelijke revisie van elk detail. Twee tekeningen uit hetzelfde CAD-model zijn geen twee onafhankelijke opmetingen. Schrijf bronverschillen weg met objectidentiteit, blad, revisie en betekenis; geen stilzwijgende verzoening.

**Deze merge bevat geen nieuw extern onderzoek, nieuwe leveranciersbevestiging, herberekening van ontwerpdebieten of nieuwe native CAD-test.** Productgegevens en technische documentatielinks zijn overgenomen uit de aangeleverde bronnen. Onbevestigde waarden houden hun oorspronkelijke status.

## A.4 Bewijsstatus en onbekende waarden

Maak per gegeven onderscheid tussen:

| Status | Betekenis |
|---|---|
| `CONFIRMED_USER` | Expliciet vastgelegde functionele keuze of projectgrens van Johan |
| `SOURCE_DIMENSION` | Letterlijke maat uit een benoemde tekening, inclusief wat zij dimensioneert |
| `VECTOR_MEASUREMENT` | Herleidbare geometrische uitlezing uit een afzonderlijk gekalibreerde bron |
| `VISUAL_CONFIRMED` | Bestaan, oriëntatie of zichtbare relatie bevestigd door foto's/video; geen automatisch exacte maat |
| `DESIGN_TARGET` | Ontwerp-/bedrijfsrichtwaarde, geen gegarandeerd gerealiseerd resultaat |
| `SUPPLIER_CONCEPT` | Voorkeursproduct of voorlopige leveranciers-envelop |
| `PENDING` / `CONFLICT` | Nog onopgelost of bronnen die niet zonder extra bewijs samenpassen |
| `EXCLUDED` | Bewust buiten het generatiewerk, in het bijzonder de magnetron |

Dit is een semantisch register voor de uitbreiding, **geen opdracht om zonder migratie de bestaande schema-enumeraties te hernoemen**. Behoud compatibiliteit met `allshield.freecad.build.v1` en documenteer schemawijzigingen.

Onbekende metrische waarden blijven `null` of krijgen een equivalent expliciet onbekend veld. Geen nominale maat of patroonstart toekennen alleen omdat een vergelijkbaar product gebruikelijk is. Een geschreven maat is exact als bronvermelding; een PDF-vector of screenshot is niet automatisch een as-built opname.

## A.5 Huidige generator: wat werkelijk bestaat

Gebruik de **laatste ZIP H2** als workspacebasis. De canonieke paden zijn `model/`, `tests/`, `reference/`, `sources/` en `user_inputs/`. De oudere overdracht H0 gebruikte `app/` en andere testnamen. De onderstaande commando's horen bij H2, niet bij een willekeurige combinatie van beide pakketten.

| Bestand in H2 | Betekenis |
|---|---|
| `model/allshield_build.py` | Actuele generator 02 |
| `model/Allshield_Build.FCMacro` | Byte-identiek aan dezelfde Python-generator |
| `model/allshield_building_02.json` | Huidige uitvoerbare invoer; schema `allshield.freecad.build.v1`; mm |
| `model/Allshield_Herstel_Weergave_02.FCMacro` | Afgebakende bibliotheek-/zichtbaarheidsreparatie op een bestaand document |
| `model/LEESMIJ_02.txt` en `model/VALIDATIE_02.json` | Beschrijving en eerdere niet-native validatiegegevens |

Test-entrypoint, zonder dialoog:

```python
model = module.build_from_json(str(json_path), overrides={
    "detail_mode": "WORK",
    "autosave": False,
    "validate_shapes": True,
})
```

De generator maakt een **nieuw document**. Importeer de module zonder `main()` tijdens batchtests: `main()` gebruikt de interactieve route en macro-overrides.

De oorspronkelijke baseline telt 449 componentrecords en 366 records met geometrie over alle varianten. De oude statische overdracht rapporteert:

| Mode | Geometrie-instanties | Prototypes | Staalbronsecties |
|---|---:|---:|---:|
| `WORK` | 141 | 109 | 14 |
| `PANELS` | 358 | 304 | 14 |

Dit zijn baseline-aantallen, geen aantallen volledig uitgewerkte solids en geen onveranderlijke eis voor de uitbreiding. Groepen/prototypes maken het documentobjectaantal hoger. De beschreven 12 bestaande equipment-instanties zijn footprints, geen nieuwe gedetailleerde machines. Nieuwe AHU-objecten vragen een verklaarde nieuwe baseline, niet kunstmatig behoud van deze aantallen. [H0, sectie 2; H1, sectie 2]

Standaard: `WORK`; vloer en gevels zichtbaar; dak en plafond verborgen; staalbroncontouren en beschikbare niet-magnetron-footprints zichtbaar; raster uit; extra volledige gevelaanzichten niet aangemaakt. Verborgen dak-/plafondobjecten zijn in de huidige implementatie niet hetzelfde als niet gegenereerde objecten.

**De AHU-topologie, gekoppelde louvre-regeling en alle bijbehorende nieuwe tests in deze handoff zijn nog niet in generator 02 geïmplementeerd.** De bestaande tests certificeren die uitbreiding dus niet.

## A.6 Bekende weergavefout en afgebakende reparatie

Het gebruikersbeeld toont losse lange plintgeometrie links, een naar beneden doorlopende wand en veel staalcontouren. De groene vloer kan selectie/preselectie zijn; de kleur bewijst geen geometriefout.

Codegebaseerde diagnose voor 01: `Component_Library` stond onder `Building`; zichtbaarheid van die groep kon lokale bronvormen naast de geplaatste links tonen. Een lokale plintbron liep tot Y=-54660 mm en een wandbron tot Z ongeveer -8380 mm. Dit past bij de screenshot, maar is **niet native bevestigd in Johans oorspronkelijke FCStd**. Dat bestand is nog niet aangeleverd. [H1, sectie 3]

Pakket 02 bevat het volgende herstelvoorstel:

- `Component_Library` buiten `Building`, standaard verborgen en niet selecteerbaar.
- Prototypes op de plaats van hun eerste echte exemplaar.
- `App::Link`-instanties met `LinkTransform=False` en expliciete `LinkPlacement`.
- `audit_world_geometry()` na recompute: effectieve `Part.getShape(instance)`-begrenzing vergelijken met de JSON.
- Afwijking groter dan 0,01 mm geeft een fout; geen stilzwijgende autosave.

Die 0,01 mm is uitsluitend een **numerieke omzettings-/plaatsingstolerantie**. Zij is geen gebouwopmeetnauwkeurigheid, leverancierstolerantie of montagegarantie. Vergroot haar niet om een fout te verbergen.

Verplaats los ogende onderdelen niet handmatig. Controleer bronvorm versus instantie, dubbele transformaties, verkeerd gelokaliseerde contouren en opgeslagen zichtbaarheid. De herstelmacro verandert alleen bibliotheekorganisatie/zichtbaarheid en mag geen gebruikersgeometrie, objectaantallen of plaatsingen wijzigen. Het herstel maakt de ontbrekende staal-solids niet af.

---

# B. Gebouw, JSON en CAD-structuur

## B.1 Vaste coördinatenconventie

```text
Eenheden: mm
Oorsprong (0,0,0): staal-/gridkruising 21/A
+X: van as 21 naar as 1
+Y: van as A naar as M
+Z: omhoog
Z=0: afgewerkt vloerniveau

X_client = 65160 - X_source
Y_client = Y_source
Z_client = Z_source
```

De oorsprong is **niet** de binnen- of buitenzijde van de gevel. Hoofdreferentie 1-21 = 65160 mm; A-M = 54160 mm. Plaats gevelvlakken met de brongebonden offsets uit het betreffende detail, niet met een universele V3-offset. [H1, sectie 5]

### Langsrichting - stations afzonderlijk behouden

| As | Client X (mm) | Referentie in gevelreeksen |
|---|---:|---|
| 21 | 0 | A en M |
| 20 | 5150 | A en M |
| 18 | 10250 | A en M |
| 16 | 15350 | A en M |
| 14 | 20450 | A en M |
| 12 | 25550 | A en M |
| 11 | 30650 | A en M |
| 10 | 35750 | A en M |
| 9 | 40850 | A en M |
| 8 | 45950 | A en M |
| 7 | 51100 | A en M |
| 6 | 52250 | Lokaal in M-maatketting |
| 5 | 53750 | A en M |
| 4 | 58940 | Lokaal in M-maatketting |
| 3 | 59100 | A en M |
| 2 | 61050 | Lokaal in A-maatketting |
| 1 | 65160 | A en M |

Deze lijst bewijst geen volledige kolom of portaal op ieder assenkruispunt. Gevel A en M blijven afzonderlijke reeksen. As 3 hoort bij hoofdspan A-E; as 4 bij F-M. As 6 is lokale/partiële staalconstructie, geen hoofdportaal over beide dakvelden. Geen overal 5000 of 5100 mm aannemen. [H1/H0; referentie-JSON v0.2]

### Dwarsrichting - referentiecatalogus

| As | Client Y (mm) | As | Client Y (mm) |
|---|---:|---|---:|
| A | 0 | G | 29290 |
| B | 13250 | H | 33290 |
| C | 18130 | J | 37240 |
| D | 22980 | K | 38590 |
| E | 27830 | L | 38750 |
| F | 27990 | M | 54160 |

Dit is de vastgelegde v0.2-referentiecatalogus uit de maatkettingen, niet een nieuwe extractie tijdens deze merge. Lokale uitbouwassen niet uit V3 aanvullen.

## B.2 Dakreferenties en staalniveaus

| Referentie | Vastgelegd gegeven | Herkomst / betekenis |
|---|---:|---|
| A-E | 27830 mm | Maatketting |
| E-F | 160 mm | Afzonderlijke scheiding/dalzone behouden; geen automatische wand tot vloer |
| F-M | 26170 mm | Maatketting |
| Nok 1 | Y=13915 mm | Midden van A-E |
| Nok 2 | Y=41075 mm | Midden van F-M |
| Dak-/gevelreferentie goot | Z=9550 mm | C4a |
| Dak-/gevelreferentie nok | Z=10300 mm | C4a |
| Staalreferentie goot | Z=9165 mm | A3/A11 |
| Staalreferentie nok | Z=9910 mm | A3/A11 |

De staaltekeningen bevatten lokale opmerkingen over nokverhogingen. Een hoogtelijn is niet zonder interpretatie de hartlijn, bovenkant of onderkant van ieder profiel. Koppel lid, flenszijde, referentievlak en lokale afwijking voordat er een solid ontstaat.

## B.3 Paneelopbouw, vloer en plint

De bouwkundige set, vooral fysieke pagina's 6-8, noemt:

- **Gevel:** 100 mm dikke PIRplus sandwichpanelen `1060WB-LL`. De uitvoer-JSON bevat 1060 mm als nominale werkbreedte bij die bron. De eerdere hypothese dat alle gevelpanelen 1000 mm breed zijn vervalt als default.
- **Dak:** geprofileerde PIRplus sandwichpanelen **132/164 mm**. Plafondonderzijde en geprofileerde dakbovenzijde zijn zijden/representaties van dezelfde sandwich-dakopbouw; geen twee gestapelde isolatiedaken en geen verzonnen tussenruimte.
- **Plint:** 250 mm totale elementdikte, bovenzijde +1000 mm. De oorspronkelijke architectuur beschrijft prefab betonelementen met 100 mm PIR-isolatiekern. Niet als 250 mm massief beton plus nog eens dezelfde kern tellen.
- **Vloer:** 200 mm beton met bovenkant Z=0. Een vloeronderkant Z=-200 mm is op zichzelf correct, geen weergavefout. In de architectuur is ook 130 mm EPS100 vloerisolatie vermeld; funderingen/ondergrond zijn niet volledig in de generator uitgewerkt.

Deze waarden zijn **ontwerpspecificaties uit maart 2025**. Hun relatie tot latere plannen en de werkelijk gebouwde toestand blijft afzonderlijk te controleren. De bestaande PANELS-stand gebruikt getekende gevelverdelingen; dat bewijst niet automatisch het fysieke voegbegin. [H1, sectie 6; G, architectuur p6-p8]

Het gevraagde `Roof > Ceiling > Sandwich_Ceiling` blijft bestaan voor logische bediening. De boomstructuur mag geen dubbeltelling in hoeveelheden, doorsneden of botsingsgeometrie veroorzaken.

## B.4 Nominaal dakprofiel en raam-/deurtypen

De aanvullende profielregistratie v0.3 beschrijft de bron-/catalogusmatch **32/1000D**:

| Eigenschap | Brongebonden nominale waarde |
|---|---:|
| Werkbreedte | 1000 mm |
| Perioden per werkbreedte | 6 |
| Kroonafstand | 166,666... mm |
| Profielhoogte | 32 mm |
| Vlakke kroon | 30 mm |
| Vlak dal | 86 mm |

De plaatdikte, exacte buigradii, geleverde fabrikant en eerste ribpositie ten opzichte van het gebouwdatum zijn niet bewezen. De huidige generator heeft nog geen volledig geprofileerd dak. Gebruik een marktmatch niet als bewijs voor die ontbrekende gegevens.

Houd bij ramen/deuren afzonderlijk bij: laag kozijn/deur met bovenlicht, hoog raam, ruwe opening, kozijn-buitenmaat, dagmaat, kozijndiepte en zetwerk. Het label **980 x 4000 mm** is niet automatisch het hoge raam. Het aanvullende bewijs bevat ongeveer **1073 mm** voor een andere PS-opening en ongeveer **1100 mm** voor een getekende buitencontour in C4a. Architectuurdetails geven voor hoge ramen **+6500 tot +8000 mm**, maar bepalen daarmee nog niet iedere dagmaat of profielsectie. [H1/H0; v0.3]

## B.5 PDF-kalibratie: geen stille herschaling

De basisreferentie v0.2 gebruikt een gecombineerde planschaal van **71,537710643 mm/PDF-punt**. Het lokale aanvullende v0.3-bewijs gebruikt alleen de 5200-mm referentie en **71,507149515 mm/PDF-punt**. Bewaar beide met hun functie. Herbereken bestaande wereldcoördinaten niet ongezien met de andere factor.

Geschreven maatkettingen, vectoren en foto's zijn verschillende bewijslagen. Controleer maat-hulplijnen, niet alleen de buitenste uiteinden van een maatstreep. Kalibreer elk blad/aanzicht apart. Geen schaaloverdracht tussen screenshots of tussen gevelvlak en hellend dakvlak. De dronehoogte van ongeveer 10 m maakt de opname niet orthografisch.

Gebruik PDF-tekst als index; bekijk voor geometrie de echte pagina/vectoren. Geen OCR tenzij de informatie anders niet beschikbaar is. De data in afgeleide JSON's/DXF zijn werkresultaten, geen extra onafhankelijke primaire bronnen.

## B.6 Logische componentboom

De bestaande `Building`-IDs blijven stabiel. Onderstaande uitbreiding met `Air_Handling` is een **voorgestelde logische indeling**, geen verklaring dat deze AHU-componenten al in JSON 02 bestaan. Engelse namen zijn software-identiteiten; definitieve instrumenttags blijven open.

```text
Building
  Reference_System
  Structure
    Steel_Source_Sections
    Unresolved_Steel
    Portal_Frames
      Frame_Axis_08
        Beam_A_to_Ridge1
    Columns
    Roof_Purlins
    Wall_Girts
    Roof_Bracing
    Wall_Bracing
  Envelope
    Floor
    Roof
      Ceiling
        Sandwich_Ceiling
      Roof_Cladding
        SteelDeck
      Roof_Flashings
    Facades
      Facade_A / Facade_M / Facade_1 / Facade_21
        Sandwich_Wall
        Plinth
        Openings
          Window_<stable_id>
            Window_Frame
            Glazing
            Exterior_Flashings
              Head_Flashing
              Jamb_Flashing_Left
              Jamb_Flashing_Right
              Sill_Flashing
            Interior_Reveal
  Internal_Buildings
  Existing_Equipment
  Existing_Services

Air_Handling                         [nieuwe samenstelling naast Building]
  Upperdeck
    Structure
    Supports
    Service_Zones
  Process_Air_Supply
    Wall_Inlet
    Duct_Route_D900
    Roll_Up_Filter
    Post_Filter_TRH
    Supply_Split
    Cooling_Path
      Process_Cooling_Coil
      Louvre_Cooling
        Damper_Body
        Belimo_Actuator
    Heat_Recovery_Path
      Electric_Heat_Resistor
      Louvre_Heat_Recovery
        Damper_Body
        Belimo_Actuator
    Main_Top_Duct
      Mixing_Zone
      Mixed_Air_Temperature_Sensor
      Supply_Distribution
    Supply_Balancing_Fan_Reference
  Process_Air_Extraction
    Extraction_Risers
      Riser_01 / Riser_02 / Riser_03 / Riser_04
    Collector
    Hot_Side_Routing_Pending
    Humid_Roof_Exhaust
  Heat_Recovery
    Recuperator_1_Process
      Process_Supply_Side
      Process_Exhaust_Side
      Condensate_Tray
    Recuperator_2_Hall
      Hall_Air_Side
      Process_Exhaust_Side
      Condensate_Tray
  Hall_Air_Recovery
    Hall_Air_Inlet
    Hall_Fan
    High_Level_Hall_Discharge
  Chilled_Water
    Chiller_1_Process_Cooling
    Chiller_2_Waterloads
    Buffer_Tank_BT_1
    Expansion_Vessel_EV_1
    Hydraulic_Connections_Pending
    Waterload_Interface_References
  Chiller_Condenser_Ventilation
    Outside_Air_Roof_Connection
    Condenser_Air_Ducting
    Roof_Fan
    Hot_Air_Roof_Connection
  Condensate_Drainage
  Controls_References
    Process_Inlet_Temperature_Loop
    Paired_Louvre_Modulation
  Building_Interfaces
    Wall_Penetration
    Roof_Penetrations
      Humid_Process_Exhaust
      Chiller_Ventilation_Connection_1
      Chiller_Ventilation_Connection_2

Component_Library                    [afzonderlijk, verborgen, geen instantie]
```

De boom toont eigenaarschap, niet de exacte volgorde van alle kanaalonderdelen. Het exacte klepmontagepunt binnen elk pad is nog niet gespecificeerd. Recuperators, chillers, sensoren en kleppen worden fysiek **eenmaal** gegenereerd; hun rol in andere subsystemen wordt via IDs/verwijzingen vastgelegd. Een schema-, stroom- of servicereferentie maakt geen tweede solid.

Een geïmporteerde machine is eigendom van Johan en staat buiten de generator. Een AHU-aansluitpunt is geen stilzwijgende machineplaceholder. Bestaande apparatus-footprints niet nogmaals als identieke AHU-machine dupliceren: eerst identiteit koppelen.

## B.7 Prestaties en representaties

Behoud `WORK` als lichte standaard en `PANELS` voor bewezen paneelverdelingen. Een toekomstige detailzone rond een raam of dakdoorvoer mag meer geometrie bevatten, zonder de hoofdcoördinaten te veranderen.

Identieke vormen en materiaalrollen kunnen een bronvorm delen met `App::Link`. Ieder exemplaar houdt zijn eigen expliciete plaatsing. Hergebruik verplicht geen regelmatig staalgrid. Alleen waar vorm en pitch bewezen zijn is een array passend. Geen afzonderlijk CAD-object voor iedere rib en geen hele gebouwfusie als een enkele grote boolean-solid.

Bronvormen buiten `Building`, standaard verborgen/niet selecteerbaar en uitgesloten van een export van fysieke instanties. Scheid referentielijnen, skins, omhullende modellen en echte solids. Geen willekeurige contour-extrusie om ontbrekend staal af te vinken.

Meet native build- en recomputetijd, FCStd-grootte, aantallen en zo mogelijk procesgeheugen. Oude CadQuery-/mocktijden zijn geen FreeCAD-benchmark. Rapporteer prestaties in de gebruikte machine/versie; geen gegarandeerde FPS verzinnen.

Voor nieuwe zwaardere details: maak `generate` en `visible` afzonderlijk. Niet benodigde detailgeometrie werkelijk niet aanmaken bespaart ander werk dan haar pas na opbouw verbergen. De huidige baseline heeft dat onderscheid nog niet overal.

---

# C. Luchtbehandeling - compleet en bijgewerkt overzicht

De nummering C.1-C.28 volgt de 28 secties van `ALLSHIELD_AHU_COMPLETE_OVERVIEW(1).md`. Alle ontwerpwaarden hieronder behouden hun oorspronkelijke benadering, voorbehoud of leveranciersstatus. De door U1 gewijzigde passages zijn als actuele architectuur herschreven, niet als extra alternatief toegevoegd.

## C.1 Overall system concept

Het systeem hoort bij de MEAM microwave dryer en heeft vier functionele delen:

1. Procesluchttoevoer naar de machine.
2. Procesluchtafzuiging en warmteterugwinning.
3. Hallucht-warmteterugwinning via uitsluitend recuperator 2.
4. Chiller-condensorventilatie en gekoeldwatercircuits.

De apparatuur wordt zoveel mogelijk vooraf geassembleerd op een upperdeck met ongeveer **40-ft containerafmetingen**, boven de machine. Prefabricage bij MEAM/TM Technics maximaliseren en montagetijd op Allshield minimaliseren. De genoemde 40 ft is hier een platformreferentie, geen volledig bemaat platformontwerp.

Proceslucht, hallucht en chiller-condensorlucht blijven afzonderlijk. Er zijn **twee recuperators** en **twee chillers**: CH-1 voor procesluchtkoeling en CH-2 voor microwave-waterloadkoeling. Procesluchtdebiet als ontwerpbedrijfsbereik ongeveer **10000-15000 m³/h**.

Seizoensbedrijf wordt beschreven als operating regions van dezelfde continue mengregeling, niet als drie vaste klepstanden. [A1, sectie 1; U1]

## C.2 Procesluchttoevoer - buitenmuur naar machine

### C.2.1 Debiet en hoofddiameter

| Bedrijfspunt | Bronwaarde |
|---|---:|
| Minimum | circa 10000 m³/h |
| Typisch | circa 10800-12000 m³/h |
| Maximum | circa 15000 m³/h |
| Hoofdkanaal buitenluchttoevoer | diameter 900 mm |

Het eerdere **diameter 1200-concept voor de buitenluchttoevoer is vervallen**. Dit geldt niet automatisch voor andere circuits of dakdoorvoeren.

Het AHU-brondocument bevat ook de volgende snelheidstabel:

| Debiet | In A1 opgegeven snelheid bij diameter 900 |
|---|---:|
| 10000 m³/h | 4,37 m/s |
| 12000 m³/h | 5,24 m/s |
| 15000 m³/h | 6,55 m/s |

**Status van deze snelheden:** letterlijk overgenomen bronwaarden, niet herberekend/gevalideerd in deze merge. Gebruik deze tabel niet ongecontroleerd als rekenbasis voor drukverlies of Pitot-selectie. Zet een consistentiecontrole van debiet, effectieve doorsnede, diameter en snelheid op de werkvoorraad; vervang bronwaarden niet zonder een afzonderlijk gemarkeerde berekening. [A1, sectie 2.1; open punt D-10]

### C.2.2 Genummerde route uit de bron

| Nr. | Onderdeel | Bronmaat / status |
|---:|---|---|
| 1 | Outside-air wall grille / wall penetration | Bestaande raampositie |
| 2 | Rechte inlet section | L circa 1000 mm |
| 3 | Rond kanaal | diameter 900, L=4200 mm |
| 4 | 90-gradenbocht | diameter 900, R=1,5D |
| 5 | Rond kanaal | diameter 900, L=4300 mm |
| 6 | Aansluit-/flenssectie | Nog geometrisch uit te werken |
| 7 | 90-gradenbocht | diameter 900, R=1,5D |
| 8 | Vertical measuring section | diameter 900, L=1000 mm |
| 9 | Overgang | diameter 900 naar 2500 x 1000 mm |
| 10 | Aansluiting upperdeck-inlet / AHU | Nog definitief te koppelen |

De muurdoorvoer komt ter plaatse van een bestaande raamopening. De bronlengtes en nummering zijn geen complete lijst wereldcoördinaten. Definitieve route en raamidentiteit koppelen aan de gebouwreferenties. De term measuring section bij nr. 8 verplaatst de Pitot niet automatisch: C.4 noemt een voorkeurslocatie voor de tweede bocht. [A1, sectie 2]

## C.3 Filtratie en parallelle luchtconditionering

### C.3.1 Actuele topologie - vervangt de oude seriële beschrijving

```text
Outside air
  -> wall inlet / diameter-900 duct route
  -> roll-up filter
  -> post-filter T/RH measurement
  -> split van dezelfde schone proces-toevoerlucht
       |
       +-- Cooling path:
       |     chiller coil(s) + eigen modulerende louvre damper
       |
       +-- Heat-recovery path:
             electric heat resistor -> recuperator 1, process-supply side
             + eigen modulerende louvre damper
       |
       +-- recombine / mixing zone aan het begin van main top duct
             -> mixed-air temperature sensor
             -> inlet fans / toevoerinterfaces van de gebruikersmachine
```

De plustekens bij de kleppen betekenen dat zij tot het pad behoren; **de precieze plaats voor/na een coil of recuperator is nog niet vastgelegd**. Het door Johan genoemde procesvolgordegegeven in het warme toevoerpad is wel: resistor, vervolgens recuperator. Leg geen halluchtleiding naar deze split of mengzone.

Het oorspronkelijke enkelvoudige schema `filter -> cooling coil -> balancing/supply fan -> machine` beschrijft de gecorrigeerde installatie niet meer volledig. De separate balancing/supply-fanfunctie uit A1 blijft geregistreerd; haar definitieve plaats en verhouding tot de machine-inletfans staan open. Teken niet op basis van twee verschillende omschrijvingen twee nieuwe, identieke supply-fans. [A1, sectie 3; U1]

### C.3.2 Roll-up filter

Het filter verwijdert stof uit de inkomende proceslucht en beschermt downstream coil en machine. Het moet servicebaar blijven. Differentiaaldrukmeting over het filter is vereist. De **T/RH-sensor staat na het filter**, niet in het vuile buitenluchtkanaal. Dit is een andere meetlocatie en functie dan de hoofdtemperatuursensor na mengen. [A1, secties 3.1-3.2]

### C.3.3 Cooling-coil concept

Voorkeursconcept: **AirTS-KQ-II** gekoeldwatercoil-unit. Genoemde leveranciers-envelop:

| Gegeven | Waarde / status |
|---|---|
| Totale omhulling | circa 1100 x 1086 x 1100 mm |
| Frontopening | circa 860 x 860 mm |
| Actief coil-/lamellenfront | vermoedelijk circa 800 x 800 mm |
| Getoonde wateraansluitingen | circa diameter 104 mm |
| Standaard ingebouwde fan | Wordt voor Allshield verwijderd; coil inline gebruiken |
| Gewenste totale koelcapaciteit | circa 30 kW |
| Gekoeld water | circa 7/12 °C |
| Waterdebiet | circa 5,2 m³/h |
| Gewenste hydraulische aansluiting | rond DN40 |
| Luchtzijdig drukverlies | Zo laag mogelijk; exacte waarde open |

Het oude concept had twee parallelle coils. **Een enkele coilmodule heeft de voorkeur indien technisch mogelijk.** Daarom staat in de actuele route coil(s), niet al een definitief aantal. Verwar twee conditioneringstakken niet met twee verplicht gekozen cooling-coils.

De getekende diameter-104-aansluiting, de voorkeur DN40 en het vermoedelijke actieve front zijn afzonderlijke brongegevens; geen definitieve aansluiting kiezen of 104 automatisch als typefout schrappen. [A1, sectie 3.3]

## C.4 Procesluchtdebietmeting

Een Pitot-gebaseerde meting is voorzien in de lange rechte diameter-900-kanaalsectie. **Voorkeur: voor de tweede bocht**, waar de bron beter ontwikkeld stromingsbeeld verwacht. De uiteindelijke instrumentpositie en rechte meetlengten blijven te koppelen aan de definitieve route. [A1, sectie 4]

### Onderhoudsconcept

De Pitot is verwijderbaar, maar fysiek alleen bereikbaar met een hoogwerker/schaarlift. Twee pneumatische leidingen lopen naar operator-/platformniveau:

- **P+ TOTAL**
- **P- STATIC**

Voorkeur voor industriële pneumatische slang met Legris/Parker-type insteekkoppelingen. Voorlopig beoogde differentiaaldrukzender: **0-50 Pa of 0-100 Pa**, vanwege de in de bron verwachte lage dynamische druk. Definitieve range koppelen aan een gecontroleerde berekening; de ranges zijn nog alternatieven.

### Maandelijkse controle zoals in A1 voorgesteld

1. Fan stoppen.
2. Beide Pitot-leidingen van de DP-transmitter loskoppelen.
3. Een grote handspuit op iedere leiding aansluiten.
4. De spuit enkele keren langzaam trekken en duwen.
5. Controleren of lucht in beide richtingen vrij beweegt.
6. Bij sterke weerstand of terugveren door onderdruk: mogelijke gedeeltelijke blokkering.
7. Alleen dan de Pitot fysiek met hoogwerker benaderen.
8. Leidingen terug aansluiten en bij stilstaande installatie ongeveer 0 Pa controleren.

Twee grote handspuiten kunnen bij het servicepunt blijven. Dit is de **overgenomen onderhoudsprocedure uit het projectoverzicht**, geen in deze merge gevalideerde fabrikantprocedure. Eindinstructie, toegang en geschiktheid bij definitieve componentkeuze vastleggen. [A1, secties 4.1-4.2]

## C.5 Machine-inlaatdistributie

Geconditioneerde proceslucht gaat via de main inlet header / main top duct naar **ongeveer drie inlaatpunten** boven op de machine. Totaal ontwerpbereik blijft circa 10000-15000 m³/h. De exacte verdeling over drie punten wordt definitief bij balancing/commissioning bepaald.

De nieuwe mengzone ligt aan het begin van deze duct, voor/boven de machine-inletfans. De hoofdtemperatuurmeting staat na mengen. De machine zelf wordt niet gegenereerd; drie functionele verbindingen zijn geen toestemming om haar footprint te tekenen. [A1, sectie 5; U1]

## C.6 Procesluchtafzuiging uit de machine

Huidig concept: **vier afzuigposities**, met vier korte stijgstukken tot ongeveer upperdeckniveau. De stromen komen samen in een compacte collector die de proceslucht-warmteterugwinning/uitlaatrouting voedt.

Doel: cavity-/enclosed-zone-druk beheersen en verhinderen dat vochtige proceslucht de hal in ontsnapt. Druksetpoint, definitieve regeling, riserdiameters, flenzen en wereldcoördinaten zijn hier niet vastgelegd. Aansluitingen blijven afhankelijk van de gebruikersmachine. [A1, sectie 6]

## C.7 Twee-recuperatorconcept

Er zijn twee fysiek afzonderlijke warmtewisselaars met verschillende functies:

| Recuperator | Koude / te verwarmen luchtzijde | Warme zijde volgens bron |
|---|---|---|
| **R1 / Recuperator 1** | Proces-toevoerlucht in het heat-recovery path | Warme vochtige machine-uitlaatlucht |
| **R2 / Recuperator 2** | Uitsluitend hallucht, retour naar de hal | Warme machine-uitlaatlucht |

Warmteoverdracht is geen rechtstreekse mengverbinding tussen beide zijden. Hallucht gaat niet door R1 als toevoerbron voor de machine en niet rechtstreeks de proceslucht-mengduct in.

**Niet opgelost:** de volgorde/verdeling van de warme procesuitlaat over R1 en R2. De bronnen bevestigen hun functies, maar leggen geen volledig serie-/parallelschema of bypassschema van die warme zijde vast. Een pijl `R1 -> R2` of `R2 -> R1` is daarom nog geen bevestigde leiding. [A1, secties 7-9; U1]

## C.8 Recuperator 1 - proceslucht

R1 is onderdeel van het procesluchtsysteem en recupereert warmte uit vochtige machine-uitlaat naar de proces-toevoerlucht. A1 beschrijft haar als doorlopend betrokken bij het machinesysteem en noemt ongeveer **10000-15000 m³/h**. In de door U1 bevestigde topologie hangt het **werkelijke toevoerluchtdebiet door de koude R1-zijde** af van de verdeling over de twee parallelle paden. De totale proceslucht mag niet automatisch in ieder regelbedrijf als volledige koude-zijde-R1-stroom worden ingevuld. [A1, sectie 8; U1]

Nominale uitlaatreferentie uit A1: circa **44 °C / 44% RH**, vochtige proceslucht; condensatie afhankelijk van bedrijfsgebied en inlaatcondities. Johans nieuwe regelvoorbeeld gebruikt ongeveer **45 °C / 44% RH aan de hot-side inlet**. Dat is een voorbeeldconditie, geen 45-graden machine-inlaatsetpoint en geen bewijs dat de koude recuperatoruitlaat die temperatuur bereikt.

Voorkeur: **Holtop cross-flow sensible plate heat exchanger, HBS-ZF1600/1600-500-10.0**. De in A1 genoemde redenen zijn groot front, lage frontalsnelheid, verwacht laag drukverlies, passieve bouw zonder bewegende delen, geschiktheid voor industriële lucht/lucht-warmteterugwinning en verwachte lagere prijs dan het Italiaanse alternatief. Die verwachting is geen nieuwe offerte- of prestatiebevestiging.

Overgenomen frontalsnelheden voor het genoemde 1600 x 1600-front:

| Debiet | Frontalsnelheid volgens A1 |
|---|---:|
| 10000 m³/h | 1,09 m/s |
| 12000 m³/h | 1,30 m/s |
| 15000 m³/h | 1,63 m/s |

Voorzie condensaatopvang, drainaansluiting en gecontroleerde afvoer naar een geschikte afvoerlocatie. Exacte kern-/kastmaten, drukverlies en aansluitingen leveranciersafhankelijk. De voorkeursmaat voor R1 is niet zonder bron een definitieve maat voor R2. [A1, sectie 8]

## C.9 Recuperator 2 - uitsluitend hallucht-warmteterugwinning

```text
Hall air -> recuperator 2, hall-air side -> hall fan / return -> hall
Warm process exhaust -> andere zijde recuperator 2 -> verdere uitlaatrouting
```

R2 verwarmt hallucht zonder de twee luchtstromen te mengen. De halluchtcirculatie is het halluchtsysteem; **geen aanvullende halluchtkeuze in de proces-inlaatmengregeling**. De warmtebron is warme procesuitlaatlucht. De precieze aanvoer daarvan staat bij C.7 nog open.

Eerder overwogen halluchtdebiet circa **10800-20000 m³/h**, eventueel hoger indien de definitieve balancing dat vereist. Halluchttemperatuurdoel circa **18 °C**, een engineering target, geen gegarandeerde gebouwtemperatuur. Uitblaas van verwarmde hallucht op hoog niveau.

In de beperkte commerciële scope is **geen uitgebreid vierpunts-halluchtdistributiesysteem** opgenomen. Voeg geen derde mengpad, geen halluchtinlaat naar de machine en geen uitgebreid halnet toe. Definitieve regeling van hallfan/R2 staat los van de bevestigde proces-inlaattemperatuurregeling en is nog niet numeriek gespecificeerd. [A1, sectie 9; U1]

## C.10 Procesuitlaat naar het dak

Na warmteterugwinning wordt de resterende vochtige proceslucht via het dak afgevoerd. Een van de drie hoofddakdoorvoeren is hiervoor bestemd.

A1 noemt als huidig doorvoerconcept **DN1000**, met anti-vogelrooster, condensaatopvang en geleiding naar een centraal drainpunt. Tijdens normal/summer regions, met minder warmteonttrekking of grotendeels doorstromen, kan de uitlaatlucht zeer vochtig zijn. In winter region verwacht de bron meer condensatie in de recuperators zelf. Deze beschrijving bepaalt geen exacte bypassrouting of condensaatberekening.

**Diameter nog als bronconflict registreren:** eerder is in het gebouwtraject DN900 voor dakdoorvoeren besproken; A1 noemt DN1000. De nieuwe mengregelcorrectie beslist deze diameterkwestie niet. Geen wereldwijd vervangen van 900 door 1000 of omgekeerd. [A1, sectie 10; U0; D-01]

## C.11 Operating regions - geen drie harde HVAC-standen

| Gebied | Actuele functionele beschrijving |
|---|---|
| **Summer region** | Cooling path dominant; coil actief wanneer nodig; mengregeling bepaalt de benodigde verhouding. |
| **Normal region** | Beide paden naar behoefte gemengd; buitenlucht blijft de procesluchtbron. |
| **Winter region** | Heat-recovery path dominant; recuperator 1 levert warmte aan proces-toevoer; resistor alleen waar nodig; recuperator 2 kan hallucht verwarmen. |

In alle gebieden blijft het procesdebiet binnen het ontwerpbereik beoogd, de uitlaatlucht via warmteterugwinning/roof exhaust lopen en de condensaatvoorziening relevant. Regionamen zijn geen discrete klepcommando's, vaste omschakeltemperaturen of toestemming om sensorfeedback te negeren. [A1, sectie 11, herzien door U1]

## C.12 Louvre dampers en continue inlaattemperatuurregeling

### C.12.1 Gekoppelde regeling

Er zijn **twee modulerende louvre dampers**, een per toevoerpad. De verhouding van hun luchtstromen bepaalt de gemengde proceslucht-inlaattemperatuur. Zij worden als **paired modulating control elements** gemodelleerd in CAD, functioneel schema en controlsreferenties.

De hoofdproceswaarde is de temperatuur in de **main top duct na samenvoeging**. Buitenluchttemperatuur, post-filter T/RH, recuperatoruitlaattemperatuur en actuatorstand zijn aanvullende inputs/diagnostics; geen van die metingen vervangt de gemeten mengtemperatuur.

Een PID stuurt de twee Belimo-actuators analoog aan:

| Regelbehoefte | Richting van de bronbevestigde actie |
|---|---|
| Meer koude lucht nodig | Cooling-path damper verder openen; recovery-path verminderen |
| Meer warme lucht nodig | Recovery-path damper verder openen; cooling-path verminderen |
| Zeer koude startup, R1 nog onvoldoende warm | Electric heat resistor tijdelijk laten bijspringen |
| Voldoende warmte uit R1 beschikbaar | Resistor afbouwen / uitschakelen |

Geen vaste percentuele complementariteitswet, flow/angle-relatie, minimumopening, PID-gain, setpoint, hysterese-omvang of fail-position is opgegeven. Programmeer zulke waarden niet als bewezen projectdata. De functionele richtingen hierboven zijn wel bevestigd. [U1]

### C.12.2 Regelvoorbeeld van Johan

- Outside air: **10 °C**.
- Recuperator hot-side inlet: ongeveer **45 °C / 44% RH**.
- Cooling-path damper bijna gesloten.
- Heat-recovery-path damper verder geopend.
- De twee toevoerstromen mengen in de main top duct; de sensor daar bepaalt de werkelijke inlaattemperatuur.

Dit is een illustratie van de regeling, geen berekende uitgangstemperatuur, geen verwarmingsvermogen en geen vaste winterstand.

### C.12.3 Regeldynamiek en hysterese

Tijdens normale stabiele productie hoeft de regeling niet agressief te blijven corrigeren. Johan noemt bij startup **bijvoorbeeld ongeveer iedere minuut** bijregelen en na thermische stabilisatie van de procescadans rustiger regelen.

Registreer ongeveer 60 s als **voorgesteld startpunt voor bijregelen**, niet als definitief vastgestelde PID-sampletijd, sensorpolling, scantijd van een PLC of beveiligingstijd. Numerieke tuning, dodeband/hysterese en overgang naar stabiel bedrijf moeten nog worden vastgelegd.

De bronformulering over gemeten temperatuur en hysterese blijft leidend. De software moet die niet herinterpreteren tot uitsluitend open-loop klepstanden of een harde buitentemperatuurschakelaar.

### C.12.4 Actuators - overgenomen productspecificatie

| Gegeven | A1-waarde / status |
|---|---|
| Geselecteerde familie/type | **Belimo SM24A-SR** |
| Voeding | 24 VAC/DC |
| Koppel | 20 Nm |
| Analoog commando | 2-10 V |
| Positieterugmelding | 2-10 V |
| Toepassingsreferentie | circa 1 m² damper, afhankelijk van constructie/wrijving |
| Projectvoorkeur minimum | 20 Nm als praktisch uitgangspunt |
| Alternatieve reserve | 40 Nm waar meer mechanische reserve vereist is |

Dit zijn uit A1 overgenomen gegevens; geen nieuwe selectie- of koppelberekening. Hou command- en feedbacksignaal apart. Twee actuatorstandsmetingen zijn diagnostics, geen tweede bron van waarheid voor T_mixed. Klepafmetingen, draairichting, montage, looptijd en krachtreserve blijven leveranciers-/engineeringcontrole.

### C.12.5 Electric heat resistor

Het element zit in het **heat-recovery path voor de proces-toevoerzijde van R1**. Het ondersteunt zeer koude startup en wordt teruggenomen wanneer R1 voldoende warmte beschikbaar heeft. Geen aparte halluchtverwarming van maken.

Vermogen, sectiematen, traploos/getrapt aansturen, vrijgavevoorwaarden en beveiligingsfuncties staan niet in de aangeleverde correctie. Houd ze open. De handoff beschrijft de functie; zij levert geen inbedrijfgestelde PLC-regeling of toestemming voor live actuator-/heateraansturing.

## C.13 Chiller 1 - procesluchtkoeling

Contractuele nummering: **CH-1 = process-air cooling chiller**.

Ontwerpgegevens uit A1: koelcapaciteit circa **30 kW**, waterdebiet circa **5,2 m³/h**, water circa **7/12 °C**. Een geïntegreerde pomp is in het leveranciersconcept aangenomen, niet definitief als pompprestatie bevestigd.

```text
CH-1 -> process-air cooling coil -> BT-1 -> CH-1
```

Dit is de overgenomen hydraulische route. Definitieve leidingen, afsluiters, servicepunten en bypassstrategie staan open. De coil ligt luchtzijdig in de cooling branch; CH-1 zit niet in het recovery-luchtpad. [A1, sectie 13]

## C.14 Chiller 2 - waterloadkoeling

Contractuele nummering: **CH-2 = microwave waterload cooling chiller**.

Waterloadbehoefte circa **80 L/min = 4,8 m³/h**. Bronconcept:

```text
CH-2 -> WL-1 -> WL-2 -> BT-1 -> CH-2
WL-1 = product-outlet waterload
WL-2 = product-inlet waterload
```

De waterloads staan in het concept **in serie**, onder voorbehoud van totaal drukverlies en capaciteit van de interne chillerpomp. Geen parallelle waterloadschakeling invoegen zonder revisie. WL-1/WL-2 blijven functionele machinegrenzen; maak daarmee geen verboden CAD-machineplaceholder.

A1 gebruikt in beide chillerlussen dezelfde tag **BT-1**. Dat legt nog niet vast of de circuits hydraulisch delen, gescheiden aansluitingen/warmtewisselaars hebben of andere arrangementen nodig zijn. **Geen gezamenlijke hydraulische knoop automatisch tekenen.** Zie C.15 en D-02. [A1, sectie 14]

## C.15 Buffervat en expansievat

| Component | Bronconcept |
|---|---|
| **BT-1** | circa 1000 L; drukgeschikt; geïsoleerd; thermische stabilisatie van gekoeld water |
| **EV-1** | circa 60 L; op de retourzijde |

Materiaalcompatibiliteit met geselecteerd water/glycol en waterbehandeling controleren. Exacte vatmaten, massa/steunpunten, aansluitingen, ontwerpdruk en de koppeling van BT-1/EV-1 aan een of beide circuits zijn nog niet gegeven.

De identieke BT-1-referentie in CH-1 en CH-2 moet expliciet opgelost worden voordat het P&ID een definitieve hydraulische verbinding krijgt. De bron zegt niet dat er twee BT-1-vaten zijn; maak ook niet zomaar een tweede vat. [A1, sectie 15 en secties 13-14]

## C.16 Koelmedium

Huidig bronconcept: gedemineraliseerd water, propyleenglycol, uiteindelijke glycolconcentratie **onder ongeveer 20 vol% tenzij vorstberekeningen anders vereisen**, en nog te bevestigen corrosie-inhibitor/waterbehandeling.

Die voorwaardelijke concentratie is geen definitief mengrecept of gegarandeerde vorstgrens. Materiaalcompatibiliteit met vat, warmtewisselaars, coil, leidingen en afdichtingen moet worden bevestigd. [A1, sectie 16]

## C.17 Chiller-condensorventilatie

De twee chillers staan binnen/op het upperdeck en hebben een **eigen buitenlucht-ventilatiecircuit**, volledig onafhankelijk van de proceslucht:

```text
Roof / outside air -> chillers / condensers -> hot condenser air -> roof exhaust
```

Huidig engineeringdebiet: circa **35000 m³/h totaal**. Concept dakfan: circa **38000 m³/h maximumklasse**, VFD-geregeld om de condensorluchtstroom te stabiliseren tegenover wind-/storminvloeden.

Eerder voorkeursreferentie: **Slingerland PMA804C**, volgens A1 circa **38200 m³/h max**, **5,5 kW**, **diameter 800 body**, VFD-bedrijf. Definitieve fanselectie afhankelijk van werkelijk kanaaldrukverlies. De bodydiameter bepaalt niet automatisch de diameter van ieder dak-/kanaalaansluitstuk.

Luchtzijdige verdeling over beide chillers en exacte dak-in/dak-uit-geometrie blijven te koppelen aan de finale 3D-opbouw. Geen condensorlucht als procesmengstroom of halluchtbron aansluiten. [A1, sectie 17]

## C.18 Dakdoorvoeren

TM Technics-scope omvat **drie hoofddakdoorvoeren**:

| Doorvoerfunctie | In A1 vastgelegd |
|---|---|
| Vochtige procesluchtuitlaat | DN1000-concept; anti-vogelrooster; condensaatopvang en centrale drain |
| Chiller ventilation connection 1 | Een van de twee buitenlucht-/condensorlucht-dakverbindingen |
| Chiller ventilation connection 2 | De andere chiller-dakverbinding |

Secties 20 en 27 van A1 noemen daarnaast **3 x DN1000**. Sectie 18 laat de exacte functie van roof-in/roof-out volgen uit de finale 3D. Bewaar dit als scope-/conceptinformatie; geen definitieve maatrelease voor ieder afzonderlijk gat.

De eerdere DN900-dakgedachte, de nu expliciete diameter-900-muurtoevoer en A1's DN1000-dakgegevens blijven gescheiden in het conflictenregister. Drie dakdoorvoeren is de huidige AHU-telling; de muurinlaat is geen vierde dakdoorvoer. Gecertificeerde dakwerker vereist volgens A1. Definitieve posities, details en constructieve compatibiliteit nog vastleggen. [A1, sectie 18; U0]

## C.19 Upperdeck-platform

Dedicated upperdeck met ongeveer 40-ft containerafmetingen, zoveel mogelijk prefab voor levering. A1 noemt als aanwezig of voorbereid:

Roll-up filter, cooling coil, balancing/supply fan, twee recuperators, bypasssecties, dampers, actuators, chillers, gekoeldwaterbuffervat, expansievat, sensoren, lokale ducting, transitions, condensaatopvang, supports en servicezones.

De electric heat resistor hoort door U1 nu expliciet bij het recovery-pad. De twee modulerende dampers moeten als gekoppelde regeleenheid herkenbaar zijn, zonder dat zij een enkel fysiek onderdeel worden.

Geen platform-/onderdeel-XYZ of draagvermogen afleiden uit alleen het begrip 40 ft. Onderbouw posities, steunpunten en onderhoud/vervangbaarheid afzonderlijk. [A1, sectie 19; U1]

## C.20 TM Technics - huidige werkafbakening

### Deel 1 - Allshield site / gebouwinterfaces

Volgens A1: drie dakdoorvoeren DN1000 als scopevermelding; anti-vogelroosters; condensaatarrangement voor vochtige uitlaat; muurinlaat op bestaande raampositie; montage/ondersteuning horizontaal buitenluchtkanaal. Gecertificeerde dakwerker, hoogwerker/schaarlift en veiligheidsplan vereist. Doorvoerdiameters blijven in detail gekoppeld aan D-01; deze merge wijzigt geen contract. [A1, sectie 20.1]

### Deel 2 - voorbereiding aan MEAM-machine

Machinezijdige flenzen installeren, platforminterfaces voorbereiden, outlet connection ducts fabriceren en tijdelijk monteren, passing controleren, vervolgens die kanaalstukken demonteren en samen met platform transporteren.

Dit is de mechanische werkscope, **niet** een opdracht aan de gebouwgenerator om de magnetron te maken. Aansluitgeometrie blijft afhankelijk van de echte machine. [A1, sectie 20.2; U0]

### Deel 3 - upperdeck-prefabricage bij TM Technics

Monteren/voorbereiden van ducts, transitions, bypasses, dampers, mechanische sensorposities, chillers, cooling coil/dummy, recuperators/dummies, condensaat, supports en aansluitsecties.

**Elektrische installatie is uitgesloten.** Alleen mechanische sensorplaatsing blijft in TM Technics-scope. Dummygebruik in CAD moet de bronregels uit C.25 volgen. U1's heater/mengregelwijziging bepaalt op zichzelf nog niet een uitbreiding van de contractuele werkafbakening; eventuele toewijzing apart bevestigen. [A1, sectie 20.3; U1]

### Deel 4 - finale installatie bij Allshield

Raming uit de bron: **2 personen, ongeveer 1-3 werkdagen**, omdat het meeste vooraf gemonteerd en fit-getest is. Dit is een verwachting, geen gegarandeerde planning of nieuwe offerte. [A1, sectie 20.4]

## C.21 Sensoren en instrumentatie

### Luchtzijde

| Meetfunctie | Actuele rol / locatie |
|---|---|
| **Temperatuur na mengen in main top duct** | Hoofdregelwaarde voor proces-inlaattemperatuur; toegevoegd/verduidelijkt door U1 |
| T/RH na roll-up filter | Werkelijke gefilterde toevoerlucht; niet in vuile inlaat en niet vervangend voor T_mixed |
| DP over roll-up filter | Filterbewaking |
| Pitot + DP | Buitenluchtdebiet, voorkeurslocatie lange rechte sectie voor tweede bocht |
| Druk in main process-air inlet | Afzonderlijke drukmeetfunctie |
| Cavity / enclosed-zone pressure | Druk in machine-/afgeschermde zone |
| T/RH of T procesuitlaat | Procesdiagnostiek / warmteterugwinning |
| Belimo analoge terugmelding | Afzonderlijk per damper; positiefeedback |

Buitenluchttemperatuur en recuperatoruitlaattemperatuur mogen aanvullende inputs/diagnostics zijn zoals U1 beschrijft. Hun exacte hardware-uitvoering/tag is niet nieuw vastgelegd. De hoofdregelwaarde blijft na mengen.

### Waterzijde

Flow indication/meting waar nodig, temperatuurmetingen, druk waar nodig en bufferniveau-indicatie indien nodig. Definitieve tags blijven onderdeel van finale P&ID-engineering. Nieuwe logische software-IDs zijn geen automatisch goedgekeurde instrumenttags. [A1, sectie 21; U1]

## C.22 Elektrische scope

Elektrische installatie door TM Technics is uit de scope gehaald. MEAM / controls engineering behandelt elektrische aansluitingen en regeling; TM Technics plaatst sensoren uitsluitend mechanisch.

Belimo-modulatie zoals in A1: 24 VAC/DC, 2-10 V command en 2-10 V feedback. De twee damperactuators en de T_mixed-regelfunctie moeten in dezelfde functionele procesregelkring te herkennen zijn. De documenten leggen nog geen I/O-adressen, bekabeling, PLC-programma of definitieve heater-elektriciteit vast. [A1, sectie 22; U1]

## C.23 Condensaatfilosofie

Condensaat kan volgens de bron optreden bij:

1. **Proceslucht-cooling coil:** tray en drain voorzien.
2. **Recuperator 1:** bij warmteterugwinning.
3. **Recuperator 2:** vooral tijdens winterbedrijf.
4. **Vochtige dakuitlaat:** opvang en afvoer naar een gedefinieerd centraal punt.

Gebouwzijdige afvoerpunten met Allshield coördineren. Routes moeten volgens de modelleringsregels naar een gedefinieerd drainpunt aflopen. Eindroutes, exacte aansluitmaten en niveaus zijn niet volledig vastgelegd; geen fictief Z-verloop invullen. [A1, sectie 23 en sectie 25]

## C.24 Modelprioriteiten voor FreeCAD / Fusion / P&ID

De oorspronkelijke modelprioriteiten blijven behouden, met de nieuwe functionele split toegevoegd:

1. Gebouwstaal: echte relevante 3D-solids, niet alleen contouren.
2. Definitieve machine-XY als **gebruikersimport / externe referentie**, niet opnieuw genereren.
3. Upperdeck.
4. Outside-air wall penetration in bestaande raampositie.
5. Diameter-900-buitenluchtroute.
6. Bochten R=1,5D.
7. Overgang diameter 900 naar 2500 x 1000.
8. Roll-up filter, post-filter T/RH en filtersensorinterfaces.
9. Cooling-coil-sectie in de cooling branch.
10. Proceslucht-fanfunctie en definitieve relatie tot de machine-inletfans.
11. Split, twee gekoppelde modulerende louvres, resistor + R1-pad, mengzone, T_mixed en main-top-duct-distributie.
12. Vier korte afzuigstijgstukken.
13. Compacte collector.
14. R1 voor proceslucht.
15. R2 uitsluitend voor hallucht.
16. Nog te specificeren bypass-/dampersecties aan overige routes; niet als extra bevestigde toevoerkeuze tekenen.
17. CH-1 en CH-2.
18. BT-1 en EV-1 plus te bevestigen hydraulische verbindingen.
19. Onafhankelijke chiller-condensorventilatie.
20. Drie dakdoorvoerfuncties; DN1000-concept versus eerdere DN900-keuze expliciet oplossen.
21. Condensaatinterfaces.
22. Onderhoudsruimte, servicezones, actuator- en sensorbereikbaarheid.

De lijst is een inhoudelijke modelprioriteit. De software-uitvoering begint eerst met de ongewijzigde native baseline en foutreproductie uit E. [A1, sectie 24; U1; H1]

## C.25 Belangrijke modelleringsregels

Geen onbevestigde maat verzinnen. Dummy-/placeholdergeometrie uit A1 mag uitsluitend een **bekende, expliciet geclassificeerde leveranciers-envelop** voorstellen. Als de relevante omhullende maat ontbreekt: metadata/lege groep, geen willekeurige kubus. Voor de magnetron geldt altijd de striktere uitsluiting: ook geen onderbouwde generator-footprint of dummy; Johan plaatst de machine zelf.

Houd de drie luchtcircuits fysiek afzonderlijk. Toon onderhoudstoegang; routeer niet door constructief staal. Dakdoorvoeren moeten bij dakconstructie en lokale versterking passen. Muuraansluiting wordt door de bestaande raam-/gevelstructuur begrensd.

Plaats apparatuur zodanig dat montage en latere vervanging mogelijk blijven, maar vul ontbrekende vrije-ruimte-eisen niet met gegokte getallen in. Condensaat naar een gedefinieerd punt laten aflopen. Actuators en sensoren bereikbaar houden zonder demontage van grote kanaaldelen. De exacte clearances zijn nog onderdeel van detailed engineering. [A1, sectie 25; U0]

## C.26 Nog af te ronden AHU-engineering

De oorspronkelijke open punten blijven actief:

- Exact drukverlies Holtop-recuperators en cooling-coil luchtzijde.
- Definitieve proceslucht-fan duty en verdeling over circa drie machine-inlaten.
- Definitief recuperator-bypassarrangement en halluchtdebiet door R2.
- Werkelijk drukverlies chiller-condensorventilatie.
- Definitieve instrumenttags, hydraulische kleppen, condensaatroutes en supportposities.
- Exacte dakdoorvoerposities, serviceclearances en leveranciersmaten voor alle apparatuur.

Door de merge expliciet toegevoegde open punten: warme-zijde-R1/R2-routing; twee klepmontagepunten; numerieke PID/hysterese en actuatorverdeling; heatervermogen/omvang/vrijgaven; fanidentiteit/-plaats; BT-1-aansluiting tussen beide watercircuits; inconsistenties rond dakdiameters en bronrekenwaarden. De nieuwe functionele mengregeling zelf staat **niet** meer als vrije architectuurkeuze open. [A1, sectie 26; U1]

## C.27 Kernwaardenregister

| Parameter | Huidige bronwaarde | Status |
|---|---|---|
| Proceslucht totaal | 10000-15000 m³/h | Ontwerpbedrijfsbereik |
| Typisch procesluchtdebiet | 10800-12000 m³/h | Benadering |
| Outside-air main duct | diameter 900 mm | Huidig toevoerconcept; oude 1200 vervallen |
| Bochtstraal toevoer | R=1,5D | Routegegeven |
| Inlaatovergang | diameter 900 -> 2500 x 1000 mm | Conceptmaat |
| Proceskoeling | circa 30 kW | Doel |
| Gekoeldwater | circa 7/12 °C; 5,2 m³/h | Ontwerp |
| Waterloads | circa 80 L/min / 4,8 m³/h | Ontwerp |
| BT-1 | circa 1000 L | Concept; hydraulische koppeling open |
| EV-1 | circa 60 L, retour | Concept; circuittoewijzing open |
| Recuperators | 2 | Functies R1 proces / R2 hal bevestigd |
| Voorkeur R1 | HBS-ZF1600/1600-500-10.0 | Leveranciersconcept |
| Procesuitlaat R1-referentie | circa 44 °C / 44% RH | A1 nominale engineeringreferentie |
| Laatste regelvoorbeeld | buiten 10 °C; hot side circa 45 °C / 44% RH | U1 voorbeeld, geen setpoint |
| Hallucht | circa 10800-20000 m³/h, mogelijk hoger | Voorlopige range |
| Haldoel | circa 18 °C | Geen gegarandeerde temperatuur |
| Louvre-actuators | 2 gekoppeld modulerend | U1 leidende architectuur |
| Actuatortype | Belimo SM24A-SR | A1 selectie |
| Koppel | 20 Nm als praktisch uitgangspunt; 40 Nm mogelijk | Mechanisch te bevestigen |
| Voeding/command/feedback | 24 VAC/DC; 2-10 V; 2-10 V | Overgenomen specificatie |
| Regelsensor | Temperatuur main top duct na mengen | Hoofdregelwaarde bevestigd |
| Inlaattemperatuursetpoint | Niet opgegeven | `PENDING` |
| PID / hysterese | Functie bevestigd, getallen open | `PENDING` tuning |
| Startup-bijregelen | Bijvoorbeeld circa 60 s | Voorstel, geen vastgelegde sampletijd |
| Heatervermogen | Niet opgegeven | `PENDING` |
| Dakdoorvoeren | 3; A1 noemt 3 x DN1000 | Diameterconflict met eerdere DN900 nog open |
| Condensorlucht totaal | circa 35000 m³/h | Doel |
| Dakfanreferentie | PMA804C; circa 38200 m³/h max; 5,5 kW; body diameter 800 | Selectie bij werkelijk drukverlies bevestigen |
| Upperdeck | circa 40 ft | Volledige detailmaten niet hier vastgelegd |

## C.28 Geconsolideerde systeemsummary

```text
PROCESS SUPPLY
Outside air -> diameter-900 wall/duct route -> roll-up filter -> post-filter T/RH
             -> SPLIT
                 Cooling path: coil(s) + modulating louvre
                 Recovery path: electric heat resistor -> R1 supply side
                                + modulating louvre
             -> MIX at start of main top duct
             -> TEMPERATURE MEASUREMENT AFTER MIXING
             -> inlet fans / approximately 3 supply interfaces
             -> Johan's microwave machine [external; not generated]

PROCESS EXHAUST
Machine -> 4 short risers -> collector
        -> heat recovery via R1 and R2 hot sides
           [order, split and bypasses not yet established]
        -> humid roof exhaust

HALL AIR - ONLY R2
Hall -> R2 hall-air side -> fan / high-level discharge -> hall
No hall-air connection to process-supply mixing.

CHILLED WATER - SOURCE CONCEPTS, BT-1 CONNECTION UNRESOLVED
CH-1 -> process cooling coil -> BT-1 -> CH-1
CH-2 -> WL-1 product outlet -> WL-2 product inlet -> BT-1 -> CH-2

CONDENSER AIR - SEPARATE
Roof/outside air -> chiller condensers -> hot-air roof discharge
```

Continue mengregeling, afzonderlijke luchtcircuits, twee warmteterugwinfuncties, twee chillerfuncties, onderhoudbare meting, condensaatopvang en maximale upperdeck-prefabricage vormen de actuele gecombineerde basis. Alleen een expliciete latere revisie mag een specifieke functie, maat of route veranderen. [A1, sectie 28, bijgewerkt door U1]

---

# D. Open punten en bronconflicten

## D.1 Besluiten die niet opnieuw als vrije keuze openstaan

| Onderwerp | Leidende keuze |
|---|---|
| Proces-inlaatconditionering | Twee parallelle toevoerpaden na het filter, daarna opnieuw mengen |
| Louvre dampers | Twee gekoppelde, analoog modulerende elementen |
| Temperatuurregeling | Gemeten temperatuur na mengen in de main top duct is de hoofdregelwaarde |
| Hallucht | Uitsluitend via R2 terug naar de hal; geen proceslucht-inlaatbron |
| Elektrische startupverwarming | Resistor in recovery path voor de proceszijde van R1 |
| Seizoensbeschrijving | Operating regions; geen drie vaste HVAC-klepstanden |
| Chillers | CH-1 procesluchtkoeling; CH-2 waterloads |
| Magnetron-CAD | Niet genereren/importeren als onderdeel van dit script; geen footprint/placeholder |
| Gebouwdatum | 21/A; bestaande coördinaten niet voor een AHU-aanpassing verschuiven |
| Oud V3 | Geen code- of geometriebron |

## D.2 Nog niet automatisch oplosbare punten

| ID | Open punt / bronverschil | Wat Copilot moet bewaren of opvragen, niet verzinnen |
|---|---|---|
| **D-01** | Eerdere dakkeuze DN900 versus A1 DN1000 en scope 3 x DN1000 | Per doorvoerfunctie status, gekozen diameter en reden/bron vastleggen. Diameter-900-muurtoevoer afzonderlijk houden. Niet alle 900/1000 als dezelfde maat behandelen. |
| **D-02** | BT-1 staat in beide hydraulische conceptlussen | Beide bronroutes bewaren. Niet automatisch de circuits samenvoegen, een extra vat tekenen of een scheidingswisselaar toevoegen. Koppeling, retour en EV-1-toewijzing bevestigen. |
| **D-03** | Warme procesuitlaat over R1 en R2 | Volgorde, parallel/serie, debietverdeling en bypasses zijn niet gespecificeerd. Wel functies en afzonderlijke koude zijden behouden. |
| **D-04** | Definitieve cooling-coil en aantal | Een module heeft voorkeur; oorspronkelijk twee parallel. Actieve 800 x 800-maat is vermoedelijk, envelope is circa. Diameter 104 uit tekening niet met DN40-voorkeur overschrijven. |
| **D-05** | Supply/balancing fan versus machine-inletfans | Niet dezelfde functie dubbel modelleren. Exacte identiteit, positie, duty en verdeling over drie inlaten bevestigen. |
| **D-06** | Regelspecificatie | Setpoint, hysterese/dodeband, PID-waarden, analoge verdelingswet, minima/maxima, actuatorrichting en feedbackafhandeling open. Circa 60 s is alleen het startupvoorstel. |
| **D-07** | Electric heat resistor | Vermogen, omhulling, aansluitingen, regelvorm, vrijgave-/beveiligingsontwerp en werkscopetoewijzing open. Geen gegokte kast of vermogen. |
| **D-08** | Pitot-locatie | Lange rechte sectie voor tweede bocht heeft bronvoorkeur; nr. 8 heet ook measuring section. Definitieve plek en transmitterrange expliciet koppelen. |
| **D-09** | Condensorventilatie | 35000 m³/h is doel; fanreferentie/duty, drukverlies, verdeling en twee dakverbindingen nog definitief uitwerken. |
| **D-10** | Bronrekenwaarden | De A1-snelheidstabel bij diameter 900 is niet opnieuw gevalideerd. Controleer debiet/doorsnede/snelheid en overige afgeleide prestatiegegevens in een apart rekenregister voordat zij selectiegegevens worden. |
| **D-11** | R1-bedrijfsdebiet en temperaturen | Totale proceslucht niet automatisch aan iedere parallelle tak toekennen; 44-graden nominale uitlaat en 45-graden hot-side voorbeeld zijn geen inlaatsetpoint. |
| **D-12** | Roof/windows/source revisions | 32/1000-match, 132/164-opbouw en 1060WB-LL-specificatie met hun bronstatus behouden. 980/1073/1100 meten verschillende object-/maatbegrippen totdat koppeling bewezen is. |
| **D-13** | Equipment placement en interfaces | Exacte upperdeck-, coil-, damper-, recuperator-, chiller-, vat- en kanaal-XYZ ontbreken deels. Een AHU-flowchart is geen positioneringsplan. |
| **D-14** | Onderhoud en condensaat | Clearances, bereikbaarheid, drainpunt en echte afschotten niet met niet-bevestigde getallen invullen. |
| **D-15** | Buiten ontwerp / feitelijke uitvoering | Bouwkundige bronnen met VOORLOPIG, TER CONTROLE of niet-voor-uitvoering-waarschuwing blijven zo geclassificeerd. Geen fictieve as-built certificatie. |
| **D-16** | Dummies versus geen aannames | Bekende voorlopige envelop herkenbaar labelen; onbekende maat metadata-only. De magnetron blijft in alle gevallen uitgesloten. |

Dit is een inhoudelijk register. Punten als D-01, D-02 en D-03 blokkeren de **definitieve uitvoering** van hun deel, niet het uitvoeren van de bestaande softwaretests of het modelleren van reeds onderbouwde onderdelen.

## D.3 Bestaande negen unresolved-records blijven behouden

De uitvoer-JSON 02 bevat de volgende IDs. Verwijder ze niet alleen omdat de nieuwe handoff uitgebreider is:

| Bestaand ID | Resterend werk |
|---|---|
| `STEEL_SOLIDS` | Individuele profielen, diepten, oriëntaties, verbindingsoffsets en matching tussen aanzichten; bronlijnen zijn geen collision solids. |
| `STEEL_INTERMEDIATE_FRAMES` | Tussenportalen die niet afzonderlijk in A3/A11 getoond zijn onderbouwen; niet puur uit het grid kopiëren. |
| `SECONDARY_STEEL` | Volledige gordingen-, wandregel- en windverbandcatalogus met werkelijke routes. |
| `ROOF_PHASE` | Eerste rib/plaatpositie ten opzichte van het datum verifiëren. |
| `CEILING_JOINTS` | Globale start/voegindeling van de dakonderzijde toewijzen. |
| `WINDOWS` | Type-/locatiekoppeling, dag-/kozijn-/ruwe maten, diepte en zetwerk scheiden. |
| `ARCHITECTURE_REVISION` | Ontwerplaagopbouw van maart 2025 toetsen aan latere bronnen; niet als gecertificeerd as-built behandelen. |
| `INTERNAL_BLOCK` | Actuele binnenbouw en hoogtes; geen obsolete volledige scheidingswanden over de hal invoegen. |
| `ROOF_FLASHINGS` | Nok, dalgoot, goot en dakrand uit brongegevens uitwerken. |

**Een geslaagde native softwaretest lost geen van deze geometrische bronvragen vanzelf op.**

---

# E. Implementatie-, test- en opleverplan

## E.1 Eerst bewaren en lokaliseren

Werk lokaal in de uitgepakte H2-map met een Copilot-sessie die toegang heeft tot bestanden en de FreeCAD-installatie. Gebruik dezelfde lokale installatie als bij de foutreproductie waar mogelijk; noteer het echte console-/GUI-pad en de volledige FreeCAD-, Python- en OCCT-versie. Een cloud-/remote omgeving heeft niet automatisch toegang tot Johans lokale installatie. Dit is overgenomen testadvies uit H2, niet een nieuwe softwarecompatibiliteitsgarantie.

Bewaar oorspronkelijke sources, reference en baselinebestanden. Maak een ontwikkelrevisie/kopie voordat er code of data verandert. Geen publieke upload, remote push of publicatie zonder expliciete toestemming; het pakket bevat interne projecttekeningen en werkelijke beelden.

Het fout-screenshot is beschikbaar. **Het oorspronkelijke foutieve FCStd is nog niet aangeleverd.** Alleen voor exacte reproductie van de opgeslagen documenttoestand is die kopie nodig; hij blokkeert niet de verse baselinebuild. Voeg hem lokaal toe aan `user_inputs/`, met gebruikte generator/herstelstap en Report view-log. Test reparaties nooit op de enige kopie.

## E.2 Native softwaretests van de ongewijzigde baseline

De testcode hieronder zit in **H2**, niet in dit nieuwe Markdownbestand. Zij is niet tijdens deze merge aangepast of opnieuw native uitgevoerd.

### Stap 1 - statische controle

Vanuit de H2-root:

```powershell
py -3 .\tests\static_check.py
```

Deze bestaande controle behandelt syntax, macro/module-overeenstemming, JSON-relaties/validator, verboden machinecomponent, bronhashes, modusselecties en negatieve invoerfixtures. Rapport: `verification/static_check.json`.

De eerdere overdracht meldt `PASS_STATIC_ONLY`. Dat bewijst niet dat FreeCAD is gestart. Maak de vereiste bronnen beschikbaar voor de hashcontrole. Presenteer de vroegere statische rapportdatum niet als een nieuwe uitvoering van deze merge.

### Stap 2 - echte FreeCADCmd

Zoek de werkelijk gebruikte executable en controleer haar CLI. Bijvoorbeeld:

```powershell
Get-ChildItem -Path 'C:\Program Files\FreeCAD*\bin\FreeCADCmd.exe' -ErrorAction SilentlyContinue
```

Die locatie is alleen een zoekvoorbeeld. Na vaststelling van het juiste pad:

```powershell
$fcCmd = 'C:\werkelijk\installatiepad\bin\FreeCADCmd.exe'
& $fcCmd --version
& $fcCmd --help
py -3 .\tests\launch_native.py --exe $fcCmd --timeout 600
```

Alternatief zonder externe Python-launcher:

```powershell
& $fcCmd (Resolve-Path .\tests\native_test.py).Path
```

De directe variant heeft geen externe timeout. Controleer ook dan het geschreven rapport; exitcode 0 of een stille console is geen voldoende PASS. Gebruik niet willekeurige systeem-Python om CAD te bouwen wanneer daarin FreeCAD niet beschikbaar is. Geen systeembeleid of globale PATH aanpassen om de test zonder overleg te forceren.

De H2-launcher gebruikt standaardbibliotheek, start `tests/native_test.py` in FreeCADCmd, sluit stdin, bewaart stdout/stderr, bewaakt timeout en beoordeelt exitcode plus JSON-uitkomst. Stop bij timeout alleen het eigen testproces; geen algemene kill van andere gebruikers-FreeCAD-processen.

De bestaande native test doorloopt **WORK en PANELS** en controleert:

- Nieuwe documenten via `build_from_json`, expliciete mode en geen autosave in de bronmap.
- Componentaanwezigheid, IDs, parents, App::Link-targets en `LinkTransform`.
- Effectieve `Part.getShape`-wereldgeometrie tegen onafhankelijk uit de JSON bepaalde bounds; niet uitsluitend `prototype.Shape`.
- Niet-lege/geldige vormen; niet-nul solidvolumes voor `box`/`prism`. Geen volume vereisen voor bedoelde `lines`, `face` of `polyline`.
- Negatieve plaatsingscontrole: in het **H2-script** een testlink tijdelijk **100 mm** verschuiven, foutdetectie eisen en herstellen zonder die fout op te slaan.
- Eigen document opslaan in een unieke outputmap, sluiten, heropenen en opnieuw controleren.

De oudere H0-testbeschrijving noemde een verschuiving van 1000 mm. Dat is een andere testvariant, geen maat van het gebouw. Gebruik de werkelijk meegeleverde H2-code en rapporteer die variant; verwar niet de twee wrappers of resultaatnamen.

Numerieke tolerantie: **0,01 mm** voor omzetting van dezelfde JSON. Bounding-box-overeenstemming alleen bewijst geen volledige vormidentiteit. Voeg bij nieuwe solids gerichte profiel-, punt-, lengte- en volumecontroles toe; verzwak de test niet om een schema-/geometriefout te maskeren.

H2-uitvoer onder `outputs/native_.../`: onder andere `freecadcmd.log`, `launcher_result.json`, `native_summary.json`, `WORK.FCStd`, `PANELS.FCStd` en audits voor/na heropenen. Bewaar tracebacks ook wanneer de builder voor zijn interne audit crasht.

### Stap 3 - echte FreeCAD-GUI

Voer in de volledige FreeCAD-applicatie uit:

```text
tests/GUI_SmokeTest.FCMacro
```

Laat de macro in de tests-map of stel `ROOT_OVERRIDE` expliciet in. Ze maakt een nieuw WORK-document, wist selectie voor screenshots, controleert bibliotheek/wereldgeometrie, maakt echte iso-/bovenaanzichtbeelden, schakelt Building uit/aan, bekijkt dak/plafond en bewaart/heropent alleen haar eigen testdocument. Andere gebruikersdocumenten blijven ongemoeid.

Uitvoer: `outputs/gui_.../`, met `GUI_WORK.FCStd` en `gui_summary.json`. De resultaattekst `AUTOMATED_CHECKS_PASS_VISUAL_REVIEW_REQUIRED` vereist nog echt beoordelen van de PNG's.

Aanvullend beoordelen/herhalen:

- Geen losse bronplint of onverklaarde wand onder/buiten de hal.
- Component_Library buiten Building; prototypes standaard verborgen, ook na schakelen en heropenen.
- `Show All` alleen op testkopie; bewust zichtbare overlappende prototypes niet als extra fysieke onderdelen tellen/exporteren.
- Roof en Ceiling afzonderlijk bedienbaar, geen dubbele isolatiedaken.
- Selecteerbaarheid echte componenten; kleuren niet met selectie verwarren.
- PANELS en later toegevoegde AHU/detailzones apart in GUI toetsen.
- Praktische build/recompute-respons, bestandsgrootte en eventueel geheugen rapporteren.

Een aangemaakt screenshot is nog geen visueel goedgekeurd screenshot. Import van `FreeCADGui` zonder een echt GUI-document is geen vervanging van deze route.

### Stap 4 - bestaand gebruikersdocument

Registreer op een kopie vooraf objectnamen, linktargets, placements, Visibility en eigen imports. Test de afgebakende herstelmacro, ook een tweede keer, zonder objecten/plaatsingen te veranderen of het origineel te overschrijven. De fresh-build GUI-test vervangt deze regressie niet.

## E.3 Vervolgens inhoudelijk gebouwmodel afwerken

Controleer met oorspronkelijke bronuitsneden en onafhankelijke aflezing in het gegenereerde model: datum 21/A, 65160/54160, lokale assen 2/4/6, nokken, laagopbouw en raamtypen. Een as wordt niet automatisch een volledig portaal.

Werk vervolgens de echte staalcatalogus uit: ID, profiel, start/eindpunt, oriëntatie, lidmarkering, bronblad, datum-/referentievlak en lokale afwijkingen. Genereer een lid eenmaal, ook wanneer het in meerdere aanzichten voorkomt. Nieuwe juiste solids mogen bestaande contourreferenties vervangen in de werkweergave, met behoud van traceerbaarheid.

Binnenbouw en roof flashings afzonderlijk; geen oude volledige brandwanden herintroduceren. Iedere gewijzigde maat krijgt oud/nieuw, bron en reden. Laat bouwkundige datacorrecties niet onzichtbaar samenvallen met softwarebugfixes.

## E.4 AHU-gegevensmodel toevoegen zonder fictieve geometrie

Splits de nieuwe AHU-uitbreiding logisch in:

1. **Componentregister:** stabiele IDs, bevestigde functie, geometry-status en parent.
2. **Functionele verbindingen:** gescheiden lucht-/watercircuits en warmtewisselaarzijden.
3. **Geometrische plaatsing:** alleen bevestigde punten, oriëntaties, enveloppen en interfaces.
4. **Controlsreferenties:** gemeten variabele, manipulated variables, feedback en nog te kiezen numerieke parameters.
5. **Bron-/conflictenregister:** U1-correcties, A1-ontwerpwaarden en D-open punten.

Behouden architectuurrelaties zijn al te registreren wanneer de 3D-coördinaten nog onbekend zijn. Zo ontstaat geen noodzaak om plaatsingen of maten te verzinnen om het functionele schema te kunnen vastleggen.

De louvre-pair krijgt een functionele relatie naar precies twee fysieke dampers. De T_mixed-sensor hoort bij de downstream mengduct, niet bij de buitenlucht of uitsluitend de warme tak. R1 heeft een supply- en een exhaust-zijde; R2 een hall- en een exhaust-zijde. De uitlaatzijdevolgorde blijft pending zolang geen bron die bepaalt.

Nieuwe componenten zoals heater, R2-fan, nieuwe coil of buffervat zonder definitieve maten krijgen geen willekeurige geometrie. Een geleverd STEP of dimensioned vendor drawing kan later als nieuwe primaire geometriebron worden geregistreerd. Zonder die bron is een voorkeursproductnaam geen XYZ-oplossing.

## E.5 Aanvullende AHU-tests - nog te implementeren

**Deze controles zijn eisen voor de nieuwe uitbreiding; zij worden niet reeds door de meegeleverde H2-testcode uitgevoerd.** Houd ze los van bestaande baseline-resultaten.

| Controle | Verwacht resultaat |
|---|---|
| Filter/split/mix | Buitenlucht door filter, dan twee paden, een downstream samenvoeging; geen oude uitsluitend seriële all-air-coil route als volledig schema. |
| Pair-membership | Twee verschillende fysieke modulerende dampers onder een gekoppelde regelrelatie; niet twee on/off-mode selectors. |
| Temperatuursensor | Main top duct na mengen, voor de machine-inlaatinterfaces; T/RH na filter blijft een aparte sensorfunctie. |
| Regelfunctie | Meer koude behoefte geeft bronbevestigde richting cooling omhoog/recovery omlaag; omgekeerd voor warm. Niet een niet-opgegeven vaste verdelingswet testen als eis. |
| Setpoint/tuning onbekend | Geen automatische default voor proces-inlaattemperatuur, PID-gains, hysterese of veiligheidsparameters; ontbrekende waarden duidelijk melden. |
| Startupverwarming | Resistor gekoppeld aan recovery-pad voor R1-supply side; geen hallheater of algemeen continu verplichte heater. |
| Hallucht | Alleen hall inlet -> R2 hallzijde -> retour naar hal; geen hallucht-pijl naar process-supply split/mix. |
| Recuperators | R1/R2 zijn verschillende fysieke IDs; zijden/rollen apart; geen fictieve luchtmenging over de warmtewisselaar en geen verzonnen hot-side serievolgorde. |
| Condensorlucht | Eigen roof/outside -> chillers -> roof route; niet verbonden met procesmengkring. |
| Waternummering | CH-1 coil; CH-2 waterloads; WL-1 product outlet voor WL-2 product inlet in het genoemde serieconcept. |
| BT-1-conflict | Gedeelde bronvermelding mag geen ongevraagde hydraulische knoop of extra vat opleveren; pending zichtbaar. |
| Muur versus dak | Diameter 900 voor process inlet niet automatisch overal; drie afzonderlijke dakfunctie-IDs met maatstatus. |
| Machine-uitsluiting | Geen gegenereerde/importerende magnetrongeometrie, footprint of placeholder; bestaande gebruikersimport ongewijzigd. |
| Onbekende maten | `null`/pending leidt niet tot nominale fallbacksolids. Een negatieve fixture moet dit aantonen. |
| Duplicaten | Een fysieke R1/R2/klep/coil bestaat eenmaal, ook als meerdere circuit-/controlreferenties ernaar wijzen. |
| Performance/export | Alleen bedoelde instanties/exportsets; verborgen prototypes en broncontouren niet als tweede installatie exporteren. |

Regelsimulaties zijn **offline** en controleren de gedocumenteerde relaties. Dit document machtigt geen echte PLC-, heater- of Belimo-aansturing. Definitieve tuning en ingebruikname zijn andere engineeringstappen.

## E.6 Opleveringscriteria

Houd vier verschillende uitspraken apart:

| Niveau | Wat daadwerkelijk bewezen moet zijn |
|---|---|
| **Statisch** | Syntax, relaties, bronintegriteit, uitsluitingen en schema geldig |
| **Native software** | FreeCAD-build/recompute, effectieve links, geldige verwachte vormen, save/reopen en behoud van gebruikersdocumenten |
| **GUI bruikbaar** | Echte beoordeelde beelden, geen bekende displayfout, logische boom en praktische prestaties |
| **Inhoudelijk geschikt voor coördinatie** | Relevante 3D-staal-/apparatuurgeometrie uit bronnen, correcte interfaces/topologie, bronconflicten opgelost of expliciet uitgesloten; niet alleen contouren |

Lever code en invoer-JSON met hash/revisie, runtimeversies, exacte commando's, stdout/stderr/tracebacks, audits, beoordeelde screenshots en een nieuw native bewaard/heropend FCStd. Rapporteer buildtijd, recomputetijd, grootte en aantallen. Changelog moet codefix, broncorrectie, AHU-architectuurwijziging en nieuwe geometrie onderscheiden.

Een PASS van bounds bewijst alleen consistentie tussen JSON en CAD voor die controle. Een ongewijzigd maar fysiek onjuist brongegeven kan dezelfde PASS opleveren. Geen volledige bronvalidatie, live-regeling, fabricagegeschiktheid of as-built-certificaat claimen wanneer die niet geleverd zijn.

---

# F. Bestanden, bronnen en startopdracht

## F.1 Gebruik met het bestaande pakket

Plaats **dit `Copilot_handoff.md` in de hoofdmap van de uitgepakte laatste ZIP**, naast `model/`, `tests/`, `reference/` en `sources/`. Het vervangt de leidende leesinstructie voor de merge, niet de bronarchieven.

Lees de oude losse handoffs alleen voor herkomst en regressiedetails. De bestaande `.github/copilot-instructions.md` verwijst nog naar de oude startdocumenten. Laat Copilot die verwijzing op de ontwikkelkopie naar dit document bijwerken, met behoud van de grenzen voor geen V3, geen machinegeometrie en geen bronwijziging zonder verantwoording. Archiveer de oude tekst voordat die verwijzing wijzigt.

Deze levering bestaat uit **een Markdownbestand**. De eerdere ZIP, Python-generator, FCMacro, tests en uitvoer-JSON zijn niet door deze merge gewijzigd. Het AHU-overzicht is hier volledig inhoudelijk opgenomen; bewaar de oorspronkelijke `ALLSHIELD_AHU_COMPLETE_OVERVIEW(1).md` daarnaast als bronbestand, bijvoorbeeld in een nieuw `sources/ahu/`-mapje. Dat mapje is een voorgestelde locatie, geen claim dat het al in H2 zit.

### Werkelijk aanwezige H2-mapstructuur

| Pad | Inhoud |
|---|---|
| `model/` | Generator 02, bouw-JSON, herstelmacro, LEESMIJ en eerdere validatie |
| `tests/` | `static_check.py`, `launch_native.py`, `native_test.py`, `GUI_SmokeTest.FCMacro` |
| `reference/` | v0.2/v0.3-bewijs, DXF/preview, oude validatietekst en pakket 01 voor regressie |
| `sources/pdf/` | Negen PDF's uit de eerdere overdracht |
| `sources/text/` | Native tekstextracties, per fysieke PDF-pagina, zonder OCR |
| `sources/images/` | Fout-screenshot, gevelbeeld, bronprofieluitsnede en gemarkeerde planfragmenten |
| `sources/video/` | Gecomprimeerde dronevideo |
| `verification/` | Eerdere statische-/herkomstcontrole en source registry |
| `user_inputs/` | Bestemd voor kopie van fout-FCStd en lokale runtimegegevens |
| `.github/copilot-instructions.md` | Oude permanente workspace-regels; startverwijzing bijwerken op ontwikkelkopie |
| `MANIFEST_SHA256.json` | Baseline-manifest; niet herschrijven alsof nieuwe documentatie oorspronkelijk al inbegrepen was |

Oudere H0-paden `app/`, `sources/plans/`, `sources/evidence/`, `user_case/`, `tests/native_smoke.py`, `tests/gui_smoke.FCMacro` en `run_native_tests.ps1` horen bij het andere pakket. Alleen gebruiken wanneer bewust die oude variant getest wordt. De actuele hoofdroute in E verwijst naar H2.

## F.2 Negen oorspronkelijke PDF's in H2

| ID | Bestand in `sources/pdf/` | Oorspronkelijke naam / relevante bladen |
|---|---|---|
| **G1** | `20260522 ter Aar Indeling totaal (002).pdf` | Volledige layout, pagina 1; 6060/2800/5200-kalibratie, apparatuur en openingen |
| **G2** | `20260730_maatvoering.pdf` | `20260730 maatvoering indeling fabriek totaal ter Aar nav gesprek Rody(1).pdf`; aanvullende maatvoering, pagina 1 |
| **G3** | `44449_Logivast_07maart2025(1).pdf` | Acht pagina's; p6-p7 doorsneden/opbouw, p8 details; ontwerpwaarschuwing niet voor uitvoering behouden |
| **G4** | `Hardeman_tekeningenset.pdf` | `Tekeningenset plantekenaar_Hardeman.pdf`; bladen/revisies eerst identificeren |
| **G5** | `a03_ovz-a.pdf` | `a03_ovz-a(1).pdf`; staal fase A, F-M, partiële as 6; bladstatus TER CONTROLE |
| **G6** | `a11_ovz-b.pdf` | `a11_ovz-b_gezien_geen_opm(1).pdf`; staal fase B, A-E; bladstatus TER CONTROLE |
| **G7** | `c04a_gevels.pdf` | `c04a_gevels_opmTS(1).pdf`; revisie 24-07-2025, status VOORLOPIG; gevels, dak, openingen |
| **G8** | `c05a_binnen.pdf` | `c05a_binnen(1).pdf`; binnenaanzichten en maatkettingen; geen automatisch bewijs van actuele volledige wanden |
| **G9** | `photos allshield inside 2026_09_05_@_12-37-16.pdf` | Vijf pagina's foto's; binnen/buiten, staal, plafond, plint, ramen/deuren |

De PDF-bestanden zijn niet allemaal goedgekeurde uitvoerings- of as-built documenten. `sources/text/` is een zoekhulp. Voor geometrische relaties altijd bladbeeld en/of vectorpaden raadplegen.

## F.3 Aanvullende beelden en afgeleide werkresultaten

| H2-bestand | Betekenis |
|---|---|
| `sources/images/USER_FAILURE_SCREENSHOT.png` | Werkelijk gebruikersbeeld van foutieve FreeCAD-weergave |
| `sources/images/IMG-20260905-WA0015.jpg` | Geveldetail: hoog raam, deur/bovenlicht, panelen, plint en afvoer |
| `sources/images/plan_5200_PS_marked.png` | Door Johan gemarkeerde 5200/PS-uitsnede |
| `sources/images/kozijn_980x4000_label.png` | Afzonderlijk kozijnlabel; niet automatisch PS of hoog raam |
| `sources/images/plan_beams_1_2_3.png` | Uitsnede met genummerde beam-bullets |
| `sources/images/c04_roof_profile_source.png` | Vergrote bronuitsnede; geen as-built profielmeting |
| `sources/video/Untitled Project.mp4` | Verkorte dronevideo; perspectief/oriëntatie en zichtbare details |
| `reference/allshield_building_reference_v0_2.json` | Basisreferenties en eerdere afleidingen; ander schema dan de uitvoer-JSON |
| `reference/allshield_roof_window_source_evidence_v0_3.json` | Aanvullend dak-/kozijnbewijs; geen zelfstandig bouwrecept |
| `reference/allshield_reference_v0_2_validation.txt` | Oude schaal-/assencontrole, geen native runtimebewijs |
| `reference/allshield_base_topview_v0_2.dxf` en preview | Afgeleide 2D-basis, niet onafhankelijk van dezelfde PDF-bronnen |
| `reference/Allshield_FreeCAD_Rebuild_01.zip` | Alleen historische foutvariant/regressie; niet actieve generator |

De AHU-overzichtstekst noemt leveranciers en voorlopige maten, maar voegt geen definitieve vendor-CAD, bestelde heatertekening of complete controls-I/O-lijst toe. Beweer niet dat die specifieke leveranciersdocumenten in H2 zitten wanneer dat niet uit het register blijkt.

## F.4 Herkomstcontrole van deze merge

De onderstaande SHA-256-waarden zijn bij deze merge uit de werkelijk beschikbare bytes gelezen. Zij bewijzen bestandsidentiteit, **niet** engineeringcorrectheid of een native testrun.

| Bestand | SHA-256 |
|---|---|
| `ALLSHIELD_AHU_COMPLETE_OVERVIEW(1).md` | `9fa58f50d97139ab6f87502034df581b8960f63c07883611cce653caa4f9bdb2` |
| `Allshield_Overdracht_Copilot.md` | `5dd73c45a91b4cb899641214f318667869755023e9dd6df24cdcbaff4ee044d1` |
| `Allshield_GitHub_Copilot_Overdracht.zip` | `2ba7b762648ad5da38c569d6e5f1aa393a1efcbfac09b1908ed2743b210dff90` |
| H2 `model/allshield_build.py` | `d09953da5f01a2c613cab92668485e9e148284c37925efec7b766c3fc20750ff` |
| H2 `model/Allshield_Build.FCMacro` | `d09953da5f01a2c613cab92668485e9e148284c37925efec7b766c3fc20750ff` |
| H2 `model/allshield_building_02.json` | `7bda242a27ede07407efe873d35efd8be2a385d23002d690ead2caf21b857656` |

Vroegere `PASS_STATIC_ONLY`-resultaten staan in het ongewijzigde pakket. Native FreeCAD/GUI, regeling, drukverlies, capaciteit en as-built opname zijn niet tijdens deze documentmerge getest.

## F.5 Behouden tooldocumentatie uit de oude overdrachten

Deze links zijn **overgenomen verwijzingen**, niet nieuw geraadpleegd bij deze bronmerge en geen bronnen voor gebouw-/AHU-maten. De lokale runtimeversie is beslissend.

```text
FreeCAD headless:
https://wiki.freecad.org/Headless_FreeCAD/en

FreeCAD Part.getShape, broncode (main kan nieuwer zijn dan lokale release):
https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/Part/App/AppPartPy.cpp

FreeCAD screenshots:
https://wiki.freecad.org/Std_ViewScreenShot/en

Lokale VS Code / Copilot agents:
https://code.visualstudio.com/docs/agents/overview
https://docs.github.com/en/copilot/how-tos/chat-with-copilot/chat-in-ide?tool=vscode

Workspace-instructies:
https://code.visualstudio.com/docs/agent-customization/custom-instructions
```

## F.6 Overzicht van doorgevoerde merge-wijzigingen

| Onderdeel | Gevolg van deze nieuwe handoff |
|---|---|
| Gebouw-/testoverdracht H1/H2 | Behouden; H2-paden/launcher zijn canoniek; oude H0-details alleen met duidelijke variantidentificatie |
| A1 sectie 3 en summary 28 | Seriele toevoerbeschrijving vervangen door split in cooling en recovery, daarna mengen |
| A1 sectie 11 | Drie modes herschreven als operating regions |
| A1 sectie 12 | Twee louvres als paired modulation; temperatuur na mengen, PID-richting, startupresistor en rustigere regeling |
| A1 secties 9/21/22/24 | Hallucht uitsluitend R2; hoofdtemperatuursensor toegevoegd; controls-/modelrollen aangepast |
| Overige A1-secties 1-28 | Componenten, route, waarden, werkafbakening, onderhoud, condensaat en open punten inhoudelijk behouden |
| Tegenspraak/ontbrekende velden | D-register, geen ongedocumenteerde technische correctie |
| Code/uitvoerbare JSON | Niet gewijzigd; AHU-implementatie en tests zijn nog werk voor Copilot |

## F.7 Startopdracht voor GitHub Copilot

```text
Lees Copilot_handoff.md volledig. Dit is de nieuwe geconsolideerde leidende
handoff voor Allshield Ter Aar: gebouw, FreeCAD, AHU, Fusion en P&ID.

Gebruik de laatste uitgepakte H2-workspace met model/, tests/, reference/ en
sources/. Bewaar baseline en bronnen. Test generator 02 eerst werkelijk in
lokale FreeCADCmd en daarna in de echte FreeCAD-GUI. Leg paden, versies,
logs, wereldplaatsingen, save/reopen en beoordeelde screenshots vast.
De fout in Component_Library/links is nog niet native bewezen opgelost.
Verschuif geen gebouwcoördinaten om een weergaveprobleem te maskeren.

Werk vervolgens brongebaseerde staal-solids en de AHU-uitbreiding uit.
Nieuwe hoofdregel: na het roll-up filter twee parallelle toevoerpaden.
Cooling path bevat coil(s); recovery path bevat electric heat resistor en
recuperator 1. De twee modulerende louvre dampers vormen een gekoppelde
continue inlaattemperatuurregeling. De twee paden mengen aan het begin
van de main top duct. De temperatuurmeting NA mengen is de hoofdregelwaarde.
Summer/normal/winter zijn operating regions, geen drie discrete klepstanden.

Hallucht uitsluitend via recuperator 2 terug naar de hal. Geen halluchtpad
naar de procesmengduct. Proceslucht, hallucht en condensorlucht gescheiden.
Geen ongefundeerde hot-side-volgorde van R1/R2 of hydraulische BT-1-koppeling.
Ontbrekende PID/heater/plaatsingswaarden niet invullen met aannames.

V3 niet als code- of geometriebron gebruiken. Behoud datum 21/A, expliciete
onregelmatige staalstations, JSON-invoer en logische parent/child-structuur,
waaronder Roof > Ceiling > Sandwich_Ceiling. Component_Library afzonderlijk.
De magnetron niet tekenen/importeren, geen footprint of placeholder; Johan
plaatst zijn eigen machine. Raak zijn eigen imports niet aan.

Volg openpuntenregister D en testplan E. De AHU-tests zijn nieuwe eisen en
zitten nog niet in de baseline-tests. Werk offline; geen live PLC/heater/
actuatoraansturing. Markeer ontwerpwaarden en onbekende maten als zodanig.

Lever code en JSON met hashes, een native getest FCStd, volledige logs,
beoordeelde screenshots, prestatiegegevens, changelog en afzonderlijke lijst
van resterende geometrie-/bronvragen. Een statische PASS of contourenmodel
is geen volledig geverifieerd installatie-/botsingsmodel.
```

**Einde van de geconsolideerde handoff.**
