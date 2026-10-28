import re
from typing import Dict, List, Any, Tuple
import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None

from modules.parser import ResumeParser


class ResumeAnalyzer:
    """
    Performs comprehensive analysis comparing a parsed resume with a job description:
    - TF-IDF Cosine Similarity
    - Skill alignment (matched, missing, bonus)
    - Domain category breakdown
    - Weighted overall match score
    - ATS friendliness check & score
    - Strengths and areas for improvement
    """

    @classmethod
    def analyze(cls, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Executes complete match analysis between resume and job description.
        """
        clean_jd = job_description.strip()
        resume_text = resume_data.get("raw_text", "")

        # 1. Skill Extraction from Job Description
        jd_skills = ResumeParser.extract_skills(clean_jd)
        resume_skills = resume_data.get("skills", {"by_category": {}, "flat_list": []})

        resume_flat_set = set(resume_skills.get("flat_list", []))
        jd_flat_set = set(jd_skills.get("flat_list", []))

        # Skill matching comparison
        matched_skills = sorted(list(resume_flat_set.intersection(jd_flat_set)))
        missing_skills = sorted(list(jd_flat_set.difference(resume_flat_set)))
        additional_skills = sorted(list(resume_flat_set.difference(jd_flat_set)))

        # Category-wise skill comparison
        category_breakdown = cls.compute_category_breakdown(
            resume_skills.get("by_category", {}),
            jd_skills.get("by_category", {})
        )

        # 2. TF-IDF Cosine Similarity Calculation
        tfidf_similarity = cls.compute_tfidf_similarity(resume_text, clean_jd)

        # 3. Technical vs Soft Skill Overlap
        tech_matched, tech_missing, tech_score = cls.calculate_subset_overlap(
            resume_skills.get("by_category", {}),
            jd_skills.get("by_category", {}),
            is_soft=False
        )
        soft_matched, soft_missing, soft_score = cls.calculate_subset_overlap(
            resume_skills.get("by_category", {}),
            jd_skills.get("by_category", {}),
            is_soft=True
        )

        # 4. ATS Friendly Audit & Score
        ats_audit = cls.audit_ats_friendliness(resume_data)

        # 5. Composite Weighted Match Score
        overall_match = cls.calculate_overall_score(
            tfidf_score=tfidf_similarity,
            tech_score=tech_score,
            soft_score=soft_score,
            ats_score=ats_audit["score"],
            has_jd_skills=len(jd_flat_set) > 0
        )

        # 6. Strengths and Areas for Improvement
        strengths, improvements = cls.generate_strengths_and_improvements(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            overall_match=overall_match,
            ats_audit=ats_audit,
            resume_data=resume_data
        )

        return {
            "overall_match_percentage": round(overall_match, 1),
            "similarity_score": round(tfidf_similarity, 1),
            "tech_skill_score": round(tech_score, 1),
            "soft_skill_score": round(soft_score, 1),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "additional_skills": additional_skills,
            "category_breakdown": category_breakdown,
            "ats_audit": ats_audit,
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "total_skills_found_in_resume": len(resume_flat_set),
            "total_skills_required_in_jd": len(jd_flat_set)
        }

    @classmethod
    def compute_tfidf_similarity(cls, text_a: str, text_b: str) -> float:
        """
        Calculates cosine similarity between two texts using TF-IDF representation.
        """
        if not text_a or not text_b:
            return 0.0

        if TfidfVectorizer is None or cosine_similarity is None:
            # Fallback to Jaccard word set similarity if sklearn is missing
            words_a = set(re.findall(r'\b[a-zA-Z]{3,}\b', text_a.lower()))
            words_b = set(re.findall(r'\b[a-zA-Z]{3,}\b', text_b.lower()))
            if not words_a or not words_b:
                return 0.0
            return float((len(words_a.intersection(words_b)) / len(words_a.union(words_b))) * 100)

        try:
            # Clean and vectorize
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=5000,
                token_pattern=r'(?u)\b[a-zA-Z0-9_.+#-]+\b'
            )
            tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            # Convert cosine score (0.0 - 1.0) to 0.0 - 100.0 with gentle scaling
            # In real-world resume matching, TF-IDF cosine between a resume and JD typically ranges from 0.15 to 0.65
            scaled = min(100.0, float(sim * 140))
            return max(0.0, scaled)
        except Exception:
            return 0.0

    @classmethod
    def calculate_subset_overlap(
        cls,
        resume_by_cat: Dict[str, List[str]],
        jd_by_cat: Dict[str, List[str]],
        is_soft: bool = False
    ) -> Tuple[List[str], List[str], float]:
        """Calculates matched, missing, and percentage score for technical or soft skills."""
        target_category = "soft_skills" if is_soft else None

        if is_soft:
            res_skills = set(resume_by_cat.get("soft_skills", []))
            jd_skills = set(jd_by_cat.get("soft_skills", []))
        else:
            res_skills = set()
            jd_skills = set()
            for cat, items in resume_by_cat.items():
                if cat != "soft_skills":
                    res_skills.update(items)
            for cat, items in jd_by_cat.items():
                if cat != "soft_skills":
                    jd_skills.update(items)

        matched = sorted(list(res_skills.intersection(jd_skills)))
        missing = sorted(list(jd_skills.difference(res_skills)))

        if not jd_skills:
            # If JD specified no specific skills of this type, award baseline 80% if resume has skills
            score = 80.0 if res_skills else 50.0
        else:
            score = (len(matched) / len(jd_skills)) * 100.0

        return matched, missing, min(100.0, score)

    @staticmethod
    def compute_category_breakdown(
        resume_cats: Dict[str, List[str]],
        jd_cats: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, Any]]:
        """Computes matching statistics for each skill category."""
        breakdown = {}
        category_names = [
            ("programming_languages", "Programming Languages"),
            ("frameworks_libraries", "Frameworks & Libraries"),
            ("databases", "Databases & Storage"),
            ("cloud_devops", "Cloud & DevOps"),
            ("ai_ml_data", "AI, ML & Data Science"),
            ("tools_platforms", "Developer Tools"),
            ("soft_skills", "Soft Skills & Management")
        ]

        for key, display_name in category_names:
            res_list = set(resume_cats.get(key, []))
            jd_list = set(jd_cats.get(key, []))

            matched = sorted(list(res_list.intersection(jd_list)))
            missing = sorted(list(jd_list.difference(res_list)))
            resume_only = sorted(list(res_list.difference(jd_list)))

            total_jd = len(jd_list)
            match_rate = round((len(matched) / total_jd * 100), 1) if total_jd > 0 else (100.0 if res_list else 0.0)

            breakdown[key] = {
                "display_name": display_name,
                "matched": matched,
                "missing": missing,
                "resume_only": resume_only,
                "matched_count": len(matched),
                "required_count": total_jd,
                "match_rate": match_rate
            }

        return breakdown

    @staticmethod
    def calculate_overall_score(
        tfidf_score: float,
        tech_score: float,
        soft_score: float,
        ats_score: float,
        has_jd_skills: bool
    ) -> float:
        """
        Computes composite match score.
        Weights:
        - Technical skills: 40%
        - TF-IDF content similarity: 35%
        - Soft skills: 15%
        - ATS & completeness: 10%
        """
        if not has_jd_skills:
            # If JD lacks identifiable keywords, rely primarily on TF-IDF and structure
            overall = (0.70 * tfidf_score) + (0.30 * ats_score)
        else:
            overall = (
                (0.40 * tech_score) +
                (0.35 * tfidf_score) +
                (0.15 * soft_score) +
                (0.10 * ats_score)
            )

        return max(5.0, min(99.0, overall))

    @staticmethod
    def audit_ats_friendliness(resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits resume against Applicant Tracking System (ATS) parsing standards.
        Returns a score (0-100) and specific checklist findings.
        """
        score = 100
        checks = []

        contact = resume_data.get("contact", {})
        sections = resume_data.get("sections_present", [])
        raw_text = resume_data.get("raw_text", "")
        word_count = len(raw_text.split())

        # 1. Email check
        if contact.get("email"):
            checks.append({
                "label": "Email Contact",
                "passed": True,
                "details": f"Found: {contact['email']}"
            })
        else:
            score -= 15
            checks.append({
                "label": "Email Contact",
                "passed": False,
                "details": "No valid email address detected. Vital for recruiter outreach."
            })

        # 2. Phone check
        if contact.get("phone"):
            checks.append({
                "label": "Phone Number",
                "passed": True,
                "details": f"Found: {contact['phone']}"
            })
        else:
            score -= 10
            checks.append({
                "label": "Phone Number",
                "passed": False,
                "details": "No direct phone number detected."
            })

        # 3. LinkedIn / Professional Profile
        if contact.get("linkedin") or contact.get("github"):
            checks.append({
                "label": "Professional Links",
                "passed": True,
                "details": "LinkedIn or GitHub profile link detected."
            })
        else:
            score -= 5
            checks.append({
                "label": "Professional Links",
                "passed": False,
                "details": "No LinkedIn or GitHub links detected. Adding portfolio links boosts recruiter trust."
            })

        # 4. Standard Core Sections
        essential_sections = ["experience", "education", "skills"]
        missing_essentials = [s for s in essential_sections if s not in sections]
        if not missing_essentials:
            checks.append({
                "label": "Core Section Structure",
                "passed": True,
                "details": "All standard sections (Experience, Education, Skills) are well organized."
            })
        else:
            score -= (len(missing_essentials) * 12)
            checks.append({
                "label": "Core Section Structure",
                "passed": False,
                "details": f"Missing or non-standard headers: {', '.join([s.title() for s in missing_essentials])}."
            })

        # 5. Word Count Check
        if 350 <= word_count <= 1100:
            checks.append({
                "label": "Document Length",
                "passed": True,
                "details": f"Optimal length ({word_count} words). Fits standard 1-2 page resume."
            })
        elif word_count < 350:
            score -= 10
            checks.append({
                "label": "Document Length",
                "passed": False,
                "details": f"Too brief ({word_count} words). Expand on achievements, duties, and project metrics."
            })
        else:
            score -= 8
            checks.append({
                "label": "Document Length",
                "passed": False,
                "details": f"Lengthy ({word_count} words). Aim for a concise 1-2 page format."
            })

        # 6. Quantifiable Metrics & Action Orientation
        metrics_found = len(re.findall(r'\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?[kmb]?|\b\d+\+\s*(?:users|clients|projects|features)', raw_text, re.IGNORECASE))
        if metrics_found >= 3:
            checks.append({
                "label": "Quantifiable Achievements",
                "passed": True,
                "details": f"Found {metrics_found} quantifiable metrics (percentages, revenues, user numbers)."
            })
        else:
            score -= 8
            checks.append({
                "label": "Quantifiable Achievements",
                "passed": False,
                "details": "Few measurable impact figures found. Include metrics like '% increased', 'X users served', or '$ revenue generated'."
            })

        final_score = max(20, min(100, score))

        return {
            "score": final_score,
            "rating": "Excellent" if final_score >= 85 else ("Good" if final_score >= 70 else "Needs Improvement"),
            "checks": checks
        }

    @staticmethod
    def generate_strengths_and_improvements(
        matched_skills: List[str],
        missing_skills: List[str],
        overall_match: float,
        ats_audit: Dict[str, Any],
        resume_data: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Generates clear, dynamic strengths and improvement points based on real data."""
        strengths = []
        improvements = []

        # Strengths
        if matched_skills:
            top_matches = ", ".join(matched_skills[:5])
            strengths.append(f"Demonstrates key required competencies including: {top_matches}.")

        if ats_audit.get("score", 0) >= 80:
            strengths.append("Clear, ATS-compliant section structure and complete contact coordinates.")

        edu = resume_data.get("education", [])
        if edu:
            strengths.append("Structured educational qualifications aligned with typical role prerequisites.")

        exp = resume_data.get("experience", [])
        if exp and len(exp) >= 2:
            strengths.append(f"Demonstrated career progression across {len(exp)} documented roles/positions.")

        if overall_match >= 75:
            strengths.append("Strong overall vocabulary and keyword overlap with the target job profile.")
        elif not strengths:
            strengths.append("Foundational skills present; adaptable for entry to mid-level alignment.")

        # Areas for Improvement
        if missing_skills:
            top_missing = ", ".join(missing_skills[:5])
            improvements.append(f"Add target keywords required by the job posting: {top_missing}.")

        # Check ATS audit items
        for check in ats_audit.get("checks", []):
            if not check.get("passed"):
                improvements.append(check.get("details"))

        if overall_match < 60:
            improvements.append("Tailor project and experience bullet points using terminology directly from the job description.")

        if not improvements:
            improvements.append("Consider adding specific certifications or recent project links to reinforce your match.")

        return strengths[:5], improvements[:5]

