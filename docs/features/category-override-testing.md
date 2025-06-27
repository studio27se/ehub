# Testing Strategy - Category Settings Override

## Overview
This document defines the comprehensive testing strategy for the category settings override functionality, covering all aspects from unit tests to user acceptance testing.

## Testing Pyramid

```
    ┌─────────────────────┐
    │   E2E Tests (5%)    │
    ├─────────────────────┤
    │ Integration (15%)   │
    ├─────────────────────┤
    │   Unit Tests (80%)  │
    └─────────────────────┘
```

## Unit Testing

### 1. Backend Unit Tests

#### Service Layer Tests

**CategoryOverrideService Tests:**
```python
import pytest
from unittest.mock import Mock, patch
from services.category_override_service import CategoryOverrideService
from exceptions.category_override_exceptions import *

class TestCategoryOverrideService:
    
    @pytest.fixture
    def service(self, mock_db):
        return CategoryOverrideService(mock_db)
    
    @pytest.fixture
    def mock_category(self):
        return Mock(
            id=123,
            name="IT Support",
            default_settings={"notifications": True, "sms": False}
        )
    
    @pytest.fixture
    def mock_ad_recipients(self):
        return [
            Mock(id=1, category_id=123, is_ad_synced=True, is_active=True),
            Mock(id=2, category_id=123, is_ad_synced=True, is_active=True),
            Mock(id=3, category_id=123, is_ad_synced=True, is_active=True)
        ]
    
    def test_get_ad_recipients_count_success(self, service, mock_category, mock_ad_recipients):
        # Arrange
        service.db.query().filter().first.return_value = mock_category
        service.db.query().filter().count.return_value = 3
        service.permission_service.can_manage_category.return_value = True
        
        # Act
        result = service.get_ad_recipients_count(123, 456)
        
        # Assert
        assert result["count"] == 3
        assert result["categoryId"] == "123"
        assert result["categoryName"] == "IT Support"
        service.permission_service.can_manage_category.assert_called_once_with(456, 123)
    
    def test_get_ad_recipients_count_no_permission(self, service):
        # Arrange
        service.permission_service.can_manage_category.return_value = False
        
        # Act & Assert
        with pytest.raises(PermissionError, match="User does not have permission"):
            service.get_ad_recipients_count(123, 456)
    
    def test_get_ad_recipients_count_category_not_found(self, service):
        # Arrange
        service.permission_service.can_manage_category.return_value = True
        service.db.query().filter().first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Category not found"):
            service.get_ad_recipients_count(123, 456)
    
    def test_override_ad_recipients_success(self, service, mock_category, mock_ad_recipients):
        # Arrange
        service.permission_service.can_manage_category.return_value = True
        service.db.query().filter().first.return_value = mock_category
        service.db.query().filter().all.return_value = mock_ad_recipients
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'abc123def456'
            
            # Act
            result = service.override_ad_recipients_settings(123, 456, confirm_override=True)
            
            # Assert
            assert result["success"] is True
            assert result["affectedRecipients"] == 3
            assert result["operationId"] == "op_abc123def456"
            assert "IT Support" in result["categoryName"]
    
    def test_override_without_confirmation(self, service):
        # Act & Assert
        with pytest.raises(ValueError, match="Override confirmation required"):
            service.override_ad_recipients_settings(123, 456, confirm_override=False)
    
    def test_override_no_default_settings(self, service):
        # Arrange
        mock_category = Mock(id=123, name="IT Support", default_settings=None)
        service.permission_service.can_manage_category.return_value = True
        service.db.query().filter().first.return_value = mock_category
        
        # Act & Assert
        with pytest.raises(ValueError, match="no default settings"):
            service.override_ad_recipients_settings(123, 456, confirm_override=True)
    
    def test_override_no_ad_recipients(self, service, mock_category):
        # Arrange
        service.permission_service.can_manage_category.return_value = True
        service.db.query().filter().first.return_value = mock_category
        service.db.query().filter().all.return_value = []
        
        # Act & Assert
        with pytest.raises(ValueError, match="No AD-synced recipients found"):
            service.override_ad_recipients_settings(123, 456, confirm_override=True)
```

#### API Controller Tests

**CategoryOverrideController Tests:**
```python
import pytest
from fastapi.testclient import TestClient
from controllers.category_override_controller import router
from services.category_override_service import CategoryOverrideService

class TestCategoryOverrideController:
    
    @pytest.fixture
    def client(self):
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        return Mock(id=456, username="testuser")
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer valid_token"}
    
    def test_get_ad_recipients_count_success(self, client, mock_user, auth_headers):
        with patch('dependencies.get_current_user', return_value=mock_user):
            with patch.object(CategoryOverrideService, 'get_ad_recipients_count') as mock_service:
                mock_service.return_value = {
                    "count": 25,
                    "categoryId": "123",
                    "categoryName": "Test Category"
                }
                
                response = client.get("/categories/123/ad-recipients/count", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 25
                assert data["categoryId"] == "123"
    
    def test_get_ad_recipients_count_forbidden(self, client, mock_user, auth_headers):
        with patch('dependencies.get_current_user', return_value=mock_user):
            with patch.object(CategoryOverrideService, 'get_ad_recipients_count') as mock_service:
                mock_service.side_effect = PermissionError("Insufficient permissions")
                
                response = client.get("/categories/123/ad-recipients/count", headers=auth_headers)
                
                assert response.status_code == 403
                assert "permissions" in response.json()["detail"].lower()
    
    def test_override_ad_recipients_success(self, client, mock_user, auth_headers):
        with patch('dependencies.get_current_user', return_value=mock_user):
            with patch.object(CategoryOverrideService, 'override_ad_recipients_settings') as mock_service:
                mock_service.return_value = {
                    "success": True,
                    "affectedRecipients": 25,
                    "categoryId": "123",
                    "categoryName": "Test Category",
                    "operationId": "op_test123456",
                    "timestamp": "2025-06-27T10:43:11Z",
                    "message": "Successfully updated settings"
                }
                
                response = client.post(
                    "/categories/123/ad-recipients/override",
                    json={"confirmOverride": True},
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["affectedRecipients"] == 25
    
    def test_override_missing_confirmation(self, client, mock_user, auth_headers):
        with patch('dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                "/categories/123/ad-recipients/override",
                json={"confirmOverride": False},
                headers=auth_headers
            )
            
            assert response.status_code == 400
            assert "confirmation" in response.json()["detail"].lower()
```

### 2. Frontend Unit Tests

#### React Component Tests

**OverrideSection Component Tests:**
```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import OverrideSection from '../OverrideSection';
import { CategoryOverrideService } from '../../services/CategoryOverrideService';

// Mock the service
jest.mock('../../services/CategoryOverrideService');
const mockService = CategoryOverrideService as jest.Mocked<typeof CategoryOverrideService>;

describe('OverrideSection', () => {
  const defaultProps = {
    categoryId: '123',
    categoryName: 'IT Support',
    hasPermission: true,
    adRecipientsCount: 25
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render override button when user has permission', () => {
    render(<OverrideSection {...defaultProps} />);
    
    const button = screen.getByRole('button', { 
      name: /override settings for 25 ad recipients/i 
    });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  it('should not render override button when user lacks permission', () => {
    render(<OverrideSection {...defaultProps} hasPermission={false} />);
    
    const button = screen.queryByRole('button', { 
      name: /override settings/i 
    });
    expect(button).not.toBeInTheDocument();
  });

  it('should disable button when no AD recipients exist', () => {
    render(<OverrideSection {...defaultProps} adRecipientsCount={0} />);
    
    const button = screen.getByRole('button', { 
      name: /override settings for 0 ad recipients/i 
    });
    expect(button).toBeDisabled();
  });

  it('should open confirmation dialog when button is clicked', async () => {
    render(<OverrideSection {...defaultProps} />);
    
    const button = screen.getByRole('button', { 
      name: /override settings/i 
    });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/confirm override operation/i)).toBeInTheDocument();
    });
  });

  it('should call service when override is confirmed', async () => {
    mockService.overrideAdRecipientSettings.mockResolvedValue({
      success: true,
      affectedRecipients: 25,
      categoryId: '123',
      categoryName: 'IT Support',
      operationId: 'op_test123',
      timestamp: '2025-06-27T10:43:11Z',
      message: 'Success'
    });

    render(<OverrideSection {...defaultProps} />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /override settings/i });
    fireEvent.click(button);
    
    // Confirm override
    const confirmButton = await screen.findByRole('button', { name: /override settings/i });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(mockService.overrideAdRecipientSettings).toHaveBeenCalledWith('123');
    });
  });

  it('should display success message after successful override', async () => {
    mockService.overrideAdRecipientSettings.mockResolvedValue({
      success: true,
      affectedRecipients: 25,
      categoryId: '123',
      categoryName: 'IT Support',
      operationId: 'op_test123',
      timestamp: '2025-06-27T10:43:11Z',
      message: 'Successfully updated settings for 25 AD-synced recipients'
    });

    render(<OverrideSection {...defaultProps} />);
    
    // Trigger override
    const button = screen.getByRole('button', { name: /override settings/i });
    fireEvent.click(button);
    
    const confirmButton = await screen.findByRole('button', { name: /override settings/i });
    fireEvent.click(confirmButton);
    
    // Check success message
    await waitFor(() => {
      expect(screen.getByText(/override completed successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/25 ad-synced recipients/i)).toBeInTheDocument();
    });
  });

  it('should display error message when override fails', async () => {
    mockService.overrideAdRecipientSettings.mockRejectedValue(
      new Error('Override operation failed')
    );

    render(<OverrideSection {...defaultProps} />);
    
    // Trigger override
    const button = screen.getByRole('button', { name: /override settings/i });
    fireEvent.click(button);
    
    const confirmButton = await screen.findByRole('button', { name: /override settings/i });
    fireEvent.click(confirmButton);
    
    // Check error message
    await waitFor(() => {
      expect(screen.getByText(/override operation failed/i)).toBeInTheDocument();
    });
  });
});
```

#### Service Tests

**CategoryOverrideService Tests:**
```typescript
import { CategoryOverrideService } from '../CategoryOverrideService';
import { jest } from '@jest/globals';

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('CategoryOverrideService', () => {
  const service = new CategoryOverrideService();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getAdRecipientsCount', () => {
    it('should return recipients count on success', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          count: 42,
          categoryId: '123',
          categoryName: 'Test Category'
        })
      } as Response);

      const result = await service.getAdRecipientsCount('123');

      expect(result).toBe(42);
      expect(mockFetch).toHaveBeenCalledWith('/api/categories/123/ad-recipients/count');
    });

    it('should throw error on HTTP error response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => 'Category not found'
      } as Response);

      await expect(service.getAdRecipientsCount('123')).rejects.toThrow('Failed to fetch AD recipients count');
    });

    it('should throw error on network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(service.getAdRecipientsCount('123')).rejects.toThrow('Network error');
    });
  });

  describe('overrideAdRecipientSettings', () => {
    it('should return success response', async () => {
      const expectedResponse = {
        success: true,
        affectedRecipients: 25,
        categoryId: '123',
        categoryName: 'Test Category',
        operationId: 'op_test123',
        timestamp: '2025-06-27T10:43:11Z',
        message: 'Success'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => expectedResponse
      } as Response);

      const result = await service.overrideAdRecipientSettings('123');

      expect(result).toEqual(expectedResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/categories/123/ad-recipients/override',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ confirmOverride: true })
        }
      );
    });
  });
});
```

## Integration Testing

### 1. API Integration Tests

**Full API Flow Tests:**
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app

class TestCategoryOverrideIntegration:
    
    @pytest.fixture(scope="class")
    def db_engine(self):
        # Use test database
        engine = create_engine("postgresql://test:test@localhost/test_ehub")
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def db_session(self, db_engine):
        SessionLocal = sessionmaker(bind=db_engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def client(self, db_session):
        def get_test_db():
            return db_session
        
        app.dependency_overrides[get_db] = get_test_db
        return TestClient(app)
    
    @pytest.fixture
    def test_data(self, db_session):
        # Create test category
        category = Category(
            id=123,
            name="Test Category",
            default_settings={"notifications": True, "sms": False}
        )
        db_session.add(category)
        
        # Create test user with permissions
        user = User(
            id=456,
            username="testuser",
            permissions=["category.manage", "category.override.ad.recipients"]
        )
        db_session.add(user)
        
        # Create AD-synced recipients
        for i in range(5):
            recipient = Recipient(
                id=i + 1,
                category_id=123,
                is_ad_synced=True,
                is_active=True,
                email=f"user{i}@example.com"
            )
            db_session.add(recipient)
        
        db_session.commit()
        return {"category": category, "user": user}
    
    def test_full_override_flow(self, client, test_data, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Get initial count
        response = client.get("/api/categories/123/ad-recipients/count", headers=headers)
        assert response.status_code == 200
        assert response.json()["count"] == 5
        
        # 2. Perform override
        response = client.post(
            "/api/categories/123/ad-recipients/override",
            json={"confirmOverride": True},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affectedRecipients"] == 5
        
        # 3. Verify audit log was created
        response = client.get(f"/api/audit/operations/{data['operationId']}", headers=headers)
        assert response.status_code == 200
        audit_data = response.json()
        assert audit_data["operation_status"] == "COMPLETED"
        assert audit_data["affected_recipients_count"] == 5
```

### 2. Database Integration Tests

**Database Transaction Tests:**
```python
class TestDatabaseIntegration:
    
    def test_override_operation_transaction_rollback(self, db_session):
        # Arrange
        category = CategoryFactory(default_settings={"notifications": True})
        recipients = RecipientFactory.create_batch(3, category=category, is_ad_synced=True)
        
        service = CategoryOverrideService(db_session)
        
        # Mock a failure during recipient update
        with patch.object(service, '_update_recipients_settings') as mock_update:
            mock_update.side_effect = Exception("Database error")
            
            # Act & Assert
            with pytest.raises(Exception):
                service.override_ad_recipients_settings(category.id, 1, confirm_override=True)
            
            # Verify rollback - no audit record should exist
            audit_count = db_session.query(CategoryOverrideAudit).count()
            assert audit_count == 0
            
            # Verify recipient settings unchanged
            for recipient in recipients:
                settings = db_session.query(CategoryRecipientSettings).filter_by(
                    recipient_id=recipient.id
                ).first()
                assert settings is None or not settings.is_override_generated
    
    def test_concurrent_override_operations(self, db_session):
        # Test that concurrent overrides don't interfere with each other
        category1 = CategoryFactory(default_settings={"notifications": True})
        category2 = CategoryFactory(default_settings={"sms": True})
        
        recipients1 = RecipientFactory.create_batch(2, category=category1, is_ad_synced=True)
        recipients2 = RecipientFactory.create_batch(3, category=category2, is_ad_synced=True)
        
        service = CategoryOverrideService(db_session)
        
        # Simulate concurrent operations
        import threading
        results = {}
        errors = {}
        
        def override_category(cat_id, result_key):
            try:
                result = service.override_ad_recipients_settings(cat_id, 1, confirm_override=True)
                results[result_key] = result
            except Exception as e:
                errors[result_key] = e
        
        thread1 = threading.Thread(target=override_category, args=(category1.id, 'cat1'))
        thread2 = threading.Thread(target=override_category, args=(category2.id, 'cat2'))
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # Verify both operations succeeded
        assert len(errors) == 0
        assert results['cat1']['affectedRecipients'] == 2
        assert results['cat2']['affectedRecipients'] == 3
```

## End-to-End Testing

### 1. Cypress E2E Tests

**User Journey Tests:**
```typescript
// cypress/integration/category-override.spec.ts

describe('Category Settings Override', () => {
  beforeEach(() => {
    // Setup test data
    cy.task('db:seed', {
      categories: [
        {
          id: 123,
          name: 'IT Support',
          default_settings: { notifications: true, sms: false }
        }
      ],
      users: [
        {
          id: 456,
          username: 'testuser',
          permissions: ['category.manage', 'category.override.ad.recipients']
        }
      ],
      recipients: [
        { id: 1, category_id: 123, is_ad_synced: true, is_active: true },
        { id: 2, category_id: 123, is_ad_synced: true, is_active: true },
        { id: 3, category_id: 123, is_ad_synced: true, is_active: true }
      ]
    });
    
    // Login as authorized user
    cy.login('testuser', 'password');
  });

  it('should complete override operation successfully', () => {
    // Navigate to category settings
    cy.visit('/categories/123/settings');
    
    // Verify override section is visible
    cy.get('[data-testid=override-section]').should('be.visible');
    cy.get('[data-testid=ad-recipients-count]').should('contain', '3');
    
    // Click override button
    cy.get('[data-testid=override-button]').click();
    
    // Verify confirmation dialog
    cy.get('[data-testid=override-confirmation-dialog]').should('be.visible');
    cy.get('[data-testid=affected-recipients-count]').should('contain', '3');
    cy.get('[data-testid=category-name]').should('contain', 'IT Support');
    
    // Confirm override
    cy.get('[data-testid=confirm-override-button]').click();
    
    // Verify loading state
    cy.get('[data-testid=override-progress]').should('be.visible');
    
    // Verify success message
    cy.get('[data-testid=success-alert]', { timeout: 10000 }).should('be.visible');
    cy.get('[data-testid=success-message]').should('contain', 'Override Completed Successfully');
    cy.get('[data-testid=operation-id]').should('exist');
    
    // Verify dialog closed
    cy.get('[data-testid=override-confirmation-dialog]').should('not.exist');
  });

  it('should handle permission errors gracefully', () => {
    // Login as user without permissions
    cy.login('limited_user', 'password');
    
    cy.visit('/categories/123/settings');
    
    // Override section should not be visible
    cy.get('[data-testid=override-section]').should('not.exist');
    
    // Should show permission warning
    cy.get('[data-testid=permission-warning]').should('be.visible');
    cy.get('[data-testid=permission-warning]').should('contain', 'insufficient permissions');
  });

  it('should handle categories with no default settings', () => {
    // Setup category without default settings
    cy.task('db:update', {
      table: 'categories',
      id: 123,
      data: { default_settings: null }
    });
    
    cy.visit('/categories/123/settings');
    
    // Override button should be disabled
    cy.get('[data-testid=override-button]').should('be.disabled');
    
    // Should show configuration warning
    cy.get('[data-testid=no-defaults-warning]').should('be.visible');
    cy.get('[data-testid=no-defaults-warning]').should('contain', 'no default settings');
  });

  it('should handle network errors', () => {
    // Intercept API call and simulate network error
    cy.intercept('POST', '/api/categories/123/ad-recipients/override', {
      forceNetworkError: true
    }).as('overrideRequest');
    
    cy.visit('/categories/123/settings');
    
    // Trigger override
    cy.get('[data-testid=override-button]').click();
    cy.get('[data-testid=confirm-override-button]').click();
    
    cy.wait('@overrideRequest');
    
    // Verify error message
    cy.get('[data-testid=error-alert]').should('be.visible');
    cy.get('[data-testid=error-message]').should('contain', 'network error');
    
    // Verify retry button
    cy.get('[data-testid=retry-button]').should('be.visible');
  });

  it('should support keyboard navigation', () => {
    cy.visit('/categories/123/settings');
    
    // Tab to override button
    cy.get('body').tab();
    cy.focused().should('have.attr', 'data-testid', 'override-button');
    
    // Press Enter to open dialog
    cy.focused().type('{enter}');
    cy.get('[data-testid=override-confirmation-dialog]').should('be.visible');
    
    // Tab to confirm button and activate
    cy.get('[data-testid=confirm-override-button]').focus().type('{enter}');
    
    // Verify operation started
    cy.get('[data-testid=override-progress]').should('be.visible');
    
    // Press Escape to close (after completion)
    cy.get('body').type('{esc}');
  });
});
```

## Performance Testing

### 1. Load Testing

**Artillery Load Test:**
```yaml
# artillery-config.yml
config:
  target: 'https://api.ehub.se'
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: 300
      arrivalRate: 20
      name: "Sustained load"
    - duration: 60
      arrivalRate: 50
      name: "Peak load"
  variables:
    authToken: "Bearer {{ $randomString() }}"

scenarios:
  - name: "Get AD Recipients Count"
    weight: 70
    flow:
      - get:
          url: "/api/categories/{{ $randomInt(1, 100) }}/ad-recipients/count"
          headers:
            Authorization: "{{ authToken }}"
          expect:
            - statusCode: 200
            - hasProperty: "count"

  - name: "Override AD Recipients"
    weight: 30
    flow:
      - post:
          url: "/api/categories/{{ $randomInt(1, 100) }}/ad-recipients/override"
          headers:
            Authorization: "{{ authToken }}"
            Content-Type: "application/json"
          json:
            confirmOverride: true
          expect:
            - statusCode: 200
            - hasProperty: "success"
```

### 2. Stress Testing

**Large Dataset Performance:**
```python
import pytest
import time
from locust import HttpUser, task, between

class CategoryOverrideUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get auth token
        self.auth_token = self.login()
    
    def login(self):
        response = self.client.post("/auth/login", json={
            "username": "testuser",
            "password": "password"
        })
        return response.json()["token"]
    
    @task(3)
    def get_recipients_count(self):
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/api/categories/123/ad-recipients/count", headers=headers)
    
    @task(1)
    def override_recipients(self):
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.post(
            "/api/categories/123/ad-recipients/override",
            json={"confirmOverride": True},
            headers=headers
        )

# Test with large dataset
def test_large_dataset_performance():
    """Test override performance with 10,000 recipients"""
    # Setup test data
    category = CategoryFactory(default_settings={"notifications": True})
    recipients = RecipientFactory.create_batch(10000, category=category, is_ad_synced=True)
    
    service = CategoryOverrideService(db_session)
    
    start_time = time.time()
    result = service.override_ad_recipients_settings(category.id, 1, confirm_override=True)
    end_time = time.time()
    
    duration = end_time - start_time
    
    # Assert performance requirements
    assert result["success"] is True
    assert result["affectedRecipients"] == 10000
    assert duration < 30  # Should complete within 30 seconds
```

## Security Testing

### 1. Authentication/Authorization Tests

```python
class TestSecurityIntegration:
    
    def test_unauthorized_access_blocked(self, client):
        # No auth token
        response = client.get("/api/categories/123/ad-recipients/count")
        assert response.status_code == 401
        
        # Invalid auth token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/categories/123/ad-recipients/count", headers=headers)
        assert response.status_code == 401
    
    def test_insufficient_permissions_blocked(self, client, limited_user_token):
        headers = {"Authorization": f"Bearer {limited_user_token}"}
        
        response = client.post(
            "/api/categories/123/ad-recipients/override",
            json={"confirmOverride": True},
            headers=headers
        )
        assert response.status_code == 403
    
    def test_csrf_protection(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Request without CSRF token should fail
        response = client.post(
            "/api/categories/123/ad-recipients/override",
            json={"confirmOverride": True},
            headers=headers
        )
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]
    
    def test_rate_limiting(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Make requests up to the limit
        for _ in range(5):
            response = client.post(
                "/api/categories/123/ad-recipients/override",
                json={"confirmOverride": True},
                headers=headers
            )
            # Some may succeed, some may fail due to business logic
        
        # The 6th request should be rate limited
        response = client.post(
            "/api/categories/123/ad-recipients/override",
            json={"confirmOverride": True},
            headers=headers
        )
        assert response.status_code == 429
        assert "rate limit" in response.json()["message"].lower()
```

### 2. Input Validation Tests

```python
class TestInputValidation:
    
    def test_sql_injection_prevention(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Attempt SQL injection in category ID
        malicious_id = "123; DROP TABLE recipients; --"
        response = client.get(f"/api/categories/{malicious_id}/ad-recipients/count", headers=headers)
        
        # Should return 404 (not found) or 400 (bad request), not 500 (server error)
        assert response.status_code in [400, 404]
        
        # Verify table still exists (make a normal request)
        response = client.get("/api/categories/123/ad-recipients/count", headers=headers)
        assert response.status_code == 200
    
    def test_xss_prevention(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Attempt XSS in request body
        xss_payload = {"confirmOverride": "<script>alert('xss')</script>"}
        response = client.post(
            "/api/categories/123/ad-recipients/override",
            json=xss_payload,
            headers=headers
        )
        
        assert response.status_code == 400
        # Response should not contain unescaped script tags
        assert "<script>" not in response.text
```

## Accessibility Testing

### 1. Automated Accessibility Tests

```typescript
// cypress/integration/accessibility.spec.ts
import 'cypress-axe';

describe('Accessibility Tests', () => {
  beforeEach(() => {
    cy.visit('/categories/123/settings');
    cy.injectAxe();
  });

  it('should have no accessibility violations on category settings page', () => {
    cy.checkA11y();
  });

  it('should have accessible override section', () => {
    cy.get('[data-testid=override-section]').should('be.visible');
    cy.checkA11y('[data-testid=override-section]');
  });

  it('should have accessible confirmation dialog', () => {
    cy.get('[data-testid=override-button]').click();
    cy.get('[data-testid=override-confirmation-dialog]').should('be.visible');
    cy.checkA11y('[data-testid=override-confirmation-dialog]');
  });

  it('should support keyboard navigation', () => {
    // Test tab navigation
    cy.get('body').tab();
    cy.focused().should('have.attr', 'data-testid', 'override-button');
    
    // Test enter key activation
    cy.focused().type('{enter}');
    cy.get('[data-testid=override-confirmation-dialog]').should('be.visible');
    
    // Test escape key
    cy.get('body').type('{esc}');
    cy.get('[data-testid=override-confirmation-dialog]').should('not.exist');
  });

  it('should have proper ARIA labels', () => {
    cy.get('[data-testid=override-button]')
      .should('have.attr', 'aria-label')
      .and('include', 'Override settings');
    
    cy.get('[data-testid=override-section]')
      .should('have.attr', 'role', 'region')
      .and('have.attr', 'aria-labelledby');
  });
});
```

## User Acceptance Testing

### 1. UAT Test Cases

**Test Case 1: Successful Override Operation**
```
Title: Administrator successfully overrides AD recipient settings
Preconditions:
- User has category management permissions
- Category has default settings configured
- Category has active AD-synced recipients

Steps:
1. Navigate to Category Settings page
2. Verify override section is visible
3. Note the number of AD recipients displayed
4. Click "Override Settings" button
5. Review confirmation dialog details
6. Confirm the override operation
7. Wait for operation completion
8. Verify success message

Expected Results:
- Override section displays current AD recipient count
- Confirmation dialog shows correct details
- Operation completes successfully
- Success message shows operation details
- Category statistics are updated
```

**Test Case 2: Permission Denied Scenario**
```
Title: User without permissions cannot access override functionality
Preconditions:
- User does not have category management permissions
- Category exists with AD recipients

Steps:
1. Navigate to Category Settings page
2. Look for override section

Expected Results:
- Override section is not visible
- Appropriate permission warning is displayed
```

### 2. UAT Checklist

**Functional Requirements:**
- [ ] Override operation updates all AD-synced recipients
- [ ] Non-AD recipients are not affected
- [ ] Individual settings are replaced with category defaults
- [ ] Operation requires explicit confirmation
- [ ] Progress indication during operation
- [ ] Success/error feedback provided
- [ ] Operation is properly audited

**Usability Requirements:**
- [ ] Clear visual distinction of override section
- [ ] Intuitive button labeling and placement
- [ ] Comprehensive confirmation dialog
- [ ] Easy-to-understand warning messages
- [ ] Responsive design on all devices
- [ ] Keyboard navigation support

**Security Requirements:**
- [ ] Permission checks are enforced
- [ ] Unauthorized access is blocked
- [ ] Audit logs capture all operations
- [ ] Rate limiting prevents abuse
- [ ] Input validation prevents injection

## Test Data Management

### 1. Test Data Setup

```python
# test_data_factory.py
import factory
from models import Category, Recipient, User, CategoryRecipientSettings

class CategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Faker('company')
    default_settings = factory.LazyFunction(lambda: {
        "notifications": True,
        "sms": False,
        "escalation_hours": 2
    })

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    username = factory.Faker('user_name')
    email = factory.Faker('email')
    permissions = factory.LazyFunction(lambda: ['category.manage'])

class RecipientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Recipient
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Faker('email')
    is_ad_synced = True
    is_active = True
    category = factory.SubFactory(CategoryFactory)

# Test data scenarios
def create_override_test_scenario():
    """Create a complete test scenario for override testing"""
    category = CategoryFactory(
        name="IT Support",
        default_settings={
            "notifications": True,
            "sms": False,
            "escalation_hours": 2
        }
    )
    
    user = UserFactory(
        username="admin_user",
        permissions=["category.manage", "category.override.ad.recipients"]
    )
    
    # Create mix of AD and non-AD recipients
    ad_recipients = RecipientFactory.create_batch(5, category=category, is_ad_synced=True)
    non_ad_recipients = RecipientFactory.create_batch(3, category=category, is_ad_synced=False)
    
    return {
        "category": category,
        "user": user,
        "ad_recipients": ad_recipients,
        "non_ad_recipients": non_ad_recipients
    }
```

### 2. Test Environment Setup

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-db:
    image: postgres:13
    environment:
      POSTGRES_DB: test_ehub
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    volumes:
      - ./test-data:/docker-entrypoint-initdb.d

  test-api:
    build: .
    environment:
      DATABASE_URL: postgresql://test:test@test-db:5432/test_ehub
      JWT_SECRET: test_secret
      RATE_LIMIT_ENABLED: true
    depends_on:
      - test-db
    ports:
      - "8001:8000"
```

## Continuous Integration

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/test-category-override.yml
name: Category Override Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_ehub
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run unit tests
      run: |
        pytest tests/unit/test_category_override.py -v --cov=services/category_override_service
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up test environment
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # Wait for services to be ready
    
    - name: Run integration tests
      run: |
        pytest tests/integration/test_category_override_api.py -v
    
    - name: Cleanup
      run: |
        docker-compose -f docker-compose.test.yml down

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '16'
    
    - name: Install Cypress
      run: npm install cypress --save-dev
    
    - name: Run E2E tests
      run: |
        npm run cy:run
      env:
        CYPRESS_baseUrl: http://localhost:3000
```

## Implementation Checklist

### Test Development
- [ ] Write unit tests for all service methods
- [ ] Create component tests for React components
- [ ] Implement API integration tests
- [ ] Set up E2E test scenarios
- [ ] Create performance test suite
- [ ] Implement security test cases
- [ ] Add accessibility test coverage

### Test Infrastructure
- [ ] Set up test databases
- [ ] Configure CI/CD pipelines
- [ ] Create test data factories
- [ ] Set up test environment automation
- [ ] Implement test reporting
- [ ] Configure code coverage tracking

### Test Execution
- [ ] Run all test suites locally
- [ ] Verify CI/CD pipeline execution
- [ ] Perform manual UAT scenarios
- [ ] Execute performance test suite
- [ ] Run security penetration tests
- [ ] Validate accessibility compliance

### Documentation
- [ ] Document test procedures
- [ ] Create test data setup guides
- [ ] Write troubleshooting guides
- [ ] Document test environment setup
- [ ] Create UAT test scripts
- [ ] Maintain test coverage reports