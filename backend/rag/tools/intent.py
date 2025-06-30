from langchain.tools import Tool
from langchain.llms.base import LLM
import json

# You should inject your own LLM instance when using this tool
llm: LLM = None  # Set this at runtime or via dependency injection

def intent_rating_tool(query: str) -> dict:
    """
    Analyzes the user's query to extract structured information for search.
    Returns a dict with extracted fields, their confidence scores,
    and a list of fields actually requested in the query.
    """
    # Handle "who is" queries as general information requests (case-insensitive)
    lower_query = query.lower()
    if lower_query.startswith('who is'):
        name = query[6:].strip()
        return {
            "intent": "GeneralInfo",
            "name": name if name else None,
            "skills": [],
            "experience": {},
            "roles": [],
            "location": None,
            "education": [],
            "certifications": [],
            "projects": [],
            "languages": [],
            "confidence": 0.95,
            "requested_fields": ["name"]
        }

    prompt = f"""
    Analyze the following job candidate search query and extract structured information.
    
    # AVAILABLE FIELDS TO EXTRACT
    # ---------------------------
    # - SKILLS: Technical skills, tools, programming languages (e.g., "Python", "React", "AWS")
    # - EXPERIENCE: Years of experience (e.g., "5+", "junior", "senior")
    # - ROLES: Job titles or roles (e.g., "developer", "data scientist")
    # - LOCATION: Geographic location (e.g., "Kathmandu", "remote")
    # - EDUCATION: Degrees or education level (e.g., "PhD", "computer science")
    # - CERTIFICATIONS: Professional certifications (e.g., "AWS Certified")
    # - PROJECTS: Specific project experience (e.g., "machine learning project")
    # - LANGUAGES: Spoken languages (e.g., "English", "Nepali")
    
    # RESPONSE FORMAT
    # --------------
    # Return a JSON object with these fields:
    # - intent: One of ["GeneralInfo", "SkillMatch", "RoleSearch", "ExperienceFilter", "LocationSearch", "EducationSearch", "MultiCriteria"]
    # - name: Extracted name if query is a "who is" question
    # - skills: List of extracted skills/tools/languages
    # - experience: Dict with min/max years if specified
    # - roles: List of job titles/roles
    # - location: Location string if specified
    # - education: List of education criteria
    # - certifications: List of certifications
    # - projects: List of project experiences
    # - languages: List of spoken languages
    # - confidence: Float between 0 and 1
    # - requested_fields: List of fields explicitly requested by the user in the query (e.g., ["skills", "location"])

    # EXAMPLES
    # --------
    # Query: "Senior Python developers in Kathmandu with 5+ years experience"
    # {{
    #     "intent": "MultiCriteria",
    #     "skills": ["Python"],
    #     "experience": {{"min": 5}},
    #     "roles": ["developer"],
    #     "location": "Kathmandu",
    #     "confidence": 0.95,
    #     "requested_fields": ["skills", "experience", "roles", "location"]
    # }}
    #
    # Query: "Show me candidates who know React and Node.js"
    # {{
    #     "intent": "SkillMatch",
    #     "skills": ["React", "Node.js"],
    #     "confidence": 0.9,
    #     "requested_fields": ["skills"]
    # }}
    #
    # Query: "Who is John Doe"
    # {{
    #     "intent": "GeneralInfo",
    #     "name": "John Doe",
    #     "confidence": 0.95,
    #     "requested_fields": ["name"]
    # }}
    #
    # ACTUAL QUERY TO PROCESS
    # ---------------------
    Query: {query}
    
    Respond ONLY with the JSON object, no other text or explanation.
    """
    if llm is None:
        raise ValueError("LLM instance not set for intent tool.")
    response = llm.invoke(prompt)
    # langchain ChatModels often return objects with `.content`
    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)
    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        parsed = json.loads(json_str)

        # Defensive: Ensure requested_fields exists and matches non-empty fields
        requested_fields = []
        for field in ["skills", "experience", "roles", "location", "education", "certifications", "projects", "languages"]:
            value = parsed.get(field)
            if value:
                # For experience, check if dict with values
                if field == "experience" and isinstance(value, dict) and any(v is not None for v in value.values()):
                    requested_fields.append(field)
                elif field != "experience":
                    requested_fields.append(field)
        parsed["requested_fields"] = parsed.get("requested_fields", requested_fields)

        return parsed
    except Exception as e:
        print("[DEBUG] Intent tool parsing error:", e, "Raw response:", response_text)
        return {
            "intent": None,
            "skills": [],
            "experience": {},
            "roles": [],
            "location": None,
            "education": [],
            "certifications": [],
            "projects": [],
            "languages": [],
            "confidence": 0.0,
            "requested_fields": []
        }

IntentRating = Tool(
    name="IntentRating",
    func=intent_rating_tool,
    description="Classifies user intent and extracts fields for downstream query planning."
)
