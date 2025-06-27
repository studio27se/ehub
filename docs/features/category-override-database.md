# Database Schema - Category Settings Override

## Overview
This document defines the database schema changes required for the category settings override functionality.

## New Tables

### 1. category_override_audit

**Purpose:** Audit trail for all category override operations

```sql
CREATE TABLE category_override_audit (
    id BIGSERIAL PRIMARY KEY,
    operation_id VARCHAR(50) UNIQUE NOT NULL,
    category_id BIGINT NOT NULL,
    category_name VARCHAR(255) NOT NULL, -- Snapshot of name at time of operation
    user_id BIGINT NOT NULL,
    user_name VARCHAR(255) NOT NULL, -- Snapshot of username at time of operation
    affected_recipients_count INTEGER NOT NULL DEFAULT 0,
    operation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    operation_status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    operation_duration_ms INTEGER, -- Operation duration in milliseconds
    error_message TEXT,
    client_ip INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT fk_category_override_audit_category 
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    CONSTRAINT fk_category_override_audit_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_operation_status 
        CHECK (operation_status IN ('STARTED', 'COMPLETED', 'FAILED')),
    CONSTRAINT chk_affected_recipients_count 
        CHECK (affected_recipients_count >= 0),
    CONSTRAINT chk_operation_duration 
        CHECK (operation_duration_ms IS NULL OR operation_duration_ms >= 0)
);

-- Indexes for performance
CREATE INDEX idx_category_override_audit_category_id ON category_override_audit(category_id);
CREATE INDEX idx_category_override_audit_user_id ON category_override_audit(user_id);
CREATE INDEX idx_category_override_audit_timestamp ON category_override_audit(operation_timestamp DESC);
CREATE INDEX idx_category_override_audit_status ON category_override_audit(operation_status);
CREATE UNIQUE INDEX idx_category_override_audit_operation_id ON category_override_audit(operation_id);

-- Partial index for active operations
CREATE INDEX idx_category_override_audit_active 
ON category_override_audit(operation_timestamp DESC) 
WHERE operation_status IN ('STARTED', 'FAILED');
```

### 2. category_override_operations

**Purpose:** Track ongoing override operations for monitoring and recovery

```sql
CREATE TABLE category_override_operations (
    id BIGSERIAL PRIMARY KEY,
    operation_id VARCHAR(50) UNIQUE NOT NULL,
    category_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    total_recipients INTEGER,
    processed_recipients INTEGER DEFAULT 0,
    batch_size INTEGER DEFAULT 100,
    current_batch INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Foreign key constraints
    CONSTRAINT fk_category_override_operations_category 
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    CONSTRAINT fk_category_override_operations_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_override_operation_status 
        CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    CONSTRAINT chk_processed_recipients 
        CHECK (processed_recipients >= 0),
    CONSTRAINT chk_total_recipients 
        CHECK (total_recipients IS NULL OR total_recipients >= 0),
    CONSTRAINT chk_batch_size 
        CHECK (batch_size > 0 AND batch_size <= 1000),
    CONSTRAINT chk_retry_count 
        CHECK (retry_count >= 0 AND retry_count <= max_retries)
);

-- Indexes for performance
CREATE INDEX idx_category_override_operations_status ON category_override_operations(status);
CREATE INDEX idx_category_override_operations_started_at ON category_override_operations(started_at DESC);
CREATE INDEX idx_category_override_operations_category_id ON category_override_operations(category_id);
CREATE UNIQUE INDEX idx_category_override_operations_operation_id ON category_override_operations(operation_id);

-- Partial index for active operations
CREATE INDEX idx_category_override_operations_active 
ON category_override_operations(started_at DESC) 
WHERE status IN ('PENDING', 'PROCESSING');
```

## Modified Tables

### 1. category_recipient_settings

**Purpose:** Track which settings were applied via override operations

```sql
-- Add new columns to existing table
ALTER TABLE category_recipient_settings 
ADD COLUMN IF NOT EXISTS updated_by_operation VARCHAR(50),
ADD COLUMN IF NOT EXISTS is_override_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS override_timestamp TIMESTAMP WITH TIME ZONE;

-- Add foreign key constraint to operation audit
ALTER TABLE category_recipient_settings
ADD CONSTRAINT fk_category_recipient_settings_operation
FOREIGN KEY (updated_by_operation) REFERENCES category_override_audit(operation_id)
ON DELETE SET NULL;

-- Add index for override-related queries
CREATE INDEX idx_category_recipient_settings_override 
ON category_recipient_settings(updated_by_operation, override_timestamp DESC)
WHERE is_override_generated = TRUE;
```

### 2. categories

**Purpose:** Add metadata for override operations

```sql
-- Add new columns to track override history
ALTER TABLE categories
ADD COLUMN IF NOT EXISTS last_override_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_override_by BIGINT,
ADD COLUMN IF NOT EXISTS override_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_override_recipients_count INTEGER DEFAULT 0;

-- Add foreign key for last override user
ALTER TABLE categories
ADD CONSTRAINT fk_categories_last_override_user
FOREIGN KEY (last_override_by) REFERENCES users(id)
ON DELETE SET NULL;

-- Add index for override statistics
CREATE INDEX idx_categories_last_override ON categories(last_override_at DESC)
WHERE last_override_at IS NOT NULL;
```

## Database Functions and Procedures

### 1. Update Category Override Statistics

```sql
CREATE OR REPLACE FUNCTION update_category_override_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update category statistics when override audit is inserted
    IF TG_OP = 'INSERT' AND NEW.operation_status = 'COMPLETED' THEN
        UPDATE categories 
        SET 
            last_override_at = NEW.operation_timestamp,
            last_override_by = NEW.user_id,
            override_count = COALESCE(override_count, 0) + 1,
            last_override_recipients_count = NEW.affected_recipients_count
        WHERE id = NEW.category_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_update_category_override_stats
    AFTER INSERT ON category_override_audit
    FOR EACH ROW
    EXECUTE FUNCTION update_category_override_stats();
```

### 2. Cleanup Old Operation Records

```sql
CREATE OR REPLACE FUNCTION cleanup_old_override_operations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete completed operations older than 30 days
    DELETE FROM category_override_operations
    WHERE status IN ('COMPLETED', 'FAILED', 'CANCELLED')
    AND completed_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log cleanup operation
    INSERT INTO system_maintenance_log (operation, affected_rows, timestamp)
    VALUES ('cleanup_override_operations', deleted_count, NOW());
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
```

### 3. Get Override Operation Progress

```sql
CREATE OR REPLACE FUNCTION get_override_operation_progress(op_id VARCHAR(50))
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'operationId', operation_id,
        'status', status,
        'totalRecipients', total_recipients,
        'processedRecipients', processed_recipients,
        'progressPercent', 
            CASE 
                WHEN total_recipients > 0 THEN 
                    ROUND((processed_recipients::DECIMAL / total_recipients) * 100, 2)
                ELSE 0 
            END,
        'startedAt', started_at,
        'lastUpdatedAt', last_updated_at,
        'completedAt', completed_at,
        'errorMessage', error_message,
        'retryCount', retry_count
    ) INTO result
    FROM category_override_operations
    WHERE operation_id = op_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

## Views for Reporting

### 1. Category Override Summary

```sql
CREATE VIEW v_category_override_summary AS
SELECT 
    c.id as category_id,
    c.name as category_name,
    c.override_count,
    c.last_override_at,
    c.last_override_recipients_count,
    u.username as last_override_by_username,
    COUNT(DISTINCT r.id) as total_ad_recipients,
    COALESCE(recent_overrides.recent_count, 0) as overrides_last_30_days
FROM categories c
LEFT JOIN users u ON c.last_override_by = u.id
LEFT JOIN recipients r ON c.id = r.category_id AND r.is_ad_synced = TRUE AND r.is_active = TRUE
LEFT JOIN (
    SELECT 
        category_id,
        COUNT(*) as recent_count
    FROM category_override_audit
    WHERE operation_timestamp > NOW() - INTERVAL '30 days'
    AND operation_status = 'COMPLETED'
    GROUP BY category_id
) recent_overrides ON c.id = recent_overrides.category_id
GROUP BY c.id, c.name, c.override_count, c.last_override_at, 
         c.last_override_recipients_count, u.username, recent_overrides.recent_count;
```

### 2. Override Operation History

```sql
CREATE VIEW v_override_operation_history AS
SELECT 
    audit.operation_id,
    audit.category_id,
    audit.category_name,
    audit.user_id,
    audit.user_name,
    audit.affected_recipients_count,
    audit.operation_timestamp,
    audit.operation_status,
    audit.operation_duration_ms,
    audit.error_message,
    audit.client_ip,
    CASE 
        WHEN audit.operation_duration_ms IS NOT NULL THEN
            ROUND(audit.operation_duration_ms / 1000.0, 2)
        ELSE NULL
    END as operation_duration_seconds
FROM category_override_audit audit
ORDER BY audit.operation_timestamp DESC;
```

## Migration Scripts

### Migration 1: Create Override Tables

```sql
-- V1.0__Create_override_tables.sql

-- Create audit table
CREATE TABLE category_override_audit (
    -- Table definition as above
);

-- Create operations tracking table  
CREATE TABLE category_override_operations (
    -- Table definition as above
);

-- Create indexes
-- Index definitions as above

-- Create functions
-- Function definitions as above

-- Create views
-- View definitions as above
```

### Migration 2: Modify Existing Tables

```sql
-- V1.1__Modify_existing_tables.sql

-- Modify category_recipient_settings
ALTER TABLE category_recipient_settings 
ADD COLUMN IF NOT EXISTS updated_by_operation VARCHAR(50),
ADD COLUMN IF NOT EXISTS is_override_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS override_timestamp TIMESTAMP WITH TIME ZONE;

-- Modify categories table
ALTER TABLE categories
ADD COLUMN IF NOT EXISTS last_override_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_override_by BIGINT,
ADD COLUMN IF NOT EXISTS override_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_override_recipients_count INTEGER DEFAULT 0;

-- Add foreign key constraints
-- Constraint definitions as above
```

### Migration 3: Data Migration

```sql
-- V1.2__Initialize_override_data.sql

-- Initialize override_count for existing categories
UPDATE categories 
SET override_count = 0 
WHERE override_count IS NULL;

-- Set default values for existing recipient settings
UPDATE category_recipient_settings 
SET is_override_generated = FALSE
WHERE is_override_generated IS NULL;
```

## Performance Considerations

### 1. Indexing Strategy

```sql
-- Composite indexes for common queries
CREATE INDEX idx_audit_category_status_timestamp 
ON category_override_audit(category_id, operation_status, operation_timestamp DESC);

CREATE INDEX idx_operations_user_status 
ON category_override_operations(user_id, status);

-- Partial indexes for active operations
CREATE INDEX idx_operations_processing 
ON category_override_operations(started_at DESC)
WHERE status = 'PROCESSING';
```

### 2. Partitioning for Large Tables

```sql
-- Partition audit table by month for better performance
CREATE TABLE category_override_audit_y2025m06 
PARTITION OF category_override_audit
FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

-- Create partition maintenance function
CREATE OR REPLACE FUNCTION maintain_audit_partitions()
RETURNS VOID AS $$
BEGIN
    -- Create next month's partition
    -- Implementation for automatic partition creation
END;
$$ LANGUAGE plpgsql;
```

### 3. Query Optimization

```sql
-- Optimized query for dashboard statistics
WITH category_stats AS (
    SELECT 
        category_id,
        COUNT(*) as total_operations,
        SUM(affected_recipients_count) as total_recipients_affected,
        MAX(operation_timestamp) as last_operation
    FROM category_override_audit 
    WHERE operation_status = 'COMPLETED'
    AND operation_timestamp > NOW() - INTERVAL '90 days'
    GROUP BY category_id
)
SELECT 
    c.name,
    COALESCE(cs.total_operations, 0) as operations_count,
    COALESCE(cs.total_recipients_affected, 0) as recipients_affected,
    cs.last_operation
FROM categories c
LEFT JOIN category_stats cs ON c.id = cs.category_id
ORDER BY cs.total_operations DESC NULLS LAST;
```

## Data Integrity and Constraints

### 1. Referential Integrity

```sql
-- Ensure operation_id references are valid
ALTER TABLE category_recipient_settings
ADD CONSTRAINT chk_valid_operation_reference
CHECK (
    updated_by_operation IS NULL OR 
    EXISTS (
        SELECT 1 FROM category_override_audit 
        WHERE operation_id = updated_by_operation
    )
);
```

### 2. Data Validation

```sql
-- Validate operation timestamps
ALTER TABLE category_override_audit
ADD CONSTRAINT chk_valid_timestamps
CHECK (operation_timestamp <= NOW() + INTERVAL '1 hour');

-- Validate recipient counts
ALTER TABLE category_override_operations
ADD CONSTRAINT chk_recipient_counts
CHECK (
    total_recipients IS NULL OR 
    processed_recipients <= total_recipients
);
```

## Backup and Recovery

### 1. Backup Strategy

```sql
-- Critical tables for backup
-- 1. category_override_audit (full backup daily)
-- 2. category_override_operations (incremental backup)
-- 3. category_recipient_settings (changes tracking)

-- Backup verification query
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename LIKE '%override%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 2. Recovery Procedures

```sql
-- Point-in-time recovery for override operations
-- Restore from backup and replay transaction log

-- Consistency check after recovery
SELECT 
    COUNT(*) as audit_records,
    COUNT(DISTINCT operation_id) as unique_operations,
    MIN(operation_timestamp) as earliest_operation,
    MAX(operation_timestamp) as latest_operation
FROM category_override_audit;
```

## Monitoring Queries

### 1. Operation Performance

```sql
-- Monitor operation performance
SELECT 
    DATE_TRUNC('hour', operation_timestamp) as hour,
    COUNT(*) as operations_count,
    AVG(affected_recipients_count) as avg_recipients,
    AVG(operation_duration_ms) as avg_duration_ms,
    COUNT(*) FILTER (WHERE operation_status = 'FAILED') as failed_count
FROM category_override_audit
WHERE operation_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', operation_timestamp)
ORDER BY hour DESC;
```

### 2. System Health

```sql
-- Check for stuck operations
SELECT 
    operation_id,
    category_id,
    user_id,
    status,
    started_at,
    NOW() - started_at as duration
FROM category_override_operations
WHERE status IN ('PENDING', 'PROCESSING')
AND started_at < NOW() - INTERVAL '1 hour';
```

## Implementation Checklist

### Development Phase
- [ ] Create migration scripts
- [ ] Implement audit tables
- [ ] Create operation tracking tables
- [ ] Add database functions
- [ ] Create performance indexes
- [ ] Implement views for reporting

### Testing Phase
- [ ] Test migration scripts on staging
- [ ] Validate referential integrity
- [ ] Performance test with sample data
- [ ] Test backup and recovery procedures
- [ ] Validate monitoring queries

### Production Deployment
- [ ] Schedule maintenance window
- [ ] Run migration scripts
- [ ] Verify data integrity
- [ ] Test application functionality
- [ ] Monitor system performance
- [ ] Set up automated monitoring