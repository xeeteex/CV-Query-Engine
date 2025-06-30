from typing import List, Dict, Optional, Tuple, Any
import json
from datetime import datetime
from langchain.tools import Tool
import logging
import re

logger = logging.getLogger(__name__)

class ExperienceScorer:
    SENIORITY_WEIGHTS = {
        'principal': 1.5,
        'lead': 1.4,
        'senior': 1.3,
        'manager': 1.3,
        'mid': 1.1,
        'engineer': 1.0,
        'developer': 1.0,
        'junior': 0.9,
        'intern': 0.6,
        'entry': 0.8
    }

    def __init__(self, query: str = ""):
        self.current_year = datetime.now().year
        self.query_terms = set(term.lower() for term in re.findall(r'\w+', query)) if query else set()

    def parse_duration(self, duration_str: str) -> Optional[Tuple[int, int]]:
        """Extracts start/end years from duration strings"""
        if not duration_str:
            return None

        try:
            if 'present' in duration_str.lower():
                parts = duration_str.split('-')
                start_year = int(parts[0].strip())
                return (start_year, self.current_year)
            if '-' in duration_str:
                start, end = duration_str.split('-')[:2]
                return (int(start.strip()), int(end.strip()))
            if '/' in duration_str:
                dates = [d.strip() for d in duration_str.split('-') if d.strip()]
                if len(dates) >= 2:
                    start_month, start_year = dates[0].split('/')
                    end_month, end_year = dates[1].split('/')
                    return (int(start_year), int(end_year))
        except (ValueError, AttributeError):
            pass
        return None

    def calculate_position_score(self, job: Dict) -> float:
        """Calculate weighted score for a single position"""
        duration = self.parse_duration(job.get('DURATION', ''))
        if not duration:
            return 0.0

        start_year, end_year = duration
        years = max(1, end_year - start_year)

        base_value = years * (1 + 0.1 * years)
        years_ago = self.current_year - end_year
        recency = max(0.8, 1.2 - (years_ago * 0.04))

        title = str(job.get('TITLE', '')).lower()
        seniority = next(
            (weight for term, weight in self.SENIORITY_WEIGHTS.items() if term in title),
            1.0
        )

        domain_boost = 1.0
        job_desc = f"{job.get('TITLE','')} {job.get('COMPANY','')} {job.get('RESPONSIBILITIES','')}".lower()
        if any(term in job_desc for term in self.query_terms if len(term) > 3):
            domain_boost = 1.3

        return base_value * recency * seniority * domain_boost

    def score_candidate(self, experience: List[Dict]) -> float:
        """Calculate total experience score for a candidate"""
        if not experience:
            return 0.0

        total = sum(self.calculate_position_score(job) for job in experience)

        if len(experience) >= 3:
            total *= 1.1

        return round(total, 2)


class ContextAggregator:
    """
    Transforms raw search results into structured summaries with:
    - Experience-prioritized sorting
    - Query-relevant highlighting
    - Consistent profile formatting
    - Selective output by requested fields
    """

    def __init__(self, query: str = "", requested_fields: Optional[List[str]] = None, memory=None):
        self.scorer = ExperienceScorer(query)
        self.query = query
        self.requested_fields = [f.lower() for f in requested_fields] if requested_fields else []
        self.memory = memory  # memory object for retrieving previous context

    def _fetch_memory(self) -> List[Dict]:
        """
        Retrieve relevant stored memory results based on the current query,
        if memory is configured.
        """
        if self.memory is None:
            return []

        try:
            # Check if this is a MongoDB collection
            if hasattr(self.memory, 'find'):
                # Simple text search in the MongoDB collection
                mem_results = list(self.memory.find(
                    {"$text": {"$search": self.query}},
                    {"score": {"$meta": "textScore"}}
                ).sort([("score", {"$meta": "textScore"})]).limit(10))
                
                # Format results to match expected format
                formatted_results = [{
                    "content": f"{doc.get('query', '')}\n{doc.get('response_summary', '')}",
                    "metadata": {
                        "source": "memory",
                        "timestamp": doc.get("timestamp", "").isoformat()
                    },
                    "score": doc.get("score", 0.0)
                } for doc in mem_results]
                
                if formatted_results:
                    logger.info(f"Retrieved {len(formatted_results)} items from memory for query.")
                return formatted_results
                
            # Fallback to query method if available
            elif hasattr(self.memory, 'query'):
                mem_results = self.memory.query(self.query, top_k=10)
                if mem_results:
                    logger.info(f"Retrieved {len(mem_results)} items from memory for query.")
                return mem_results or []
                
            return []
            
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}", exc_info=True)
            return []

    def process_results(self, search_results: List[Dict]) -> List[Dict]:
        """
        Process both fresh search results and memory results,
        combine and score candidates, prepare for aggregation.
        """
        # Fetch memory results and merge with fresh search results
        memory_results = self._fetch_memory()
        combined_results = (search_results or []) + memory_results

        candidates = {}

        for result in combined_results:
            if not isinstance(result, dict):
                continue

            metadata = result.get('metadata', {})
            candidate_id = (
                metadata.get('id')
                or metadata.get('EMAIL')
                or str(hash(json.dumps(metadata, sort_keys=True)))
            )

            if candidate_id not in candidates:
                candidates[candidate_id] = {
                    'metadata': metadata,
                    'experience': self._parse_field(metadata, 'EXPERIENCE'),
                    'skills': self._parse_field(metadata, 'SKILLS'),
                    'score': 0.0,
                    'text_chunks': []
                }

                candidates[candidate_id]['score'] = self.scorer.score_candidate(
                    candidates[candidate_id]['experience']
                )

            text = result.get('text', result.get('page_content', ''))
            if text.strip():
                candidates[candidate_id]['text_chunks'].append({
                    'text': text,
                    'score': float(result.get('score', 0.0))
                })

        return sorted(
            candidates.values(),
            key=lambda x: (x['score'], x['metadata'].get('RELEVANCE', 0.0)),
            reverse=True
        )

    def _parse_field(self, metadata: Dict, field: str) -> List:
        value = metadata.get(field, [])
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [value] if value else []
        return value if isinstance(value, list) else [value]

    def highlight_query_terms(self, text: str) -> str:
        if not self.query:
            return text
        for term in set(term.lower() for term in re.findall(r'\w+', self.query) if len(term) > 3):
            text = re.sub(
                f'({term})',
                r'**\1**',
                text,
                flags=re.IGNORECASE
            )
        return text

    def generate_profile(self, candidate: Dict) -> str:
        parts = []
        meta = candidate['metadata']
        rf = self.requested_fields  # shorthand

        parts.append(
            f"\n## {meta.get('NAME', 'Unnamed Candidate')} "
            f"(Experience Score: {candidate['score']:.1f})"
        )

        if ('contact' in rf or not rf):
            contact = []
            if meta.get('EMAIL'):
                contact.append(f"✉️ {meta['EMAIL']}")
            if meta.get('PHONE'):
                contact.append(f"📞 {meta['PHONE']}")
            if meta.get('LINKEDIN'):
                contact.append(f"🔗 {meta['LINKEDIN']}")
            if contact:
                parts.append("\n" + " | ".join(contact))

        if ('location' in rf or not rf):
            if meta.get('LOCATION'):
                parts.append(f"**Location:** {meta['LOCATION']}")
            if meta.get('CURRENT_COMPANY'):
                parts.append(f"**Current Role:** {meta['CURRENT_COMPANY']}")

        if ('experience' in rf or not rf) and candidate['experience']:
            parts.append("\n### Professional Experience")
            for job in sorted(candidate['experience'], key=lambda j: -self.scorer.calculate_position_score(j))[:3]:
                parts.append(
                    f"- **{job.get('TITLE', 'Unknown Position')}** at *{job.get('COMPANY', 'Unknown')}* ({job.get('DURATION', 'N/A')})"
                )
                responsibilities = job.get('RESPONSIBILITIES', [])
                if isinstance(responsibilities, str):
                    responsibilities = [r.strip() for r in responsibilities.split(';') if r.strip()]
                for resp in responsibilities[:2]:
                    parts.append(f"  - {self.highlight_query_terms(resp)}")

        if ('skills' in rf or not rf) and candidate['skills']:
            parts.append("\n### Technical Skills")
            if isinstance(candidate['skills'], dict):
                for category, items in candidate['skills'].items():
                    parts.append(
                        f"- **{category.title()}:** {', '.join(str(i) for i in items[:8])}{'...' if len(items) > 8 else ''}"
                    )
            else:
                parts.append("- " + ", ".join(str(s) for s in candidate['skills'][:15]))

        if ('excerpts' in rf or not rf) and candidate['text_chunks']:
            parts.append("\n### Relevant Experience Highlights")
            for i, chunk in enumerate(sorted(candidate['text_chunks'], key=lambda x: -x['score'])[:2], start=1):
                highlighted = self.highlight_query_terms(chunk['text'])
                parts.append(
                    f"\n**Excerpt {i}** (Relevance: {chunk['score']:.2f}):\n> {highlighted[:300]}{'...' if len(highlighted) > 300 else ''}"
                )

        return "\n".join(parts)

    def aggregate(self, search_results: List[Dict]) -> str:
        if not search_results:
            return "No matching candidates found."
        profiles = self.process_results(search_results)
        output = [
            f"# Candidate Search Results ({len(profiles)} matches)",
            f"**Query:** {self.query}",
            f"**Sorted by:** Experience Score + Relevance\n"
        ]
        for candidate in profiles:
            output.append(self.generate_profile(candidate))
            output.append("\n---")
        return "\n".join(output)


# LangChain Tool Interface
def aggregate_contexts(search_results: List[dict], query: str = "", max_candidates: int = 10, requested_fields: Optional[List[str]] = None, memory=None):
    if not search_results:
        logger.warning("No search results provided to aggregate_contexts")
        return []

    search_results = sorted(search_results, key=lambda x: x.get('score', 0), reverse=True)
    if len(search_results) > max_candidates:
        logger.info(f"Truncating candidates from {len(search_results)} to {max_candidates}")
        search_results = search_results[:max_candidates]

    aggregator = ContextAggregator(query, requested_fields, memory)
    return aggregator.aggregate(search_results)


ContextAggregatorTool = Tool(
    name="ExperiencePrioritizedContextAggregator",
    func=aggregate_contexts,
    description="""Formats CV search results with:
1. Experience-weighted sorting
2. Query term highlighting
3. Structured profile display
4. Domain-aware scoring
5. Output filtered by requested fields (e.g., skills, experience, location, excerpts, contact)
""",
)
