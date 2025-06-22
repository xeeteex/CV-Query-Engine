import os
import json
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_mistralai.chat_models import ChatMistralAI
from rag.pinecone_client import query_chunks

def search_cv(query: str) -> str:
    """Search through CV documents in the vector database"""
    try:
        print(f"Searching for: {query}")  # Debug print
        chunks = query_chunks(query, top_k=5)
        print(f"Found {len(chunks)} chunks")  # Debug print
        
        if not chunks:
            return "No relevant CV information found for this query."
        
        # Join chunks with clear separators
        result = "\n\n--- CV Document ---\n\n".join(chunks)
        print(f"Returning result with {len(result)} characters")  # Debug print
        return result
    except Exception as e:
        print(f"Error in search_cv: {str(e)}")  # Debug print
        return f"Error searching CVs: {str(e)}"

retrieval_tool = Tool(
    name="CVSearchTool",
    func=search_cv,
    description="Search through uploaded CV documents to find information about candidates' skills, experience, education, work history, or any other CV-related information. ALWAYS use this tool when asked about candidates, their qualifications, or CV content. Extract the information and format it as a structured response."
)

def get_agentic_chain():
    llm = ChatMistralAI(
        api_key=os.getenv("MISTRAL_API_KEY"),
        model="mistral-small-latest",
        temperature=0.7,  # Lower temperature for more focused responses
        max_tokens=2000,  # Limit response length
    )

    return initialize_agent(
        tools=[retrieval_tool],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=2,  # Reduced to prevent loops
        early_stopping_method="generate",  # Stop when final answer is generated
        return_intermediate_steps=False,  # Don't return intermediate steps
    )

def filter_relevant_candidates(chunks: list, query: str) -> list:
    """Filter chunks to only include those relevant to the specific query"""
    try:
        if not chunks:
            return []
        
        # Create a prompt to determine relevance
        relevance_prompt = f"""
        You are a CV filtering expert. Your task is to determine which CV chunks are relevant to a specific query.
        
        QUERY: "{query}"
        
        For each CV chunk below, determine if the candidate has relevant experience, skills, or qualifications that match the query.
        Consider:
        - Technical skills mentioned in the query
        - Work experience related to the query
        - Education or certifications relevant to the query
        - Any other qualifications that would make this candidate suitable
        
        CV CHUNKS:
        """
        
        # Add each chunk with a clear separator
        for i, chunk in enumerate(chunks):
            relevance_prompt += f"\n--- CHUNK {i+1} ---\n{chunk}\n"
        
        relevance_prompt += f"""
        
        Return ONLY a JSON array of chunk numbers (1-based) that are relevant to the query "{query}".
        For example: [1, 3, 5] if chunks 1, 3, and 5 are relevant.
        
        Be strict in your filtering - only include chunks where the candidate clearly has relevant experience or skills.
        If no chunks are relevant, return an empty array: []
        
        IMPORTANT: Return ONLY the JSON array, no additional text or explanations.
        """
        
        llm = ChatMistralAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            model="mistral-small",
            temperature=0.1,
        )
        
        response = llm.invoke(relevance_prompt)
        print(f"Relevance filter response: {response.content}")
        
        # Parse the response to get relevant chunk indices
        try:
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            # Find JSON array in the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                relevant_indices = json.loads(json_str)
                
                # Convert 1-based indices to 0-based and filter chunks
                relevant_chunks = []
                for idx in relevant_indices:
                    if 1 <= idx <= len(chunks):
                        relevant_chunks.append(chunks[idx - 1])
                
                print(f"Filtered to {len(relevant_chunks)} relevant chunks out of {len(chunks)} total")
                return relevant_chunks
            else:
                print("No JSON array found in relevance response, returning all chunks")
                return chunks
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed for relevance filter: {str(e)}")
            print(f"Failed JSON string: {content}")
            # Fallback: return all chunks if parsing fails
            return chunks
            
    except Exception as e:
        print(f"Error in filter_relevant_candidates: {str(e)}")
        # Fallback: return all chunks if filtering fails
        return chunks

def extract_structured_cv_data(cv_text: str) -> dict:
    """Extract structured CV data from text and return as JSON"""
    try:
        print(f"Extracting structured data from text of length: {len(cv_text)}")
        print(f"First 200 characters: {cv_text[:200]}...")
        
        # Create a structured prompt for the LLM to extract information
        prompt = f"""
        You are a CV data extraction expert. Extract the following information from this CV text and return it as a valid JSON object with these exact fields:
        
        {{
            "NAME": "Full name of the person",
            "LOCATION": "Address, city, country",
            "CONTACT": {{
                "PHONE": "Phone number",
                "EMAIL": "Email address",
                "LINKEDIN": "LinkedIn profile if available",
                "GITHUB": "GitHub profile if available"
            }},
            "EDUCATION": [
                {{
                    "DEGREE": "Degree name",
                    "INSTITUTION": "School/University name",
                    "LOCATION": "Institution location",
                    "DURATION": "Year or duration",
                    "PERCENTAGE": "Grade/Percentage if mentioned"
                }}
            ],
            "EXPERIENCE": [
                {{
                    "TITLE": "Job title",
                    "COMPANY": "Company name",
                    "LOCATION": "Company location",
                    "DURATION": "Duration/period",
                    "RESPONSIBILITIES": ["List of key responsibilities"]
                }}
            ],
            "SKILLS": {{
                "TECHNICAL": ["Technical skills"],
                "SOFT_SKILLS": ["Soft skills"],
                "LANGUAGES": ["Programming languages"],
                "TOOLS": ["Tools and technologies"]
            }},
            "CERTIFICATIONS": ["List of certifications"],
            "PROJECTS": ["Notable projects"],
            "MISCELLANEOUS": "Any other relevant information"
        }}
        
        CV Text:
        {cv_text}
        
        IMPORTANT: Return ONLY the JSON object, no additional text, explanations, or markdown formatting. The response must be valid JSON that can be parsed by json.loads().
        """
        
        llm = ChatMistralAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            model="mistral-small",
            temperature=0.1,
        )
        
        response = llm.invoke(prompt)
        print(f"LLM Response: {response.content[:500]}...")
        
        # Try to extract JSON from the response
        try:
            # Clean the response content
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            # Find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                print(f"Extracted JSON string: {json_str[:200]}...")
                
                # Parse the JSON
                parsed_data = json.loads(json_str)
                print(f"Successfully parsed JSON for: {parsed_data.get('NAME', 'Unknown')}")
                return parsed_data
            else:
                print("No JSON brackets found in response")
                # Try to extract name from the text directly
                name = extract_name_from_text(cv_text)
                return {
                    "NAME": name or "Extraction failed - no JSON found",
                    "LOCATION": "",
                    "CONTACT": {"PHONE": "", "EMAIL": "", "LINKEDIN": "", "GITHUB": ""},
                    "EDUCATION": [],
                    "EXPERIENCE": [],
                    "SKILLS": {"TECHNICAL": [], "SOFT_SKILLS": [], "LANGUAGES": [], "TOOLS": []},
                    "CERTIFICATIONS": [],
                    "PROJECTS": [],
                    "MISCELLANEOUS": content
                }
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {str(e)}")
            print(f"Failed JSON string: {content[:200]}...")
            
            # Try to extract name from the text directly
            name = extract_name_from_text(cv_text)
            return {
                "NAME": name or "JSON parsing failed",
                "LOCATION": "",
                "CONTACT": {"PHONE": "", "EMAIL": "", "LINKEDIN": "", "GITHUB": ""},
                "EDUCATION": [],
                "EXPERIENCE": [],
                "SKILLS": {"TECHNICAL": [], "SOFT_SKILLS": [], "LANGUAGES": [], "TOOLS": []},
                "CERTIFICATIONS": [],
                "PROJECTS": [],
                "MISCELLANEOUS": content
            }
            
    except Exception as e:
        print(f"Error in extract_structured_cv_data: {str(e)}")
        # Try to extract name from the text directly
        name = extract_name_from_text(cv_text)
        return {
            "NAME": name or "Error occurred",
            "LOCATION": "",
            "CONTACT": {"PHONE": "", "EMAIL": "", "LINKEDIN": "", "GITHUB": ""},
            "EDUCATION": [],
            "EXPERIENCE": [],
            "SKILLS": {"TECHNICAL": [], "SOFT_SKILLS": [], "LANGUAGES": [], "TOOLS": []},
            "CERTIFICATIONS": [],
            "PROJECTS": [],
            "MISCELLANEOUS": f"Error: {str(e)}"
        }

def extract_name_from_text(text: str) -> str:
    """Extract name from CV text using simple heuristics"""
    try:
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # Look for patterns that might indicate a name
                # Usually names are in ALL CAPS or Title Case at the beginning
                if (line.isupper() and len(line.split()) <= 4 and len(line) > 3) or \
                   (line[0].isupper() and len(line.split()) <= 4 and len(line) > 3 and not any(word.lower() in ['email', 'phone', 'address', 'cv', 'resume'] for word in line.split())):
                    return line
        return "Unknown"
    except Exception as e:
        print(f"Error extracting name: {str(e)}")
        return "Unknown"
