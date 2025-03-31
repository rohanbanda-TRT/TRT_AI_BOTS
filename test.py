"""
TRT AI Bots URL Mapping
-----------------------
This file contains the mapping between IP-based URLs and their corresponding domain names
for the TRT AI Bots applications.
"""

# Current IP-based URLs with corresponding Streamlit files
IP_BASED_URLS = {
    "http://13.200.205.196:8501/": "Driver screening API (driver_screening_app.py)",
    "http://13.200.205.196:8502/": "AI content generation API (content_generator.py)",
    "http://13.200.205.196:8503/": "Grammar check API (grammer_check.py)",
    "http://13.200.205.196:8504/": "Performance evaluation API (performance_analyzer.py)",
    "http://13.200.205.196:8506/": "Document RAG API (document_rag_app.py)",
    "http://13.200.205.196:8507/": "Answer verification API (answer_verifier_app.py)",
    "http://13.200.205.196:8508/": "Medical bot API (medical_bot_app.py)",
    "http://13.200.205.196:8509/": "Video transcription API (video_transcription_app.py)",
    "http://13.200.205.196:8510/": "Interior Design bot API (interior_design_app.py)"
}

# New domain-based URLs for the same applications
DOMAIN_BASED_URLS = {
    "trt-demo-driver-screening.demotrt.com": ["driver_screening_app.py", "http://13.200.205.196:8501/"],
    "trt-demo-content-generator.demotrt.com": ["content_generator.py", "http://13.200.205.196:8502/"],
    "trt-demo-grammer-checker.demotrt.com": ["grammer_check.py", "http://13.200.205.196:8503/"],
    "trt-demo-performance-improver.demotrt.com": ["performance_analyzer.py", "http://13.200.205.196:8504/"],
    "trt-demo-document-assistant.demotrt.com": ["document_rag_app.py", "http://13.200.205.196:8506/"],
    "trt-demo-answer-verifier.demotrt.com": ["answer_verifier_app.py", "http://13.200.205.196:8507/"],
    "trt-demo-medical-assistant.demotrt.com": ["medical_bot_app.py", "http://13.200.205.196:8508/"],
    "trt-demo-video-transcriber.demotrt.com": ["video_transcription_app.py", "http://13.200.205.196:8509/"],
    "trt-demo-interior-designer.demotrt.com": ["interior_design_app.py", "http://13.200.205.196:8510/"]
}