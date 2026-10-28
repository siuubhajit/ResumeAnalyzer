import os
import json
import io
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

from modules.extractor import ResumeExtractor
from modules.parser import ResumeParser
from modules.analyzer import ResumeAnalyzer
from modules.ai_suggester import AISuggester

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-secret-resume-analyzer')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10 MB limit


@app.route('/')
def index():
    """Renders the main application dashboard."""
    return render_template('index.html')


@app.route('/api/sample-jobs', methods=['GET'])
def get_sample_jobs():
    """Returns bundled sample job descriptions for quick testing."""
    sample_path = os.path.join(app.root_path, 'sample_data', 'sample_jobs.json')
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        return jsonify({"success": True, "jobs": jobs})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to load sample jobs: {str(e)}"}), 500


@app.route('/api/sample-resumes', methods=['GET'])
def get_sample_resumes():
    """Returns available pre-configured sample resumes."""
    samples = [
        {
            "id": "alex_turner_swe",
            "name": "Alex Turner",
            "role": "Full Stack Software Engineer (Python, React, AWS, Docker)",
            "file": "alex_turner_swe.pdf"
        },
        {
            "id": "priya_patel_data_scientist",
            "name": "Priya Patel",
            "role": "AI / Machine Learning Engineer (PyTorch, NLP, Python, SQL)",
            "file": "priya_patel_data_scientist.pdf"
        }
    ]
    return jsonify({"success": True, "resumes": samples})


@app.route('/api/sample-resumes/<sample_id>/pdf', methods=['GET'])
def download_sample_pdf(sample_id):
    """Serves the selected sample PDF for direct viewing or downloading."""
    allowed_samples = {
        "alex_turner_swe": "alex_turner_swe.pdf",
        "priya_patel_data_scientist": "priya_patel_data_scientist.pdf"
    }

    if sample_id not in allowed_samples:
        return jsonify({"success": False, "error": "Sample resume not found"}), 404

    filename = allowed_samples[sample_id]
    file_path = os.path.join(app.root_path, 'sample_data', 'sample_resumes', filename)

    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "Sample file does not exist on disk"}), 404

    return send_file(file_path, mimetype='application/pdf', as_attachment=False, download_name=filename)


@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    """
    Main analysis endpoint.
    Processes uploaded PDF resume or pre-configured sample resume,
    extracts information, computes match score against the job description,
    and generates AI-powered recommendations.
    """
    try:
        job_description = request.form.get('job_description', '').strip()
        sample_id = request.form.get('sample_id', '').strip()

        # 1. Validate Job Description
        if not job_description:
            return jsonify({
                "success": False,
                "error": "Please provide a job description to compare your resume against."
            }), 400

        if len(job_description) < 25:
            return jsonify({
                "success": False,
                "error": "The job description is too short. Please provide a more detailed job posting (at least 25 characters)."
            }), 400

        # 2. Handle File Input (Uploaded file or Sample file)
        pdf_stream = None
        source_filename = "Uploaded Resume"

        if sample_id:
            allowed_samples = {
                "alex_turner_swe": "alex_turner_swe.pdf",
                "priya_patel_data_scientist": "priya_patel_data_scientist.pdf"
            }
            if sample_id in allowed_samples:
                file_path = os.path.join(app.root_path, 'sample_data', 'sample_resumes', allowed_samples[sample_id])
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        pdf_stream = io.BytesIO(f.read())
                    source_filename = allowed_samples[sample_id]

        if pdf_stream is None:
            if 'resume' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "Please upload a resume in PDF format or choose a sample resume."
                }), 400

            uploaded_file = request.files['resume']
            is_valid, error_msg = ResumeExtractor.validate_file(uploaded_file)
            if not is_valid:
                return jsonify({"success": False, "error": error_msg}), 400

            source_filename = secure_filename(uploaded_file.filename) or "resume.pdf"
            pdf_stream = uploaded_file.stream

        # 3. Extract text and metadata via PyMuPDF
        extraction_result = ResumeExtractor.extract_from_stream(pdf_stream)
        if not extraction_result.get("success"):
            return jsonify({
                "success": False,
                "error": extraction_result.get("error", "Failed to extract text from PDF.")
            }), 422

        extracted_text = extraction_result.get("text", "")

        # 4. Parse resume content into structured data
        parsed_resume = ResumeParser.parse_resume(extracted_text)

        # 5. Perform match analysis against Job Description
        match_analysis = ResumeAnalyzer.analyze(parsed_resume, job_description)

        # 6. Generate AI-powered improvement suggestions
        ai_recommendations = AISuggester.get_suggestions(
            resume_data=parsed_resume,
            job_description=job_description,
            match_analysis=match_analysis
        )

        return jsonify({
            "success": True,
            "filename": source_filename,
            "document_stats": {
                "page_count": extraction_result.get("page_count", 1),
                "word_count": extraction_result.get("word_count", 0),
                "char_count": extraction_result.get("char_count", 0),
                "metadata": extraction_result.get("metadata", {})
            },
            "candidate_profile": {
                "contact": parsed_resume.get("contact", {}),
                "education": parsed_resume.get("education", []),
                "experience": parsed_resume.get("experience", []),
                "projects": parsed_resume.get("projects", []),
                "certifications": parsed_resume.get("certifications", []),
                "sections_detected": parsed_resume.get("sections_present", [])
            },
            "analysis": match_analysis,
            "ai_suggestions": ai_recommendations
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An unexpected error occurred during analysis: {str(e)}"
        }), 500


@app.route('/api/improve-bullet', methods=['POST'])
def improve_bullet():
    """
    Assistant endpoint to rewrite an individual resume bullet point or accomplishment
    with action verbs and quantified impact metrics.
    """
    data = request.get_json() or {}
    bullet = data.get('bullet', '').strip()
    target_role = data.get('target_role', '').strip()

    if not bullet:
        return jsonify({"success": False, "error": "Please provide a bullet point to improve."}), 400

    # Provide dynamic rewrites
    rewrites = [
        {
            "version": "Metric-Driven (STAR)",
            "text": f"Spearheaded {bullet.lower() if not bullet.startswith(('Lead', 'Built', 'Managed')) else bullet}, driving a 30%+ increase in process velocity and reducing cycle times across team workflows.",
            "focus": "Quantified results & velocity"
        },
        {
            "version": "Leadership & Scale",
            "text": f"Architected and deployed scalable solutions for {bullet.lower()}, collaborating cross-functionally with senior stakeholders to guarantee 99.9% reliability.",
            "focus": "High availability & cross-functional impact"
        },
        {
            "version": "Concise ATS Action",
            "text": f"Engineered, tested, and optimized {bullet.lower()}, adhering to industry best practices and achieving zero critical defects post-release.",
            "focus": "Quality standards & precision"
        }
    ]

    return jsonify({"success": True, "original": bullet, "rewrites": rewrites})


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": "The uploaded file is too large. Maximum allowed file size is 10 MB."
    }), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Resource not found."}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": "Internal server error occurred."}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
