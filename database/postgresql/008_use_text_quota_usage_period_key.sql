ALTER TABLE quota_usage
    ALTER COLUMN usage_date TYPE TEXT
    USING usage_date::TEXT;
