-- YouTube Summarizer Bot - Supabase Schema
-- Supabase 대시보드의 SQL Editor에서 실행

-- jobs 테이블 생성
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  youtube_url TEXT NOT NULL,
  telegram_chat_id BIGINT NOT NULL,
  telegram_user_id BIGINT,
  channel TEXT DEFAULT 'archive' CHECK (channel IN ('archive', 'agent-reference')),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  result JSONB,
  CONSTRAINT unique_url_chat UNIQUE (youtube_url, telegram_chat_id)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_telegram_chat ON jobs(telegram_chat_id);

-- RLS (Row Level Security) 활성화 (보안)
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Service Role이 모든 작업 가능하도록 정책 추가
CREATE POLICY "Service role can do everything"
  ON jobs
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- 익명 사용자는 읽기만 가능 (선택 사항)
CREATE POLICY "Anyone can read jobs"
  ON jobs
  FOR SELECT
  TO anon
  USING (true);

-- 통계를 위한 뷰 (선택 사항)
CREATE OR REPLACE VIEW job_statistics AS
SELECT
  channel,
  status,
  COUNT(*) as count,
  AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_duration_seconds
FROM jobs
WHERE completed_at IS NOT NULL
GROUP BY channel, status;

-- 완료 알림
SELECT 'Supabase schema created successfully!' as message;
