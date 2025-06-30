import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from langchain.llms.base import LLM

# Import tools
from .tools.query_analyzer import QueryAnalyzer, QueryResponse
from .tools import intent as _intent_module
from .tools.query_planner import IntentResult, query_planner_tool, QueryPlan
from .tools.pinecone_retriever import pinecone_retriever_tool
from .tools.context_aggregator import aggregate_contexts
from .tools.candidate_summarizer import candidate_summarizer_tool
from .tools.synthesizer import synthesizer_tool
from .tools.memory_manager import save_memory, load_recent_memory

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class PipelineResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    candidates: Optional[List[dict]] = None
    sources: Optional[List[str]] = None
    error: Optional[str] = None
    debug: Optional[dict] = None

def run_cv_query_pipeline(
    user_query: str,
    llm: LLM,
    email: str,
    session_id: Optional[str] = None,
    top_k: int = 5,
    memory_context_limit: int = 3,
    debug: bool = True,
    memory: Optional[Any] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Full RAG pipeline with memory:
    - Load recent memory
    - Append memory context to user query
    - Query analysis and intent detection
    - Query planning and retrieval
    - Candidate summarization and synthesis
    - Save conversation to memory
    """

    pipeline_state = {"original_query": user_query, "steps": {}}

    try:
        # 1. Load recent memory for context
        memory_context_text = ""
        if memory is not None:
            try:
                # Include user context in the memory query if available
                additional_context = {}
                if user_context:
                    additional_context = {
                        k: v for k, v in user_context.items() 
                        if k in ["user_id", "ip_address", "user_agent"]
                    }
                
                recent_memories = load_recent_memory(
                    email=email, 
                    session_id=session_id, 
                    limit=memory_context_limit
                )
                
                if recent_memories:
                    memory_context_text = "\n".join(
                        f"Q: {m.get('query', '')}\nA: {m.get('response', '')}" 
                        for m in reversed(recent_memories)
                    )
                    if debug:
                        logger.info(f"[0] Loaded {len(recent_memories)} memory contexts")
            except Exception as e:
                logger.error(f"Error loading memory context: {e}")
                memory_context_text = ""

        # Append memory context to current query
        combined_query = f"{memory_context_text}\n\nNew Query: {user_query}" if memory_context_text else user_query
        if debug:
            logger.info("[0] Loaded memory context:\n%s", memory_context_text)

        # 2. Query Analysis
        analyzer = QueryAnalyzer(llm)
        analysis = analyzer.analyze(combined_query)
        pipeline_state["steps"]["query_analysis"] = analysis.dict()
        if debug:
            logger.info("[1] Query analysis: %s", analysis.dict())

        if analysis.immediate_response:
            return PipelineResponse(success=True, response=analysis.immediate_response).dict()

        if analysis.is_toxic and not analysis.should_process:
            return PipelineResponse(
                success=False,
                error=analysis.rejection_reason,
                response="Please rephrase your query professionally"
            ).dict()

        processed_query = analysis.modified_query or combined_query

        # 3. Intent Detection
        _intent_module.llm = llm  # Inject llm
        intent_dict = _intent_module.intent_rating_tool(processed_query)
        intent_result = IntentResult(**intent_dict)
        pipeline_state["steps"]["intent_detection"] = intent_result.dict()
        if debug:
            logger.info("[2] Intent detection: %s", intent_result.dict())

        if intent_result.confidence < 0.3:
            return PipelineResponse(
                success=False,
                error="Low intent confidence",
                response="Could not understand your query. Please try rephrasing."
            ).dict()

        # 4. Query Planning
        plan = query_planner_tool(intent_result.dict(), analysis.dict(), llm)
        pipeline_state["steps"]["query_planning"] = plan.dict()
        if debug:
            logger.info("[3] Query plan: %s", plan.dict())

        if plan.route == "reject":
            return PipelineResponse(
                success=False,
                error=plan.rejection_reason,
                response="Query cannot be processed"
            ).dict()

        # 5. Retrieval
        results = pinecone_retriever_tool(
            query=processed_query,
            filters=plan.metadata_filters,
            top_k=top_k,
            llm=llm
        )
        # Retry without filters if no results
        if not results and plan.metadata_filters:
            if debug:
                logger.info("[4a] No results with filters, retrying without filters")
            results = pinecone_retriever_tool(
                query=processed_query,
                filters={},
                top_k=top_k,
                llm=llm
            )

        if debug:
            logger.info("[4] Retrieved %d results", len(results))

        if not results:
            return PipelineResponse(
                success=True,
                response="No matching candidates found"
            ).dict()

        # 6. Context Aggregation with Memory
        context = aggregate_contexts(
            search_results=results, 
            query=processed_query,
            memory=memory,
            max_candidates=top_k
        )
        pipeline_state["steps"]["context_aggregation"] = {"num_candidates": len(context)}
        if debug:
            logger.info("[5] Context aggregated for %d candidates", len(context))

        # 7. Candidate Summarization
        answer = candidate_summarizer_tool(context, processed_query, llm)
        pipeline_state["steps"]["candidate_summarization"] = {"answer_snippet": str(answer)[:200]}
        if debug:
            logger.info("[6] Candidate summarization completed")

        # 8. Synthesize detailed candidate summaries
        candidates = synthesizer_tool(answer, results, llm)
        pipeline_state["steps"]["synthesis"] = {"num_summaries": len(candidates)}
        if debug:
            logger.info("[7] Synthesized %d candidate summaries", len(candidates))

        answer_text = answer.content if hasattr(answer, 'content') else str(answer)

        # 9. Save to memory for future context if memory is enabled
        if memory is not None:
            try:
                # Add metadata to the memory
                memory_metadata = {
                    "source": "pipeline",
                    "query_type": analysis.get("intent") if hasattr(analysis, 'get') else "unknown",
                    "candidate_count": len(candidates) if candidates else 0
                }
                
                # Include user context if available
                if user_context:
                    memory_metadata.update({
                        k: v for k, v in user_context.items()
                        if k in ["user_id", "ip_address", "user_agent"]
                    })
                
                save_memory(
                    email=email,
                    session_id=session_id,
                    query=user_query,
                    response=answer,
                    llm=llm,
                    user_context=user_context
                )
                if debug:
                    logger.info(f"[8] Saved interaction to memory for {email}")
            except Exception as e:
                logger.error(f"Failed to save to memory: {e}")
                if debug:
                    logger.exception("Memory save error details:")

        # 10. Return final response
        # Ensure sources are valid strings
        sources = []
        for r in results:
            source = r.get("metadata", {}).get("source")
            if source is None:
                source = "Unknown source"
            sources.append(str(source))
            
        return PipelineResponse(
            success=True,
            response=answer_text,
            candidates=candidates,
            sources=sources,
            debug=pipeline_state if debug else None
        ).dict()

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
        return PipelineResponse(
            success=False,
            error=str(e),
            response="An error occurred while processing your query"
        ).dict()
