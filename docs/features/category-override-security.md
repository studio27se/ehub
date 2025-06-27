# Security Requirements - Category Settings Override

## Overview
This document defines the security requirements and implementation guidelines for the category settings override functionality.

## Security Principles

### 1. Principle of Least Privilege
- Users can only override settings for categories they have explicit management permissions for
- Override functionality is only accessible to users with category management roles
- Administrative actions require elevated permissions

### 2. Defense in Depth
- Multiple layers of authorization checks
- Input validation at multiple levels
- Audit logging for all operations
- Rate limiting to prevent abuse

### 3. Fail Secure
- Default to denying access when permissions are unclear
- Graceful degradation when security checks fail
- Clear error messages without exposing sensitive information

## Authentication Requirements

### 1. User Authentication
**Requirement:** All API requests must include valid authentication tokens

**Implementation:**
```typescript
// JWT token validation
interface AuthToken {
  userId: number;
  username: string;
  roles: string[];
  permissions: string[];
  exp: number;
  iat: number;
}

// Token validation middleware
const validateAuthToken = (token: string): AuthToken => {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET) as AuthToken;
    
    if (decoded.exp < Date.now() / 1000) {
      throw new Error('Token expired');
    }
    
    return decoded;
  } catch (error) {
    throw new AuthenticationError('Invalid or expired token');
  }
};
```

### 2. Session Management
**Requirements:**
- Session timeout after 8 hours of inactivity
- Concurrent session limits (max 3 sessions per user)
- Session invalidation on permission changes

**Implementation:**
```typescript
// Session validation
const validateSession = async (userId: number, sessionId: string): Promise<boolean> => {
  const session = await SessionStore.get(sessionId);
  
  if (!session || session.userId !== userId) {
    return false;
  }
  
  if (session.lastActivity < Date.now() - SESSION_TIMEOUT) {
    await SessionStore.invalidate(sessionId);
    return false;
  }
  
  // Update last activity
  await SessionStore.updateActivity(sessionId);
  return true;
};
```

## Authorization Requirements

### 1. Permission Model

**Required Permissions:**
- `category.manage` - Basic category management
- `category.override.ad.recipients` - Override AD recipient settings
- `category.audit.view` - View override audit logs

**Permission Hierarchy:**
```
category.admin (includes all below)
├── category.manage
├── category.override.ad.recipients  
├── category.audit.view
└── category.settings.modify
```

### 2. Role-Based Access Control (RBAC)

**Roles:**
```typescript
interface Role {
  id: string;
  name: string;
  permissions: string[];
  categoryAccess: 'all' | 'assigned' | 'none';
}

const ROLES = {
  SYSTEM_ADMIN: {
    id: 'system_admin',
    name: 'System Administrator',
    permissions: ['category.admin', 'category.override.ad.recipients'],
    categoryAccess: 'all'
  },
  CATEGORY_MANAGER: {
    id: 'category_manager', 
    name: 'Category Manager',
    permissions: ['category.manage', 'category.override.ad.recipients'],
    categoryAccess: 'assigned'
  },
  CATEGORY_VIEWER: {
    id: 'category_viewer',
    name: 'Category Viewer', 
    permissions: ['category.audit.view'],
    categoryAccess: 'assigned'
  }
};
```

### 3. Category-Level Permissions

**Implementation:**
```typescript
const checkCategoryAccess = async (
  userId: number, 
  categoryId: number, 
  requiredPermission: string
): Promise<boolean> => {
  // Get user roles and permissions
  const userRoles = await getUserRoles(userId);
  const userPermissions = await getUserPermissions(userId);
  
  // Check if user has required permission
  if (!userPermissions.includes(requiredPermission)) {
    auditLog('ACCESS_DENIED', {
      userId,
      categoryId,
      requiredPermission,
      reason: 'Missing permission'
    });
    return false;
  }
  
  // Check category-specific access
  const hasAccess = await checkUserCategoryAccess(userId, categoryId);
  if (!hasAccess) {
    auditLog('ACCESS_DENIED', {
      userId,
      categoryId,
      requiredPermission,
      reason: 'No category access'
    });
    return false;
  }
  
  return true;
};
```

## Input Validation and Sanitization

### 1. API Input Validation

**Schema Validation:**
```typescript
import Joi from 'joi';

const overrideRequestSchema = Joi.object({
  confirmOverride: Joi.boolean().valid(true).required(),
  categoryId: Joi.number().integer().positive().required()
});

const validateOverrideRequest = (data: any): ValidationResult => {
  const { error, value } = overrideRequestSchema.validate(data);
  
  if (error) {
    throw new ValidationError('Invalid request data', error.details);
  }
  
  return value;
};
```

### 2. SQL Injection Prevention

**Parameterized Queries:**
```python
# Correct - Using parameterized queries
def get_ad_recipients_count(category_id: int) -> int:
    query = """
        SELECT COUNT(*) 
        FROM recipients 
        WHERE category_id = %s 
        AND is_ad_synced = TRUE 
        AND is_active = TRUE
    """
    return db.execute(query, (category_id,)).fetchone()[0]

# Incorrect - Vulnerable to SQL injection
def get_ad_recipients_count_vulnerable(category_id: str) -> int:
    query = f"""
        SELECT COUNT(*) 
        FROM recipients 
        WHERE category_id = {category_id}
    """
    # DON'T DO THIS - SQL injection vulnerability
```

### 3. Data Sanitization

**Output Encoding:**
```typescript
const sanitizeOutput = (data: any): any => {
  if (typeof data === 'string') {
    return escapeHtml(data);
  }
  
  if (Array.isArray(data)) {
    return data.map(sanitizeOutput);
  }
  
  if (typeof data === 'object' && data !== null) {
    const sanitized: any = {};
    for (const [key, value] of Object.entries(data)) {
      sanitized[key] = sanitizeOutput(value);
    }
    return sanitized;
  }
  
  return data;
};
```

## Audit Logging and Monitoring

### 1. Audit Requirements

**Events to Log:**
- All override operations (success and failure)
- Permission checks and access denials
- Authentication attempts
- Session management events
- Configuration changes

**Audit Log Format:**
```typescript
interface AuditEvent {
  eventId: string;
  timestamp: Date;
  userId: number;
  username: string;
  action: string;
  resource: string;
  resourceId: string;
  result: 'SUCCESS' | 'FAILURE' | 'DENIED';
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  sessionId: string;
}
```

### 2. Audit Implementation

```typescript
const auditLogger = {
  logOverrideOperation(
    userId: number,
    categoryId: number,
    result: 'SUCCESS' | 'FAILURE',
    details: any,
    context: RequestContext
  ) {
    const event: AuditEvent = {
      eventId: generateUuid(),
      timestamp: new Date(),
      userId,
      username: context.user.username,
      action: 'CATEGORY_OVERRIDE',
      resource: 'category',
      resourceId: categoryId.toString(),
      result,
      details: {
        categoryName: details.categoryName,
        affectedRecipients: details.affectedRecipients,
        operationId: details.operationId,
        ...details
      },
      ipAddress: context.ipAddress,
      userAgent: context.userAgent,
      sessionId: context.sessionId
    };
    
    // Store in audit database
    auditDatabase.insert(event);
    
    // Send to security monitoring system
    securityMonitor.send(event);
  }
};
```

### 3. Real-time Monitoring

**Security Alerts:**
```typescript
const securityMonitor = {
  // Monitor for suspicious patterns
  checkSuspiciousActivity(event: AuditEvent) {
    // Multiple failed attempts
    if (this.countFailedAttempts(event.userId, '5m') > 5) {
      this.triggerAlert('MULTIPLE_FAILED_ATTEMPTS', event);
    }
    
    // Unusual activity patterns
    if (this.isUnusualActivity(event)) {
      this.triggerAlert('UNUSUAL_ACTIVITY', event);
    }
    
    // Privilege escalation attempts
    if (this.isPrivilegeEscalation(event)) {
      this.triggerAlert('PRIVILEGE_ESCALATION', event);
    }
  },
  
  triggerAlert(type: string, event: AuditEvent) {
    // Send to security team
    alertingService.sendSecurityAlert({
      type,
      severity: this.getSeverity(type),
      event,
      timestamp: new Date()
    });
  }
};
```

## Rate Limiting and Abuse Prevention

### 1. API Rate Limiting

**Implementation:**
```typescript
import rateLimit from 'express-rate-limit';

// Override operation rate limiting
const overrideRateLimit = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 5, // 5 requests per minute
  message: {
    error: 'RATE_LIMIT_EXCEEDED',
    message: 'Too many override requests. Please wait before trying again.',
    retryAfter: 60
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => `override:${req.user.id}`,
  handler: (req, res) => {
    auditLogger.logRateLimitExceeded(req.user.id, 'OVERRIDE_OPERATION', req.ip);
    res.status(429).json(req.rateLimit.message);
  }
});

// Apply to override endpoints
app.use('/api/categories/:id/override', overrideRateLimit);
```

### 2. Distributed Rate Limiting

**Redis Implementation:**
```typescript
class DistributedRateLimiter {
  private redis: Redis;
  
  async checkLimit(
    key: string, 
    limit: number, 
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number; resetTime: number }> {
    const multi = this.redis.multi();
    const now = Date.now();
    const window = windowSeconds * 1000;
    const windowStart = now - window;
    
    // Remove old entries
    multi.zremrangebyscore(key, 0, windowStart);
    
    // Count current requests
    multi.zcard(key);
    
    // Add current request
    multi.zadd(key, now, `${now}-${Math.random()}`);
    
    // Set expiration
    multi.expire(key, windowSeconds);
    
    const results = await multi.exec();
    const currentCount = results[1][1] as number;
    
    return {
      allowed: currentCount < limit,
      remaining: Math.max(0, limit - currentCount - 1),
      resetTime: now + window
    };
  }
}
```

## Data Protection and Privacy

### 1. Data Minimization

**Principles:**
- Only collect necessary data for override operations
- Don't expose individual recipient details in responses
- Limit audit data retention to compliance requirements

**Implementation:**
```typescript
// Good - Minimal data exposure
interface OverrideResponse {
  success: boolean;
  affectedRecipients: number; // Count only
  categoryId: string;
  operationId: string;
  timestamp: string;
}

// Bad - Exposing sensitive data
interface BadOverrideResponse {
  success: boolean;
  recipients: {
    id: number;
    email: string; // PII exposure
    phone: string; // PII exposure
    settings: any;
  }[];
}
```

### 2. Data Encryption

**At Rest:**
```sql
-- Encrypt sensitive fields in audit logs
CREATE TABLE category_override_audit (
    id BIGSERIAL PRIMARY KEY,
    operation_id VARCHAR(50) NOT NULL,
    category_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    user_details_encrypted BYTEA, -- Encrypted user details
    operation_details_encrypted BYTEA, -- Encrypted operation details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**In Transit:**
- Enforce HTTPS/TLS 1.3 for all API communication
- Certificate pinning for critical endpoints
- HSTS headers to prevent downgrade attacks

### 3. GDPR Compliance

**Right to Erasure:**
```typescript
const handleDataDeletionRequest = async (userId: number) => {
  // Anonymize audit logs instead of deletion for compliance
  await db.query(`
    UPDATE category_override_audit 
    SET user_details_encrypted = NULL,
        user_id = NULL,
        user_name = 'DELETED_USER'
    WHERE user_id = $1
  `, [userId]);
  
  // Maintain operation integrity while removing PII
  auditLogger.logDataDeletion(userId, 'GDPR_ERASURE');
};
```

## Security Headers and CSRF Protection

### 1. Security Headers

```typescript
app.use((req, res, next) => {
  // Content Security Policy
  res.setHeader('Content-Security-Policy', 
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
  );
  
  // Prevent XSS
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  
  // HSTS
  res.setHeader('Strict-Transport-Security', 
    'max-age=31536000; includeSubDomains; preload'
  );
  
  // Prevent information disclosure
  res.removeHeader('X-Powered-By');
  
  next();
});
```

### 2. CSRF Protection

```typescript
import csrf from 'csurf';

// CSRF protection for state-changing operations
const csrfProtection = csrf({
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict'
  }
});

// Apply CSRF protection to override endpoints
app.use('/api/categories/:id/override', csrfProtection);
```

## Incident Response

### 1. Security Incident Detection

**Automated Detection:**
```typescript
const detectSecurityIncidents = {
  // Detect multiple failed override attempts
  detectBruteForce(userId: number) {
    const failedAttempts = this.getFailedAttempts(userId, '15m');
    if (failedAttempts >= 10) {
      return {
        type: 'BRUTE_FORCE_ATTACK',
        severity: 'HIGH',
        userId,
        description: `${failedAttempts} failed override attempts in 15 minutes`
      };
    }
  },
  
  // Detect privilege escalation attempts
  detectPrivilegeEscalation(event: AuditEvent) {
    if (event.result === 'DENIED' && event.action === 'CATEGORY_OVERRIDE') {
      return {
        type: 'PRIVILEGE_ESCALATION',
        severity: 'MEDIUM',
        userId: event.userId,
        description: 'Attempted override without sufficient permissions'
      };
    }
  }
};
```

### 2. Incident Response Procedures

**Automated Response:**
```typescript
const incidentResponse = {
  handleSecurityIncident(incident: SecurityIncident) {
    switch (incident.type) {
      case 'BRUTE_FORCE_ATTACK':
        this.temporarilyLockUser(incident.userId, '30m');
        this.notifySecurityTeam(incident);
        break;
        
      case 'PRIVILEGE_ESCALATION':
        this.flagUserForReview(incident.userId);
        this.notifySecurityTeam(incident);
        break;
        
      case 'SUSPICIOUS_ACTIVITY':
        this.requireAdditionalAuth(incident.userId);
        this.notifySecurityTeam(incident);
        break;
    }
  }
};
```

## Security Testing Requirements

### 1. Penetration Testing

**Test Scenarios:**
- Authentication bypass attempts
- Authorization escalation attacks
- SQL injection testing
- XSS/CSRF vulnerability testing
- Rate limiting bypass attempts

### 2. Security Automation

**Static Analysis:**
```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run SAST scan
        uses: github/super-linter@v4
        env:
          VALIDATE_TYPESCRIPT_ES: true
          VALIDATE_JAVASCRIPT_ES: true
          
      - name: Run dependency check
        run: npm audit --audit-level high
        
      - name: Run CodeQL analysis
        uses: github/codeql-action/analyze@v2
```

## Compliance Requirements

### 1. SOC 2 Type II

**Control Requirements:**
- Access controls for system operations
- Change management procedures
- Monitoring and logging of system activity
- Data backup and recovery procedures

### 2. ISO 27001

**Security Controls:**
- A.9.1 Business requirements for access control
- A.9.2 User access management
- A.12.4 Logging and monitoring
- A.14.2 Security in development and support processes

## Implementation Checklist

### Development Phase
- [ ] Implement authentication middleware
- [ ] Add authorization checks
- [ ] Create audit logging system
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Configure security headers
- [ ] Set up CSRF protection

### Testing Phase
- [ ] Security penetration testing
- [ ] Authentication/authorization testing
- [ ] Input validation testing
- [ ] Rate limiting testing
- [ ] Audit logging verification
- [ ] OWASP ZAP scanning

### Deployment Phase
- [ ] Security configuration review
- [ ] SSL/TLS certificate installation
- [ ] Security monitoring setup
- [ ] Incident response procedures
- [ ] Security documentation
- [ ] Staff security training

### Ongoing Maintenance
- [ ] Regular security assessments
- [ ] Dependency vulnerability scanning
- [ ] Audit log review procedures
- [ ] Incident response plan updates
- [ ] Security awareness training
- [ ] Compliance audits