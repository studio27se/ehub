# Mall för Dokumentation av GET-anrop

Använd denna mall när du dokumenterar GET-anrop från mobilapplikationen.

## GET-anrop Mall

### Grundinformation
- **Endpoint URL**: `/api/[resurse]/[action]`
- **Modul**: [Modulnamn från listan]
- **Kodposition**: `src/[mapp]/[fil].ts:radnummer`
- **Metod**: GET

### Funktionalitet
- **Syfte**: [Kort beskrivning av vad anropet gör]
- **Utlösare**: [När/varför anropas denna endpoint]
- **Frekvens**: [Hur ofta anropas detta - vid start, vid användarinteraktion, kontinuerligt, etc.]

### Tekniska Detaljer
- **Query Parameters**:
  - `param1`: [typ] - [beskrivning]
  - `param2`: [typ] - [beskrivning]
- **Path Parameters**:
  - `{id}`: [typ] - [beskrivning]
- **Headers**: [Speciella headers som krävs]
- **Autentisering**: [JWT token, API key, etc.]

### Response
- **Format**: JSON/XML/Text
- **Struktur**:
  ```json
  {
    "field1": "värde",
    "field2": 123,
    "nested": {
      "subfield": "värde"
    }
  }
  ```

### Optimeringsmöjligheter
- **Cachning**: [Kan resultatet cachas? Hur länge?]
- **Paginering**: [Används paginering? Är den optimal?]
- **Filtering**: [Kan data filtreras på servern istället för klienten?]
- **Batch requests**: [Kan flera anrop kombineras?]

### Exempel

```typescript
// Exempel från mobilappen
async getUserProfile(userId: string): Promise<UserProfile> {
  const response = await this.http.get(`/api/users/${userId}/profile`, {
    headers: { Authorization: `Bearer ${this.authToken}` }
  }).toPromise();
  return response as UserProfile;
}
```

### Status och Kommentarer
- **Status**: 🔄 Under dokumentation / ✅ Dokumenterat / ❌ Behöver optimering
- **Prioritet**: Hög/Medium/Låg
- **Anteckningar**: [Ytterligare kommentarer eller observationer]

---

## Exempel på Komplett Dokumentation

### Grundinformation
- **Endpoint URL**: `/api/projects/{projectId}`
- **Modul**: Projekthantering
- **Kodposition**: `src/services/project.service.ts:67`
- **Metod**: GET

### Funktionalitet
- **Syfte**: Hämtar detaljerad information om ett specifikt projekt
- **Utlösare**: När användaren navigerar till projektdetaljsidan
- **Frekvens**: Vid användarinteraktion (klick på projekt)

### Tekniska Detaljer
- **Query Parameters**: Inga
- **Path Parameters**:
  - `{projectId}`: string - Unikt ID för projektet
- **Headers**: 
  - `Authorization: Bearer {jwt_token}`
  - `Content-Type: application/json`
- **Autentisering**: JWT token

### Response
- **Format**: JSON
- **Struktur**:
  ```json
  {
    "id": "proj_123",
    "name": "Projekt Namn",
    "description": "Projekt描述",
    "status": "active",
    "client": {
      "id": "client_456", 
      "name": "Klientnamn"
    },
    "team": [...],
    "tasks": [...],
    "timeline": {...}
  }
  ```

### Optimeringsmöjligheter
- **Cachning**: Kan cachas i 5 minuter för oförändrade projekt
- **Paginering**: Inte tillämpligt för enskilda projekt
- **Filtering**: Möjlighet att specificera vilka fält som behövs
- **Batch requests**: Kan kombineras med relaterade anrop för team/tasks

### Status och Kommentarer
- **Status**: ✅ Dokumenterat
- **Prioritet**: Medium
- **Anteckningar**: Överväg att lägga till optional fields parameter för att minska response size