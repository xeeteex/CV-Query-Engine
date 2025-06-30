from langchain.tools import Tool
import uuid
import json
from typing import List, Dict, Optional
from ..pinecone_client import query_chunks  # Your existing Pinecone query logic
import logging

logger = logging.getLogger(__name__)

class PineconeRetriever:
    """
    Enhanced Pinecone retriever with:
    - Advanced metadata filtering
    - Hybrid keyword/semantic search
    - Optional LLM reranking
    - Robust error handling
    """
    
    def __init__(self, llm=None):
        self.llm = llm

    def _process_filters(self, filters: Optional[Dict]) -> Dict:
        """Normalize and validate Pinecone metadata filters"""
        processed = {}
        if not filters:
            return processed
            
        def _prefix(k):
            # Add 'metadata.' prefix unless key already prefixed or is a logical operator
            if k.startswith('metadata.') or k.startswith('$'):
                return k
            return f'metadata.{k}'
        
        for key, value in filters.items():
            # Handle logical operators $or, $and that have list of dicts
            if key.startswith('$') and isinstance(value, list):
                logical_clauses = []
                for clause in value:
                    clause_processed = {}
                    for ck, cv in clause.items():
                        clause_processed[_prefix(ck)] = cv
                    logical_clauses.append(clause_processed)
                processed[key] = logical_clauses
                continue
            
            # Handle nested keys (e.g., skills.technical)
            if '.' in key:
                processed[_prefix(key)] = value
            # Handle regex filters
            elif isinstance(value, dict) and '$regex' in value:
                processed[_prefix(key)] = {
                    '$regex': value['$regex'],
                    '$options': 'i'
                }
            # Handle range queries ($gte, $lte)
            elif isinstance(value, dict) and ('$gte' in value or '$lte' in value):
                processed[_prefix(key)] = value
            else:
                processed[_prefix(key)] = value
                
        return processed

    def _post_filter_by_keywords(self, results: List[Dict], query: str) -> List[Dict]:
        """Apply additional keyword matching to results to improve precision"""
        if not query:
            return results
            
        keyword = query.strip().lower()
        filtered = []
        
        for doc in results:
            meta = doc.get('metadata', {})
            # Normalize possible language fields, try multiple common keys
            langs = self._extract_languages(meta)
            lang_match = any(keyword in lang.lower() for lang in langs)
            text_match = keyword in doc.get('text', '').lower()
            
            if lang_match or text_match:
                filtered.append(doc)
        
        return filtered if filtered else results

    def _extract_languages(self, metadata: Dict) -> List[str]:
        """Extract languages from metadata in various possible formats"""
        for key in ['languages', 'LANGUAGES']:
            lang_field = metadata.get(key)
            if lang_field:
                try:
                    if isinstance(lang_field, str):
                        # Try to parse JSON string
                        return json.loads(lang_field)
                    elif isinstance(lang_field, (list, tuple, set)):
                        return list(lang_field)
                    else:
                        # Fallback to str conversion
                        return [str(lang_field)]
                except (json.JSONDecodeError, TypeError):
                    return []
        return []

    def _rerank_with_llm(self, results: List[Dict], query: str, top_k: int) -> List[Dict]:
        """Use LLM to rerank results by relevance score (0-1)"""
        if not self.llm or not results:
            return results[:top_k]
            
        try:
            reranked = []
            # Limit number of docs to rerank to control cost
            for doc in results[:top_k * 2]:
                score = self._calculate_relevance_score(doc, query)
                doc['rerank_score'] = score
                reranked.append(doc)
            # Sort descending by rerank_score
            reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
            return reranked[:top_k]
        except Exception as e:
            logger.warning(f"LLM reranking failed: {e}")
            return results[:top_k]

    def _calculate_relevance_score(self, doc: Dict, query: str) -> float:
        """Prompt LLM to rate relevance of doc to query, returns float 0-1"""
        prompt = f"""
Rate the relevance of this CV excerpt to the search query.
Respond ONLY with a number between 0 (irrelevant) and 1 (perfect match).

Query: {query}
Excerpt: {doc.get('text', '')}
Score: """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            score = float(content.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"Error parsing LLM relevance score: {e}")
            return doc.get('score', 0.0)

    def retrieve(
        self,
        query: str,
        filters: Optional[Dict] = None,
        top_k: int = 5,
        rerank: bool = True
    ) -> List[Dict]:
        """
        Main retrieval method with enhanced functionality

        Args:
            query: Search query string
            filters: Pinecone metadata filters
            top_k: Number of results to return
            rerank: Whether to use LLM reranking
        
        Returns:
            List of document dicts with fields: id, score, metadata, text
        """
        try:
            # 1. Initial Pinecone semantic search
            results = query_chunks(
                query=query,
                filters=self._process_filters(filters),
                top_k=top_k * 3  # Over-fetch for reranking and filtering
            )
            
            # 2. Standardize results format
            processed = []
            for item in results:
                processed.append({
                    'id': item.get('id', str(uuid.uuid4())),
                    'score': float(item.get('score', 0.0)),
                    'metadata': item.get('metadata', {}),
                    'text': item.get('text', item.get('page_content', ''))
                })
            
            # 3. Optional keyword-based post-filtering to improve precision
            processed = self._post_filter_by_keywords(processed, query)
            
            # 4. Sort by initial semantic score descending
            processed.sort(key=lambda x: x['score'], reverse=True)
            
            # 5. Optional LLM reranking
            if rerank and self.llm:
                processed = self._rerank_with_llm(processed, query, top_k)
            else:
                processed = processed[:top_k]
            
            return processed
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            # Fallback simple query
            return query_chunks(query, top_k=top_k)


# LangChain Tool Interface
def pinecone_retriever_tool(
    query: str,
    filters: dict = None,
    top_k: int = 5,
    llm=None
) -> list:
    retriever = PineconeRetriever(llm)
    return retriever.retrieve(query, filters, top_k)

PineconeRetrieverTool = Tool(
    name="PineconeRetriever",
    func=pinecone_retriever_tool,
    description="""
    Enhanced document retriever that:
    1. Performs semantic search with metadata filtering
    2. Applies keyword matching to results
    3. Optionally reranks results using an LLM for relevance
    """
)
