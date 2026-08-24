-- 驾驶舱用户数据表迁移
-- 创建 user_dashboard_data 表

CREATE TABLE IF NOT EXISTS user_dashboard_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    data_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, data_type)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_dashboard_data_user_id ON user_dashboard_data(user_id);
CREATE INDEX IF NOT EXISTS idx_user_dashboard_data_type ON user_dashboard_data(data_type);

-- 添加列（如果表已存在但缺少列）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_dashboard_data' AND column_name = 'id'
    ) THEN
        ALTER TABLE user_dashboard_data ADD COLUMN id UUID PRIMARY KEY DEFAULT gen_random_uuid();
    END IF;
END $$;
