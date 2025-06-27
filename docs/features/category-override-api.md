# API Specification - Category Settings Override

## Overview
This document defines the REST API specifications for the category settings override functionality.

## Base URL
```
https://api.ehub.se/v2
```

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer {jwt_token}
```

## Endpoints

### 1. Get AD Recipients Count

**Endpoint:** `GET /categories/{categoryId}/ad-recipients/count`

**Description:** Retrieve the number of AD-synced recipients for a specific category.

**Parameters:**
- `categoryId` (path, required): Category identifier

**Request Example:**
```http
GET /categories/123/ad-recipients/count HTTP/1.1
Host: api.ehub.se
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response Schema:**
```json
{
  "count": {
    "type": "integer",
    "description": "Number of AD-synced recipients",
    "minimum": 0
  },
  "categoryId": {
    "type": "string",
    "description": "Category identifier"
  },
  "categoryName": {
    "type": "string",
    "description": "Human-readable category name"
  }
}
```

**Response Examples:**

Success (200):
```json
{
  "count": 45,
  "categoryId": "123",
  "categoryName": "IT Support"
}
```

Not Found (404):
```json
{
  "error": "NOT_FOUND",
  "message": "Category not found",
  "categoryId": "123"
}
```

Forbidden (403):
```json
{
  "error": "FORBIDDEN",
  "message": "Insufficient permissions to access this category",
  "requiredPermission": "category.manage"
}
```

### 2. Override AD Recipients Settings

**Endpoint:** `POST /categories/{categoryId}/ad-recipients/override`

**Description:** Override all AD-synced recipients' settings with category default settings.

**Parameters:**
- `categoryId` (path, required): Category identifier

**Request Schema:**
```json
{
  "confirmOverride": {
    "type": "boolean",
    "description": "Explicit confirmation that user wants to proceed",
    "const": true
  }
}
```

**Request Example:**
```http
POST /categories/123/ad-recipients/override HTTP/1.1
Host: api.ehub.se
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "confirmOverride": true
}
```

**Response Schema:**
```json
{
  "success": {
    "type": "boolean",
    "description": "Operation success status"
  },
  "affectedRecipients": {
    "type": "integer",
    "description": "Number of recipients updated",
    "minimum": 0
  },
  "categoryId": {
    "type": "string",
    "description": "Category identifier"
  },
  "categoryName": {
    "type": "string",
    "description": "Human-readable category name"
  },
  "operationId": {
    "type": "string",
    "description": "Unique operation identifier for tracking",
    "pattern": "^op_[a-f0-9]{12}$"
  },
  "timestamp": {
    "type": "string",
    "format": "date-time",
    "description": "Operation completion timestamp (ISO 8601)"
  },
  "message": {
    "type": "string",
    "description": "Human-readable operation result message"
  }
}
```

**Response Examples:**

Success (200):
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

Bad Request - Missing Confirmation (400):
```json
{
  "error": "BAD_REQUEST",
  "message": "Override confirmation is required",
  "field": "confirmOverride",
  "expectedValue": true
}
```

Conflict - No Default Settings (409):
```json
{
  "error": "CONFLICT",
  "message": "Category has no default settings configured",
  "categoryId": "123",
  "categoryName": "IT Support"
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "type": "string",
    "description": "Error type code",
    "enum": ["BAD_REQUEST", "UNAUTHORIZED", "FORBIDDEN", "NOT_FOUND", "CONFLICT", "INTERNAL_SERVER_ERROR"]
  },
  "message": {
    "type": "string",
    "description": "Human-readable error message"
  },
  "details": {
    "type": "object",
    "description": "Additional error context (optional)"
  },
  "timestamp": {
    "type": "string",
    "format": "date-time",
    "description": "Error occurrence timestamp"
  },
  "requestId": {
    "type": "string",
    "description": "Unique request identifier for debugging"
  }
}
```

### HTTP Status Codes

| Status Code | Description | Usage |
|-------------|-------------|-------|
| 200 | OK | Successful operation |
| 400 | Bad Request | Invalid request data or missing confirmation |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | User lacks required permissions |
| 404 | Not Found | Category does not exist |
| 409 | Conflict | Category lacks default settings or other business rule conflict |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

## Rate Limiting

### Limits
- **Override Operations**: 5 requests per minute per user
- **Count Queries**: 60 requests per minute per user

### Rate Limit Headers
```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1672531200
```

### Rate Limit Exceeded Response (429)
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many override requests. Please wait before trying again.",
  "retryAfter": 45,
  "limit": 5,
  "window": "1 minute"
}
```

## Data Validation

### Request Validation Rules

#### confirmOverride field
- Required for override operations
- Must be explicitly set to `true`
- Boolean type only

#### categoryId parameter
- Must be a valid integer
- Must exist in the system
- User must have access to the category

### Response Data Validation

#### operationId format
- Pattern: `op_[a-f0-9]{12}`
- Example: `op_abc123def456`

#### timestamp format
- ISO 8601 format with timezone
- Example: `2025-06-27T10:43:11Z`

## Security Considerations

### Permission Requirements
- User must have `category.manage` permission for the specific category
- Permission is verified before any operation

### Audit Logging
All operations are logged with:
- User ID and username
- Category ID and name
- Operation timestamp
- Number of affected recipients
- Operation result (success/failure)
- IP address and user agent

### Data Protection
- No sensitive recipient data is exposed in API responses
- Only aggregate counts are returned
- Individual recipient identifiers are not included

## Pagination

For future extensions, if recipient lists are needed:

### Query Parameters
```
?page=1&limit=50&sort=name&order=asc
```

### Pagination Response Format
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "pages": 3,
    "hasNext": true,
    "hasPrev": false
  }
}
```

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: eHUB Category Override API
  description: API for overriding AD-synced recipient category settings
  version: 1.0.0
  contact:
    name: eHUB API Support
    email: api-support@ehub.se

servers:
  - url: https://api.ehub.se/v2
    description: Production server
  - url: https://api-staging.ehub.se/v2
    description: Staging server

security:
  - BearerAuth: []

paths:
  /categories/{categoryId}/ad-recipients/count:
    get:
      summary: Get AD recipients count
      description: Retrieve the number of AD-synced recipients for a category
      operationId: getAdRecipientsCount
      tags:
        - Category Override
      parameters:
        - name: categoryId
          in: path
          required: true
          schema:
            type: integer
            minimum: 1
          description: Category identifier
      responses:
        '200':
          description: Successfully retrieved count
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CountResponse'
        '403':
          description: Insufficient permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: Category not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /categories/{categoryId}/ad-recipients/override:
    post:
      summary: Override AD recipients settings
      description: Override all AD-synced recipients' settings with category defaults
      operationId: overrideAdRecipientsSettings
      tags:
        - Category Override
      parameters:
        - name: categoryId
          in: path
          required: true
          schema:
            type: integer
            minimum: 1
          description: Category identifier
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OverrideRequest'
      responses:
        '200':
          description: Override operation completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OverrideResponse'
        '400':
          description: Bad request or missing confirmation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '403':
          description: Insufficient permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: Category not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '409':
          description: Category has no default settings
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    CountResponse:
      type: object
      required:
        - count
        - categoryId
        - categoryName
      properties:
        count:
          type: integer
          minimum: 0
          description: Number of AD-synced recipients
        categoryId:
          type: string
          description: Category identifier
        categoryName:
          type: string
          description: Human-readable category name

    OverrideRequest:
      type: object
      required:
        - confirmOverride
      properties:
        confirmOverride:
          type: boolean
          const: true
          description: Explicit confirmation required

    OverrideResponse:
      type: object
      required:
        - success
        - affectedRecipients
        - categoryId
        - categoryName
        - operationId
        - timestamp
        - message
      properties:
        success:
          type: boolean
          description: Operation success status
        affectedRecipients:
          type: integer
          minimum: 0
          description: Number of recipients updated
        categoryId:
          type: string
          description: Category identifier
        categoryName:
          type: string
          description: Human-readable category name
        operationId:
          type: string
          pattern: '^op_[a-f0-9]{12}$'
          description: Unique operation identifier
        timestamp:
          type: string
          format: date-time
          description: Operation completion timestamp
        message:
          type: string
          description: Human-readable result message

    ErrorResponse:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
          enum:
            - BAD_REQUEST
            - UNAUTHORIZED
            - FORBIDDEN
            - NOT_FOUND
            - CONFLICT
            - RATE_LIMIT_EXCEEDED
            - INTERNAL_SERVER_ERROR
          description: Error type code
        message:
          type: string
          description: Human-readable error message
        details:
          type: object
          description: Additional error context
        timestamp:
          type: string
          format: date-time
          description: Error occurrence timestamp
        requestId:
          type: string
          description: Unique request identifier

tags:
  - name: Category Override
    description: Operations for overriding AD-synced recipient settings
```

## Usage Examples

### JavaScript/TypeScript

```typescript
interface OverrideApiClient {
  async getAdRecipientsCount(categoryId: number): Promise<CountResponse> {
    const response = await fetch(`/api/categories/${categoryId}/ad-recipients/count`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }
    
    return response.json();
  }

  async overrideAdRecipients(categoryId: number): Promise<OverrideResponse> {
    const response = await fetch(`/api/categories/${categoryId}/ad-recipients/override`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ confirmOverride: true })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }
    
    return response.json();
  }
}
```

### cURL Examples

Get AD recipients count:
```bash
curl -X GET "https://api.ehub.se/v2/categories/123/ad-recipients/count" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

Override AD recipients settings:
```bash
curl -X POST "https://api.ehub.se/v2/categories/123/ad-recipients/override" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"confirmOverride": true}'
```

## Testing

### Test Data Requirements
- Categories with and without default settings
- AD-synced and non-AD-synced recipients
- Users with various permission levels

### Mock Responses for Testing

```json
// Success responses for automated testing
{
  "getAdRecipientsCount": {
    "count": 25,
    "categoryId": "456",
    "categoryName": "Test Category"
  },
  "overrideSuccess": {
    "success": true,
    "affectedRecipients": 25,
    "categoryId": "456", 
    "categoryName": "Test Category",
    "operationId": "op_test123456",
    "timestamp": "2025-06-27T10:43:11Z",
    "message": "Successfully updated settings for 25 AD-synced recipients"
  }
}
```

## Monitoring and Metrics

### Key Metrics to Track
- API response times (p50, p95, p99)
- Success/error rates by endpoint
- Override operation frequency
- Number of recipients affected per operation
- User permission errors

### Health Check Endpoint
```
GET /health/category-override
```

Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "permissions": "ok",
    "audit_logging": "ok"
  },
  "timestamp": "2025-06-27T10:43:11Z"
}
```