# Kategoriinställningar - Override för AD-synkade mottagare

## Översikt

Denna specifikation beskriver implementeringen av funktionalitet för att "skriva över" kategoriinställningar för befintliga AD-mottagare i eHUB-systemet.

## Bakgrund

idag är det möjligt att ändra standard mottagarinställningar för en kategori (vilket endast implementeras på mottagare synkade från AD). Dock saknas möjligheten att skriva över alla AD-synkade mottagares inställningar för denna kategori med standardinställningarna från kategorin.

## Funktionella krav

### Nuvarande flöde
1. Kategorin skapas med standardinställningar för mottagare från AD-synk
2. Befintliga mottagare får standardinställningar: AD-synkade från kategorin, och övriga de systemvida inställningarna
3. (valbar) Mottagarnas inställningar ändras individuellt
4. (valbar) Kategorins standardinställningar ändras

### Nytt krav - steg 5
5. Standardinställningarna för kategorin skjuts ut till alla mottagare synkade från AD-synk, vilket skriver över de tidigare individuellt inställda valen för den kategorin

## Tekniska krav

### Behörigheter
- Funktionen ska knytas till samma permission ID som krävs för att justera kategorier
- Användaren måste ha lämplig behörighet för att kunna använda funktionen

### Säkerhet
- Innan man skjuter över ändringen måste användaren bekräfta att de vet vad de gör via en bekräftelsedialog
- Åtgärden ska loggas för audit-trail

### Användarupplevelse
- Funktionen ska vara tillgänglig i kategoriadministrationsgränssnittet
- Bekräftelsedialog ska tydligt förklara konsekvenserna av åtgärden
- Användaren ska se hur många mottagare som kommer att påverkas

## Arkitektur

### Frontend (ehub-webapp)
- UI-komponenter för kategoriinställningar
- Bekräftelsedialog
- API-integration

### Backend (ehub-backend-api)
- API-endpoint för override-funktionalitet
- Affärslogik för att uppdatera mottagarinställningar
- Loggning och audit-trail

## Detaljerade specifikationer

Se separata dokument för:
- [Frontend Implementation](./category-override-frontend.md)
- [Backend Implementation](./category-override-backend.md)
- [Database Schema](./category-override-database.md)
- [API Specification](./category-override-api.md)
- [UI/UX Specification](./category-override-ui.md)
- [Security Requirements](./category-override-security.md)
- [Testing Strategy](./category-override-testing.md)

## Implementation Timeline

### Fas 1: Backend Implementation
- Database schema changes
- API endpoint development
- Permission validation
- Audit logging

### Fas 2: Frontend Implementation  
- UI components
- API integration
- Confirmation dialogs
- User feedback

### Fas 3: Testing & Validation
- Unit tests
- Integration tests
- User acceptance testing
- Security validation

## Risker och överväganden

### Tekniska risker
- Performance impact vid uppdatering av många mottagare
- Data consistency under uppdateringsprocessen
- Rollback-scenario vid fel

### Användarrisker
- Oavsiktlig överskrivning av individuella inställningar
- Förvirring kring när inställningar kommer från kategori vs individuella val

## Slutleverans

- Fullständig implementation i både frontend och backend
- Dokumentation för administratörer
- Testresultat och verifikation
- Deployment-instruktioner