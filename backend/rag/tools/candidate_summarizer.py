from langchain.tools import Tool
from langchain.llms.base import LLM
from typing import List, Dict, Union, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class CandidateSummarizer:
    def __init__(self, llm: LLM, max_workers: int = 3, max_chunks: int = 10):
        """
        Initialize CandidateSummarizer with parallel processing capabilities.
        
        Args:
            llm: Language model instance
            max_workers: Maximum parallel workers for processing chunks
            max_chunks: Maximum number of chunks to process
        """
        self.llm = llm
        self.max_workers = max_workers
        self.max_chunks = max_chunks
    
    def _format_single_chunk(self, chunk: Dict, idx: int) -> Optional[str]:
        """
        Format a single chunk with error handling.
        
        Args:
            chunk: One candidate chunk dictionary
            idx: Index for labeling
            
        Returns:
            Formatted string or None if error
        """
        try:
            if isinstance(chunk, dict):
                text = chunk.get('text', '') or chunk.get('page_content', '')
                meta = chunk.get('metadata', {})
                
                # Build header with candidate name and location if available
                header = f"Candidate {idx + 1}:"
                if meta.get('NAME'):
                    header += f" {meta['NAME']}"
                if meta.get('LOCATION'):
                    header += f" ({meta['LOCATION']})"
                
                # Append score for reference if present
                if 'score' in chunk:
                    header += f" [Score: {chunk['score']:.2f}]"
                
                return f"{header}\n{text.strip()}"
            
            # Fallback formatting if not dict
            return f"Item {idx + 1}:\n{str(chunk)}"
        
        except Exception as e:
            logger.error(f"Error formatting chunk {idx + 1}: {str(e)}")
            return None
    
    def format_chunks(self, chunks: Union[str, List[Dict]], max_chunks: Optional[int] = None) -> str:
        """
        Convert raw chunks into formatted context string with parallel processing.
        
        Args:
            chunks: List of chunk dictionaries or a pre-formatted string
            max_chunks: Optional override for max chunks to process
            
        Returns:
            Joined formatted context string
        """
        if not chunks:
            return ""
        
        if isinstance(chunks, str):
            # Already formatted
            return chunks
        
        # Sort chunks by score descending if available
        if all(isinstance(c, dict) and 'score' in c for c in chunks):
            chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)
        
        max_to_process = max_chunks or self.max_chunks
        if len(chunks) > max_to_process:
            logger.info(f"Limiting chunks from {len(chunks)} to {max_to_process}")
            chunks = chunks[:max_to_process]
        
        formatted_chunks = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(chunks) or 1)) as executor:
            futures = {
                executor.submit(self._format_single_chunk, chunk, idx): idx
                for idx, chunk in enumerate(chunks)
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    # Keep original order by idx
                    formatted_chunks.append((futures[future], result))
        
        # Sort by original chunk order
        formatted_chunks.sort(key=lambda x: x[0])
        
        # Join with double newlines for readability
        return "\n\n".join(chunk for _, chunk in formatted_chunks)

    def generate_response(self, context: str, query: str) -> str:
        """
        Generate LLM response with comprehensive field extraction.
        
        Args:
            context: Formatted candidate context text
            query: User's original query
            
        Returns:
            LLM-generated summary string
        """
        prompt = f"""
[INSTRUCTIONS]
Analyze these candidate profiles and create a detailed report answering:
"{query}"

[REQUIREMENTS]
1. For EACH candidate, include ALL of these sections if available:
   - Full Name
   - Current/Most Recent Role
   - All Education (institutions, degrees, fields of study, dates)
   - All Work Experience (companies, positions, durations, key achievements)
   - All Skills (technical and soft skills)
   - Location
   - Contact Information (if available)
   - Any other relevant details

2. Format:
   - Use clear section headers (##, ###)
   - Use bullet points for lists
   - Include all relevant details, not just one item per category
   - Keep the response organized and easy to read

3. Additional Instructions:
   - Don't skip any fields that are present in the candidate data
   - If a candidate has multiple items in a category (e.g., multiple degrees), list them all
   - Keep the total response under 500 words

[CANDIDATE DATA]
{context}

[RESPONSE FORMAT]
# Candidate Report for: [Query]

## [Candidate Full Name]
### Current/Most Recent Role
- [Role] at [Company] (if available)

### Education
- [Degree] in [Field], [Institution] ([Years])
- [Additional degrees...]

### Work Experience
- [Job Title] at [Company] ([Duration])
  - [Key achievement/responsibility]

### Skills
- [Skill 1], [Skill 2], [Skill 3], ...

### Location
- [City, Country]

[Repeat for each candidate]

## Summary
[Brief summary of findings]
"""
        try:
            response = self.llm.invoke(prompt)
            text = getattr(response, 'content', str(response))
            return text.strip()
        except Exception as e:
            logger.error(f"LLM invocation failed: {str(e)}")
            return "Unable to generate response due to system error."

def candidate_summarizer_tool(
    top_chunks: Union[str, List[Dict]], 
    user_query: str, 
    llm: LLM,
    max_chunks: int = 10,
    max_workers: int = 3
) -> str:
    """
    Process candidate chunks and generate a summary response.
    
    Args:
        top_chunks: List of candidate chunks or pre-formatted string
        user_query: The original user query
        llm: Language model instance
        max_chunks: Maximum number of chunks to process
        max_workers: Number of parallel workers for processing
        
    Returns:
        Formatted response string
    """
    try:
        executor = CandidateSummarizer(llm=llm, max_workers=max_workers, max_chunks=max_chunks)
        formatted_context = executor.format_chunks(top_chunks, max_chunks=max_chunks)

        if not formatted_context.strip():
            return "No relevant candidate information found to process."

        return executor.generate_response(formatted_context, user_query)
    except Exception as e:
        logger.error(f"Error in candidate_summarizer_tool: {str(e)}", exc_info=True)
        return "An error occurred while processing the candidate information."

CandidateSummarizerTool = Tool(
    name="CandidateSummarizer",
    func=candidate_summarizer_tool,
    description="""
    Transforms raw candidate data into professional summaries by:
    1. Extracting key qualifications
    2. Matching experience to query requirements
    3. Presenting in consistent, readable format
    """
)
