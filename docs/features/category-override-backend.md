# Backend Implementation - Category Settings Override

## Översikt
Detta dokument specificerar backend-implementeringen för funktionen att skriva över kategoriinställningar för AD-synkade mottagare i ehub-backend-api.

## API Endpoints

### 1. Get AD Recipients Count
**Endpoint:** `GET /api/categories/{categoryId}/ad-recipients/count`

**Beskrivning:** Hämtar antal AD-synkade mottagare för en specifik kategori

**Request:**
```http
GET /api/categories/123/ad-recipients/count
Authorization: Bearer {token}
```

**Response:**
```json
{
  "count": 45,
  "categoryId": "123",
  "categoryName": "IT Support"
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized
- `403` - Forbidden (ingen behörighet för kategorin)
- `404` - Category not found

### 2. Override AD Recipients Settings
**Endpoint:** `POST /api/categories/{categoryId}/ad-recipients/override`

**Beskrivning:** Skriver över alla AD-synkade mottagares inställningar med kategoridefaultvärden

**Request:**
```http
POST /api/categories/123/ad-recipients/override
Authorization: Bearer {token}
Content-Type: application/json

{
  "confirmOverride": true
}
```

**Response:**
```json
{
  "success": true,
  "affectedRecipients": 45,
  "categoryId": "123",
  "categoryName": "IT Support",
  "operationId": "op_abc123def456",
  "timestamp": "2025-06-27T10:43:11Z",
  "message": "Successfully updated settings for 45 AD-synced recipients"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request (missing confirmation)
- `401` - Unauthorized
- `403` - Forbidden (ingen behörighet)
- `404` - Category not found
- `409` - Conflict (kategori har inga defaultinställningar)
- `500` - Internal Server Error

## Database Schema Changes

### 1. Audit Log Table
**Tabell:** `category_override_audit`

```sql
CREATE TABLE category_override_audit (
    id BIGSERIAL PRIMARY KEY,
    operation_id VARCHAR(50) UNIQUE NOT NULL,
    category_id BIGINT NOT NULL REFERENCES categories(id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    affected_recipients_count INTEGER NOT NULL,
    operation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    operation_status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED', -- STARTED, COMPLETED, FAILED
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_category_override_audit_category ON category_override_audit(category_id);
CREATE INDEX idx_category_override_audit_user ON category_override_audit(user_id);
CREATE INDEX idx_category_override_audit_timestamp ON category_override_audit(operation_timestamp);
```

### 2. Temporary Operation Tracking
**Tabell:** `category_override_operations`

```sql
CREATE TABLE category_override_operations (
    id BIGSERIAL PRIMARY KEY,
    operation_id VARCHAR(50) UNIQUE NOT NULL,
    category_id BIGINT NOT NULL REFERENCES categories(id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    total_recipients INTEGER,
    processed_recipients INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);
```

## Service Layer Implementation

### 1. CategoryOverrideService
**Fil:** `services/category_override_service.py`

```python
from typing import Dict, List, Optional
from sqlalchemy import and_, text
from sqlalchemy.orm import Session
from models import Category, Recipient, CategoryRecipientSettings, User
from services.permission_service import PermissionService
from services.audit_service import AuditService
import uuid
from datetime import datetime

class CategoryOverrideService:
    def __init__(self, db: Session):
        self.db = db
        self.permission_service = PermissionService(db)
        self.audit_service = AuditService(db)
    
    def get_ad_recipients_count(self, category_id: int, user_id: int) -> Dict:
        """Hämta antal AD-synkade mottagare för en kategori"""
        
        # Kontrollera behörigheter
        if not self.permission_service.can_manage_category(user_id, category_id):
            raise PermissionError("User does not have permission to manage this category")
        
        # Hämta kategori
        category = self.db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise ValueError("Category not found")
        
        # Räkna AD-synkade mottagare
        count = self.db.query(Recipient).filter(
            and_(
                Recipient.category_id == category_id,
                Recipient.is_ad_synced == True,
                Recipient.is_active == True
            )
        ).count()
        
        return {
            "count": count,
            "categoryId": str(category_id),
            "categoryName": category.name
        }
    
    def override_ad_recipients_settings(self, category_id: int, user_id: int, confirm_override: bool = False) -> Dict:
        """Skriv över alla AD-synkade mottagares inställningar"""
        
        if not confirm_override:
            raise ValueError("Override confirmation required")
        
        # Kontrollera behörigheter
        if not self.permission_service.can_manage_category(user_id, category_id):
            raise PermissionError("User does not have permission to manage this category")
        
        # Hämta kategori och dess defaultinställningar
        category = self.db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise ValueError("Category not found")
        
        if not category.default_settings:
            raise ValueError("Category has no default settings configured")
        
        # Generera operation ID
        operation_id = f"op_{uuid.uuid4().hex[:12]}"
        
        try:
            # Starta operation tracking
            self._start_operation_tracking(operation_id, category_id, user_id)
            
            # Hämta AD-synkade mottagare
            ad_recipients = self.db.query(Recipient).filter(
                and_(
                    Recipient.category_id == category_id,
                    Recipient.is_ad_synced == True,
                    Recipient.is_active == True
                )
            ).all()
            
            affected_count = len(ad_recipients)
            
            if affected_count == 0:
                raise ValueError("No AD-synced recipients found for this category")
            
            # Uppdatera inställningar för varje mottagare
            self._update_recipients_settings(ad_recipients, category.default_settings, operation_id)
            
            # Logga framgångsrik operation
            self.audit_service.log_category_override(
                operation_id=operation_id,
                category_id=category_id,
                user_id=user_id,
                affected_count=affected_count,
                status='COMPLETED'
            )
            
            # Markera operation som klar
            self._complete_operation_tracking(operation_id, affected_count)
            
            return {
                "success": True,
                "affectedRecipients": affected_count,
                "categoryId": str(category_id),
                "categoryName": category.name,
                "operationId": operation_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": f"Successfully updated settings for {affected_count} AD-synced recipients"
            }
            
        except Exception as e:
            # Logga fel
            self.audit_service.log_category_override(
                operation_id=operation_id,
                category_id=category_id,
                user_id=user_id,
                affected_count=0,
                status='FAILED',
                error_message=str(e)
            )
            
            self._fail_operation_tracking(operation_id, str(e))
            raise
    
    def _start_operation_tracking(self, operation_id: str, category_id: int, user_id: int):
        """Starta operation tracking"""
        operation = CategoryOverrideOperation(
            operation_id=operation_id,
            category_id=category_id,
            user_id=user_id,
            status='PROCESSING'
        )
        self.db.add(operation)
        self.db.commit()
    
    def _update_recipients_settings(self, recipients: List[Recipient], default_settings: Dict, operation_id: str):
        """Uppdatera mottagarinställningar batch-wise"""
        
        batch_size = 100
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            for recipient in batch:
                # Ta bort befintliga individuella inställningar
                self.db.query(CategoryRecipientSettings).filter(
                    and_(
                        CategoryRecipientSettings.recipient_id == recipient.id,
                        CategoryRecipientSettings.category_id == recipient.category_id
                    )
                ).delete()
                
                # Skapa nya inställningar baserat på kategoridefault
                new_settings = CategoryRecipientSettings(
                    recipient_id=recipient.id,
                    category_id=recipient.category_id,
                    settings=default_settings,
                    is_default=True,
                    updated_by_operation=operation_id,
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_settings)
            
            # Commit batch
            self.db.commit()
    
    def _complete_operation_tracking(self, operation_id: str, affected_count: int):
        """Markera operation som slutförd"""
        self.db.execute(
            text("""
                UPDATE category_override_operations 
                SET status = 'COMPLETED', 
                    processed_recipients = :count,
                    completed_at = NOW()
                WHERE operation_id = :op_id
            """),
            {"count": affected_count, "op_id": operation_id}
        )
        self.db.commit()
    
    def _fail_operation_tracking(self, operation_id: str, error_message: str):
        """Markera operation som misslyckad"""
        self.db.execute(
            text("""
                UPDATE category_override_operations 
                SET status = 'FAILED', 
                    error_message = :error,
                    completed_at = NOW()
                WHERE operation_id = :op_id
            """),
            {"error": error_message, "op_id": operation_id}
        )
        self.db.commit()
```

### 2. Permission Service Extension
**Fil:** `services/permission_service.py`

```python
# Lägg till ny permission constant
CATEGORY_OVERRIDE_PERMISSION = "category.override.ad.recipients"

class PermissionService:
    # ... befintliga metoder
    
    def can_override_ad_recipients(self, user_id: int, category_id: int) -> bool:
        """Kontrollera om användaren kan skriva över AD-mottagarinställningar"""
        # Samma behörighet som för att justera kategorier
        return self.can_manage_category(user_id, category_id)
    
    def can_manage_category(self, user_id: int, category_id: int) -> bool:
        """Kontrollera om användaren kan hantera kategorin"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Kontrollera användarens roller och behörigheter
        return self._has_category_management_permission(user, category_id)
```

## API Controllers

### 1. CategoryOverrideController
**Fil:** `controllers/category_override_controller.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.category_override import OverrideRequest, OverrideResponse, CountResponse
from services.category_override_service import CategoryOverrideService
from dependencies import get_db, get_current_user
from models import User

router = APIRouter(prefix="/api/categories", tags=["category-override"])

@router.get("/{category_id}/ad-recipients/count", response_model=CountResponse)
async def get_ad_recipients_count(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hämta antal AD-synkade mottagare för en kategori"""
    try:
        service = CategoryOverrideService(db)
        result = service.get_ad_recipients_count(category_id, current_user.id)
        return CountResponse(**result)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this category"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/{category_id}/ad-recipients/override", response_model=OverrideResponse)
async def override_ad_recipients_settings(
    category_id: int,
    request: OverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Skriv över AD-mottagarinställningar med kategoridefaultvärden"""
    try:
        service = CategoryOverrideService(db)
        result = service.override_ad_recipients_settings(
            category_id=category_id,
            user_id=current_user.id,
            confirm_override=request.confirmOverride
        )
        return OverrideResponse(**result)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage this category"
        )
    except ValueError as e:
        if "confirmation required" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Override confirmation is required"
            )
        elif "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "no default settings" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category has no default settings configured"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        # Logga unexpected errors
        logger.error(f"Unexpected error in override operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during the override operation"
        )
```

## Data Models

### 1. Pydantic Schemas
**Fil:** `schemas/category_override.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OverrideRequest(BaseModel):
    confirmOverride: bool = Field(..., description="Confirmation that user wants to proceed with override")

class CountResponse(BaseModel):
    count: int = Field(..., description="Number of AD-synced recipients")
    categoryId: str = Field(..., description="Category ID")
    categoryName: str = Field(..., description="Category name")

class OverrideResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    affectedRecipients: int = Field(..., description="Number of recipients affected")
    categoryId: str = Field(..., description="Category ID")
    categoryName: str = Field(..., description="Category name")
    operationId: str = Field(..., description="Unique operation identifier")
    timestamp: str = Field(..., description="Operation timestamp (ISO format)")
    message: str = Field(..., description="Human-readable operation result message")

class OperationStatus(BaseModel):
    operationId: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    totalRecipients: Optional[int] = None
    processedRecipients: int = 0
    startedAt: datetime
    completedAt: Optional[datetime] = None
    errorMessage: Optional[str] = None
```

### 2. SQLAlchemy Models
**Fil:** `models/category_override.py`

```python
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class CategoryOverrideAudit(Base):
    __tablename__ = "category_override_audit"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    operation_id = Column(String(50), unique=True, nullable=False)
    category_id = Column(BigInteger, ForeignKey('categories.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    affected_recipients_count = Column(Integer, nullable=False)
    operation_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    operation_status = Column(String(20), nullable=False, default='COMPLETED')
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="override_audits")
    user = relationship("User", back_populates="category_overrides")

class CategoryOverrideOperation(Base):
    __tablename__ = "category_override_operations"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    operation_id = Column(String(50), unique=True, nullable=False)
    category_id = Column(BigInteger, ForeignKey('categories.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), nullable=False, default='PENDING')
    total_recipients = Column(Integer, nullable=True)
    processed_recipients = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    category = relationship("Category")
    user = relationship("User")
```

## Error Handling

### 1. Custom Exceptions
**Fil:** `exceptions/category_override_exceptions.py`

```python
class CategoryOverrideException(Exception):
    """Base exception for category override operations"""
    pass

class CategoryNotFoundException(CategoryOverrideException):
    """Category not found"""
    pass

class NoDefaultSettingsException(CategoryOverrideException):
    """Category has no default settings"""
    pass

class NoAdRecipientsException(CategoryOverrideException):
    """No AD-synced recipients found"""
    pass

class OverrideOperationFailedException(CategoryOverrideException):
    """Override operation failed"""
    def __init__(self, operation_id: str, message: str):
        self.operation_id = operation_id
        super().__init__(message)
```

## Performance Optimizations

### 1. Batch Processing
- Uppdatera mottagare i batches om 100 för att undvika långa transaktioner
- Använd bulk operations där möjligt

### 2. Database Optimizations
```sql
-- Index för snabbare queries
CREATE INDEX CONCURRENTLY idx_recipients_ad_synced_active 
ON recipients(category_id, is_ad_synced, is_active) 
WHERE is_ad_synced = true AND is_active = true;

-- Index för audit queries
CREATE INDEX CONCURRENTLY idx_category_override_audit_composite
ON category_override_audit(category_id, operation_timestamp DESC);
```

### 3. Async Processing för stora dataset
```python
from celery import Celery

@celery.task
def async_override_ad_recipients(category_id: int, user_id: int, operation_id: str):
    """Async task för att hantera stora override-operationer"""
    # Implementation för bakgrundsbearbetning
    pass
```

## Security Considerations

### 1. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/{category_id}/ad-recipients/override")
@limiter.limit("5/minute")  # Max 5 override operations per minut
async def override_ad_recipients_settings(...):
    # Implementation
```

### 2. Audit Logging
- Logga alla override-operationer
- Inkludera användarinformation, timestamp, och resultat
- Bevara audit trail för compliance

### 3. Transaction Safety
```python
from sqlalchemy.exc import SQLAlchemyError

def override_with_transaction(self, category_id: int, user_id: int):
    """Execute override within a transaction with rollback capability"""
    try:
        # Begin transaction
        # Perform updates
        self.db.commit()
    except SQLAlchemyError as e:
        self.db.rollback()
        raise OverrideOperationFailedException(operation_id, str(e))
```

## Testing Requirements

### 1. Unit Tests
**Fil:** `tests/test_category_override_service.py`

```python
import pytest
from services.category_override_service import CategoryOverrideService
from tests.factories import CategoryFactory, RecipientFactory, UserFactory

class TestCategoryOverrideService:
    def test_get_ad_recipients_count_success(self, db_session):
        # Setup
        category = CategoryFactory()
        user = UserFactory(permissions=['category.manage'])
        ad_recipients = RecipientFactory.create_batch(5, category=category, is_ad_synced=True)
        
        service = CategoryOverrideService(db_session)
        
        # Execute
        result = service.get_ad_recipients_count(category.id, user.id)
        
        # Assert
        assert result['count'] == 5
        assert result['categoryId'] == str(category.id)
    
    def test_override_ad_recipients_success(self, db_session):
        # Setup
        category = CategoryFactory(default_settings={'notifications': True})
        user = UserFactory(permissions=['category.manage'])
        ad_recipients = RecipientFactory.create_batch(3, category=category, is_ad_synced=True)
        
        service = CategoryOverrideService(db_session)
        
        # Execute
        result = service.override_ad_recipients_settings(category.id, user.id, confirm_override=True)
        
        # Assert
        assert result['success'] is True
        assert result['affectedRecipients'] == 3
        assert 'operationId' in result
    
    def test_override_without_permission_raises_error(self, db_session):
        # Setup
        category = CategoryFactory()
        user = UserFactory(permissions=[])  # No permissions
        
        service = CategoryOverrideService(db_session)
        
        # Execute & Assert
        with pytest.raises(PermissionError):
            service.override_ad_recipients_settings(category.id, user.id, confirm_override=True)
```

### 2. Integration Tests
**Fil:** `tests/test_category_override_api.py`

```python
import pytest
from httpx import AsyncClient

class TestCategoryOverrideAPI:
    @pytest.mark.asyncio
    async def test_override_api_success(self, async_client: AsyncClient, auth_headers):
        # Setup test data
        category_id = 123
        
        # Execute
        response = await async_client.post(
            f"/api/categories/{category_id}/ad-recipients/override",
            json={"confirmOverride": True},
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'affectedRecipients' in data
```

## Deployment Considerations

### 1. Migration Scripts
```sql
-- Migration för nya tabeller
-- V1.0__Add_category_override_tables.sql

-- V1.1__Add_category_override_indexes.sql
```

### 2. Configuration
```python
# settings.py
CATEGORY_OVERRIDE_BATCH_SIZE = 100
CATEGORY_OVERRIDE_MAX_RECIPIENTS = 10000
CATEGORY_OVERRIDE_TIMEOUT_SECONDS = 300
```

### 3. Monitoring
- Health checks för override-operationer
- Metrics för operation success rate
- Alerting för misslyckade operationer

## Implementation Checklist

### Development
- [ ] Implementera CategoryOverrideService
- [ ] Skapa API endpoints
- [ ] Lägg till database migrations
- [ ] Implementera permission checks
- [ ] Lägg till audit logging
- [ ] Skapa Pydantic schemas
- [ ] Implementera error handling

### Testing
- [ ] Unit tests för service layer
- [ ] Integration tests för API endpoints
- [ ] Performance tests för stora dataset
- [ ] Security tests för permissions
- [ ] End-to-end tests

### Documentation
- [ ] API dokumentation (OpenAPI/Swagger)
- [ ] Database schema dokumentation
- [ ] Deployment guides
- [ ] Troubleshooting guides