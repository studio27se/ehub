---
title: "Mobilapplikationens GET-anrop"
---

# Mobilapplikationens GET-anrop

Denna sida dokumenterar alla GET-anrop som görs från mobilapplikationen (ehub-app-ionic repo) till backend, organiserat per modul.

## Syfte

Dokumentationen syftar till att:
- Få en förståelse för alla platser som behöver justeras från klientbaserad hantering av data till serverhantering
- Kunna använda listan till att effektivisera datasvarshanteringen på serversidan
- Identifiera vilka endpoints som behöver optimeras

## Dokumentationsstruktur

För varje GET-anrop dokumenteras:
- **Endpoint URL**: Den fullständiga URL:en som anropas
- **Modul**: Vilken funktionell modul anropet tillhör
- **Kodposition**: Exakt var i koden anropet görs (fil och rad)
- **Syfte**: Vad anropet används till
- **Parametrar**: Vilka parametrar som skickas med
- **Returdata**: Typ av data som förväntas tillbaka

## Moduler

### 📱 Användarhantering
*GET-anrop relaterade till användarautentisering, profiler och behörigheter*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 🏢 Företagsinformation  
*GET-anrop för hämtning av företagsdata och organisationsstruktur*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 📊 Dashboard och Rapporter
*GET-anrop för dashboard-data och rapportgenerering*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 💰 Ekonomi och Fakturering
*GET-anrop för ekonomisk data, fakturor och betalningar*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 📝 Projekthantering
*GET-anrop för projekt, uppgifter och tidsrapportering*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 👥 Kundhantering (CRM)
*GET-anrop för kunddata, kontakter och relationer*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 📄 Dokumenthantering
*GET-anrop för dokumenthämtning och filhantering*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### ⚙️ Inställningar och Konfiguration
*GET-anrop för systeminställningar och användarpreferenser*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 🔔 Notifieringar
*GET-anrop för notifieringar och meddelanden*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

### 📈 Analytics och Statistik
*GET-anrop för användarstatistik och systemanalys*

| Endpoint | Kodposition | Syfte | Parametrar | Status |
|----------|-------------|--------|------------|--------|
| *Dokumentation pågår* | | | | 🔄 |

## Instruktioner för Dokumentation

### Steg-för-steg Process

1. **Klona ehub-app-ionic repository**
   ```bash
   git clone [ehub-app-ionic-repo-url]
   cd ehub-app-ionic
   ```

2. **Sök efter GET-anrop i koden**
   ```bash
   # Sök efter HTTP GET-anrop
   grep -r "\.get(" src/ --include="*.ts" --include="*.js"
   grep -r "GET" src/ --include="*.ts" --include="*.js"
   grep -r "httpGet" src/ --include="*.ts" --include="*.js"
   
   # Sök efter Angular HttpClient GET-anrop
   grep -r "http\.get" src/ --include="*.ts"
   grep -r "this\.http\.get" src/ --include="*.ts"
   ```

3. **Identifiera moduler**
   - Granska mapp- och filstruktur i `src/`
   - Identifiera funktionella områden
   - Matcha GET-anrop till respektive modul

4. **Dokumentera varje anrop**
   För varje GET-anrop, fyll i tabellen med:
   - **Endpoint**: Full URL eller relativ sökväg
   - **Kodposition**: `filnamn.ts:radnummer` eller `mapp/filnamn.ts:radnummer`
   - **Syfte**: Kort beskrivning av vad anropet gör
   - **Parametrar**: Query parameters, path parameters
   - **Status**: ✅ Dokumenterat, 🔄 Under granskning, ❌ Behöver optimering

### Exempel på Dokumentation

```markdown
| /api/users/profile | src/services/user.service.ts:45 | Hämtar användarens profilinformation | userId (path param) | ✅ |
| /api/companies/{id}/settings | src/pages/settings/settings.ts:120 | Laddar företagsinställningar | companyId (path param) | ✅ |
```

### Tools för Automatisk Upptäckt

För att förenkla processen kan följande verktyg användas:

```bash
# Skapa en fil som listar alla GET-anrop
find src/ -name "*.ts" -exec grep -Hn "\.get(" {} \; > get_requests.txt

# Sök efter Angular HTTP GET-anrop specifikt
find src/ -name "*.ts" -exec grep -Hn "this\.http\.get\|this\.httpClient\.get" {} \; > angular_get_requests.txt
```

## Status för Dokumentation

- **Total progress**: 0% (0/10 moduler dokumenterade)
- **Senast uppdaterad**: *Väntar på initial dokumentation*
- **Ansvarig**: Development team med access till ehub-app-ionic repository

## Nästa Steg

1. Få access till ehub-app-ionic repository
2. Utför kodanalys enligt instruktionerna ovan
3. Populera tabellerna med faktiska GET-anrop
4. Prioritera endpoints för optimering
5. Skapa actionable items för refactoring från client-side till server-side hantering

---

*Denna dokumentation uppdateras kontinuerligt när nya GET-anrop identifieras eller befintliga modifieras.*