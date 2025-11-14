#!/bin/bash
set -e

echo "🚀 AI Multi-Agent Starter Kit - Codespaces Setup"
echo "================================================="

# 環境変数の確認
echo "📋 Checking environment variables..."

# .env ファイルを GitHub Secrets から自動生成
echo "🔑 Generating .env from GitHub Secrets..."

cat > /workspace/.env << EOF
# AI Multi-Agent Starter Kit - Environment Variables
# Auto-generated from GitHub Secrets

# Environment
ENVIRONMENT=${ENVIRONMENT:-development}

# Execution Mode
# DRY_RUN mode: All external API calls are mocked (zero cost)
DRY_RUN=${DRY_RUN:-true}

# Runner Configuration
# RUNNER_ENABLED: Set to 'false' to disable background task execution
RUNNER_ENABLED=${RUNNER_ENABLED:-false}

# API Keys
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}

# LLM Configuration
# OpenAI is disabled by default (set to 'true' to enable)
OPENAI_ENABLED=${OPENAI_ENABLED:-false}

# LLM Provider Priority (comma-separated)
# Default: anthropic,gemini,perplexity
LLM_PRIORITY=${LLM_PRIORITY:-anthropic,gemini,perplexity}

# Perplexity Search-Only Mode (prevents usage for non-search tasks)
PERPLEXITY_SEARCH_ONLY=${PERPLEXITY_SEARCH_ONLY:-true}

# Budget and Cost Controls
# Maximum daily cost in USD (0.0 = zero-cost mode with mocked API calls)
LLM_DAILY_MAX_COST_USD=${LLM_DAILY_MAX_COST_USD:-0.0}

# Maximum Perplexity requests per day (0 = disabled in DRY_RUN mode)
PERPLEXITY_MAX_REQUESTS_PER_DAY=${PERPLEXITY_MAX_REQUESTS_PER_DAY:-0}

# Timeout and Retry Settings
LLM_TIMEOUT=${LLM_TIMEOUT:-60}
LLM_MAX_RETRIES=${LLM_MAX_RETRIES:-3}

# Model Selection (optional - defaults are set in llm_router.py)
ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-claude-3-5-sonnet-20241022}
ANTHROPIC_MAX_TOKENS=${ANTHROPIC_MAX_TOKENS:-4096}

GEMINI_MODEL=${GEMINI_MODEL:-gemini-1.5-pro}
GEMINI_MAX_TOKENS=${GEMINI_MAX_TOKENS:-8192}

PERPLEXITY_MODEL=${PERPLEXITY_MODEL:-llama-3.1-sonar-large-128k-online}
PERPLEXITY_MAX_TOKENS=${PERPLEXITY_MAX_TOKENS:-4096}

OPENAI_MODEL=${OPENAI_MODEL:-gpt-4}
OPENAI_MAX_TOKENS=${OPENAI_MAX_TOKENS:-4096}

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/ai_agents

# Redis
REDIS_URL=redis://redis:6379

# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Applications Config
# Care Scheduler
CARE_SCHEDULER_ENABLED=true

# SNS Auto
SNS_AUTO_ENABLED=true
TWITTER_API_KEY=${TWITTER_API_KEY}
TWITTER_API_SECRET=${TWITTER_API_SECRET}
FACEBOOK_ACCESS_TOKEN=${FACEBOOK_ACCESS_TOKEN}
INSTAGRAM_ACCESS_TOKEN=${INSTAGRAM_ACCESS_TOKEN}
LINKEDIN_ACCESS_TOKEN=${LINKEDIN_ACCESS_TOKEN}

# HR Matching
HR_MATCHING_ENABLED=true

# Security
SECRET_KEY=${SECRET_KEY:-dev-secret-key-change-in-production}
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://*.app.github.dev
EOF

echo "✅ .env file created successfully"

# Python依存関係のインストール
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r /workspace/requirements.txt

echo "✅ Python dependencies installed"

# 権限設定
chmod +x /workspace/.devcontainer/setup.sh

# Git設定
echo "🔧 Configuring Git..."
git config --global --add safe.directory /workspace

# GitHub CLI認証チェック
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI is available"
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI authenticated"
    else
        echo "⚠️  GitHub CLI not authenticated. Run 'gh auth login' to authenticate."
    fi
fi

# Docker Composeの準備
echo "🐳 Preparing Docker services..."
cd /workspace

# 環境変数の確認レポート
echo ""
echo "================================================="
echo "📊 Environment Status"
echo "================================================="
echo "✅ Workspace: /workspace"
echo "✅ .env file: Created"
echo "✅ Python: $(python --version)"
echo "✅ Git: $(git --version)"

if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API Key: Set"
else
    echo "⚠️  OpenAI API Key: Not set"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ Anthropic API Key: Set"
else
    echo "⚠️  Anthropic API Key: Not set"
fi

if [ -n "$PERPLEXITY_API_KEY" ]; then
    echo "✅ Perplexity API Key: Set"
else
    echo "⚠️  Perplexity API Key: Not set"
fi

if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ Gemini API Key: Set"
else
    echo "⚠️  Gemini API Key: Not set"
fi

echo ""
echo "================================================="
echo "🎯 Quick Start Commands"
echo "================================================="
echo "  Start all services:    docker-compose -f docker/compose.dev.yml up -d"
echo "  View logs:             docker-compose -f docker/compose.dev.yml logs -f"
echo "  Stop services:         docker-compose -f docker/compose.dev.yml down"
echo "  Run API server:        uvicorn api.server:app --reload --host 0.0.0.0"
echo "  Run tests:             pytest"
echo "  Search demo:           python -m core.demo_search \"介護DXの最新トレンド\""
echo "================================================="
echo ""
echo "✨ Setup complete! Ready to start development."
