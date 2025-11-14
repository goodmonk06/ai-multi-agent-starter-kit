"""
LLM Router - LLMプロバイダーの選定とルーティング

機能:
- LLMプロバイダーの優先順位管理
- 自動フォールバック
- 使用量追跡
- プロバイダー別の有効/無効設定
"""

import os
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import structlog
from datetime import datetime

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
        enable_openai: bool = False
    ):
        """
        LLMルーターを初期化

        Args:
            priority: LLMプロバイダーの優先順位リスト
            enable_openai: OpenAIを有効にするか
        """
        # 環境変数から設定を読み込み
        self.enable_openai = enable_openai or os.getenv("OPENAI_ENABLED", "false").lower() == "true"

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

        # 使用統計
        self.usage_stats = {provider: 0 for provider in LLMProvider}

        # クライアントキャッシュ
        self._clients: Dict[str, Any] = {}

        logger.info(
            "LLMRouter initialized",
            priority=self.priority,
            openai_enabled=self.enable_openai
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
        # 希望するプロバイダーが指定され、利用可能な場合
        if preferred_provider:
            config = self.providers_config.get(preferred_provider)
            if config and config.get("enabled"):
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
                if config and config.get("enabled"):
                    logger.info("Using Perplexity for search task")
                    return LLMProvider.PERPLEXITY

        # 優先順位に従って選定
        available = self.get_available_providers()

        if not available:
            logger.error("No LLM providers available")
            return None

        selected = available[0]
        logger.info(
            "Provider selected",
            provider=selected,
            available_count=len(available)
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
        LLMを使ってテキストを生成

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

        try:
            result = await self._call_provider(
                provider=provider,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            )

            # 使用統計を更新
            self.usage_stats[provider] += 1

            return {
                "status": "success",
                "provider": provider,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(
                "Provider call failed",
                provider=provider,
                error=str(e)
            )

            # フォールバック: 次の利用可能なプロバイダーを試す
            return await self._fallback_generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                failed_provider=provider,
                task_type=task_type
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
            "openai_enabled": self.enable_openai
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
