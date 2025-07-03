import uuid
import json
from processing.extractors.pdf_extractor import PDFExtractor
from processing.normalizers.role_metadata_extractor import RoleMetadataExtractor
from services.deduplicator import Deduplicator
from typing import Dict, Optional

class UploadPipeline:
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.metadata_extractor = RoleMetadataExtractor()

    async def process(self, file_bytes: bytes, filename: str) -> Optional[Dict]:
        try:
            print(f"[DEBUG] Starting processing for file: {filename}")
            # 1. Deduplication check
            file_hash = await Deduplicator.get_file_hash(file_bytes)
            if await Deduplicator.is_duplicate(file_hash):
                print("[DEBUG] Duplicate file detected")
                return None

            # 2. Extract and clean text
            print("[DEBUG] Extracting text from PDF...")
            extracted = await self.pdf_extractor.extract(file_bytes)
            print(f"[DEBUG] Extracted text length: {len(extracted.get('raw_text', ''))} chars")
            
            if not extracted or 'raw_text' not in extracted or not extracted['raw_text'].strip():
                print("[ERROR] No text was extracted from the PDF")
                return None

            # 3. Extract metadata + classify role
            print("[DEBUG] Extracting metadata...")
            result = await self.metadata_extractor.extract(extracted["raw_text"])
            print(f"[DEBUG] Metadata extraction result: {bool(result)}")
            print(f"[DEBUG] Extracted role: {result.get('role', 'unknown')}")

            # 4. Prepare Pinecone-compatible metadata
            pinecone_metadata = self._prepare_pinecone_metadata(
                result.get("metadata", {}),
                result.get("display_metadata", {}),
                file_hash,
                extracted["is_scanned"],
                extracted["raw_text"][:2000],
                result['role']  # ✅ Pass the role
            )

            print(f"[DEBUG] Pinecone metadata prepared: {list(pinecone_metadata.keys())}")

            # 5. Prepare final payload
            payload = {
                "id": f"cv_{uuid.uuid4().hex[:8]}",
                "embedding_input": extracted["raw_text"],
                "metadata": pinecone_metadata,
                "namespace": f"role_{result.get('role', 'other')}"
            }
            return payload
        except Exception as e:
            print(f"[ERROR] An error occurred during processing: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _prepare_pinecone_metadata(self, metadata: dict, display_metadata: dict, 
                                 file_hash: str, is_scanned: bool, raw_text_snippet: str,
                                 role: str) -> dict:  
        """Convert metadata to Pinecone-compatible format"""
        
        # Extract education information - check both metadata and display_metadata
        education_degrees = []
        education_institutions = []
        
        # First check display_metadata (where the education actually is)
        education_data = display_metadata.get("education", [])
        if not education_data:
            # Fallback to metadata if not in display_metadata
            education_data = metadata.get("education", [])
        
        for edu in education_data:
            if isinstance(edu, str):
                # If it's already a string, try to parse it
                try:
                    # Handle string representation of dict
                    if edu.startswith('{') and edu.endswith('}'):
                        import ast
                        edu_dict = ast.literal_eval(edu)
                        if isinstance(edu_dict, dict):
                            education_degrees.append(str(edu_dict.get("degree", "")).strip())
                            education_institutions.append(str(edu_dict.get("institution", "")).strip())
                    else:
                        education_degrees.append(str(edu).strip())
                except:
                    education_degrees.append(str(edu).strip())
            elif isinstance(edu, dict):
                education_degrees.append(str(edu.get("degree", "")).strip())
                education_institutions.append(str(edu.get("institution", "")).strip())
        
        # Remove empty strings
        education_degrees = [d for d in education_degrees if d]
        education_institutions = [i for i in education_institutions if i]

        # Ensure skills is a list
        skills_data = metadata.get("skills", [])
        if isinstance(skills_data, list):
            skills_list = skills_data
        else:
            skills_list = []

        # Extract experience information - check both metadata and display_metadata
        job_roles = []
        job_companies = []
    
        # First check display_metadata (where the experience actually is)
        experience_data = display_metadata.get("experience", [])
        if not experience_data:
            # Fallback to metadata if not in display_metadata
            experience_data = metadata.get("experience", [])
    
        if isinstance(experience_data, list):
            for exp in experience_data:
                if isinstance(exp, dict):
                    role = exp.get("role") or exp.get("title") or exp.get("position")
                    company = exp.get("company") or exp.get("employer") or exp.get("organization")
                    if role:
                        job_roles.append(str(role).strip())
                if company:
                    job_companies.append(str(company).strip())
    
        # Extract projects - check both locations
        projects = []
        projects_data = display_metadata.get("projects", [])
        if not projects_data:
            projects_data = metadata.get("projects", [])
    
        if isinstance(projects_data, list):
            projects = [str(p).strip() for p in projects_data if p and str(p).strip()]


        # Flat metadata for filtering
        pinecone_metadata = {
            "name": str(metadata.get("name", "")),
            "email": str(metadata.get("email", "")),
            "phone": str(metadata.get("phone", "")),
            "role": str(role),  # ✅ Add missing role field
            "skills": [str(skill) for skill in skills_list if skill],
            "education": [str(degree) for degree in education_degrees if degree],
            "education_institutions": [str(institution) for institution in education_institutions if institution],
            "job_roles":job_roles,
            "job_companies":job_companies,
            "projects":projects,
            "file_hash": str(file_hash).strip(),
            "is_scanned": bool(is_scanned),
            "raw_text": str(raw_text_snippet).strip()
        }

        # Convert display metadata to JSON string
        if display_metadata:
            try:
                pinecone_metadata["display_data"] = json.dumps({
                    "education": display_metadata.get("education", []),
                    "experience": display_metadata.get("experience", []),
                    "projects": display_metadata.get("projects", []),
                    "skills": display_metadata.get("skills", {}),
                    "certifications": display_metadata.get("certifications", []),
                    "references": display_metadata.get("references", [])
                })
            except Exception as e:
                print(f"[WARNING] Failed to serialize display_data: {e}")

        # Debug print before cleanup
        print(f"[DEBUG] Raw metadata before cleanup - job_roles: {pinecone_metadata.get('job_roles')}")
        print(f"[DEBUG] Raw metadata before cleanup - job_companies: {pinecone_metadata.get('job_companies')}")
        print(f"[DEBUG] Raw metadata before cleanup - projects: {pinecone_metadata.get('projects')}")

        # Remove empty values to avoid Pinecone issues
        cleaned_metadata = {k: v for k, v in pinecone_metadata.items() 
                          if v and v != "" and v != []}
        
        print(f"[DEBUG] Final metadata keys: {list(cleaned_metadata.keys())}")
        print(f"[DEBUG] Final metadata - job_roles: {cleaned_metadata.get('job_roles', 'NOT FOUND')}")
        print(f"[DEBUG] Final metadata - job_companies: {cleaned_metadata.get('job_companies', 'NOT FOUND')}")
        print(f"[DEBUG] Final metadata - projects: {cleaned_metadata.get('projects', 'NOT FOUND')}")
        
        return cleaned_metadata