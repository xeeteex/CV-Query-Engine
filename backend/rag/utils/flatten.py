import os
import json
import re
from typing import Dict, List, Any, Union, Optional
from langchain_mistralai import ChatMistralAI

# Initialize LLM for enhanced extraction
llm = ChatMistralAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-small-latest",
    temperature=0.1,
)

def extract_with_llm(text: str, field: str) -> Any:
    """Enhanced LLM extraction with robust error handling and schema validation"""
    if not text or not text.strip():
        return None
    
    # Define comprehensive extraction schemas for each field
    extraction_schemas = {
        "education": {
            "description": "Extract education history with degree, institution, etc.",
            "required": ["DEGREE"],
            "schema": {
                "DEGREE": "string",
                "INSTITUTION": "string",
                "LOCATION": "string",
                "DURATION": "string",
                "FIELD_OF_STUDY": "string",
                "GRADE": "string",
                "ACHIEVEMENTS": "list"
            },
            "mandatory": True
        },
        "experience": {
            "description": "Extract work experience with company, title, responsibilities",
            "required": ["TITLE"],
            "schema": {
                "TITLE": "string",
                "COMPANY": "string",
                "LOCATION": "string",
                "DURATION": "string",
                "EMPLOYMENT_TYPE": "string",
                "RESPONSIBILITIES": "list",
                "SKILLS": "list",
                "ACHIEVEMENTS": "list"
            },
            "mandatory": True
        },
        "skills": {
            "description": "Extract and categorize technical and soft skills",
            "schema": {
                "TECHNICAL": "list",
                "SOFT_SKILLS": "list",
                "LANGUAGES": "list",
                "TOOLS": "list",
                "CERTIFICATIONS": "list"
            }
        },
        "projects": {
            "description": "Extract projects with technologies and achievements",
            "schema": {
                "NAME": "string",
                "DESCRIPTION": "string",
                "TECHNOLOGIES": "list",
                "DURATION": "string",
                "ACHIEVEMENTS": "list"
            }
        },
        "name": {
            "description": "Extract the candidate's full name",
            "schema": {
                "NAME": "string"
            }
        },
        "languages": {
            "description": "Extract languages with proficiency levels",
            "schema": "list"
        }
    }

    schema = extraction_schemas.get(field.lower(), {})
    if not schema:
        return [] if field.lower() in ["education", "experience"] else {}

    prompt = f"""
    You are a CV parsing expert. Extract ONLY the {field.upper()} information from this CV text.
    
    RULES:
    - Return ONLY valid JSON that matches this schema: {schema['schema']}
    - Required fields: {schema.get('required', [])}
    - For missing data, use empty strings/arrays
    - No explanations or comments
    - Never use markdown formatting
    
    SCHEMA DETAILS:
    {schema['description']}
    
    CV TEXT:
    {text}
    """

    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean response and extract JSON
            content = content.replace('```json', '').replace('```', '').strip()
            result = json.loads(content)
            
            # Validate against schema
            if isinstance(result, dict):
                for req_field in schema.get('required', []):
                    if req_field not in result:
                        result[req_field] = ""
            
            return result
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {field}: {str(e)}")
            if attempt == max_retries - 1:
                if schema.get('mandatory', False):
                    return [{"DEGREE": "Unknown"}] if field == "education" else [{"TITLE": "No experience"}]
                return [] if field.lower() in ["education", "experience"] else {}
    
    return [] if field.lower() in ["education", "experience"] else {}

def clean_text(text: str) -> str:
    """Enhanced text cleaner with better normalization"""
    if not isinstance(text, str):
        return ""
    
    # Normalize whitespace and clean special cases
    text = ' '.join(text.split())
    text = text.strip(" ,;:\u2022-*•")
    
    # Remove standalone numbers or punctuation
    if not re.search(r"[A-Za-z]", text):
        return ""
    
    return text.title() if text.isupper() else text

def clean_metadata_structure(data: Any) -> Any:
    """Recursively clean and validate metadata structure"""
    if isinstance(data, str):
        return clean_text(data)
    elif isinstance(data, list):
        cleaned = [clean_metadata_structure(item) for item in data]
        return [item for item in cleaned if item not in [None, "", []]]
    elif isinstance(data, dict):
        cleaned = {k: clean_metadata_structure(v) for k, v in data.items()}
        return {k: v for k, v in cleaned.items() if v not in [None, "", {}]}
    return data

def extract_metadata_from_cv(cv_text: str) -> dict:
    """Comprehensive metadata extraction with smart fallbacks"""
    if not cv_text or not cv_text.strip():
        return {}

    # Extract basic contact info first
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", cv_text)
    phone_match = re.search(r"(\+?\d[\d\s\-\(\)]{7,})", cv_text)
    linkedin_match = re.search(r"linkedin\.com/[\w\-]+", cv_text, re.I)
    github_match = re.search(r"github\.com/[\w\-]+", cv_text, re.I)

    # Extract all sections using LLM
    metadata = {
        "NAME": extract_with_llm(cv_text, "name").get("NAME", ""),
        "CONTACT": {
            "EMAIL": email_match.group(0) if email_match else "",
            "PHONE": phone_match.group(0) if phone_match else "",
            "LINKEDIN": f"https://www.{linkedin_match.group(0)}" if linkedin_match else "",
            "GITHUB": f"https://www.{github_match.group(0)}" if github_match else ""
        },
        "EDUCATION": extract_with_llm(cv_text, "education") or [],
        "EXPERIENCE": extract_with_llm(cv_text, "experience") or [],
        "SKILLS": extract_with_llm(cv_text, "skills") or {},
        "PROJECTS": extract_with_llm(cv_text, "projects") or [],
        "LANGUAGES": extract_with_llm(cv_text, "languages") or [],
    }

    # Extract certifications from skills if present
    if isinstance(metadata["SKILLS"], dict):
        metadata["CERTIFICATIONS"] = metadata["SKILLS"].pop("CERTIFICATIONS", [])

    return clean_metadata_structure(metadata)

def validate_and_fill_metadata(cv_text: str, metadata: dict) -> dict:
    """Intelligent validation that preserves good data"""
    if not isinstance(metadata, dict):
        return {}
    
    # Name validation
    if not metadata.get("NAME"):
        first_line = cv_text.split('\n')[0].strip()
        if 2 <= len(first_line.split()) <= 4:
            metadata["NAME"] = clean_text(first_line)

    # Education validation
    if not metadata.get("EDUCATION"):
        metadata["EDUCATION"] = [{"DEGREE": "Unknown"}]
    elif isinstance(metadata["EDUCATION"], list):
        for edu in metadata["EDUCATION"]:
            if not edu.get("DEGREE"):
                edu["DEGREE"] = "Unknown"

    # Experience validation
    if not metadata.get("EXPERIENCE"):
        metadata["EXPERIENCE"] = [{"TITLE": "No professional experience"}]
    elif isinstance(metadata["EXPERIENCE"], list):
        for exp in metadata["EXPERIENCE"]:
            if not exp.get("TITLE"):
                exp["TITLE"] = "Unknown position"

    return metadata

def flatten_metadata(metadata: dict, raw_text: str = "") -> dict:
    """
    Optimized flattening that:
    - Preserves nested structures as JSON strings
    - Maintains original data quality
    - Adds debugging information
    """
    if not isinstance(metadata, dict):
        return {}

    # Start with basic fields
    flattened = {
        "NAME": metadata.get("NAME", ""),
        "EMAIL": metadata.get("CONTACT", {}).get("EMAIL", ""),
        "RAW_TEXT_SNIPPET": raw_text[:500]  # Store first 500 chars for context
    }

    # Add complex fields as JSON strings
    complex_fields = [
        "EDUCATION", "EXPERIENCE", "SKILLS", 
        "PROJECTS", "LANGUAGES", "CERTIFICATIONS"
    ]
    
    for field in complex_fields:
        if field in metadata and metadata[field]:
            flattened[field] = json.dumps(metadata[field])

    # Add full metadata for reference
    flattened["FULL_METADATA_JSON"] = json.dumps(metadata)

    # Clean empty values but preserve all valid data
    return {k: v for k, v in flattened.items() if v not in [None, "", "null", "{}", "[]"]}