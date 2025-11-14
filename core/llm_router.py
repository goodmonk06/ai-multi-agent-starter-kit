"""
LLM Router - LLMプロバイダーの選定とルーティング

機能:
- LLMプロバイダーの優先順位管理
- 自動フォールバック
- 使用量追跡
- プロバイダー別の有効/無効設定
- レート制限管理
- タイムアウト・リトライ処理
- メモリ最適化
"""

import os
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from collections import deque
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class LLMProvider(str, Enum):
    """サポートするLLMプロバイダー"""
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"
    OPENAI = "openai"


class LLMRouter:
    """
    LLMプロバイダーを選定し、リクエストをルーティング

    優先順位（デフォルト）:
    1. Anthropic (Claude)
    2. Gemini
    3. Perplexity

    OpenAIはデフォルトで無効
    """

    def __init__(
        self,
        priority: Optional[List[str]] = None,
        enable_openai: bool = False,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        LLMルーターを初期化

        Args:
            priority: LLMプロバイダーの優先順位リスト
            enable_openai: OpenAIを有効にするか
            max_retries: 最大リトライ回数
            timeout: タイムアウト(秒)
        """
        # 環境変数から設定を読み込み
        self.enable_openai = enable_openai or os.getenv("OPENAI_ENABLED", "false").lower() == "true"

        # Perplexityを検索専用にするか
        self.perplexity_search_only = os.getenv("PERPLEXITY_SEARCH_ONLY", "true").lower() == "true"

        # DRY_RUNモード（モック応答、実際のAPI呼び出しなし）
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # 日次コスト予算（USD）
        self.daily_max_cost = float(os.getenv("LLM_DAILY_MAX_COST_USD", "0.0"))
        self.daily_cost_used = 0.0
        self.cost_reset_date = datetime.now().date()

        # タイムアウト・リトライ設定
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delays = [2, 4, 8]  # エクスポネンシャルバックオフ (秒)

        # 優先順位を設定（環境変数 > 引数 > デフォルト）
        env_priority = os.getenv("LLM_PRIORITY")
        if env_priority:
            self.priority = [p.strip() for p in env_priority.split(",")]
        elif priority:
            self.priority = priority
        else:
            # デフォルト優先順位: Anthropic → Gemini → Perplexity
            self.priority = [
                LLMProvider.ANTHROPIC,
                LLMProvider.GEMINI,
                LLMProvider.PERPLEXITY
            ]

        # OpenAIが無効な場合はリストから除外
        if not self.enable_openai and LLMProvider.OPENAI in self.priority:
            self.priority.remove(LLMProvider.OPENAI)
            logger.info("OpenAI is disabled and removed from priority list")

        # プロバイダー別の設定
        self.providers_config = self._load_provider_configs()

        # 使用統計（最大1000件まで保持、古いものから削除）
        self.usage_stats = {provider: 0 for provider in LLMProvider}
        self.usage_history = deque(maxlen=1000)  # メモリリーク対策

        # レート制限管理（プロバイダー別）
        self.rate_limits = {
            LLMProvider.ANTHROPIC: {"requests_per_minute": 50, "tokens_per_minute": 40000},
            LLMProvider.GEMINI: {"requests_per_minute": 60, "tokens_per_minute": 32000},
            LLMProvider.PERPLEXITY: {"requests_per_minute": 20, "tokens_per_minute": 10000},
            LLMProvider.OPENAI: {"requests_per_minute": 60, "tokens_per_minute": 90000},
        }
        self.request_timestamps = {provider: deque(maxlen=100) for provider in LLMProvider}

        # クライアントキャッシュ
        self._clients: Dict[str, Any] = {}

        # エラーカウント（連続エラーでサーキットブレーカー発動）
        self.error_counts = {provider: 0 for provider in LLMProvider}
        self.circuit_breaker_threshold = 5  # 連続5回失敗でブレーカー発動
        self.circuit_breaker_reset_time = 300  # 5分後にリセット
        self.circuit_breaker_timers = {provider: None for provider in LLMProvider}

        logger.info(
            "LLMRouter initialized",
            priority=self.priority,
            openai_enabled=self.enable_openai,
            perplexity_search_only=self.perplexity_search_only,
            dry_run=self.dry_run,
            daily_max_cost=self.daily_max_cost,
            timeout=self.timeout
        )

    def _load_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        """各プロバイダーの設定を読み込む"""
        return {
            LLMProvider.ANTHROPIC: {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
                "max_tokens": int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
            },
            LLMProvider.GEMINI: {
                "api_key": os.getenv("GEMINI_API_KEY"),
                "model": os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
                "enabled": bool(os.getenv("GEMINI_API_KEY")),
                "max_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "8192"))
            },
            LLMProvider.PERPLEXITY: {
                "api_key": os.getenv("PERPLEXITY_API_KEY"),
                "model": os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online"),
                "enabled": bool(os.getenv("PERPLEXITY_API_KEY")),
                "max_tokens": int(os.getenv("PERPLEXITY_MAX_TOKENS", "4096"))
            },
            LLMProvider.OPENAI: {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4"),
                "enabled": self.enable_openai and bool(os.getenv("OPENAI_API_KEY")),
                "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
            }
        }

    def get_available_providers(self) -> List[str]:
        """利用可能なプロバイダーのリストを取得"""
        available = []
        for provider in self.priority:
            config = self.providers_config.get(provider)
            if config and config.get("enabled"):
                available.append(provider)

        return available

    def _is_circuit_breaker_open(self, provider: str) -> bool:
        """サーキットブレーカーが開いているか確認"""
        timer = self.circuit_breaker_timers.get(provider)
        if timer is None:
            return False

        # リセット時間が経過していればブレーカーを閉じる
        if time.time() - timer > self.circuit_breaker_reset_time:
            self.circuit_breaker_timers[provider] = None
            self.error_counts[provider] = 0
            logger.info("Circuit breaker reset", provider=provider)
            return False

        return True

    def _check_rate_limit(self, provider: str) -> bool:
        """レート制限をチェック"""
        now = time.time()
        timestamps = self.request_timestamps.get(provider, deque())

        # 1分以上前のタイムスタンプを削除
        while timestamps and now - timestamps[0] > 60:
            timestamps.popleft()

        # レート制限チェック
        rate_limit = self.rate_limits.get(provider, {})
        rpm = rate_limit.get("requests_per_minute", 60)

        if len(timestamps) >= rpm:
            logger.warning("Rate limit reached", provider=provider, rpm=rpm)
            return False

        return True

    def _check_daily_budget(self) -> bool:
        """日次予算をチェック"""
        # 日付が変わっていればリセット
        today = datetime.now().date()
        if today > self.cost_reset_date:
            self.daily_cost_used = 0.0
            self.cost_reset_date = today
            logger.info("Daily cost budget reset", date=today)

        # 予算チェック
        if self.daily_cost_used >= self.daily_max_cost:
            logger.warning(
                "Daily cost budget exceeded",
                used=self.daily_cost_used,
                limit=self.daily_max_cost
            )
            return False

        return True

    def _record_cost(self, provider: str, tokens: int) -> None:
        """コストを記録（概算）"""
        # プロバイダー別の概算コスト（per 1M tokens）
        cost_per_million = {
            LLMProvider.ANTHROPIC: 3.0,  # Claude 3.5 Sonnet
            LLMProvider.GEMINI: 1.25,    # Gemini 1.5 Pro
            LLMProvider.PERPLEXITY: 1.0, # Sonar Large
            LLMProvider.OPENAI: 30.0,    # GPT-4
        }

        rate = cost_per_million.get(provider, 1.0)
        cost = (tokens / 1_000_000) * rate
        self.daily_cost_used += cost

        logger.info(
            "API cost recorded",
            provider=provider,
            tokens=tokens,
            cost_usd=f"${cost:.4f}",
            daily_total=f"${self.daily_cost_used:.4f}"
        )

    def _get_mock_response(self, prompt: str, provider: str, task_type: Optional[str]) -> str:
        """DRY_RUNモード用のモックレスポンスを生成"""
        logger.info("Generating mock response (DRY_RUN mode)", provider=provider, task_type=task_type)

        if task_type == "search":
            return f"""[MOCK SEARCH RESULT]
Provider: {provider}
Query: {prompt[:100]}...

検索結果:
1. サンプル結果1: 関連する情報が見つかりました
2. サンプル結果2: 追加の詳細情報
3. サンプル結果3: さらなる参考情報

この結果はDRY_RUNモードのモックレスポンスです。
実際のAPI呼び出しは行われていません。
"""
        else:
            return f"""[MOCK LLM RESPONSE]
Provider: {provider}
Task Type: {task_type or 'general'}
Prompt: {prompt[:100]}...

応答:
ご質問ありがとうございます。

この応答はDRY_RUNモードで生成されたモックレスポンスです。
実際のLLM API（{provider}）は呼び出されていません。
コストは発生していません。

実際のAPI呼び出しを行うには:
1. .envファイルで DRY_RUN=false に設定
2. LLM_DAILY_MAX_COST_USD を適切な値に設定
3. 各プロバイダーのAPI Keyが正しく設定されているか確認

よろしくお願いいたします。
"""

    def select_provider(
        self,
        preferred_provider: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> Optional[str]:
        """
        最適なLLMプロバイダーを選定

        Args:
            preferred_provider: 希望するプロバイダー（指定可能）
            task_type: タスクタイプ（search, generate, analyze等）

        Returns:
            選定されたプロバイダー名、または None
        """
        # 希望するプロバイダーが指定された場合
        if preferred_provider:
            # OpenAIが無効で指定された場合は拒否
            if preferred_provider == LLMProvider.OPENAI and not self.enable_openai:
                logger.error(
                    "OpenAI is disabled, cannot use as preferred provider",
                    provider=preferred_provider
                )
                preferred_provider = None  # フォールバック

            # Perplexityが検索専用で、検索以外のタスクで指定された場合は拒否
            elif (preferred_provider == LLMProvider.PERPLEXITY and
                  self.perplexity_search_only and
                  task_type != "search"):
                logger.warning(
                    "Perplexity is search-only, falling back",
                    provider=preferred_provider,
                    task_type=task_type
                )
                preferred_provider = None  # フォールバック

            # 有効なプロバイダーかチェック
            elif preferred_provider:
                config = self.providers_config.get(preferred_provider)
                if config and config.get("enabled"):
                    # サーキットブレーカーチェック
                    if self._is_circuit_breaker_open(preferred_provider):
                        logger.warning(
                            "Circuit breaker is open for preferred provider",
                            provider=preferred_provider
                        )
                        preferred_provider = None  # フォールバック
                    else:
                        logger.info("Using preferred provider", provider=preferred_provider)
                        return preferred_provider
                else:
                    logger.warning(
                        "Preferred provider not available, falling back",
                        provider=preferred_provider
                    )

        # タスクタイプに基づく特殊なルーティング
        if task_type == "search":
            # 検索タスクはPerplexityを優先
            if LLMProvider.PERPLEXITY in self.priority:
                config = self.providers_config.get(LLMProvider.PERPLEXITY)
                if (config and config.get("enabled") and
                    not self._is_circuit_breaker_open(LLMProvider.PERPLEXITY)):
                    logger.info("Using Perplexity for search task")
                    return LLMProvider.PERPLEXITY

        # 優先順位に従って選定
        available = self.get_available_providers()

        # Perplexityが検索専用の場合、検索以外のタスクでは除外
        if self.perplexity_search_only and task_type != "search":
            available = [p for p in available if p != LLMProvider.PERPLEXITY]

        # サーキットブレーカーが開いているプロバイダーを除外
        available = [p for p in available if not self._is_circuit_breaker_open(p)]

        # レート制限を超えているプロバイダーを除外
        available = [p for p in available if self._check_rate_limit(p)]

        if not available:
            logger.error("No LLM providers available")
            return None

        selected = available[0]
        logger.info(
            "Provider selected",
            provider=selected,
            available_count=len(available),
            task_type=task_type
        )

        return selected

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LLMを使ってテキストを生成（リトライ・タイムアウト付き）

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            system_prompt: システムプロンプト
            preferred_provider: 希望するプロバイダー
            task_type: タスクタイプ

        Returns:
            生成結果
        """
        provider = self.select_provider(preferred_provider, task_type)

        if not provider:
            return {
                "status": "error",
                "error": "No available LLM provider",
                "result": ""
            }

        # DRY_RUNモードの場合はモックレスポンスを返す
        if self.dry_run:
            mock_response = self._get_mock_response(prompt, provider, task_type)
            logger.info("DRY_RUN mode: returning mock response", provider=provider)
            return {
                "status": "success",
                "provider": provider,
                "result": mock_response,
                "timestamp": datetime.now().isoformat(),
                "dry_run": True,
                "cost": "$0.00"
            }

        # 日次予算チェック
        if not self._check_daily_budget():
            logger.error(
                "Daily budget exceeded, returning error",
                used=self.daily_cost_used,
                limit=self.daily_max_cost
            )
            return {
                "status": "error",
                "error": f"Daily budget exceeded: ${self.daily_cost_used:.2f} / ${self.daily_max_cost:.2f}",
                "result": "",
                "suggestion": "Increase LLM_DAILY_MAX_COST_USD or wait until tomorrow"
            }

        # リトライロジック
        for retry in range(self.max_retries):
            try:
                result = await self._call_provider_with_timeout(
                    provider=provider,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt
                )

                # 成功: 使用統計を更新
                self.usage_stats[provider] += 1
                self.usage_history.append({
                    "provider": provider,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                })

                # レート制限の記録
                self.request_timestamps[provider].append(time.time())

                # コストを記録（概算でmax_tokensを使用）
                estimated_tokens = max_tokens or 4096
                self._record_cost(provider, estimated_tokens)

                # エラーカウントをリセット
                self.error_counts[provider] = 0

                return {
                    "status": "success",
                    "provider": provider,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "retries": retry,
                    "estimated_cost": f"${(estimated_tokens / 1_000_000) * 3.0:.4f}"
                }

            except asyncio.TimeoutError:
                logger.warning(
                    "Provider call timeout",
                    provider=provider,
                    retry=retry,
                    timeout=self.timeout
                )
                if retry < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delays[min(retry, len(self.retry_delays) - 1)])
                    continue
                else:
                    self._record_error(provider)

            except Exception as e:
                logger.error(
                    "Provider call failed",
                    provider=provider,
                    retry=retry,
                    error=str(e)
                )
                if retry < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delays[min(retry, len(self.retry_delays) - 1)])
                    continue
                else:
                    self._record_error(provider)

        # 全リトライ失敗: フォールバック
        return await self._fallback_generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            failed_provider=provider,
            task_type=task_type
        )

    def _record_error(self, provider: str) -> None:
        """エラーを記録し、サーキットブレーカーをチェック"""
        self.error_counts[provider] += 1
        self.usage_history.append({
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
            "success": False
        })

        # サーキットブレーカー発動
        if self.error_counts[provider] >= self.circuit_breaker_threshold:
            self.circuit_breaker_timers[provider] = time.time()
            logger.error(
                "Circuit breaker opened",
                provider=provider,
                error_count=self.error_counts[provider],
                reset_time=self.circuit_breaker_reset_time
            )

    async def _call_provider_with_timeout(
        self,
        provider: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """タイムアウト付きでプロバイダーを呼び出す"""
        return await asyncio.wait_for(
            self._call_provider(
                provider=provider,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            ),
            timeout=self.timeout
        )

    async def _call_provider(
        self,
        provider: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        特定のプロバイダーを呼び出す

        Args:
            provider: プロバイダー名
            prompt: プロンプト
            max_tokens: 最大トークン数
            temperature: 温度
            system_prompt: システムプロンプト

        Returns:
            生成されたテキスト
        """
        config = self.providers_config.get(provider)
        if not config or not config.get("enabled"):
            raise ValueError(f"Provider {provider} is not available")

        # 最大トークン数のデフォルト値
        if max_tokens is None:
            max_tokens = config.get("max_tokens", 4096)

        # プロバイダー別の実装
        if provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(
                prompt, max_tokens, temperature, system_prompt, config
            )
        elif provider == LLMProvider.GEMINI:
            return await self._call_gemini(
                prompt, max_tokens, temperature, system_prompt, config
            )
        elif provider == LLMProvider.PERPLEXITY:
            return await self._call_perplexity(
                prompt, max_tokens, temperature, system_prompt, config
            )
        elif provider == LLMProvider.OPENAI:
            return await self._call_openai(
                prompt, max_tokens, temperature, system_prompt, config
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _call_anthropic(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        config: Dict[str, Any]
    ) -> str:
        """Anthropic (Claude) APIを呼び出す"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=config["api_key"])

            messages = [{"role": "user", "content": prompt}]

            response = client.messages.create(
                model=config["model"],
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=messages
            )

            return response.content[0].text

        except ImportError:
            logger.error("anthropic package not installed")
            raise ValueError("Anthropic client not available. Install: pip install anthropic")
        except Exception as e:
            logger.error("Anthropic API call failed", error=str(e))
            raise

    async def _call_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        config: Dict[str, Any]
    ) -> str:
        """Google Gemini APIを呼び出す"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=config["api_key"])
            model = genai.GenerativeModel(config["model"])

            # システムプロンプトとプロンプトを結合
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            response = model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )

            return response.text

        except ImportError:
            logger.error("google-generativeai package not installed")
            raise ValueError("Gemini client not available. Install: pip install google-generativeai")
        except Exception as e:
            logger.error("Gemini API call failed", error=str(e))
            raise

    async def _call_perplexity(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        config: Dict[str, Any]
    ) -> str:
        """Perplexity APIを呼び出す"""
        try:
            import httpx

            url = "https://api.perplexity.ai/chat/completions"

            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": config["model"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                return data["choices"][0]["message"]["content"]

        except ImportError:
            logger.error("httpx package not installed")
            raise ValueError("HTTP client not available. Install: pip install httpx")
        except Exception as e:
            logger.error("Perplexity API call failed", error=str(e))
            raise

    async def _call_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        config: Dict[str, Any]
    ) -> str:
        """OpenAI APIを呼び出す"""
        try:
            import openai

            client = openai.OpenAI(api_key=config["api_key"])

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=config["model"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content

        except ImportError:
            logger.error("openai package not installed")
            raise ValueError("OpenAI client not available. Install: pip install openai")
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise

    async def _fallback_generate(
        self,
        prompt: str,
        max_tokens: Optional[int],
        temperature: float,
        system_prompt: Optional[str],
        failed_provider: str,
        task_type: Optional[str]
    ) -> Dict[str, Any]:
        """フォールバック: 他のプロバイダーで再試行"""
        logger.info("Attempting fallback", failed_provider=failed_provider)

        available = self.get_available_providers()

        # 失敗したプロバイダーを除外
        available = [p for p in available if p != failed_provider]

        if not available:
            return {
                "status": "error",
                "error": f"All providers failed. Last failed: {failed_provider}",
                "result": ""
            }

        # 次のプロバイダーで試行
        next_provider = available[0]
        logger.info("Trying fallback provider", provider=next_provider)

        try:
            result = await self._call_provider(
                provider=next_provider,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            )

            self.usage_stats[next_provider] += 1

            return {
                "status": "success",
                "provider": next_provider,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "fallback_from": failed_provider
            }

        except Exception as e:
            logger.error("Fallback provider also failed", provider=next_provider, error=str(e))

            # さらにフォールバック
            if len(available) > 1:
                return await self._fallback_generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    failed_provider=next_provider,
                    task_type=task_type
                )
            else:
                return {
                    "status": "error",
                    "error": f"All providers failed. Last: {next_provider}",
                    "result": ""
                }

    def get_usage_stats(self) -> Dict[str, Any]:
        """使用統計を取得"""
        total_requests = sum(self.usage_stats.values())

        return {
            "total_requests": total_requests,
            "by_provider": dict(self.usage_stats),
            "available_providers": self.get_available_providers(),
            "priority": self.priority,
            "openai_enabled": self.enable_openai,
            "dry_run": self.dry_run,
            "daily_cost_used": f"${self.daily_cost_used:.4f}",
            "daily_cost_limit": f"${self.daily_max_cost:.2f}",
            "budget_remaining": f"${max(0, self.daily_max_cost - self.daily_cost_used):.4f}"
        }

    def set_priority(self, priority: List[str]) -> None:
        """優先順位を変更"""
        # OpenAIが無効な場合は除外
        if not self.enable_openai:
            priority = [p for p in priority if p != LLMProvider.OPENAI]

        self.priority = priority
        logger.info("Priority updated", priority=priority)

    def enable_provider(self, provider: str) -> None:
        """プロバイダーを有効化"""
        if provider == LLMProvider.OPENAI:
            self.enable_openai = True
            if provider not in self.priority:
                self.priority.append(provider)

        logger.info("Provider enabled", provider=provider)

    def disable_provider(self, provider: str) -> None:
        """プロバイダーを無効化"""
        if provider in self.priority:
            self.priority.remove(provider)

        if provider == LLMProvider.OPENAI:
            self.enable_openai = False

        logger.info("Provider disabled", provider=provider)


# グローバルインスタンス（シングルトン）
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """LLMルーターのグローバルインスタンスを取得"""
    global _llm_router

    if _llm_router is None:
        _llm_router = LLMRouter()

    return _llm_router


def reset_llm_router() -> None:
    """LLMルーターをリセット（テスト用）"""
    global _llm_router
    _llm_router = None
