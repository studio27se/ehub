# Deployment Considerations - Category Settings Override

## Overview
This document outlines the deployment strategy, infrastructure requirements, and operational considerations for the category settings override feature.

## Deployment Strategy

### 1. Phased Rollout Plan

**Phase 1: Infrastructure Preparation**
- Database schema deployment
- Backend API deployment to staging
- Configuration updates
- Monitoring setup

**Phase 2: Backend Deployment**
- Production API deployment
- Permission system updates
- Audit logging activation
- Security measures implementation

**Phase 3: Frontend Deployment**
- UI component deployment
- Feature flag activation
- User permission verification
- Integration testing

**Phase 4: Full Release**
- Feature flag removal
- User training and documentation
- Performance monitoring
- Feedback collection

### 2. Deployment Timeline

```
Week 1: Infrastructure and Database
├── Database migration scripts
├── Monitoring setup
├── Security configuration
└── Staging environment preparation

Week 2: Backend Implementation
├── API deployment to staging
├── Permission system integration
├── Audit logging implementation
└── Security testing

Week 3: Frontend Implementation  
├── UI component deployment
├── Integration with backend APIs
├── User acceptance testing
└── Accessibility verification

Week 4: Production Deployment
├── Production deployment
├── Feature flag management
├── User training
└── Performance monitoring
```

## Infrastructure Requirements

### 1. Database Requirements

**Storage:**
- Additional 500MB for audit tables (estimated for 100,000 operations/year)
- Partitioning strategy for audit tables
- Index storage overhead (~200MB)

**Performance:**
- Database connection pool increase (+10 connections)
- Query optimization for batch operations
- Automated maintenance for audit data cleanup

**Backup:**
- Extended backup retention for audit data (7 years)
- Point-in-time recovery capability
- Cross-region backup replication

### 2. Application Server Requirements

**Memory:**
- Additional 256MB heap space for batch processing
- Redis cache for rate limiting (50MB)
- Session storage for concurrent operations

**CPU:**
- Peak load handling for batch operations
- Background task processing capability
- Monitoring and alerting overhead

**Storage:**
- Application logs (~100MB/month)
- Temporary file storage for large operations
- Configuration file storage

### 3. Network and Security

**Load Balancer Configuration:**
```nginx
# nginx.conf additions
location /api/categories/*/ad-recipients/override {
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_buffering off;
    
    # Rate limiting
    limit_req zone=override_rate_limit burst=5 nodelay;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
}
```

**Firewall Rules:**
- API endpoint access restrictions
- Database connection limits
- Monitoring endpoint security

## Configuration Management

### 1. Environment Variables

**Production Configuration:**
```bash
# Category Override Feature Settings
CATEGORY_OVERRIDE_ENABLED=true
CATEGORY_OVERRIDE_BATCH_SIZE=100
CATEGORY_OVERRIDE_MAX_RECIPIENTS=10000
CATEGORY_OVERRIDE_TIMEOUT_SECONDS=300
CATEGORY_OVERRIDE_RATE_LIMIT_PER_MINUTE=5
CATEGORY_OVERRIDE_AUDIT_RETENTION_DAYS=2555  # 7 years

# Database Settings
AUDIT_TABLE_PARTITIONING=true
AUDIT_CLEANUP_ENABLED=true
AUDIT_CLEANUP_SCHEDULE="0 2 * * 0"  # Weekly on Sunday 2 AM

# Security Settings
CSRF_PROTECTION_ENABLED=true
SECURITY_HEADERS_ENABLED=true
RATE_LIMITING_ENABLED=true

# Monitoring Settings
METRICS_ENABLED=true
AUDIT_ALERTS_ENABLED=true
PERFORMANCE_MONITORING=true
```

**Staging Configuration:**
```bash
# Reduced limits for testing
CATEGORY_OVERRIDE_BATCH_SIZE=10
CATEGORY_OVERRIDE_MAX_RECIPIENTS=1000
CATEGORY_OVERRIDE_TIMEOUT_SECONDS=60
AUDIT_RETENTION_DAYS=30
```

### 2. Feature Flags

**Implementation:**
```typescript
// Feature flag configuration
export const FEATURE_FLAGS = {
  CATEGORY_OVERRIDE_ENABLED: {
    default: false,
    environments: {
      development: true,
      staging: true,
      production: false  // Initially disabled
    }
  },
  CATEGORY_OVERRIDE_UI_ENABLED: {
    default: false,
    roles: ['admin', 'category_manager'],
    permissions: ['category.override.ad.recipients']
  }
};

// Usage in components
const isOverrideEnabled = useFeatureFlag('CATEGORY_OVERRIDE_ENABLED');
const hasUIAccess = useFeatureFlag('CATEGORY_OVERRIDE_UI_ENABLED');
```

## Database Migration Strategy

### 1. Migration Scripts

**Migration Sequence:**
```sql
-- V1.0__Create_override_audit_table.sql
CREATE TABLE category_override_audit (
    -- Table definition
);

-- V1.1__Create_override_operations_table.sql  
CREATE TABLE category_override_operations (
    -- Table definition
);

-- V1.2__Add_override_columns.sql
ALTER TABLE category_recipient_settings 
ADD COLUMN updated_by_operation VARCHAR(50);

-- V1.3__Create_indexes.sql
CREATE INDEX idx_category_override_audit_category_id 
ON category_override_audit(category_id);

-- V1.4__Create_functions.sql
CREATE OR REPLACE FUNCTION update_category_override_stats()
RETURNS TRIGGER AS $$
-- Function definition
$$;
```

### 2. Migration Validation

**Pre-migration Checks:**
```sql
-- Check current database size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check for conflicting data
SELECT COUNT(*) FROM categories WHERE default_settings IS NULL;
SELECT COUNT(*) FROM recipients WHERE is_ad_synced IS NULL;
```

**Post-migration Validation:**
```sql
-- Verify new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('category_override_audit', 'category_override_operations');

-- Verify indexes created
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('category_override_audit', 'category_override_operations');

-- Test functions
SELECT update_category_override_stats();
```

### 3. Rollback Plan

**Rollback Scripts:**
```sql
-- Rollback_V1.4__Drop_functions.sql
DROP FUNCTION IF EXISTS update_category_override_stats();

-- Rollback_V1.3__Drop_indexes.sql
DROP INDEX IF EXISTS idx_category_override_audit_category_id;

-- Rollback_V1.2__Remove_override_columns.sql
ALTER TABLE category_recipient_settings 
DROP COLUMN IF EXISTS updated_by_operation;

-- Rollback_V1.1__Drop_override_operations_table.sql
DROP TABLE IF EXISTS category_override_operations;

-- Rollback_V1.0__Drop_override_audit_table.sql
DROP TABLE IF EXISTS category_override_audit;
```

## Application Deployment

### 1. Backend Deployment

**Docker Configuration:**
```dockerfile
# Dockerfile.api
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Kubernetes Deployment:**
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ehub-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ehub-api
  template:
    metadata:
      labels:
        app: ehub-api
    spec:
      containers:
      - name: api
        image: ehub/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ehub-secrets
              key: database-url
        - name: CATEGORY_OVERRIDE_ENABLED
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Frontend Deployment

**Build Configuration:**
```json
{
  "scripts": {
    "build:staging": "NODE_ENV=staging npm run build",
    "build:production": "NODE_ENV=production npm run build",
    "deploy:staging": "npm run build:staging && aws s3 sync build/ s3://ehub-staging-bucket",
    "deploy:production": "npm run build:production && aws s3 sync build/ s3://ehub-production-bucket"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "typescript": "^4.9.0"
  }
}
```

**CDN Configuration:**
```yaml
# cloudfront-config.yml
Distribution:
  DistributionConfig:
    CacheBehaviors:
      - PathPattern: "/static/*"
        TargetOriginId: S3Origin
        ViewerProtocolPolicy: redirect-to-https
        CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # CachingOptimized
      - PathPattern: "/api/*"
        TargetOriginId: APIOrigin
        ViewerProtocolPolicy: redirect-to-https
        CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # CachingDisabled
        OriginRequestPolicyId: 88a5eaf4-2fd4-4709-b370-b4c650ea3fcf  # CORS-S3Origin
```

## Monitoring and Alerting

### 1. Application Metrics

**Key Metrics to Monitor:**
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Operation metrics
override_operations_total = Counter(
    'category_override_operations_total',
    'Total number of override operations',
    ['status', 'category_id']
)

override_operation_duration = Histogram(
    'category_override_operation_duration_seconds',
    'Time spent processing override operations',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

override_recipients_affected = Histogram(
    'category_override_recipients_affected',
    'Number of recipients affected by override operations',
    buckets=[1, 10, 50, 100, 500, 1000, 5000]
)

# Current state metrics
active_override_operations = Gauge(
    'category_override_active_operations',
    'Number of currently active override operations'
)
```

**Dashboard Configuration:**
```yaml
# grafana-dashboard.json
{
  "dashboard": {
    "title": "Category Override Operations",
    "panels": [
      {
        "title": "Override Operations Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(category_override_operations_total[5m])",
            "legendFormat": "Operations/sec"
          }
        ]
      },
      {
        "title": "Operation Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(category_override_operations_total{status=\"success\"}[5m]) / rate(category_override_operations_total[5m]) * 100",
            "legendFormat": "Success %"
          }
        ]
      },
      {
        "title": "Average Recipients per Operation",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(category_override_recipients_affected_sum[5m]) / rate(category_override_recipients_affected_count[5m])",
            "legendFormat": "Avg Recipients"
          }
        ]
      }
    ]
  }
}
```

### 2. Alert Configuration

**Prometheus Alerts:**
```yaml
# alerts.yml
groups:
- name: category_override
  rules:
  - alert: HighOverrideFailureRate
    expr: rate(category_override_operations_total{status="failed"}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High failure rate for category override operations"
      description: "Override operation failure rate is {{ $value }} failures/sec"

  - alert: LongRunningOverrideOperation
    expr: category_override_active_operations > 0 AND time() - category_override_operation_start_time > 600
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Override operation running for more than 10 minutes"
      description: "Operation {{ $labels.operation_id }} has been running for {{ $value }} seconds"

  - alert: TooManyActiveOperations
    expr: category_override_active_operations > 5
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Too many concurrent override operations"
      description: "{{ $value }} override operations are currently active"
```

**Log Monitoring:**
```yaml
# log-alerts.yml
- name: category_override_logs
  rules:
  - alert: OverridePermissionDenied
    expr: increase(log_messages_total{level="warning",message=~".*override.*permission.*denied.*"}[5m]) > 10
    labels:
      severity: warning
    annotations:
      summary: "Multiple permission denied attempts for override operations"

  - alert: OverrideOperationError
    expr: increase(log_messages_total{level="error",service="category_override"}[5m]) > 5
    labels:
      severity: critical
    annotations:
      summary: "Multiple errors in override operations"
```

## Security Hardening

### 1. Production Security Configuration

**API Security:**
```python
# security_config.py
SECURITY_CONFIG = {
    'CORS_ORIGINS': ['https://ehub.se', 'https://app.ehub.se'],
    'CORS_METHODS': ['GET', 'POST'],
    'CORS_HEADERS': ['Authorization', 'Content-Type', 'X-CSRF-Token'],
    
    'RATE_LIMITING': {
        'override_operations': '5/minute',
        'count_queries': '60/minute',
        'general_api': '1000/hour'
    },
    
    'HEADERS': {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'"
    }
}
```

**Database Security:**
```sql
-- Create dedicated user for category override operations
CREATE USER category_override_service WITH PASSWORD 'secure_random_password';

-- Grant minimal required permissions
GRANT SELECT ON categories TO category_override_service;
GRANT SELECT ON recipients TO category_override_service;
GRANT SELECT, INSERT, UPDATE ON category_recipient_settings TO category_override_service;
GRANT INSERT ON category_override_audit TO category_override_service;
GRANT ALL ON category_override_operations TO category_override_service;

-- Revoke unnecessary permissions
REVOKE ALL ON users FROM category_override_service;
REVOKE DELETE ON categories FROM category_override_service;
```

### 2. Compliance Configuration

**Audit Logging:**
```python
# audit_config.py
AUDIT_CONFIG = {
    'RETENTION_PERIOD_DAYS': 2555,  # 7 years for compliance
    'LOG_LEVEL': 'INFO',
    'INCLUDE_PII': False,
    'ENCRYPT_SENSITIVE_FIELDS': True,
    'BACKUP_AUDIT_LOGS': True,
    'REAL_TIME_MONITORING': True
}
```

**Data Encryption:**
```yaml
# encryption-config.yml
encryption:
  at_rest:
    database: AES-256
    audit_logs: AES-256
    backups: AES-256
  in_transit:
    api_communication: TLS-1.3
    database_connections: SSL
    internal_services: mTLS
```

## Performance Optimization

### 1. Database Optimization

**Index Strategy:**
```sql
-- Performance indexes for override operations
CREATE INDEX CONCURRENTLY idx_recipients_ad_synced_category 
ON recipients(category_id, is_ad_synced, is_active) 
WHERE is_ad_synced = true AND is_active = true;

CREATE INDEX CONCURRENTLY idx_category_settings_recipient 
ON category_recipient_settings(recipient_id, category_id, is_override_generated);

-- Partitioning strategy for audit table
CREATE TABLE category_override_audit_y2025 PARTITION OF category_override_audit
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

**Query Optimization:**
```sql
-- Optimized query for recipient count
EXPLAIN ANALYZE
SELECT COUNT(*) 
FROM recipients r
WHERE r.category_id = $1 
  AND r.is_ad_synced = true 
  AND r.is_active = true;

-- Batch update optimization
UPDATE category_recipient_settings 
SET settings = $2, 
    is_override_generated = true,
    updated_by_operation = $3
WHERE recipient_id = ANY($1);
```

### 2. Application Optimization

**Caching Strategy:**
```python
# caching.py
from redis import Redis
import json

class OverrideCacheService:
    def __init__(self):
        self.redis = Redis.from_url(os.getenv('REDIS_URL'))
    
    def cache_recipients_count(self, category_id: int, count: int):
        key = f"ad_recipients_count:{category_id}"
        self.redis.setex(key, 300, count)  # 5 minute cache
    
    def get_cached_recipients_count(self, category_id: int) -> int:
        key = f"ad_recipients_count:{category_id}"
        cached = self.redis.get(key)
        return int(cached) if cached else None
    
    def invalidate_category_cache(self, category_id: int):
        pattern = f"*{category_id}*"
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
```

**Async Processing:**
```python
# async_processing.py
from celery import Celery

celery_app = Celery('category_override')

@celery_app.task
def process_large_override(category_id: int, user_id: int, operation_id: str):
    """Process override operations with more than 1000 recipients asynchronously"""
    try:
        service = CategoryOverrideService()
        result = service.process_override_async(category_id, user_id, operation_id)
        return result
    except Exception as e:
        # Handle error and update operation status
        service.mark_operation_failed(operation_id, str(e))
        raise
```

## Backup and Recovery

### 1. Backup Strategy

**Database Backup:**
```bash
#!/bin/bash
# backup_override_data.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/category_override"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup audit data
pg_dump -h $DB_HOST -U $DB_USER -t category_override_audit \
  --data-only --column-inserts $DB_NAME > $BACKUP_DIR/audit_$DATE.sql

# Backup operations data
pg_dump -h $DB_HOST -U $DB_USER -t category_override_operations \
  --data-only --column-inserts $DB_NAME > $BACKUP_DIR/operations_$DATE.sql

# Compress backups
gzip $BACKUP_DIR/*_$DATE.sql

# Upload to S3
aws s3 sync $BACKUP_DIR s3://ehub-backups/category-override/

# Cleanup local files older than 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
```

### 2. Recovery Procedures

**Recovery Plan:**
```bash
#!/bin/bash
# recovery_procedures.sh

# 1. Stop application services
kubectl scale deployment ehub-api --replicas=0

# 2. Restore database from backup
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f backup_file.sql

# 3. Verify data integrity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT COUNT(*) FROM category_override_audit;
SELECT COUNT(*) FROM category_override_operations;
"

# 4. Restart application services
kubectl scale deployment ehub-api --replicas=3

# 5. Verify application health
curl -f http://api.ehub.se/health
```

## Deployment Checklist

### Pre-deployment
- [ ] Database migration scripts tested
- [ ] Backup procedures verified
- [ ] Security configuration reviewed
- [ ] Performance testing completed
- [ ] Monitoring setup verified
- [ ] Documentation updated

### Deployment
- [ ] Feature flags configured
- [ ] Database migrations applied
- [ ] Application deployed to staging
- [ ] Integration tests passed
- [ ] Security scan completed
- [ ] Performance validation done

### Post-deployment
- [ ] Health checks passing
- [ ] Metrics collection working
- [ ] Alerts configured
- [ ] User training completed
- [ ] Documentation published
- [ ] Feedback collection started

### Rollback Plan
- [ ] Rollback scripts prepared
- [ ] Data backup verified
- [ ] Recovery procedures tested
- [ ] Communication plan ready
- [ ] Monitoring for issues
- [ ] Post-rollback validation

## Maintenance and Support

### 1. Regular Maintenance Tasks

**Daily:**
- Monitor override operation metrics
- Check for failed operations
- Review security alerts
- Verify backup completion

**Weekly:**
- Analyze performance trends
- Clean up old operation records
- Review audit logs
- Update security configurations

**Monthly:**
- Performance optimization review
- Security compliance audit
- Capacity planning assessment
- Documentation updates

### 2. Support Procedures

**Issue Escalation:**
```
Level 1: Application Support
├── Monitor dashboards
├── Check basic functionality
├── Restart services if needed
└── Escalate to Level 2

Level 2: Development Team
├── Investigate application logs
├── Analyze database performance
├── Review code for issues
└── Escalate to Level 3

Level 3: Senior Engineers
├── Deep technical investigation
├── Database optimization
├── Infrastructure changes
└── Emergency fixes
```

**Emergency Contacts:**
- On-call engineer: +46-XXX-XXXX-XXX
- Database administrator: +46-XXX-XXXX-XXX
- Security team: security@ehub.se
- Product owner: FredrikElliot@ehub.se

This comprehensive deployment guide ensures a smooth rollout of the category settings override feature with proper monitoring, security, and support procedures in place.