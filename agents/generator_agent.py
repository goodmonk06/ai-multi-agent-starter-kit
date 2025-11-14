"""
Generator Agent - コンテンツ生成とレスポンス作成を担当

機能:
- テキスト生成
- SNS投稿の作成
- メール/メッセージの自動生成
- レポート作成
"""

from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime

logger = structlog.get_logger()


class GeneratorAgent:
    """コンテンツを生成するエージェント"""

    def __init__(self, llm_client=None, memory_store=None):
        self.llm = llm_client
        self.memory = memory_store
        self.templates = {}
        logger.info("GeneratorAgent initialized")

    async def generate_content(
        self,
        content_type: str,
        context: Dict[str, Any],
        style: str = "professional",
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        コンテンツを生成する

        Args:
            content_type: コンテンツタイプ (sns_post, email, report, message)
            context: コンテキスト情報
            style: スタイル (professional, casual, formal, friendly)
            max_length: 最大文字数

        Returns:
            生成されたコンテンツ
        """
        logger.info("Generating content", type=content_type, style=style)

        if content_type == "sns_post":
            return await self._generate_sns_post(context, style, max_length)
        elif content_type == "email":
            return await self._generate_email(context, style)
        elif content_type == "report":
            return await self._generate_report(context)
        elif content_type == "message":
            return await self._generate_message(context, style)
        else:
            return await self._generate_generic(context, style, max_length)

    async def _generate_sns_post(
        self,
        context: Dict[str, Any],
        style: str,
        max_length: Optional[int]
    ) -> Dict[str, Any]:
        """SNS投稿を生成"""
        prompt = self._build_prompt(
            "Create an engaging social media post",
            context,
            style
        )

        content = await self._call_llm(prompt, max_length or 280)

        result = {
            "type": "sns_post",
            "content": content,
            "hashtags": self._extract_hashtags(content),
            "character_count": len(content),
            "timestamp": datetime.now().isoformat(),
            "style": style
        }

        # メモリに保存
        if self.memory:
            await self.memory.store(
                f"generated:sns:{datetime.now().timestamp()}",
                result
            )

        return result

    async def _generate_email(
        self,
        context: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """メールを生成"""
        subject = context.get("subject", "")
        recipient = context.get("recipient", "")

        prompt = self._build_prompt(
            f"Write a {style} email about: {subject}",
            context,
            style
        )

        body = await self._call_llm(prompt)

        return {
            "type": "email",
            "subject": subject,
            "recipient": recipient,
            "body": body,
            "timestamp": datetime.now().isoformat(),
            "style": style
        }

    async def _generate_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """レポートを生成"""
        title = context.get("title", "Report")
        data = context.get("data", {})

        prompt = f"""Generate a comprehensive report with the following:
Title: {title}
Data: {data}

Include:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Recommendations
"""

        content = await self._call_llm(prompt, max_length=5000)

        return {
            "type": "report",
            "title": title,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "sections": self._parse_sections(content)
        }

    async def _generate_message(
        self,
        context: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """メッセージを生成"""
        purpose = context.get("purpose", "")
        recipient_info = context.get("recipient_info", {})

        prompt = self._build_prompt(
            f"Create a {style} message for: {purpose}",
            context,
            style
        )

        message = await self._call_llm(prompt, max_length=500)

        return {
            "type": "message",
            "content": message,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat(),
            "style": style
        }

    async def _generate_generic(
        self,
        context: Dict[str, Any],
        style: str,
        max_length: Optional[int]
    ) -> Dict[str, Any]:
        """汎用コンテンツ生成"""
        prompt = self._build_prompt(
            context.get("instruction", "Generate content"),
            context,
            style
        )

        content = await self._call_llm(prompt, max_length)

        return {
            "type": "generic",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "style": style
        }

    def _build_prompt(
        self,
        instruction: str,
        context: Dict[str, Any],
        style: str
    ) -> str:
        """プロンプトを構築"""
        prompt = f"{instruction}\n\n"
        prompt += f"Style: {style}\n"

        if "audience" in context:
            prompt += f"Audience: {context['audience']}\n"

        if "tone" in context:
            prompt += f"Tone: {context['tone']}\n"

        if "key_points" in context:
            prompt += f"Key Points:\n"
            for point in context["key_points"]:
                prompt += f"- {point}\n"

        return prompt

    async def _call_llm(
        self,
        prompt: str,
        max_length: Optional[int] = None
    ) -> str:
        """LLMを呼び出してコンテンツを生成"""
        # LLMクライアントが設定されていれば実際に呼び出す
        if self.llm:
            # 実際の実装では、OpenAI/Anthropic APIを呼び出す
            # response = await self.llm.generate(prompt, max_tokens=max_length)
            # return response
            pass

        # フォールバック: テンプレートベースの生成
        return f"[Generated content based on: {prompt[:100]}...]"

    def _extract_hashtags(self, text: str) -> List[str]:
        """テキストからハッシュタグを抽出"""
        import re
        return re.findall(r'#\w+', text)

    def _parse_sections(self, content: str) -> List[Dict[str, str]]:
        """コンテンツをセクションに分解"""
        sections = []
        current_section = None

        for line in content.split('\n'):
            if line.startswith('#'):
                if current_section:
                    sections.append(current_section)
                current_section = {"title": line.strip('#').strip(), "content": ""}
            elif current_section:
                current_section["content"] += line + "\n"

        if current_section:
            sections.append(current_section)

        return sections

    async def register_template(
        self,
        template_name: str,
        template_content: str
    ) -> None:
        """テンプレートを登録"""
        self.templates[template_name] = template_content
        logger.info("Template registered", name=template_name)

    async def use_template(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """テンプレートを使ってコンテンツを生成"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template = self.templates[template_name]

        # 変数を置換
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template
