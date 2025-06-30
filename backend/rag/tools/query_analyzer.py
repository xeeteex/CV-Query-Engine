from typing import Dict, Optional, Union, List, Tuple
from pydantic import BaseModel
import re
import logging
from langchain.tools import Tool
from langchain.llms.base import LLM

logger = logging.getLogger(__name__)

class ToxicityLevels:
    MILD = 1
    MODERATE = 2
    SEVERE = 3

class QueryResponse(BaseModel):
    """Enhanced response format with toxicity scoring"""
    should_process: bool = False
    immediate_response: Optional[str] = None
    modified_query: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_toxic: bool = False
    toxicity_level: Optional[int] = None
    toxicity_categories: List[str] = []
    is_greeting: bool = False

class QueryAnalyzer:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.greetings = {
            "hello", "hi", "hey", "greetings", 
            "good morning", "good afternoon", "good evening"
        }
        self.small_talk_phrases = {
            "how are you", "what's up", "who are you",
            "what can you do", "tell me about yourself"
        }

        # Tiered toxicity patterns with severity scores
        self.toxic_patterns = [
            # Mild (profanity, mild insults)
            (r"\b(dumb|stupid|idiot|fool|shit|damn)\b", ToxicityLevels.MILD, "profanity"),
            
            # Moderate (stronger insults, discriminatory terms)
            (r"\b(retard|moron|asshole|bitch|bastard)\b", ToxicityLevels.MODERATE, "insult"),
            (r"\b(hate\b.*\b(you|people))\b", ToxicityLevels.MODERATE, "hate_speech"),
            
            # Severe (threats, extreme discrimination)
            (r"\b(kill\b.*\b(yourself|others))\b", ToxicityLevels.SEVERE, "threat"),
            (r"\b(rape|murder|suicide)\b", ToxicityLevels.SEVERE, "violence"),
            (r"\b(nigger|fag|chink|spic)\b", ToxicityLevels.SEVERE, "slur"),
            (r"\b(women|men|blacks|whites)\s+(are|should)\s+(stupid|die)\b", ToxicityLevels.SEVERE, "discrimination")
        ]

    def _detect_toxicity(self, query: str) -> Dict:
        """Enhanced toxicity detection with severity scoring"""
        detected_level = 0
        categories = set()
        
        for pattern, level, category in self.toxic_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                detected_level = max(detected_level, level)
                categories.add(category)
        
        if detected_level > 0:
            safe_query = self._rewrite_query(query, detected_level)
            return {
                "is_toxic": True,
                "toxicity_level": detected_level,
                "toxicity_categories": list(categories),
                "rejection_reason": self._get_rejection_message(detected_level, categories),
                "safe_query": safe_query
            }
        return {"is_toxic": False}

    def _get_rejection_message(self, level: int, categories: List[str]) -> str:
        """Generates appropriate rejection message based on severity"""
        if level == ToxicityLevels.MILD:
            return "Please maintain professional language"
        elif level == ToxicityLevels.MODERATE:
            return "Inappropriate language detected"
        else:  # SEVERE
            return "Query violates content policy"

    def _rewrite_query(self, query: str, toxicity_level: int) -> Optional[str]:
        """Adaptive query sanitization based on toxicity level"""
        prompt = f"""Rewrite this query to be professional while preserving intent:
        
        Original: {query}
        
        Rules:
        1. Remove all inappropriate language
        2. Maintain professional tone
        3. {"Only preserve core meaning" if toxicity_level >= ToxicityLevels.MODERATE else "Keep original intent"}
        4. {"Remove any discriminatory content" if toxicity_level == ToxicityLevels.SEVERE else ""}
        
        Rewritten Query:"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip() if hasattr(response, "content") else str(response).strip()
        except Exception as e:
            logger.error(f"Query rewrite failed: {str(e)}")
            return None

    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting"""
        clean_query = query.lower().strip("?!.,")
        return (
            clean_query in self.greetings or
            any(clean_query.startswith(g) for g in self.greetings)
        )

    def _is_small_talk(self, query: str) -> bool:
        """Check for conversational queries"""
        query_lower = query.lower()
        return any(phrase in query_lower for phrase in self.small_talk_phrases)

    def _generate_response(self, query: str) -> str:
        """Generate professional responses to greetings/small talk"""
        prompt = f"""You're a professional CV search assistant. Respond to this user message in 1-2 sentences:

        User: {query}

        Professional Response:"""
        
        try:
            response = self.llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            return text.strip()
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return "Hello! I'm your CV search assistant. How can I help?"

    def analyze(self, query: str) -> QueryResponse:
        """Enhanced analysis pipeline with toxicity scoring"""
        if not query.strip():
            return QueryResponse(
                immediate_response="Please provide a search query about candidates.",
                should_process=False
            )

        # Check for greetings/small talk
        if self._is_greeting(query) or self._is_small_talk(query):
            return QueryResponse(
                immediate_response=self._generate_response(query),
                should_process=False,
                is_greeting=True
            )

        # Enhanced toxicity check
        toxicity = self._detect_toxicity(query)
        if toxicity["is_toxic"]:
            return QueryResponse(
                is_toxic=True,
                toxicity_level=toxicity.get("toxicity_level"),
                toxicity_categories=toxicity.get("toxicity_categories", []),
                rejection_reason=toxicity.get("rejection_reason"),
                modified_query=toxicity.get("safe_query"),
                should_process=toxicity.get("safe_query") is not None
            )

        # All checks passed - process normally
        return QueryResponse(
            should_process=True,
            modified_query=query
        )

def create_query_analyzer_tool(llm: LLM) -> Tool:
    analyzer = QueryAnalyzer(llm)
    return Tool(
        name="Query_Analyzer",
        func=analyzer.analyze,
        description="""
        Enhanced query processing with:
        1. Multi-level toxicity detection (mild/moderate/severe)
        2. Greeting/small talk handling
        3. Adaptive query rewriting
        """
    )