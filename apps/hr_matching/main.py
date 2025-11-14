"""
HR Matching Application - メインアプリケーション

機能:
- 候補者と求人のマッチング
- スキル分析
- 面接スケジューリング
- 自動フィードバック生成
"""

from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime

logger = structlog.get_logger()


class HrMatchingApp:
    """採用マッチングアプリケーション"""

    def __init__(self, agents: Dict[str, Any], workflow, memory):
        self.agents = agents
        self.workflow = workflow
        self.memory = memory
        self.matches = {}
        logger.info("HrMatchingApp initialized")

    async def match_candidates(
        self,
        job_posting: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        matching_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        候補者と求人をマッチング

        Args:
            job_posting: 求人情報
            candidates: 候補者リスト
            matching_criteria: マッチング基準

        Returns:
            マッチング結果（スコア順）
        """
        logger.info(
            "Matching candidates",
            job_id=job_posting.get("job_id"),
            candidate_count=len(candidates)
        )

        analyzer = self.agents.get("analyzer")

        if not analyzer:
            return [{"error": "Analyzer agent not available"}]

        # 各候補者をスコアリング
        matches = []

        for candidate in candidates:
            score = self._calculate_match_score(
                job_posting,
                candidate,
                matching_criteria or {}
            )

            match = {
                "candidate_id": candidate.get("candidate_id"),
                "candidate_name": candidate.get("name"),
                "job_id": job_posting.get("job_id"),
                "job_title": job_posting.get("title"),
                "match_score": score["total_score"],
                "score_breakdown": score["breakdown"],
                "strengths": score["strengths"],
                "gaps": score["gaps"],
                "matched_at": datetime.now().isoformat()
            }

            matches.append(match)

        # スコア順にソート
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        # 上位マッチをメモリに保存
        match_id = f"match_{job_posting.get('job_id')}_{datetime.now().timestamp()}"
        self.matches[match_id] = matches

        if self.memory:
            await self.memory.store(f"hr_match:{match_id}", matches)

        return matches

    async def analyze_resume(
        self,
        resume_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        履歴書を分析

        Args:
            resume_data: 履歴書データ

        Returns:
            分析結果
        """
        logger.info(
            "Analyzing resume",
            candidate_id=resume_data.get("candidate_id")
        )

        analyzer = self.agents.get("analyzer")

        if not analyzer:
            return {"error": "Analyzer agent not available"}

        # 履歴書データを構造化
        analysis_data = [{
            "candidate_id": resume_data.get("candidate_id"),
            "skills": resume_data.get("skills", []),
            "experience_years": resume_data.get("experience_years", 0),
            "education": resume_data.get("education", []),
            "work_history": resume_data.get("work_history", [])
        }]

        analysis = await analyzer.analyze_data(
            analysis_data,
            analysis_type="general"
        )

        # スキル抽出
        skills_summary = self._extract_skills_summary(resume_data)

        result = {
            "candidate_id": resume_data.get("candidate_id"),
            "skills_summary": skills_summary,
            "experience_level": self._determine_experience_level(
                resume_data.get("experience_years", 0)
            ),
            "key_strengths": self._identify_strengths(resume_data),
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        }

        return result

    async def schedule_interview(
        self,
        candidate_id: str,
        job_id: str,
        interviewer_ids: List[str],
        preferred_times: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        面接をスケジュール

        Args:
            candidate_id: 候補者ID
            job_id: 求人ID
            interviewer_ids: 面接官IDリスト
            preferred_times: 希望時間帯

        Returns:
            スケジュール結果
        """
        logger.info(
            "Scheduling interview",
            candidate=candidate_id,
            job=job_id
        )

        scheduler = self.agents.get("scheduler")
        generator = self.agents.get("generator")

        if not scheduler:
            return {"error": "Scheduler agent not available"}

        # 面接タスクを作成
        interview_task = {
            "task_id": f"interview_{candidate_id}_{job_id}",
            "task_type": "interview_schedule",
            "candidate_id": candidate_id,
            "job_id": job_id,
            "interviewer_ids": interviewer_ids,
            "preferred_times": preferred_times,
            "priority": 7
        }

        schedule_result = await scheduler.schedule_task(**interview_task)

        # 通知メールを生成
        if generator:
            email = await generator.generate_content(
                content_type="email",
                context={
                    "subject": "Interview Invitation",
                    "recipient": "candidate",
                    "purpose": "interview_invitation",
                    "job_id": job_id,
                    "interview_details": schedule_result
                },
                style="professional"
            )

            schedule_result["notification_email"] = email

        return schedule_result

    async def generate_feedback(
        self,
        candidate_id: str,
        interview_notes: Dict[str, Any],
        decision: str
    ) -> Dict[str, Any]:
        """
        フィードバックを生成

        Args:
            candidate_id: 候補者ID
            interview_notes: 面接メモ
            decision: 決定 (accept, reject, hold)

        Returns:
            生成されたフィードバック
        """
        logger.info(
            "Generating feedback",
            candidate=candidate_id,
            decision=decision
        )

        generator = self.agents.get("generator")
        compliance = self.agents.get("compliance")

        if not generator:
            return {"error": "Generator agent not available"}

        # フィードバックを生成
        feedback_context = {
            "purpose": "interview_feedback",
            "candidate_id": candidate_id,
            "interview_notes": interview_notes,
            "decision": decision,
            "tone": "constructive"
        }

        feedback = await generator.generate_content(
            content_type="message",
            context=feedback_context,
            style="professional"
        )

        # コンプライアンスチェック（差別的表現など）
        if compliance:
            check = await compliance.check_compliance(
                feedback.get("content"),
                compliance_type="content_policy"
            )

            if not check.get("passed"):
                logger.warning(
                    "Feedback compliance issues",
                    violations=check["violations"]
                )
                feedback["needs_review"] = True
                feedback["compliance_issues"] = check["violations"]

        feedback["candidate_id"] = candidate_id
        feedback["decision"] = decision
        feedback["generated_at"] = datetime.now().isoformat()

        # メモリに保存
        if self.memory:
            await self.memory.store(
                f"feedback:{candidate_id}",
                feedback
            )

        return feedback

    def _calculate_match_score(
        self,
        job_posting: Dict[str, Any],
        candidate: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """マッチスコアを計算"""
        scores = {}

        # スキルマッチ
        required_skills = set(job_posting.get("required_skills", []))
        candidate_skills = set(candidate.get("skills", []))
        skill_match = len(required_skills & candidate_skills) / len(required_skills) if required_skills else 0
        scores["skills"] = skill_match * 100

        # 経験年数マッチ
        required_years = job_posting.get("required_experience_years", 0)
        candidate_years = candidate.get("experience_years", 0)
        experience_score = min(candidate_years / required_years, 1.5) * 100 if required_years > 0 else 100
        scores["experience"] = min(experience_score, 100)

        # 学歴マッチ
        education_match = 80  # デフォルトスコア
        if "required_education" in job_posting and "education" in candidate:
            # 簡易的な学歴マッチング
            education_match = 100 if job_posting["required_education"] in str(candidate["education"]) else 60
        scores["education"] = education_match

        # 総合スコア
        weights = criteria.get("weights", {
            "skills": 0.5,
            "experience": 0.3,
            "education": 0.2
        })

        total_score = sum(
            scores[key] * weights.get(key, 0)
            for key in scores.keys()
        )

        # 強みとギャップを特定
        strengths = []
        gaps = []

        if scores["skills"] >= 80:
            strengths.append("Strong skill match")
        elif scores["skills"] < 50:
            gaps.append("Skill gaps exist")

        if scores["experience"] >= 100:
            strengths.append("Exceeds experience requirements")
        elif scores["experience"] < 70:
            gaps.append("Limited relevant experience")

        return {
            "total_score": total_score,
            "breakdown": scores,
            "strengths": strengths,
            "gaps": gaps
        }

    def _extract_skills_summary(
        self,
        resume_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """スキルサマリーを抽出"""
        skills = resume_data.get("skills", [])

        # スキルをカテゴリ分け
        technical_keywords = ["python", "java", "javascript", "sql", "aws", "docker"]
        soft_skills_keywords = ["leadership", "communication", "teamwork"]

        summary = {
            "technical": [s for s in skills if any(k in s.lower() for k in technical_keywords)],
            "soft_skills": [s for s in skills if any(k in s.lower() for k in soft_skills_keywords)],
            "other": []
        }

        # 分類されなかったスキル
        categorized = set(summary["technical"] + summary["soft_skills"])
        summary["other"] = [s for s in skills if s not in categorized]

        return summary

    def _determine_experience_level(self, years: int) -> str:
        """経験レベルを判定"""
        if years < 2:
            return "junior"
        elif years < 5:
            return "mid-level"
        elif years < 10:
            return "senior"
        else:
            return "expert"

    def _identify_strengths(
        self,
        resume_data: Dict[str, Any]
    ) -> List[str]:
        """強みを特定"""
        strengths = []

        if resume_data.get("experience_years", 0) >= 5:
            strengths.append("Experienced professional")

        skills_count = len(resume_data.get("skills", []))
        if skills_count >= 10:
            strengths.append("Diverse skill set")

        return strengths
