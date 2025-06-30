from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import logging
from langchain.tools import Tool
from langchain.llms.base import LLM

logger = logging.getLogger(__name__)

class IntentResult(BaseModel):
    """Structured output from intent detection"""
    intent: str
    skills: List[str] = []
    experience: Dict[str, Any] = {}
    roles: List[str] = []
    location: Optional[str] = None
    education: List[str] = []
    certifications: List[str] = []
    projects: List[str] = []
    languages: List[str] = []
    confidence: float = 0.0
    requested_fields: List[str] = []

class QueryPlan(BaseModel):
    """
    Complete retrieval strategy specification
    """
    query_type: str = Field(
        ...,
        description="One of: MetadataQuery, CVContentQuery, MultiHopQuery, GeneralQuery"
    )
    metadata_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pinecone filter conditions with weights"
    )
    suggested_top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Optimal number of results to retrieve"
    )
    requires_reranking: bool = Field(
        True,
        description="Whether results need score-based reranking"
    )
    route: str = Field(
        "process",
        description="One of: process, clarify, reject, redirect"
    )
    rejection_reason: Optional[str] = Field(
        None,
        description="Reason for rejection if route=reject"
    )
    handling_instructions: Optional[str] = Field(
        None,
        description="Special handling guidance"
    )
    requested_fields: List[str] = Field(
        default_factory=list,
        description="Fields that user explicitly requested in query"
    )

    @validator('query_type')
    def validate_query_type(cls, v):
        valid_types = {
            "MetadataQuery", "CVContentQuery",
            "MultiHopQuery", "GeneralQuery", "BlockedQuery"
        }
        if v not in valid_types:
            raise ValueError(f"Invalid query type. Must be one of {valid_types}")
        return v

    @validator('route')
    def validate_route(cls, v):
        valid_routes = {"process", "clarify", "reject", "redirect"}
        if v not in valid_routes:
            raise ValueError(f"Invalid route. Must be one of {valid_routes}")
        return v

def build_skill_filters(skills: List[str]) -> Dict[str, Any]:
    """Build Pinecone $in filter for skills (case-insensitive by lower-casing)."""
    if not skills:
        return {}
    skills_norm = [s.lower() for s in skills]
    return {"skills.technical": {"$in": skills_norm}}

def build_experience_filters(exp: Dict[str, Any]) -> Dict[str, Any]:
    """Construct numeric range filters for years of experience."""
    filters: Dict[str, Any] = {}
    if "min" in exp and exp["min"] is not None:
        filters["$gte"] = exp["min"]
    if "max" in exp and exp["max"] is not None:
        filters["$lte"] = exp["max"]
    return {"experience_years": filters} if filters else {}

def build_location_filter(location: Optional[str]) -> Dict[str, Any]:
    """Simple equality filter for location."""
    if not location:
        return {}
    return {"location": {"$eq": location}}

def build_roles_filter(roles: List[str]) -> Dict[str, Any]:
    if not roles:
        return {}
    roles_norm = [r.lower() for r in roles]
    return {"current_role": {"$in": roles_norm}}

def build_education_filter(education: List[str]) -> Dict[str, Any]:
    if not education:
        return {}
    edu_norm = [e.lower() for e in education]
    return {"education": {"$in": edu_norm}}

def build_certifications_filter(certs: List[str]) -> Dict[str, Any]:
    if not certs:
        return {}
    certs_norm = [c.lower() for c in certs]
    return {"certifications": {"$in": certs_norm}}

def build_projects_filter(projects: List[str]) -> Dict[str, Any]:
    if not projects:
        return {}
    projs_norm = [p.lower() for p in projects]
    return {"projects": {"$in": projs_norm}}

def build_languages_filter(langs: List[str]) -> Dict[str, Any]:
    if not langs:
        return {}
    langs_norm = [l.lower() for l in langs]
    return {"languages": {"$in": langs_norm}}

def query_planner_tool(intent: Dict[str, Any], analysis: Dict[str, Any] = None, llm: LLM = None) -> QueryPlan:
    """
    Generates a retrieval strategy with weighted filtering
    """
    try:
        # 1. Handle toxic queries (if any)
        if analysis and analysis.get("is_toxic"):
            return QueryPlan(
                query_type="BlockedQuery",
                route="reject",
                rejection_reason=analysis.get("rejection_reason"),
                handling_instructions="Query contained inappropriate language",
                requested_fields=[]
            )

        # 2. Handle general knowledge queries (redirect)
        if analysis and analysis.get("requires_general_knowledge"):
            return QueryPlan(
                query_type="GeneralQuery",
                route="redirect",
                handling_instructions="Focus on CV-related aspects",
                requested_fields=[]
            )

        intent_obj = IntentResult(**intent) if not isinstance(intent, IntentResult) else intent

        requested_fields = intent_obj.requested_fields or []

        # Build filters only for requested fields
        filters: Dict[str, Any] = {}

        if "skills" in requested_fields:
            filters.update(build_skill_filters(intent_obj.skills))
        if "experience" in requested_fields:
            filters.update(build_experience_filters(intent_obj.experience))
        if "location" in requested_fields:
            filters.update(build_location_filter(intent_obj.location))
        if "roles" in requested_fields:
            filters.update(build_roles_filter(intent_obj.roles))
        if "education" in requested_fields:
            filters.update(build_education_filter(intent_obj.education))
        if "certifications" in requested_fields:
            filters.update(build_certifications_filter(intent_obj.certifications))
        if "projects" in requested_fields:
            filters.update(build_projects_filter(intent_obj.projects))
        if "languages" in requested_fields:
            filters.update(build_languages_filter(intent_obj.languages))

        # Determine query_type based on number of filters and intent
        if not filters:
            q_type = "GeneralQuery"
        elif len(filters) == 1:
            q_type = "MetadataQuery"
        else:
            q_type = "MultiHopQuery"

        # Suggested top_k depends on confidence & intent complexity
        suggested_k = 5 + int(10 * intent_obj.confidence)

        # reranking required if multiple filters or high confidence
        rerank = True if len(filters) > 0 else False

        return QueryPlan(
            query_type=q_type,
            metadata_filters=filters,
            suggested_top_k=suggested_k,
            requires_reranking=rerank,
            route="process",
            requested_fields=requested_fields
        )

    except Exception as e:
        logger.error(f"Query planning failed: {str(e)}")
        return QueryPlan(
            query_type="GeneralQuery",
            route="process",
            handling_instructions="Fallback plan due to error",
            requested_fields=[]
        )

QueryPlanner = Tool(
    name="CV_Query_Planner",
    func=query_planner_tool,
    description="""
    Generates weighted retrieval strategies:
    1. Converts intent to database filters with match weights
    2. Determines search type (metadata/content/hybrid)
    3. Sets safety and routing instructions
    4. Builds filters only for requested fields
    """
)
