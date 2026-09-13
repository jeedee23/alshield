# Native testplan - FreeCADCmd en GUI

## Wat is nodig?

Een lokale, werkende FreeCAD-installatie met `FreeCADCmd.exe` voor het geometrie-/documentgedeelte en de volledige FreeCAD-applicatie voor weergave. Gebruik bij voorkeur dezelfde versie als waarmee Johan de fout zag. Noteer de exacte versie, build, Python- en OCCT-versie; neem geen specifieke versie of installatiepad aan.

Copilot moet in de omgeving werken die toegang heeft tot deze installatie en tot de uitgepakte map. Een lokale Agent-sessie in VS Code kan terminalcommando's uitvoeren wanneer dat toegestaan is. Een cloudsessie op GitHub krijgt niet automatisch toegang tot de FreeCAD-installatie op Johans computer. [W2]

FreeCADCmd kan Python-bestanden uitvoeren en zonder grafische interface documenten/geometrie verwerken. [W1] Dat vervangt geen visuele test: deze fout betreft mede de zichtbaarheid van groepen, prototypes en links. Daarvoor is de echte FreeCAD-GUI nodig.

## A. Bewaar het bewijs

Laat `model/` en `reference/` aanvankelijk ongewijzigd. Sla een kopie van Johans foute document in `user_inputs/` op en noteer of generator 01, herstelmacro 02 of generator 02 is gebruikt. Test nooit reparaties op de enige kopie. De afbeelding `sources/images/USER_FAILURE_SCREENSHOT.png` zit al in het pakket; het bijbehorende native document niet.

De meegeleverde scripts genereren nieuwe testdocumenten. Ze openen niet automatisch Johans eigen document. De aparte herstelmacro doet dat wel met het actieve document; voer die daarom pas uit na diagnose en op een kopie.

## B. Statische controle

Vanuit de hoofdmap:

```powershell
py -3 .\tests\static_check.py
```

Deze controleert JSON-structuur, moeder/kind-relaties via de generatorvalidator, gelijkheid van macro en Python-code, bronhashes, modusselecties en twee negatieve invoercontroles. Uitvoer: `verification/static_check.json`.

Dit is hier uitgevoerd. `PASS_STATIC_ONLY` betekent NIET dat FreeCAD is gestart. De ruwe bron-PDF's en referentie-JSON moeten aanwezig zijn voor de hashcontrole.

## C. Native headless tests

Zoek het uitvoerbare bestand, bijvoorbeeld met PowerShell:

```powershell
Get-ChildItem -Path 'C:\Program Files\FreeCAD*\bin\FreeCADCmd.exe' -ErrorAction SilentlyContinue
```

Deze zoeklocatie is een voorbeeld. Zoek zo nodig de werkelijk gebruikte installatie, ook wanneer die elders staat. Controleer het gevonden pad; meerdere installaties zijn mogelijk.

Vul het echte pad in:

```powershell
$fcCmd = 'C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe' # VOORBEELD: aanpassen
& $fcCmd --version
& $fcCmd --help
py -3 .\tests\launch_native.py --exe $fcCmd --timeout 600
```

De meegeleverde Python-launcher gebruikt alleen de standaardbibliotheek, geen externe modules. Hij start `FreeCADCmd` met `tests/native_test.py`, sluit stdin, bewaart stdout/stderr, bewaakt een timeout en controleert zowel exitcode als JSON-resultaat. Hij verandert geen systeembeleid en installeert niets.

Zonder losse systeem-Python kun je het testscript rechtstreeks door FreeCADCmd laten uitvoeren:

```powershell
& $fcCmd (Resolve-Path .\tests\native_test.py).Path
```

De directe variant heeft geen externe timeout. Controleer altijd het geschreven `native_summary.json`; een stille console of exitcode 0 is niet voldoende. Bij oudere of afwijkende builds eerst de feitelijke CLI via `--help` controleren. [W1]

### Werkelijk geteste zaken in `native_test.py`

Het script importeert de generator zonder `main()` uit te voeren, gebruikt de JSON met expliciete overrides en doorloopt WORK en PANELS. Het vergelijkt effectieve `Part.getShape`-geometrie met een onafhankelijk berekende begrenzing uit de JSON.

Het controleert aanwezigheid en parent-relaties van componenten, App::Link-verwijzingen, `LinkTransform`, niet-lege/geldige vormen en niet-nul solidvolumes voor `box` en `prism`. Voor `lines`, `face` en `polyline` eist het terecht geen volume. De staalbroncontouren zijn dus NIET plots bewezen staal-solids door deze test.

Voor iedere modus wordt een nieuw `.FCStd` in een unieke `outputs/native_.../`-map geschreven, gesloten, heropend en opnieuw gecontroleerd. Een negatieve controle verschuift uitsluitend in geheugen een testlink 100 mm, vereist dat de controle dit detecteert en herstelt die link zonder de fout op te slaan.

De numerieke begrenzingstolerantie is 0,01 mm. Die is veel strikter dan de bronresolutie omdat ze alleen de omzetting van DEZELFDE JSON naar FreeCAD test. Ze mag nooit als geometrische nauwkeurigheid van het gebouw worden gerapporteerd. Een bounding box is bovendien geen volledige vormidentiteit: voeg bij verdere ontwikkeling gerichte lengte-, profiel-, volume- en puntencontroles toe.

### Uitvoer

Een unieke outputmap bevat onder andere:

- `freecadcmd.log`, `launcher_result.json`, `native_summary.json`;
- `WORK.FCStd`, `PANELS.FCStd`;
- per modus een audit voor en na opslaan/heropenen met world-bounds en aantallen.

Als de generator crasht voordat zijn interne audit klaar is, moet het buitenste testscript de traceback bewaren. Een crash is een testfout, geen toestemming om de controle uit te schakelen. Bewaar ook versie- en omgevingsgegevens.

## D. Native GUI-weergave

Start de volledige FreeCAD-GUI en voer `tests/GUI_SmokeTest.FCMacro` uit. Houd de macro in de uitgepakte tests-map. Wanneer je haar naar een andere locatie kopieert, stel `ROOT_OVERRIDE` expliciet in.

De macro maakt een nieuw WORK-document, wist selectie voor de screenshots, controleert geometrie en bibliotheekstructuur, maakt echte iso-/bovenaanzichtbeelden, schakelt `Building` uit/aan en controleert of prototypes onzichtbaar blijven. Ze maakt ook een beeld met dak en plafond aan, bewaart alleen dit nieuwe testdocument, heropent het en maakt een laatste screenshot. Andere geopende documenten worden niet opgeslagen of gesloten.

Uitvoer is `outputs/gui_.../`, inclusief `GUI_WORK.FCStd` en `gui_summary.json`. De uitkomst kan `AUTOMATED_CHECKS_PASS_VISUAL_REVIEW_REQUIRED` zijn: bekijk dan daadwerkelijk de afbeeldingen. Een script dat een afbeelding opslaat heeft die afbeelding nog niet visueel beoordeeld.

Vervolgcontroles door Copilot/Johan:

- Vergelijk met het probleembeeld: geen losse bronplinten of wandvlakken onder de hal.
- Controleer zichtbaarheid na `Building` uit/aan, `Component_Library` verbergen en opnieuw openen.
- Controleer `Show All` op een testkopie. Bewust getoonde prototypes kunnen overlappen met instanties; ze mogen niet als extra gebouwonderdelen worden geteld of met STEP meegeexporteerd worden.
- Controleer de individuele dak-/plafondschakelaars en selectie van een echte component.
- Herhaal de GUI-controle voor PANELS en de nieuw ontwikkelde detailzones.
- Meet praktische responstijden, modelgrootte en desgewenst procesgeheugen. Geen gegarandeerde FPS- of geheugencijfers verzinnen.

De GUI-startmacro behandelt de ongewijzigde WORK-baseline. Werk haar mee bij zodra het schema of de generatorinterface verandert, maar behoud de bestaande regressiegevallen.

## E. Implementatiecontrole is niet broncontrole

Een geslaagde headless en GUI-test bewijst nog niet dat een raam aan de juiste gevelpositie zit of dat een lid werkelijk bestaat. Controleer daarna enkele onafhankelijke meetkettingen en bronuitsneden: datum 21/A, 65160/54160 mm, lokale assen 2/4/6, nokken en bronprofielen. Meet de relevante geometrie in het gegenereerde FreeCAD-document; gebruik niet alleen opnieuw dezelfde generatorfunctie.

Controleer ook dat de toekomstige gedetailleerde staalonderdelen niet dubbel worden gegenereerd uit meerdere aanzichten, en dat oude volledige scheidingswanden niet worden heringevoerd. Bewaar voor iedere gewijzigde maat de bron en het oude/nieuwe gegeven.

## F. Criteria voor oplevering

**Technisch testbaar:** native build, recompute, linktransformaties, geldige verwachte vormen, save/reopen en geen onbedoelde wijzigingen aan gebruikersdocumenten.

**Visueel bruikbaar:** echte screenshots beoordeeld, bronbibliotheek correct verborgen, bekende weergavefout niet meer aanwezig, heldere boom en werkbare bestandsgrootte.

**Inhoudelijk voltooid voor installatiecoordinatie:** de vereiste staal-solids en secundaire delen zijn uit bronnen uitgewerkt, open punten zijn opgelost of expliciet uitgesloten, en de weergegeven geometrie is niet louter een verzameling broncontouren. De huidige baseline voldoet nog niet aan dit laatste criterium.

## Documentatie, geraadpleegd bij de overdracht

[W1] Officiele FreeCAD-documentatie: `https://wiki.freecad.org/Headless_FreeCAD/en` - uitvoeren zonder GUI, scriptbestanden en CLI. Niet alle API-/weergavefunctionaliteit is beschikbaar in consolemodus.

[W2] Officiele VS Code-documentatie: `https://code.visualstudio.com/docs/agents/overview` - lokaal, remote of cloud uitvoeren; agents met terminaltools en machtigingen.

[W3] Officiele VS Code-documentatie: `https://code.visualstudio.com/docs/agent-customization/custom-instructions` - `.github/copilot-instructions.md` als workspace-instructies. De projectregels zijn in dat bestand opgenomen; controleer dat jouw omgeving ze toepast.

Deze documentatie beschrijft toolmogelijkheden; de bouwkundige feiten komen uit de opgenomen projectbronnen.
