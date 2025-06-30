import json
import logging
from typing import List, Dict, Union, Any
from pydantic import BaseModel
from langchain.tools import Tool
from langchain.llms.base import LLM

logger = logging.getLogger(__name__)

class CandidateProfile(BaseModel):
    name: str = "Candidate"
    location: str = ""
    experience: List[Dict] = []
    skills: Dict[str, List[str]] = {}
    education: List[Dict] = []
    contact: Dict = {}
    summary: str = ""
    raw_data: Dict = {}
    query_relevance: Dict = {}

class QueryAwareSynthesizer:
    def __init__(self, llm: LLM):
        self.llm = llm

    def _parse_field(self, field: Any) -> Union[List, Dict]:
        if isinstance(field, str):
            try:
                return json.loads(field)
            except json.JSONDecodeError:
                try:
                    return json.loads(field.replace('\\"', '"').replace("'", '"'))
                except json.JSONDecodeError:
                    return [] if field.strip().startswith('[') else {}
        return field or ([] if isinstance(field, list) else {})

    def _extract_query_focus(self, query: str, candidate: Dict) -> Dict:
        focus = {}
        query_lower = query.lower()

        field_triggers = {
            'experience': ['experience', 'years', 'senior', 'junior'],
            'skills': ['skill', 'technology', 'python', 'java', 'aws', 'react'],
            'education': ['education', 'degree', 'university', 'college'],
            'location': ['location', 'city', 'remote', 'hybrid']
        }

        for field, triggers in field_triggers.items():
            if any(trigger in query_lower for trigger in triggers):
                focus[field] = self._parse_field(candidate.get(field.upper(), candidate.get(field)))

        return focus

    def _format_skills(self, skills: Union[Dict, List]) -> str:
        if isinstance(skills, dict):
            return ', '.join(f"{k}: {', '.join(v[:3])}" for k, v in skills.items())
        return ', '.join(str(s) for s in skills[:5]) if isinstance(skills, list) else ''

    def _format_education(self, education: List) -> str:
        if not isinstance(education, list):
            return ''
        formatted = []
        for edu in education[:3]:
            degree = edu.get('DEGREE', 'Degree')
            inst = edu.get('INSTITUTION', '')
            loc = edu.get('LOCATION', '')
            grade = edu.get('GRADE', '')
            parts = [degree, inst]
            if loc:
                parts.append(loc)
            if grade:
                parts.append(f"Grade: {grade}")
            formatted.append(' - '.join(parts))
        return '; '.join(formatted)

    def _build_query_aware_prompt(self, candidate: Dict, query: str) -> str:
        focus = self._extract_query_focus(query, candidate)
        prompt_parts = [
            f"Create a professional summary for {candidate.get('name', 'Candidate')}",
            f"focusing on aspects relevant to: '{query}'",
            "\nKey Qualifications:"
        ]

        if 'experience' in focus and focus['experience']:
            prompt_parts.append(f"- Experience: {len(focus['experience'])} relevant positions")
        if 'skills' in focus and focus['skills']:
            prompt_parts.append(f"- Skills: {self._format_skills(focus['skills'])}")
        if 'education' in focus and focus['education']:
            prompt_parts.append(f"- Education: {self._format_education(focus['education'])}")
        if 'location' in focus and focus['location']:
            prompt_parts.append(f"- Location: {focus['location']}")

        prompt_parts.append("\nConcise Professional Summary:")
        return "\n".join(prompt_parts)

    def generate_summary(self, candidate: Dict, query: str = "") -> str:
        try:
            if not query:
                prompt = f"Summarize this candidate: {json.dumps(candidate, indent=2)}"
            else:
                prompt = self._build_query_aware_prompt(candidate, query)
            response = self.llm.invoke(prompt)
            return str(getattr(response, 'content', response)).strip()
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Summary not available"
            
    def batch_generate_summaries(self, candidates: List[Dict], queries: List[str]) -> List[str]:
        if not candidates:
            return []
            
        # If queries not provided, use empty strings
        if not queries:
            queries = [""] * len(candidates)
            
        # Prepare batch prompts
        prompts = []
        for candidate, query in zip(candidates, queries):
            if not query:
                prompts.append(f"Summarize this candidate: {json.dumps(candidate, indent=2)}")
            else:
                prompts.append(self._build_query_aware_prompt(candidate, query))
                
        try:
            # Use batch inference if supported
            if hasattr(self.llm, 'batch'):
                responses = self.llm.batch(prompts)
                return [str(getattr(r, 'content', r)).strip() for r in responses]
            else:
                # Fallback to sequential processing
                return [self.generate_summary(c, q) for c, q in zip(candidates, queries)]
        except Exception as e:
            logger.error(f"Batch summary generation failed: {e}")
            return ["Summary not available"] * len(candidates)

    def process_candidate(self, raw_data: Dict, query: str = "") -> CandidateProfile:
        education = self._parse_field(raw_data.get('EDUCATION', []))
        # fallback to FULL_METADATA_JSON if empty
        if not education:
            full_meta = raw_data.get('FULL_METADATA_JSON')
            if full_meta:
                try:
                    meta = self._parse_field(full_meta)
                    if isinstance(meta, dict) and 'EDUCATION' in meta:
                        education = self._parse_field(meta['EDUCATION'])
                except Exception as e:
                    logger.warning(f"Failed to parse FULL_METADATA_JSON for education: {e}")

        parsed_data = {
            'name': raw_data.get('NAME', raw_data.get('name', 'Candidate')),
            'location': raw_data.get('LOCATION', ''),
            'experience': self._parse_field(raw_data.get('EXPERIENCE', [])),
            'skills': self._parse_field(raw_data.get('SKILLS', {})),
            'education': education,
            'contact': self._parse_field(raw_data.get('CONTACT', {})),
            'raw_data': raw_data,
            'query_relevance': self._extract_query_focus(query, raw_data)
        }
        parsed_data['summary'] = self.generate_summary(parsed_data, query)
        return CandidateProfile(**parsed_data)

def synthesizer_tool(
    answer: str,
    top_chunks: List[Dict],
    llm: LLM,
    query: str = "",
    batch_size: int = 10  # Increased default batch size for better performance
) -> List[Dict]:
    if not top_chunks:
        logger.warning("No chunks provided to synthesizer")
        return []

    synthesizer = QueryAwareSynthesizer(llm)
    summaries = []
    
    # Process in batches
    for i in range(0, len(top_chunks), batch_size):
        batch = top_chunks[i:i + batch_size]
        batch_metadatas = [chunk.get("metadata", {}) for chunk in batch]
        
        try:
            # Use batch processing for better performance
            batch_summaries = synthesizer.batch_generate_summaries(
                batch_metadatas, 
                [query] * len(batch_metadatas)  # Same query for all in batch
            )
            
            # Process successful batch
            for metadata, summary in zip(batch_metadatas, batch_summaries):
                summaries.append({
                    "name": metadata.get("NAME", metadata.get("name", "Unknown")),
                    "summary": summary,
                    "metadata": metadata,
                    "score": metadata.get("score", 0.0)
                })
                
        except Exception as e:
            logger.error(f"Batch processing failed, falling back to individual processing: {e}", exc_info=True)
            # Fallback to individual processing if batch fails
            for chunk in batch:
                try:
                    metadata = chunk.get("metadata", {})
                    summary = synthesizer.generate_summary(metadata, query)
                    summaries.append({
                        "name": metadata.get("NAME", metadata.get("name", "Unknown")),
                        "summary": summary,
                        "metadata": metadata,
                        "score": metadata.get("score", 0.0)
                    })
                except Exception as ex:
                    logger.error(f"Error processing candidate individually: {ex}")
                    # Add a placeholder for failed candidates
                    summaries.append({
                        "name": metadata.get("NAME", metadata.get("name", "Unknown")),
                        "summary": "Summary not available due to processing error",
                        "metadata": metadata,
                        "score": metadata.get("score", 0.0)
                    })

    summaries.sort(key=lambda x: x.get("score", 0), reverse=True)
    return summaries


# Original Tool declaration (you can modify as needed)
Synthesizer = Tool(
    name="Synthesizer",
    func=lambda answer, chunks, llm, query="": synthesizer_tool(answer, chunks, llm, query),
    description="Enhanced candidate synthesizer with proper EDUCATION parsing and query-aware summaries."
)
