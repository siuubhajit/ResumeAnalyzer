import re
from typing import Dict, List, Any, Optional


class ResumeParser:
    """
    Parses resume text into structured components:
    - Contact Information (email, phone, LinkedIn, GitHub, links)
    - Technical and Soft Skills (categorized)
    - Education
    - Work Experience & Internships
    - Projects
    - Certifications
    """

    # Comprehensive skill dictionary organized by domain
    SKILL_TAXONOMY = {
        "programming_languages": [
            "python", "javascript", "typescript", "java", "c++", "c#", "c",
            "go", "golang", "rust", "kotlin", "swift", "ruby", "php", "r",
            "scala", "dart", "shell", "bash", "powershell", "perl", "sql", "matlab"
        ],
        "frameworks_libraries": [
            "react", "react.js", "next.js", "vue", "vue.js", "angular", "node.js",
            "express", "express.js", "flask", "django", "fastapi", "spring",
            "spring boot", "asp.net", ".net", "dotnet", "ruby on rails", "rails",
            "laravel", "tailwind", "tailwind css", "bootstrap", "redux", "svelte",
            "jquery", "graphql", "rest api", "restful api", "grpc"
        ],
        "databases": [
            "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
            "cassandra", "elasticsearch", "firebase", "supabase", "dynamodb",
            "oracle", "bigquery", "mariadb", "couchdb", "neo4j", "snowflake"
        ],
        "cloud_devops": [
            "aws", "amazon web services", "azure", "google cloud", "gcp",
            "docker", "kubernetes", "k8s", "terraform", "ci/cd", "cicd",
            "jenkins", "github actions", "gitlab ci", "ansible", "helm",
            "linux", "unix", "nginx", "apache", "serverless", "cloudformation",
            "prometheus", "grafana"
        ],
        "ai_ml_data": [
            "machine learning", "deep learning", "artificial intelligence", "ai",
            "data science", "pytorch", "tensorflow", "scikit-learn", "sklearn",
            "pandas", "numpy", "scipy", "keras", "nlp", "natural language processing",
            "computer vision", "opencv", "large language models", "llm", "llms",
            "generative ai", "genai", "rag", "hugging face", "langchain",
            "transformers", "data analysis", "matplotlib", "seaborn", "tableau",
            "power bi", "spark", "hadoop", "xgboost"
        ],
        "tools_platforms": [
            "git", "github", "gitlab", "bitbucket", "jira", "confluence",
            "postman", "figma", "vs code", "visual studio", "docker desktop",
            "pycharm", "intellij", "webpack", "vite", "npm", "yarn", "pnpm"
        ],
        "soft_skills": [
            "leadership", "communication", "teamwork", "collaboration",
            "problem solving", "critical thinking", "time management",
            "adaptability", "flexibility", "mentorship", "work ethic",
            "attention to detail", "emotional intelligence", "decision making",
            "project management", "conflict resolution", "creativity",
            "agile", "scrum", "interpersonal skills", "presentation"
        ]
    }

    # Common section header patterns
    SECTION_PATTERNS = {
        "education": r"(?i)(?:^|\n)(?:education|academic\s+background|qualifications|academic\s+history)\b",
        "experience": r"(?i)(?:^|\n)(?:work\s+experience|professional\s+experience|experience|employment\s+history|internships?|work\s+history)\b",
        "skills": r"(?i)(?:^|\n)(?:skills|technical\s+skills|core\s+competencies|technologies|proficiencies|tools\s+&\s+technologies)\b",
        "projects": r"(?i)(?:^|\n)(?:projects|key\s+projects|academic\s+projects|personal\s+projects|technical\s+projects)\b",
        "certifications": r"(?i)(?:^|\n)(?:certifications?|licenses?|credentials|certificates|courses)\b",
        "summary": r"(?i)(?:^|\n)(?:summary|professional\s+summary|objective|career\s+objective|about\s+me|profile)\b"
    }

    @classmethod
    def parse_resume(cls, text: str) -> Dict[str, Any]:
        """
        Parses resume text into a structured dictionary.
        """
        contact = cls.extract_contact_info(text)
        sections = cls.split_into_sections(text)
        skills = cls.extract_skills(text)
        education = cls.extract_education(sections.get("education", "") or text)
        experience = cls.extract_experience(sections.get("experience", "") or text)
        projects = cls.extract_projects(sections.get("projects", "") or text)
        certifications = cls.extract_certifications(sections.get("certifications", "") or text)

        return {
            "contact": contact,
            "sections_present": list(sections.keys()),
            "sections_content": sections,
            "skills": skills,
            "education": education,
            "experience": experience,
            "projects": projects,
            "certifications": certifications,
            "raw_text": text
        }

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, Any]:
        """Extracts email, phone number, LinkedIn, GitHub, and portfolio links."""
        contact = {
            "name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "portfolio": "",
            "links": []
        }

        # 1. Email extraction
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        emails = re.findall(email_pattern, text)
        if emails:
            contact["email"] = emails[0].strip()

        # 2. Phone extraction (international and US/India formats)
        phone_pattern = r'(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{10,13})'
        phones = re.findall(phone_pattern, text)
        for phone in phones:
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            if 10 <= len(cleaned_phone) <= 15:
                contact["phone"] = phone.strip()
                break

        # 3. LinkedIn
        linkedin_pattern = r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/(?:in|profile)\/([a-zA-Z0-9_-]+)'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact["linkedin"] = linkedin_match.group(0).strip()

        # 4. GitHub
        github_pattern = r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_-]+)'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            contact["github"] = github_match.group(0).strip()

        # 5. Generic URLs / Portfolios
        url_pattern = r'https?:\/\/(?!www\.linkedin\.com|www\.github\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?'
        urls = re.findall(url_pattern, text)
        if urls:
            contact["portfolio"] = urls[0].strip()
            contact["links"] = [u.strip() for u in urls[:5]]

        # 6. Candidate Name heuristic (first 1-3 lines before email/phone)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:4]:
            # If line does not have email, phone, url, or common resume titles
            if (not re.search(email_pattern, line) and
                not re.search(r'\d{3}', line) and
                not re.search(r'(?i)(curriculum|resume|page|email|phone|github)', line) and
                len(line.split()) <= 4 and len(line) < 40):
                contact["name"] = line
                break

        return contact

    @classmethod
    def split_into_sections(cls, text: str) -> Dict[str, str]:
        """
        Splits text into logical resume sections by identifying major headers.
        """
        matches = []
        for sec_name, pattern in cls.SECTION_PATTERNS.items():
            for m in re.finditer(pattern, text):
                matches.append((m.start(), sec_name, m.group(0)))

        # Sort matches by character position in the document
        matches.sort(key=lambda x: x[0])

        sections = {}
        for i, (start_idx, sec_name, matched_text) in enumerate(matches):
            end_idx = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            # Content after the header title
            content = text[start_idx + len(matched_text):end_idx].strip()
            # If section already encountered, append
            if sec_name in sections:
                sections[sec_name] += "\n" + content
            else:
                sections[sec_name] = content

        return sections

    @classmethod
    def extract_skills(cls, text: str) -> Dict[str, Any]:
        """
        Extracts skills by matching against the comprehensive skill taxonomy.
        Returns grouped skills and a flat list of unique skills.
        """
        lower_text = " " + text.lower() + " "
        detected_categories = {}
        all_skills_flat = set()

        for category, skill_list in cls.SKILL_TAXONOMY.items():
            found_in_cat = []
            for skill in skill_list:
                # Skill matching with word boundary protection
                # Handle special characters like c++, c#, .net, node.js
                escaped = re.escape(skill)
                # Word boundary check, allowing for punctuation
                pattern = r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'
                if re.search(pattern, lower_text):
                    found_in_cat.append(skill)
                    all_skills_flat.add(skill)

            detected_categories[category] = sorted(found_in_cat)

        return {
            "by_category": detected_categories,
            "flat_list": sorted(list(all_skills_flat)),
            "technical_count": sum(
                len(skills) for cat, skills in detected_categories.items() if cat != "soft_skills"
            ),
            "soft_count": len(detected_categories.get("soft_skills", []))
        }

    @staticmethod
    def extract_education(edu_text: str) -> List[Dict[str, str]]:
        """
        Extracts educational degrees, majors, institutions, and years.
        """
        degrees = []
        degree_patterns = [
            r"(?i)\b(b\.?s\.?c?|bachelor(?:'s)?(?:\s+of\s+[a-zA-Z\s]+)?|b\.?tech|b\.?e\.?)\b",
            r"(?i)\b(m\.?s\.?c?|master(?:'s)?(?:\s+of\s+[a-zA-Z\s]+)?|m\.?tech|m\.?e\.?|m\.?b\.?a\.?)\b",
            r"(?i)\b(ph\.?d\.?|doctor(?:ate)?(?:\s+of\s+[a-zA-Z\s]+)?)\b",
            r"(?i)\b(associate(?:'s)?\s+degree|diploma)\b"
        ]

        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        gpa_pattern = r'(?i)\b(?:gpa|cgpa|grade)[:\s]*([0-4](?:\.\d{1,2})?|[0-9](?:\.\d{1,2})?)\s*(?:\/\s*(?:4|10)(?:\.0)?)?'

        lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
        current_entry = None

        for line in lines:
            has_degree = False
            for pat in degree_patterns:
                m = re.search(pat, line)
                if m:
                    has_degree = True
                    break

            if has_degree or any(kw in line.lower() for kw in ["university", "institute", "college", "school"]):
                years = re.findall(year_pattern, line)
                gpa_match = re.search(gpa_pattern, line)

                entry = {
                    "text": line,
                    "degree": m.group(0).strip() if has_degree and m else "",
                    "institution": "",
                    "year": " - ".join(years) if years else "",
                    "gpa": gpa_match.group(1).strip() if gpa_match else ""
                }

                # Try to extract institution name if keyword exists
                inst_match = re.search(r'(?i)([A-Za-z\s]+(?:University|Institute|College|Academy|School)[A-Za-z\s]*)', line)
                if inst_match:
                    entry["institution"] = inst_match.group(1).strip()

                degrees.append(entry)

        return degrees[:5]

    @staticmethod
    def extract_experience(exp_text: str) -> List[Dict[str, Any]]:
        """
        Extracts job entries, dates, company names, and bullet points.
        """
        entries = []
        date_pattern = r'(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}\s*(?:-|–|to)\s*(?:present|current|\w+\.?\s+\d{4})|\b\d{4}\s*(?:-|–|to)\s*(?:present|current|\d{4})\b'
        lines = [l.strip() for l in exp_text.split('\n') if l.strip()]

        current_entry = None

        for line in lines:
            date_match = re.search(date_pattern, line)
            is_bullet = bool(re.match(r'^[-•*▪]\s*', line))

            if date_match and not is_bullet:
                # New role found
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    "title_line": line,
                    "date_range": date_match.group(0).strip(),
                    "bullets": []
                }
            elif is_bullet and current_entry:
                cleaned_bullet = re.sub(r'^[-•*▪]\s*', '', line).strip()
                if cleaned_bullet:
                    current_entry["bullets"].append(cleaned_bullet)
            elif current_entry and len(current_entry["bullets"]) < 8 and len(line) > 20:
                current_entry["bullets"].append(line)

        if current_entry:
            entries.append(current_entry)

        # If no entries found with date patterns, create a structured summary from bullet lines
        if not entries:
            bullets = [re.sub(r'^[-•*▪]\s*', '', l) for l in lines if len(l) > 25][:6]
            if bullets:
                entries.append({
                    "title_line": "Experience Highlights",
                    "date_range": "Not specified",
                    "bullets": bullets
                })

        return entries[:6]

    @staticmethod
    def extract_projects(proj_text: str) -> List[Dict[str, Any]]:
        """Extracts key projects and highlights."""
        projects = []
        lines = [l.strip() for l in proj_text.split('\n') if l.strip()]
        current_project = None

        for line in lines:
            is_bullet = bool(re.match(r'^[-•*▪]\s*', line))
            if not is_bullet and (len(line) < 70 or "|" in line or ":" in line) and not line.endswith('.'):
                if current_project:
                    projects.append(current_project)
                current_project = {
                    "name": line,
                    "details": []
                }
            elif is_bullet and current_project:
                current_project["details"].append(re.sub(r'^[-•*▪]\s*', '', line))
            elif current_project and len(line) > 20:
                current_project["details"].append(line)

        if current_project:
            projects.append(current_project)

        return projects[:6]

    @staticmethod
    def extract_certifications(cert_text: str) -> List[str]:
        """Extracts list of certifications and licenses."""
        cert_lines = []
        lines = [l.strip() for l in cert_text.split('\n') if l.strip()]
        for line in lines:
            cleaned = re.sub(r'^[-•*▪\d\.]\s*', '', line).strip()
            if 4 <= len(cleaned) <= 120:
                cert_lines.append(cleaned)
        return cert_lines[:8]

