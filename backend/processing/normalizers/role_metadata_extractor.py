from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai.chat_models import ChatMistralAI
import json
import re
from typing import Dict, List, Optional, Union
from config.settings import settings
from pydantic import BaseModel, validator, Field

# Define structured models for validation
class EducationItem(BaseModel):
    degree: str
    institution: str
    duration: Optional[str] = None
    field_of_study: Optional[str] = None
    location: Optional[str] = None

class ExperienceItem(BaseModel):
    role: str
    company: str
    location: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class SkillsStructure(BaseModel):
    technical: List[str] = []
    tools: List[str] = []
    soft: List[str] = []

class ExtractedMetadata(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []
    skills: Union[List[str], SkillsStructure] = Field(default_factory=list)
    certifications: List[str] = []
    references: List[str] = []
    role: str = "other"

    @validator('role')
    def validate_role(cls, v):
        valid_roles = RoleMetadataExtractor.ROLES + ["network_engineer", "it_support", "other"]
        return v if v in valid_roles else "other"

class RoleMetadataExtractor:
    ROLES =  [
    "Software Engineer",
    "Web Developer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Analyst",
    "Project Manager",
    "Civil Engineer",
    "Electrical Engineer",
    "Mechanical Engineer",
    "Marketing Officer",
    "Sales Executive",
    "Accountant",
    "Finance Officer",
    "Human Resource Manager",
    "Graphic Designer",
    "UI/UX Designer",
    "Content Writer",
    "Digital Marketing Specialist",
    "Customer Service Representative",
    "Administrative Assistant",
    "Operations Manager",
    "IT Officer",
    "Lecturer",
    "School Teacher",
    "Social Worker",
    "Field Officer",
    "Monitoring and Evaluation Officer",
    "Business Development Officer",
    "Network Administrator"
]

    def __init__(self):
        self.llm = ChatMistralAI(
            api_key=settings.MISTRAL_API_KEY,
            temperature=0.1,
            model_name="mistral-medium-latest"
        )
        
        # Simplified and more effective prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a CV parser. Extract information from the CV and return it as valid JSON.

CRITICAL RULES:
1. Extract exact information only - don't infer or add details
2. For skills, categorize into technical skills, tools/software, and soft skills
3. Extract COMPLETE degree names including field of study (e.g., "Bachelor's of Science in Computer Science and Information Technology" NOT just "Bachelor's of Science")
4. Keep descriptions brief and comprehensive
5. Use "Unknown" if information is not clearly stated

Return JSON in this exact format:
{{
  "name": "Full Name it should be a complete name",
  "email": "email@domain.com", 
  "phone": "phone number",
  "education": [
    {{
      "degree": "degree name",
      "institution": "school/university name",
      "duration": "year or date range",
      "field_of_study": "subject area",
      "location": "city, country"
    }}
  ],
  "experience": [
    {{
      "role": "job title",
      "company": "company name", 
      "location": "city, country",
      "duration": "date range",
      "description": "brief description of key responsibilities"
    }}
  ],
  "skills": {{
    "technical": ["list of technical skills"],
    "tools": ["list of tools/software"],
    "soft": ["list of soft skills"]
  }},
  "certifications": ["list of certifications"],
  "references": ["reference names and titles"],
  "role": "primary_role_classification"
}}

EDUCATION EXTRACTION RULES:
- If degree shows "Bachelor's of Science in Computer Science", extract the FULL title
- If degree shows "BscIT" or "BSc IT", expand to "Bachelor's of Science in Information Technology"
- If degree shows "MSc", expand to "Master's of Science"
- Always include the field of study in the degree name


Role classification guidelines:
- network_engineer: Network, telecom, infrastructure, FTTH, GPON, fiber
- it_support: Technical support, troubleshooting, system administration, hardware
- software_engineer: Programming, development, coding, software design, application
- data_scientist: Data analysis, ML, statistics, data mining, research, modeling
- devops_engineer: DevOps, CI/CD, cloud, automation, deployment, containers
- product_manager: Product management, strategy, roadmap, user feedback, planning
- project_manager: Project management, coordination, timeline, stakeholder, budget
- qa_engineer: Testing, quality assurance, bugs, test cases, automation testing
- ui_ux_designer: UI/UX, user interface, user experience, prototyping, wireframes, Figma
- graphic_designer: Graphic design, Adobe, Photoshop, Illustrator, visual content
- business_analyst: Business analysis, requirements, stakeholder, process improvement
- marketing_specialist: Marketing, SEO, campaigns, branding, digital marketing
- hr_specialist: Recruitment, HR, employee relations, onboarding, payroll
- finance_officer: Finance, accounting, budgeting, audit, reconciliation
- sales_executive: Sales, lead generation, customer acquisition, CRM, negotiation
- civil_engineer: Construction, design, estimation, site supervision, drawings
- teacher: Teaching, curriculum, lesson planning, classroom, student engagement
- social_worker: Social work, community, field visits, advocacy, NGO programs
- other: If doesn't fit above categories

IMPORTANT: 
- Return ONLY valid JSON, no extra text
- Ensure all brackets and quotes are properly closed
- Extract complete degree titles with field of study"""),
            ("human", "Extract comprehensive information from this CV:\n\n{text}")
        ])

    async def extract(self, text: str) -> Dict:
        """Extract metadata from CV text"""
        # Clean the text
        cleaned_text = self._clean_text(text)
        
        # Default result structure
        default_result = {
            "metadata": {
                "name": "",
                "email": "",
                "education": [],
                "education_institutions": [],
                "job_roles": [],
                "job_companies": [],
                "projects": [],
                "skills": [],
                "certifications": [],
                "references": []
            },
            "display_metadata": {
                "education": [],
                "experience": [],
                "projects": [],
                "skills": {"technical": [], "tools": [], "soft": []},
                "references": [],
                "certifications": []
            },
            "role": "other"
        }

        try:
            # Limit text length for LLM processing
            text_chunk = cleaned_text[:9000]
            
            # Get LLM response
            chain = self.prompt | self.llm
            response = await chain.ainvoke({"text": text_chunk})
            
            # Print raw LLM response
            print("\n=== LLM RAW RESPONSE ===")
            print(response.content if hasattr(response, 'content') else str(response))
            print("=== END LLM RESPONSE ===\n")
            
            # Extract and parse JSON
            content = response.content if hasattr(response, 'content') else str(response)
            parsed_data = self._parse_json_response(content)
            
            if not parsed_data:
                print("LLM extraction failed, using fallback")
                return self._fallback_extraction(text) or default_result
                
            # Validate and format
            validated = self._validate_and_clean(parsed_data)
            return self._format_output(validated)
            
        except Exception as e:
            print(f"Extraction error: {str(e)}")
            return self._fallback_extraction(text) or default_result

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts and format text"""
        # Fix common OCR errors
        fixes = {
            '9': 't', 'ﬁ': 'fi', 'ﬀ': 'ff',
            'Communica-on': 'Communication',
            'organiza9on': 'organization',
            'connec9vity': 'connectivity'
        }
        
        cleaned = text
        for wrong, correct in fixes.items():
            cleaned = cleaned.replace(wrong, correct)
        
        # Remove null chars and normalize whitespace
        cleaned = cleaned.replace('\u0000', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Extract and parse JSON from LLM response"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None

    def _validate_and_clean(self, data: Dict) -> Dict:
        """Validate and clean extracted data"""
        cleaned_data = {}
        
        # Basic contact info
        cleaned_data['name'] = str(data.get('name', '')).strip()
        cleaned_data['email'] = str(data.get('email', '')).strip()
     
        
        # Education
        education = data.get('education', [])
        cleaned_data['education'] = []
        for edu in education if isinstance(education, list) else []:
            if isinstance(edu, dict):
                cleaned_data['education'].append({
                    'degree': str(edu.get('degree', '')).strip(),
                    'institution': str(edu.get('institution', '')).strip(),
                    'duration': str(edu.get('duration', '')).strip(),
                    'field_of_study': str(edu.get('field_of_study', '')).strip(),
                    'location': str(edu.get('location', '')).strip()
                })
        
        # Experience
        experience = data.get('experience', [])
        cleaned_data['experience'] = []
        for exp in experience if isinstance(experience, list) else []:
            if isinstance(exp, dict):
                cleaned_data['experience'].append({
                    'role': str(exp.get('role', '')).strip(),
                    'company': str(exp.get('company', '')).strip(),
                    'location': str(exp.get('location', '')).strip(),
                    'duration': str(exp.get('duration', '')).strip(),
                    'description': str(exp.get('description', '')).strip()
                })
        
        # Projects
        projects = data.get('projects', [])
        cleaned_data['projects'] = []
        for proj in projects if isinstance(projects, list) else []:
            if isinstance(proj, dict):
                technologies = proj.get('technologies', [])
                if isinstance(technologies, list):
                    tech_list = [str(t).strip() for t in technologies if t]
                else:
                    tech_list = []
                
                cleaned_data['projects'].append({
                    'name': str(proj.get('name', '')).strip(),
                    'description': str(proj.get('description', '')).strip(),
                    'technologies': tech_list,
                    'duration': str(proj.get('duration', '')).strip()
                })

        # Skills
        skills = data.get('skills', {})
        if isinstance(skills, dict):
            cleaned_data['skills'] = {
                'technical': [str(s).strip() for s in skills.get('technical', []) if s],
                'tools': [str(s).strip() for s in skills.get('tools', []) if s],
                'soft': [str(s).strip() for s in skills.get('soft', []) if s]
            }
        else:
            # Handle legacy list format
            skill_list = skills if isinstance(skills, list) else []
            cleaned_data['skills'] = {
                'technical': [str(s).strip() for s in skill_list if s],
                'tools': [],
                'soft': []
            }
        
        # Other fields
        cleaned_data['certifications'] = [str(c).strip() for c in data.get('certifications', []) if c]
        cleaned_data['references'] = [str(r).strip() for r in data.get('references', []) if r]
        
        # Role classification
        role = str(data.get('role', 'other')).lower()
        cleaned_data['role'] = role if role in [r.lower() for r in self.ROLES] + ['other'] else 'other'
        
        return cleaned_data

    def _format_output(self, data: Dict) -> Dict:
        """Format data for final output"""
        skills_dict = data.get('skills', {'technical': [], 'tools': [], 'soft': []})
        all_skills = skills_dict.get('technical', []) + skills_dict.get('tools', []) + skills_dict.get('soft', [])
        
        return {
            "metadata": {
                "name": data.get('name', ''),
                "email": data.get('email', ''),
                "phone": data.get('phone', ''),
                "education": [str(e) for e in data.get('education', [])],
                "education_institutions": data.get('education_institutions', []),
                "job_roles": data.get('job_roles', []),
                "job_companies": data.get('job_companies', []),
                "projects": data.get('projects', []),
                "skills": all_skills,
                "certifications": data.get('certifications', []),
                "references": data.get('references', [])
            },
            "display_metadata": {
                "education": data.get('education', []),
                "experience": data.get('experience', []),
                "projects": data.get('projects', []),
                "skills": skills_dict,
                "certifications": data.get('certifications', []),
                "references": data.get('references', [])
            },
            "role": data.get('role', 'other')
        }

    def _fallback_extraction(self, text: str) -> Optional[Dict]:
        """Simple regex-based fallback extraction"""
        try:
            # Extract basic info using regex
            name_match = re.search(r'^([A-Z][A-Z\s]+)', text.strip())
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
            
            # Simple skills extraction
            skills = []
            technical_keywords = ['python', 'javascript', 'java', 'react', 'angular', 'vue', 'node', 'django', 'flask', 'html', 'css', 'sql', 'mongodb', 'postgresql', 'git', 'docker', 'kubernetes', 'aws', 'azure', 'linux', 'windows', 'flutter', 'dart', 'c++', 'c#', 'php', 'laravel', 'bootstrap', 'firebase', 'rest api', 'graphql']
            tools_keywords = ['github', 'gitlab', 'jira', 'confluence', 'slack', 'figma', 'photoshop', 'illustrator', 'sketch', 'visual studio', 'vscode', 'intellij', 'eclipse', 'postman', 'swagger']
            soft_keywords = ['teamwork', 'leadership', 'communication', 'problem solving', 'analytical', 'creative', 'adaptable', 'organized', 'detail oriented', 'time management']

            text_lower = text.lower()
            technical_skills = [keyword.title() for keyword in technical_keywords if keyword in text_lower]
            tool_skills = [keyword.title() for keyword in tools_keywords if keyword in text_lower]
            soft_skills = [keyword.title() for keyword in soft_keywords if keyword in text_lower]
            
            # Basic education extraction
            education_patterns = [
                r'bachelor[\'s]*\s+(?:of\s+)?(?:science|arts|engineering|technology)(?:\s+in\s+[\w\s]+)?',
                r'master[\'s]*\s+(?:of\s+)?(?:science|arts|engineering|technology)(?:\s+in\s+[\w\s]+)?',
                r'phd|doctorate|ph\.d\.?',
                r'diploma\s+in\s+[\w\s]+',
                r'certificate\s+in\s+[\w\s]+'
            ]

            return {
                "metadata": {
                    "name": name_match.group(1).strip() if name_match else "",
                    "email": email_match.group(1) if email_match else "",
                    "phone": re.sub(r'[^\d+]', '', phone_match.group(1)) if phone_match else "",
                    "education": [],
                    "education_institutions": [],
                    "job_roles": [],
                    "job_companies": [],
                    "projects": [],
                    "skills": technical_skills + tool_skills + soft_skills,
                    "certifications": [],
                    "references": []
                },
                "display_metadata": {
                    "education": [],
                    "experience": [],
                    "projects": [],
                    "skills": {"technical": technical_skills, "tools": tool_skills, "soft": soft_skills},
                    "certifications": [],
                    "references": []
                },
                "role": "other"
            }
        except Exception:
            return None