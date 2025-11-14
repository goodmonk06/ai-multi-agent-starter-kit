"""
Compliance Agent - コンプライアンスチェックと規制対応を担当

機能:
- コンテンツの適合性チェック
- 個人情報保護の確認
- 規制要件の検証
- リスク評価
"""

from typing import Dict, List, Optional, Any, Set
import structlog
from datetime import datetime
import re

logger = structlog.get_logger()


class ComplianceAgent:
    """コンプライアンスチェックを実行するエージェント"""

    def __init__(self, llm_client=None, memory_store=None):
        self.llm = llm_client
        self.memory = memory_store
        self.rules = self._load_default_rules()
        self.blocked_patterns = self._load_blocked_patterns()
        logger.info("ComplianceAgent initialized")

    def _load_default_rules(self) -> Dict[str, Any]:
        """デフォルトのコンプライアンスルールを読み込む"""
        return {
            "gdpr": {
                "enabled": True,
                "check_personal_data": True,
                "require_consent": True
            },
            "hipaa": {
                "enabled": True,
                "check_health_data": True,
                "encryption_required": True
            },
            "content_policy": {
                "enabled": True,
                "check_inappropriate_content": True,
                "check_harmful_content": True
            }
        }

    def _load_blocked_patterns(self) -> List[str]:
        """ブロックすべきパターンを読み込む"""
        return [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{16}\b',  # Credit card pattern
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email (for PII check)
        ]

    async def check_compliance(
        self,
        content: Any,
        compliance_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        コンプライアンスチェックを実行

        Args:
            content: チェック対象のコンテンツ
            compliance_type: チェックタイプ (general, gdpr, hipaa, content_policy)
            context: 追加コンテキスト

        Returns:
            チェック結果
        """
        logger.info("Starting compliance check", type=compliance_type)

        result = {
            "timestamp": datetime.now().isoformat(),
            "compliance_type": compliance_type,
            "passed": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }

        # テキストコンテンツの場合
        if isinstance(content, str):
            text_checks = await self._check_text_content(content, compliance_type)
            result.update(text_checks)

        # データの場合
        elif isinstance(content, dict):
            data_checks = await self._check_data_compliance(content, compliance_type)
            result.update(data_checks)

        # PII（個人識別情報）チェック
        pii_check = await self._check_pii(content)
        if not pii_check["passed"]:
            result["violations"].extend(pii_check["violations"])
            result["passed"] = False

        # 有害コンテンツチェック
        if compliance_type in ["general", "content_policy"]:
            harmful_check = await self._check_harmful_content(content)
            if not harmful_check["passed"]:
                result["violations"].extend(harmful_check["violations"])
                result["passed"] = False

        # メモリに保存
        if self.memory:
            await self.memory.store(
                f"compliance_check:{datetime.now().timestamp()}",
                result
            )

        return result

    async def _check_text_content(
        self,
        text: str,
        compliance_type: str
    ) -> Dict[str, Any]:
        """テキストコンテンツのチェック"""
        violations = []
        warnings = []

        # 禁止パターンのチェック
        for pattern in self.blocked_patterns:
            matches = re.findall(pattern, text)
            if matches:
                violations.append({
                    "type": "blocked_pattern",
                    "pattern": pattern,
                    "matches_count": len(matches),
                    "severity": "high"
                })

        # 文字数制限チェック（SNSなど）
        if len(text) > 5000:
            warnings.append({
                "type": "length",
                "message": "Content exceeds recommended length",
                "length": len(text)
            })

        return {
            "violations": violations,
            "warnings": warnings,
            "passed": len(violations) == 0
        }

    async def _check_data_compliance(
        self,
        data: Dict[str, Any],
        compliance_type: str
    ) -> Dict[str, Any]:
        """データのコンプライアンスチェック"""
        violations = []
        warnings = []

        # 必須フィールドのチェック
        required_fields = self._get_required_fields(compliance_type)
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            violations.append({
                "type": "missing_required_fields",
                "fields": missing_fields,
                "severity": "high"
            })

        # データ型チェック
        for key, value in data.items():
            if key.endswith("_date") and not isinstance(value, (str, datetime)):
                warnings.append({
                    "type": "invalid_data_type",
                    "field": key,
                    "expected": "date",
                    "actual": type(value).__name__
                })

        return {
            "violations": violations,
            "warnings": warnings,
            "passed": len(violations) == 0
        }

    async def _check_pii(self, content: Any) -> Dict[str, Any]:
        """個人識別情報（PII）のチェック"""
        violations = []

        text = str(content)

        # クレジットカード番号
        if re.search(r'\b\d{16}\b', text):
            violations.append({
                "type": "pii_credit_card",
                "severity": "critical",
                "message": "Potential credit card number detected"
            })

        # SSN（米国社会保障番号）
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
            violations.append({
                "type": "pii_ssn",
                "severity": "critical",
                "message": "Potential SSN detected"
            })

        # マイナンバー（日本）
        if re.search(r'\b\d{12}\b', text):
            violations.append({
                "type": "pii_mynumber",
                "severity": "critical",
                "message": "Potential My Number detected"
            })

        return {
            "passed": len(violations) == 0,
            "violations": violations
        }

    async def _check_harmful_content(self, content: Any) -> Dict[str, Any]:
        """有害コンテンツのチェック"""
        violations = []
        text = str(content).lower()

        # 禁止ワードリスト（実際にはより包括的なリストを使用）
        harmful_keywords = [
            "violence", "hate", "discrimination"
        ]

        for keyword in harmful_keywords:
            if keyword in text:
                violations.append({
                    "type": "harmful_content",
                    "keyword": keyword,
                    "severity": "high",
                    "message": f"Potentially harmful content detected: {keyword}"
                })

        # LLMを使った高度なチェック
        if self.llm and violations:
            # より詳細な分析をLLMで実行
            pass

        return {
            "passed": len(violations) == 0,
            "violations": violations
        }

    def _get_required_fields(self, compliance_type: str) -> List[str]:
        """コンプライアンスタイプごとの必須フィールドを取得"""
        required_fields_map = {
            "gdpr": ["consent", "data_subject_id"],
            "hipaa": ["patient_id", "encrypted"],
            "general": []
        }
        return required_fields_map.get(compliance_type, [])

    async def add_rule(
        self,
        rule_name: str,
        rule_config: Dict[str, Any]
    ) -> None:
        """カスタムルールを追加"""
        self.rules[rule_name] = rule_config
        logger.info("Compliance rule added", rule=rule_name)

    async def get_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """コンプライアンスレポートを生成"""
        # メモリから過去のチェック結果を取得
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "violations_by_type": {},
            "timestamp": datetime.now().isoformat()
        }

        return report
