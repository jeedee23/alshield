# Allshield - werken op twee machines en lokale branches

## Doel

Werk op meerdere machines zonder twee versies van hetzelfde model door elkaar te halen. Gebruik een machine met RustDesk als de **canonieke integratiemachine**. Daar is `main` de enige branch waarop gedeelde bronnen en goedgekeurd werk samenkomen.

Een tweede machine werkt uitsluitend in een eigen, lokale branch-directory. Copilot op die machine mag niet tegelijk in `main` werken of bestanden rechtstreeks uit een andere werkmap kopieren.

Lees altijd eerst `01_OVERDRACHT_COPILOT.md`, `02_TESTPLAN.md` en `.github/copilot-instructions.md`. Deze werkwijze verandert geen van de bron-, test- en modelregels uit die bestanden.

## Belangrijke correctie: branch is geen gedeelde mapstructuur

Elke Git-branch is een volledige momentopname van de repository. Een branch-directory bevat daarom een eigen werkende kopie van **alle** projectmappen, ook `pdf docs/` en `sources/`.

Gebruik dus nooit een netwerkshare, cloud-syncmap, junction of symlink om alleen `pdf docs/` of `sources/` fysiek tussen `main` en branch-directories te delen. Dat kan onvolledige bestanden, onbeheerde wijzigingen en niet-herleidbare modelresultaten opleveren.

De afspraak is functioneel, niet fysiek:

| Onderwerp | Wie schrijft | Waar gebeurt het |
|---|---|---|
| Gedeelde PDF's, foto's, video's en bronregisters | Alleen de gebruiker op de canonieke integratiemachine | `main` |
| Bouwkundige FreeCAD-/JSON-/Python-uitwerking | Alleen de toegewezen werker | `allshield-building` |
| AHU, kanalen en hun expliciet afgesproken koppelingen | Alleen de toegewezen werker | `allshield-ahu` |
| Samenvoegen en eindcontrole | Alleen op de canonieke integratiemachine | `main` |

De namen bevatten bewust geen spaties: gebruik `allshield-building` en `allshield-ahu`, niet `allshield building` of `allshield AHU`.

## Aanbevolen directory-indeling

Op een machine mogen aparte Git-worktrees naast elkaar bestaan. Dit zijn volledige werkdirectories; alleen de Git-objectopslag wordt lokaal gedeeld. Voorbeeld:

```text
D:\allshield_divers\worktrees\
  allshield-main\       # canonieke integratiewerkmap, branch main
  allshield-building\   # alleen branch allshield-building
  allshield-ahu\        # alleen branch allshield-ahu
```

Maak deze directories alleen op een lokale schijf van die ene machine. Een tweede fysieke machine krijgt zijn eigen clone of een gecontroleerd overgedragen Git-bundle. Deel nooit een actieve werkdirectory tussen machines.

## Branches maken op de werker-machine

Voorwaarde: begin met een schone, lokale clone die op `main` staat. Controleer eerst de map en branch:

```powershell
Get-Location
git status --short --branch
git worktree list
```

Als `git status` gewijzigde bestanden toont, stop dan. Maak geen branch bovenop onbekend of niet-gecommit werk.

Voer vanuit de lokale `allshield-main`-werkmap uit:

```powershell
git switch main
git worktree add ..\allshield-building -b allshield-building main
git worktree add ..\allshield-ahu -b allshield-ahu main
```

Werk daarna uitsluitend vanuit de juiste map, bijvoorbeeld:

```powershell
Set-Location ..\allshield-building
git status --short --branch
```

Als de branch al bestaat, maak hem niet opnieuw. Voeg dan de bestaande branch als worktree toe:

```powershell
git worktree add ..\allshield-building allshield-building
```

Gebruik op een tweede fysieke machine dezelfde structuur in een afzonderlijke lokale clone. Het ophalen van die clone of bundle gebeurt alleen via een door de gebruiker toegestane locatie. Deze instructie geeft geen toestemming om naar een remote te pushen of projectmateriaal te publiceren.

## Regels voor Copilot in een branch-directory

1. Controleer voor elke wijziging met `git status --short --branch` dat de huidige branch de toegewezen branch is.
2. Bewerk alleen bestanden die voor die branch-opdracht nodig zijn. `allshield-building` en `allshield-ahu` mogen niet tegelijk hetzelfde generator-, JSON-, macro- of documentbestand wijzigen.
3. Laat `model/`, `reference/`, bronarchieven en gebruikersdocumenten ongemoeid tenzij de opdracht en de projectregels die wijziging expliciet toelaten.
4. Schrijf gegenereerde resultaten naar een nieuwe, unieke branch-eigen outputmap. Overschrijf geen bestaande gebruikersdocumenten of baselineresultaten.
5. Voer de relevante statische, native en waar nodig GUI-controles uit volgens `02_TESTPLAN.md`. Rapporteer ontbrekende tests als niet uitgevoerd.
6. Leg de wijziging vast in een lokale commit met een korte, inhoudelijke boodschap. Een lokale commit is geen toestemming om te pushen.

Voor een normale, gecontroleerde branchwijziging:

```powershell
git status --short
git diff --check
git add -- <alleen-de-gecontroleerde-bestanden>
git commit -m "Beschrijf de afgebakende wijziging"
```

Gebruik nooit `git add .` wanneer er gegenereerde uitvoer, onbekende bestanden of materiaal van de gebruiker in de werkmap kan staan.

## Gedeelde bronnen toevoegen via main

Wanneer de gebruiker een nieuwe bruikbare PDF, foto of andere bron toevoegt, gebeurt dat uitsluitend op de canonieke `main`-werkmap:

1. Voeg het bronbestand toe zonder bestaande bronnen te overschrijven of te wissen.
2. Werk het toepasselijke bronnenregister en herkomstbewijs bij volgens de bestaande projectregels.
3. Commit die bronwijziging op `main` na de relevante controles.
4. Draag de commit vervolgens gecontroleerd over naar de benodigde werker-branch(es).

De werker mag een nieuwe vondst wel melden in een handoff, maar plaatst deze niet door een bestand handmatig naar een andere actieve directory te kopieren.

## Wijzigingen handmatig overdragen zonder push

Voor een tekstuele of gemengde wijziging maakt de eigenaar van een branch een patch inclusief binaire bestanden. Dit gebeurt pas nadat de eigen tests zijn uitgevoerd en de commit(s) zijn gecontroleerd:

```powershell
git format-patch --binary main..allshield-building -o ..\transfer\allshield-building
```

Op de canonieke integratiemachine wordt de patch eerst beoordeeld. Pas daarna kan de gebruiker of aangewezen integrator in de `main`-werkmap toepassen:

```powershell
git switch main
git am D:\allshield_divers\transfer\allshield-building\*.patch
```

Bij een conflict niet bestanden heen en weer kopieren. Stop de toepassing met `git am --abort`, bepaal welke branch eigenaar is van het betreffende bestand en los het conflict alleen in de integratiewerkmap op. Voer daarna opnieuw de relevante controles uit.

Een nieuwe `main`-commit met gedeelde bronnen gaat in de omgekeerde richting: maak op de integratiemachine een patch van de nieuwe `main`-commit(s) en laat de benodigde werker die toepassen in zijn eigen branch. Zo ontvangen beide branches dezelfde bronhistorie zonder fysieke mappen te delen.

## Korte beslisregel

- Is het een bron die voor beide taken nuttig is? Voeg deze een keer toe op canonieke `main`, commit hem, en draag die commit over.
- Is het bouwkundige modelwerk? Doe het alleen in `allshield-building`.
- Is het AHU-/ductingwerk? Doe het alleen in `allshield-ahu`.
- Moet een bestand door beide branches worden aangepast? Wijs eerst een eigenaar aan en integreer de eerste wijziging in `main` voordat de tweede branch verdergaat.

Daarmee blijft `main` de gecontroleerde waarheid en blijven de twee lokale branch-directories onafhankelijk genoeg voor Copilot-sessies op verschillende machines.