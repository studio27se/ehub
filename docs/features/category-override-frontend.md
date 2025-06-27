# Frontend Implementation - Category Settings Override

## Översikt
Detta dokument specificerar frontend-implementeringen för funktionen att skriva över kategoriinställningar för AD-synkade mottagare i ehub-webapp.

## Komponenter som behöver skapas/modifieras

### 1. CategorySettingsPage
**Fil:** `src/pages/CategorySettings/CategorySettingsPage.tsx`

**Ändringar:**
- Lägg till "Override AD Recipients" knapp i kategorikonfigurationssektionen
- Knappen ska endast visas för användare med rätt behörigheter
- Knappen ska visa antal AD-synkade mottagare som kommer påverkas

```tsx
interface CategorySettingsPageProps {
  categoryId: string;
}

const CategorySettingsPage: React.FC<CategorySettingsPageProps> = ({ categoryId }) => {
  const [adRecipientsCount, setAdRecipientsCount] = useState<number>(0);
  const [hasOverridePermission, setHasOverridePermission] = useState<boolean>(false);

  // Ny funktion för override
  const handleOverrideSettings = async () => {
    setShowConfirmDialog(true);
  };

  return (
    <div>
      {/* Befintligt innehåll */}
      
      {hasOverridePermission && (
        <div className="override-section">
          <Button 
            variant="warning"
            onClick={handleOverrideSettings}
            disabled={adRecipientsCount === 0}
          >
            Skriv över AD-mottagarinställningar ({adRecipientsCount} mottagare)
          </Button>
        </div>
      )}
    </div>
  );
};
```

### 2. OverrideConfirmationDialog
**Fil:** `src/components/OverrideConfirmationDialog/OverrideConfirmationDialog.tsx`

**Ny komponent:**
```tsx
interface OverrideConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  affectedRecipientsCount: number;
  categoryName: string;
}

const OverrideConfirmationDialog: React.FC<OverrideConfirmationDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  affectedRecipientsCount,
  categoryName
}) => {
  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogTitle>Bekräfta överskrivning av inställningar</DialogTitle>
      <DialogContent>
        <Alert severity="warning">
          <AlertTitle>Varning: Denna åtgärd kan inte ångras</AlertTitle>
          Du kommer att skriva över inställningar för {affectedRecipientsCount} AD-synkade mottagare 
          i kategorin "{categoryName}" med kategoridefaultinställningarna.
        </Alert>
        
        <Typography variant="body2" sx={{ mt: 2 }}>
          Alla individuella inställningar som dessa mottagare har kommer att försvinna och 
          ersättas med standardinställningarna för denna kategori.
        </Typography>
        
        <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
          Är du säker på att du vill fortsätta?
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Avbryt</Button>
        <Button 
          onClick={onConfirm} 
          variant="contained" 
          color="warning"
          autoFocus
        >
          Ja, skriv över inställningar
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

### 3. CategoryOverrideService
**Fil:** `src/services/CategoryOverrideService.ts`

**Ny service:**
```typescript
interface OverrideRequest {
  categoryId: string;
}

interface OverrideResponse {
  success: boolean;
  affectedRecipients: number;
  message: string;
}

interface AdRecipientsCountResponse {
  count: number;
}

class CategoryOverrideService {
  private baseUrl = '/api/categories';

  async getAdRecipientsCount(categoryId: string): Promise<number> {
    const response = await fetch(`${this.baseUrl}/${categoryId}/ad-recipients/count`);
    if (!response.ok) {
      throw new Error('Failed to fetch AD recipients count');
    }
    const data: AdRecipientsCountResponse = await response.json();
    return data.count;
  }

  async overrideAdRecipientSettings(categoryId: string): Promise<OverrideResponse> {
    const response = await fetch(`${this.baseUrl}/${categoryId}/ad-recipients/override`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ categoryId })
    });

    if (!response.ok) {
      throw new Error('Failed to override AD recipient settings');
    }

    return response.json();
  }
}

export default new CategoryOverrideService();
```

## State Management

### Redux Actions
**Fil:** `src/store/categories/actions.ts`

```typescript
// Nya actions
export const OVERRIDE_AD_RECIPIENTS_REQUEST = 'OVERRIDE_AD_RECIPIENTS_REQUEST';
export const OVERRIDE_AD_RECIPIENTS_SUCCESS = 'OVERRIDE_AD_RECIPIENTS_SUCCESS';
export const OVERRIDE_AD_RECIPIENTS_FAILURE = 'OVERRIDE_AD_RECIPIENTS_FAILURE';
export const FETCH_AD_RECIPIENTS_COUNT_REQUEST = 'FETCH_AD_RECIPIENTS_COUNT_REQUEST';
export const FETCH_AD_RECIPIENTS_COUNT_SUCCESS = 'FETCH_AD_RECIPIENTS_COUNT_SUCCESS';
export const FETCH_AD_RECIPIENTS_COUNT_FAILURE = 'FETCH_AD_RECIPIENTS_COUNT_FAILURE';

export const overrideAdRecipients = (categoryId: string) => async (dispatch: Dispatch) => {
  dispatch({ type: OVERRIDE_AD_RECIPIENTS_REQUEST });
  
  try {
    const result = await CategoryOverrideService.overrideAdRecipientSettings(categoryId);
    dispatch({ 
      type: OVERRIDE_AD_RECIPIENTS_SUCCESS, 
      payload: result 
    });
    return result;
  } catch (error) {
    dispatch({ 
      type: OVERRIDE_AD_RECIPIENTS_FAILURE, 
      payload: error.message 
    });
    throw error;
  }
};

export const fetchAdRecipientsCount = (categoryId: string) => async (dispatch: Dispatch) => {
  dispatch({ type: FETCH_AD_RECIPIENTS_COUNT_REQUEST });
  
  try {
    const count = await CategoryOverrideService.getAdRecipientsCount(categoryId);
    dispatch({ 
      type: FETCH_AD_RECIPIENTS_COUNT_SUCCESS, 
      payload: count 
    });
    return count;
  } catch (error) {
    dispatch({ 
      type: FETCH_AD_RECIPIENTS_COUNT_FAILURE, 
      payload: error.message 
    });
    throw error;
  }
};
```

## Behörighetshantering

### PermissionService utökning
**Fil:** `src/services/PermissionService.ts`

```typescript
// Lägg till ny permission constant
export const PERMISSIONS = {
  // ... befintliga permissions
  CATEGORY_OVERRIDE_AD_RECIPIENTS: 'category.override.ad.recipients',
};

// Lägg till metod för att kontrollera override-behörighet
export const canOverrideAdRecipients = (userPermissions: string[]): boolean => {
  return userPermissions.includes(PERMISSIONS.CATEGORY_OVERRIDE_AD_RECIPIENTS);
};
```

## Error Handling

### Felhantering i komponenter
```typescript
const handleOverrideError = (error: Error) => {
  console.error('Override failed:', error);
  
  // Visa användarmeddelande
  setErrorMessage(`Kunde inte skriva över inställningar: ${error.message}`);
  
  // Logga för debugging
  logger.error('Category override failed', {
    categoryId,
    error: error.message,
    timestamp: new Date().toISOString()
  });
};
```

## Användarfeedback

### Loading States
- Visa spinner under override-operation
- Disable knapp under pågående operation
- Progress indicator för stora uppdateringar

### Success/Error Messages
- Toast-meddelanden för framgångsrik operation
- Detaljerade felmeddelanden vid problem
- Bekräftelse med antal påverkade mottagare

## Styling

### CSS Classes
```scss
.override-section {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px solid #ff9800;
  border-radius: 4px;
  background-color: #fff3e0;
  
  .override-button {
    background-color: #ff9800;
    color: white;
    
    &:hover {
      background-color: #f57c00;
    }
    
    &:disabled {
      background-color: #cccccc;
    }
  }
}

.override-confirmation-dialog {
  .warning-content {
    color: #d32f2f;
    font-weight: 500;
  }
}
```

## Testing Requirements

### Unit Tests
- `CategorySettingsPage` komponententester
- `OverrideConfirmationDialog` komponententester  
- `CategoryOverrideService` servicetester
- Redux actions och reducers tester

### Integration Tests
- Fullständigt användarflöde från knappklick till bekräftelse
- Error scenarios
- Permission-baserad synlighet

### E2E Tests
```typescript
describe('Category Settings Override', () => {
  it('should allow authorized user to override AD recipient settings', async () => {
    // Logga in som användare med rätt behörigheter
    await loginAsAdmin();
    
    // Navigera till kategorisida
    await page.goto('/categories/123/settings');
    
    // Klicka på override-knapp
    await page.click('[data-testid=override-ad-recipients-button]');
    
    // Bekräfta i dialog
    await page.click('[data-testid=confirm-override-button]');
    
    // Verifiera framgång
    await expect(page.locator('[data-testid=success-message]')).toBeVisible();
  });
});
```

## Performance Considerations

### Optimering
- Lazy loading av OverrideConfirmationDialog
- Debounce för AD recipients count API calls
- Caching av permission checks
- Optimistic updates med rollback

### Monitoring
- Spåra användarinteraktioner med override-funktionen
- Performance metrics för API calls
- Error rate monitoring

## Accessibility

### WCAG Compliance
- Proper ARIA labels för alla interaktiva element
- Keyboard navigation support
- Screen reader support för varningsmeddelanden
- Color contrast compliance för varningselement

```tsx
// Exempel på accessibility
<Button
  aria-label={`Skriv över inställningar för ${adRecipientsCount} AD-synkade mottagare`}
  aria-describedby="override-warning-text"
  onClick={handleOverrideSettings}
>
  Skriv över AD-mottagarinställningar
</Button>

<p id="override-warning-text" className="sr-only">
  Denna åtgärd kommer att ersätta alla individuella inställningar med kategoridefaultvärden och kan inte ångras.
</p>
```

## Implementation Checklist

### Utveckling
- [ ] Skapa OverrideConfirmationDialog komponent
- [ ] Modifiera CategorySettingsPage
- [ ] Implementera CategoryOverrideService
- [ ] Lägg till Redux actions och reducers
- [ ] Uppdatera PermissionService
- [ ] Lägg till CSS styling

### Testing
- [ ] Enhetstester för alla nya komponenter
- [ ] Integrationstester för användarflöden
- [ ] E2E-tester för kritiska scenarios
- [ ] Accessibility testing
- [ ] Performance testing

### Documentation
- [ ] Component documentation
- [ ] API integration guide
- [ ] User guide updates
- [ ] Developer onboarding documentation