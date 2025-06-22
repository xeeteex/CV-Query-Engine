import os, uuid, shutil
from dotenv import load_dotenv
from fastapi_mcp import FastApiMCP

# Load environment variables first
load_dotenv()

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from rag.extractor import extract_pdf, extract_docx
from rag.chunker import chunk_text
from rag.pinecone_client import store_chunks, query_chunks
from rag.agentic_rag import get_agentic_chain, extract_structured_cv_data, filter_relevant_candidates

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split('.')[-1].lower()
    path = f"temp/{uuid.uuid4()}.{ext}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if ext == "pdf":
        text = extract_pdf(path)
    elif ext == "docx":
        text = extract_docx(path)
    else:
        return {"error": "Unsupported file format"}

    chunks = chunk_text(text)
    store_chunks(chunks, file.filename)

    return {"message": f"{len(chunks)} chunks stored from {file.filename}"}

@app.post("/ask/")
async def ask_question(payload: dict):
    try:
        question = payload.get("question", "q")
        if not question:
            return {"error": "Question is required"}
        
        # Step 1: Get initial chunks from vector database
        chunks = query_chunks(question, top_k=8)
        
        if not chunks:
            return {
                "answer": "No CV documents found in the database. Please upload some CV files first using the /upload/ endpoint.",
                "sources": [],
                "structured_data": []
            }
        
        # Step 2: Filter for relevance to the specific query
        print(f"Filtering {len(chunks)} chunks for relevance to: {question}")
        relevant_chunks = filter_relevant_candidates(chunks, question)
        
        if not relevant_chunks:
            return {
                "answer": f"No candidates found with relevant experience for: '{question}'. Try broadening your search criteria.",
                "sources": [],
                "structured_data": []
            }
        
        print(f"Found {len(relevant_chunks)} relevant chunks out of {len(chunks)} total chunks")
        
        # Step 3: Extract structured data only from relevant chunks
        structured_data = []
        seen_names = set()  # To avoid duplicates
        successful_extractions = 0
        
        for i, chunk in enumerate(relevant_chunks):
            try:
                print(f"\n--- Processing relevant chunk {i+1}/{len(relevant_chunks)} ---")
                structured_cv = extract_structured_cv_data(chunk)
                
                # Check if this is a duplicate candidate (same name)
                candidate_name = structured_cv.get('NAME', '').strip()
                if candidate_name and candidate_name not in seen_names:
                    seen_names.add(candidate_name)
                    structured_data.append(structured_cv)
                    if not candidate_name.startswith('Extraction failed') and not candidate_name.startswith('JSON parsing failed') and not candidate_name.startswith('Error occurred'):
                        successful_extractions += 1
                elif not candidate_name:
                    # If no name found, still add it but with a unique identifier
                    structured_cv['NAME'] = f"Unknown Candidate {len(structured_data) + 1}"
                    structured_data.append(structured_cv)
                    
            except Exception as e:
                print(f"Error extracting structured data from chunk {i+1}: {str(e)}")
                # Add fallback structured data
                structured_data.append({
                    "NAME": f"Extraction Failed - Candidate {len(structured_data) + 1}",
                    "LOCATION": "",
                    "CONTACT": {"PHONE": "", "EMAIL": "", "LINKEDIN": "", "GITHUB": ""},
                    "EDUCATION": [],
                    "EXPERIENCE": [],
                    "SKILLS": {"TECHNICAL": [], "SOFT_SKILLS": [], "LANGUAGES": [], "TOOLS": []},
                    "CERTIFICATIONS": [],
                    "PROJECTS": [],
                    "MISCELLANEOUS": chunk
                })
        
        # Create a focused answer based on the query
        if len(structured_data) == 1:
            cv = structured_data[0]
            
            # Check if extraction failed and show raw data instead
            if cv['NAME'].startswith('Extraction failed') or cv['NAME'].startswith('JSON parsing failed') or cv['NAME'].startswith('Error occurred'):
                answer = f"Found 1 candidate with relevant experience for '{question}'. Here's the raw content:\n\n"
                answer += cv['MISCELLANEOUS']
            else:
                answer = f"Found 1 candidate with relevant experience for '{question}':\n\n"
                answer += f"**{cv['NAME']}**\n"
                
                if cv['LOCATION']:
                    answer += f"Location: {cv['LOCATION']}\n"
                
                if cv['CONTACT']['EMAIL']:
                    answer += f"Email: {cv['CONTACT']['EMAIL']}\n"
                
                if cv['CONTACT']['PHONE']:
                    answer += f"Phone: {cv['CONTACT']['PHONE']}\n"
                
                answer += "\n"
                
                # Show relevant experience
                if cv['EXPERIENCE']:
                    answer += "**Relevant Experience:**\n"
                    for exp in cv['EXPERIENCE']:
                        answer += f"• {exp.get('TITLE', '')} at {exp.get('COMPANY', '')} ({exp.get('DURATION', '')})\n"
                        if exp.get('RESPONSIBILITIES'):
                            for resp in exp.get('RESPONSIBILITIES', [])[:3]:  # Show top 3 responsibilities
                                answer += f"  - {resp}\n"
                    answer += "\n"
                
                # Show relevant skills
                if cv['SKILLS']['TECHNICAL']:
                    answer += f"**Technical Skills:** {', '.join(cv['SKILLS']['TECHNICAL'])}\n\n"
                
                if cv['EDUCATION']:
                    answer += "**Education:**\n"
                    for edu in cv['EDUCATION']:
                        answer += f"• {edu.get('DEGREE', '')} from {edu.get('INSTITUTION', '')} ({edu.get('DURATION', '')})\n"
            
        else:
            # Multiple relevant candidates
            answer = f"Found {len(structured_data)} candidates with relevant experience for '{question}':\n\n"
            
            if successful_extractions < len(structured_data):
                answer += f"Note: {len(structured_data) - successful_extractions} candidates had extraction issues. Showing available information.\n\n"
            
            for i, cv in enumerate(structured_data, 1):
                answer += f"**{i}. {cv['NAME']}**\n"
                
                # If extraction failed, show a note about raw data
                if cv['NAME'].startswith('Extraction failed') or cv['NAME'].startswith('JSON parsing failed') or cv['NAME'].startswith('Error occurred'):
                    answer += "(Raw CV data available)\n\n"
                else:
                    if cv['LOCATION']:
                        answer += f"Location: {cv['LOCATION']}\n"
                    
                    if cv['CONTACT']['EMAIL']:
                        answer += f"Email: {cv['CONTACT']['EMAIL']}\n"
                    
                    # Show most relevant experience
                    if cv['EXPERIENCE']:
                        answer += "**Relevant Experience:**\n"
                        for exp in cv['EXPERIENCE'][:2]:  # Show top 2 experiences
                            answer += f"• {exp.get('TITLE', '')} at {exp.get('COMPANY', '')} ({exp.get('DURATION', '')})\n"
                        answer += "\n"
                    
                    # Show relevant skills
                    if cv['SKILLS']['TECHNICAL']:
                        answer += f"**Key Skills:** {', '.join(cv['SKILLS']['TECHNICAL'][:5])}\n\n"
                
                answer += "---\n\n"
            
            # Add summary
            answer += f"**Summary:** Found {len(structured_data)} candidates matching your criteria for '{question}'."
        
        return {
            "answer": answer,
            "sources": relevant_chunks,  # Only return relevant chunks as sources
            "structured_data": structured_data
        }
        
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")
        return {
            "error": f"Error processing question: {str(e)}",
            "answer": "Unable to process your question. Please try again.",
            "sources": [],
            "structured_data": []
        }


mcp = FastApiMCP(app)
mcp.mount()