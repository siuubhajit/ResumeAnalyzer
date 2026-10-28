import os
import json
import re
from typing import Dict, List, Any

# Attempt import of official google-genai SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class AISuggester:
    """
    Generates intelligent resume improvement suggestions using:
    1. Google Gemini API (if GEMINI_API_KEY is configured in .env)
    2. Intelligent Contextual Fallback Engine (guarantees 100% offline/out-of-box functionality)
    """

    DEFAULT_MODEL = "gemini-2.5-flash"

    @classmethod
    def get_suggestions(
        cls,
        resume_data: Dict[str, Any],
        job_description: str,
        match_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinates AI suggestion generation, falling back gracefully if API is unavailable.
        """
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        model_name = os.getenv("GEMINI_MODEL", cls.DEFAULT_MODEL).strip() or cls.DEFAULT_MODEL

        if api_key and genai is not None:
            try:
                gemini_result = cls._call_gemini_api(
                    api_key=api_key,
                    model_name=model_name,
                    resume_data=resume_data,
                    job_description=job_description,
                    match_analysis=match_analysis
                )
                if gemini_result.get("success"):
                    return gemini_result
            except Exception as e:
                # Log or fall back
                pass

        # Fallback to intelligent rule-based contextual generator
        return cls._generate_contextual_fallback(resume_data, job_description, match_analysis)

    @classmethod
    def _call_gemini_api(
        cls,
        api_key: str,
        model_name: str,
        resume_data: Dict[str, Any],
        job_description: str,
        match_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calls Google Gemini API using the official google-genai SDK to get structured suggestions.
        """
        client = genai.Client(api_key=api_key)

        matched_skills = match_analysis.get("matched_skills", [])
        missing_skills = match_analysis.get("missing_skills", [])
        overall_score = match_analysis.get("overall_match_percentage", 0)

        prompt = f"""
You are an expert ATS (Applicant Tracking System) recruiter and career coach.
Analyze the following resume against the target job description and provide structured, high-impact recommendations.

--- TARGET JOB DESCRIPTION ---
{job_description[:3000]}

--- RESUME CONTENT ---
Candidate Name: {resume_data.get('contact', {}).get('name', 'Candidate')}
Matched Skills: {', '.join(matched_skills[:15]) if matched_skills else 'None'}
Missing Skills: {', '.join(missing_skills[:15]) if missing_skills else 'None'}
Current Estimated Match Score: {overall_score}%

Resume Text:
{resume_data.get('raw_text', '')[:3500]}

--- INSTRUCTIONS ---
Respond ONLY with a valid JSON object (no markdown code blocks, no backticks, no preamble).
The JSON must adhere to this exact schema:
{{
  "summary_critique": "A 2-3 sentence assessment of how the resume currently positions the candidate for this specific role.",
  "tailored_summary_suggestion": "A compelling 3-4 sentence professional summary tailored specifically to the job description.",
  "bullet_improvements": [
    {{
      "original_concept": "Brief description of an existing weak or generic bullet from resume",
      "improved_bullet": "Rewritten bullet point using strong action verbs, quantifiable metrics, and STAR method (Situation, Task, Action, Result).",
      "reason": "Why this revision increases ATS ranking and recruiter impact."
    }},
    {{
      "original_concept": "Second bullet to improve",
      "improved_bullet": "Rewritten bullet point with impact",
      "reason": "Explanation"
    }},
    {{
      "original_concept": "Third bullet to improve",
      "improved_bullet": "Rewritten bullet point with impact",
      "reason": "Explanation"
    }}
  ],
  "keyword_integration_tips": [
    "Tip 1 on where and how to integrate missing technical keywords naturally.",
    "Tip 2 on soft skills or terminology.",
    "Tip 3 on industry standards."
  ],
  "action_verbs_recommended": ["Engineered", "Orchestrated", "Accelerated", "Spearheaded", "Optimized", "Automated"],
  "recruiter_verdict": "A brief conclusion rating the candidate's interview readiness for this role."
}}
"""

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            raw_response = response.text.strip()
            # Clean possible markdown wrapping if returned
            if raw_response.startswith("```"):
                raw_response = re.sub(r'^```(?:json)?\n', '', raw_response)
                raw_response = re.sub(r'\n```$', '', raw_response)

            data = json.loads(raw_response)
            data["source"] = f"Gemini AI ({model_name})"
            data["success"] = True
            return data

        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def _generate_contextual_fallback(
        cls,
        resume_data: Dict[str, Any],
        job_description: str,
        match_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates contextual, actionable suggestions using algorithmic intelligence when API key is not configured.
        """
        matched = match_analysis.get("matched_skills", [])
        missing = match_analysis.get("missing_skills", [])
        score = match_analysis.get("overall_match_percentage", 50)
        contact = resume_data.get("contact", {})
        cand_name = contact.get("name") or "Professional"

        # Action verbs pool
        action_verbs = [
            "Architected", "Spearheaded", "Streamlined", "Accelerated",
            "Deployed", "Engineered", "Automated", "Orchestrated", "Benchmarked"
        ]

        # Dynamic bullet points based on missing skills or existing experience
        experience_items = resume_data.get("experience", [])
        bullet_improvements = []

        if missing:
            top_missing = missing[:3]
            bullet_improvements.append({
                "original_concept": f"General development mentioning {matched[0] if matched else 'core tasks'}",
                "improved_bullet": f"Engineered scalable solutions leveraging {', '.join(top_missing)}, boosting process execution efficiency by 32% and reducing operational latency.",
                "reason": f"Directly addresses high-priority missing technical keywords: {', '.join(top_missing)}."
            })
            bullet_improvements.append({
                "original_concept": "Collaborated with team to ship features",
                "improved_bullet": "Spearheaded cross-functional sprint deliverables in an Agile environment, partnering with product managers to deliver 5+ key milestones 2 weeks ahead of schedule.",
                "reason": "Quantifies delivery velocity and emphasizes cross-functional leadership."
            })
            bullet_improvements.append({
                "original_concept": "Responsible for maintaining and debugging services",
                "improved_bullet": "Automated regression testing and CI/CD deployment pipelines, decreasing incident resolution time (MTTR) by 45% across production environments.",
                "reason": "Replaces passive duty description ('Responsible for') with active results-driven phrasing."
            })
        else:
            bullet_improvements.append({
                "original_concept": "Worked on backend APIs and database queries",
                "improved_bullet": "Architected high-throughput RESTful microservices handling 100K+ daily requests, optimizing database query indexing to achieve sub-50ms latency.",
                "reason": "Demonstrates architectural scale and measurable system performance."
            })
            bullet_improvements.append({
                "original_concept": "Assisted in frontend UI development",
                "improved_bullet": "Engineered responsive, accessible user interfaces compliant with WCAG standards, improving user retention and page interaction time by 28%.",
                "reason": "Highlights design accessibility and measurable business metrics."
            })
            bullet_improvements.append({
                "original_concept": "Participated in weekly standups and code reviews",
                "improved_bullet": "Conducted rigorous peer code reviews and mentored junior engineers, reducing post-release defect density by 22% across 8 consecutive sprints.",
                "reason": "Showcases seniority, code quality ownership, and team mentorship."
            })

        # Dynamic Tailored Summary
        key_matches = ", ".join(matched[:4]) if matched else "software development and problem-solving"
        target_focus = missing[0] if missing else "scalable technologies"
        tailored_summary = (
            f"Results-oriented professional with demonstrated proficiency in {key_matches}. "
            f"Track record of designing reliable, high-performance systems and rapidly integrating modern frameworks like {target_focus}. "
            f"Eager to leverage strong technical foundation and analytical problem-solving to drive immediate business value for this role."
        )

        keyword_tips = [
            f"Integrate missing core skills ({', '.join(missing[:4]) if missing else 'industry-standard tools'}) in your technical skills grid and project descriptions.",
            "Use the STAR method (Situation, Task, Action, Result) for every bullet point to make accomplishments measurable.",
            "Mirror the exact job title and specialized vocabulary from the job description in your professional headline."
        ]

        verdict = (
            f"Candidate profile currently exhibits an estimated {score}% alignment. "
            "Incorporating the recommended high-frequency keywords and quantified bullet points will substantially increase recruiter callback rates."
        )

        return {
            "success": True,
            "source": "Contextual AI Engine (Local)",
            "summary_critique": f"The resume demonstrates good baseline competencies in {key_matches}, but requires closer keyword alignment with the job description's specific toolchain.",
            "tailored_summary_suggestion": tailored_summary,
            "bullet_improvements": bullet_improvements,
            "keyword_integration_tips": keyword_tips,
            "action_verbs_recommended": action_verbs,
            "recruiter_verdict": verdict
        }
