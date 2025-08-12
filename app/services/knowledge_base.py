import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
import openai
from typing import List, Dict, Any

class KnowledgeBaseService:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        self.vector_store = None
        
        # Get the absolute path to the chroma_db directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.chroma_db_path = os.path.join(current_dir, "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
        
    def reset_knowledge_base(self):
        """
        Reset the knowledge base by clearing all existing embeddings
        """
        try:
            import shutil
            if os.path.exists(self.chroma_db_path):
                shutil.rmtree(self.chroma_db_path)
                print(f"Cleared existing knowledge base at {self.chroma_db_path}")
            self.vector_store = None
            return True
        except Exception as e:
            print(f"Error resetting knowledge base: {e}")
            return False
    
    def process_knowledge_base(self, documents_path: str, force_reset: bool = False):
        """
        Process company knowledge base documents and store in vector database
        """
        # Reset if requested
        if force_reset:
            self.reset_knowledge_base()
        documents = []
        
        # Load documents from various sources
        for root, dirs, files in os.walk(documents_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if file.endswith('.pdf'):
                        loader = PyPDFLoader(file_path)
                        documents.extend(loader.load())
                    elif file.endswith('.docx'):
                        loader = Docx2txtLoader(file_path)
                        documents.extend(loader.load())
                    elif file.endswith('.txt'):
                        loader = TextLoader(file_path, encoding='utf-8')
                        documents.extend(loader.load())
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {str(e)}")
                    continue
        
        if not documents:
            raise Exception("No documents were successfully loaded. Please check your file types and paths.")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Store in vector database
        self.vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.chroma_db_path
        )
        
        return len(splits)
    
    def analyze_rfp(self, rfp_text: str, rfp_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze RFP against company knowledge base
        """
        if not self.vector_store:
            # Attempt to load existing vector store if not already loaded
            try:
                # Check if the chroma_db directory exists and has content
                if not os.path.exists(self.chroma_db_path):
                    raise Exception("ChromaDB directory not found")
                
                # Load the existing vector store
                self.vector_store = Chroma(
                    persist_directory=self.chroma_db_path,
                    embedding_function=self.embeddings
                )
                
                # Test if the vector store has documents
                if not self.vector_store._collection.count():
                    raise Exception("Vector store is empty")
                    
            except Exception as e:
                # Don't raise exception here - let the calling code handle initialization
                print(f"Knowledge base not loaded: {e}")
                self.vector_store = None
        
        # Retrieve maximum context from knowledge base - get all available documents
        try:
            # Get total document count to retrieve all available context
            total_docs = self.vector_store._collection.count()
            # Use min of total docs or a high number to get maximum context
            k_value = min(total_docs, 200)  # Retrieve up to 200 chunks for maximum context
            relevant_docs = self.vector_store.similarity_search(rfp_text, k=k_value)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            print(f"Retrieved {len(relevant_docs)} document chunks from knowledge base (total available: {total_docs})")
        except Exception as e:
            print(f"Error retrieving knowledge base context: {e}")
            # Fallback to original approach
            relevant_docs = self.vector_store.similarity_search(rfp_text, k=50)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Keep full RFP text for analysis
        
        # Use full knowledge base context without truncation
        
        # Create comprehensive prompt that combines metadata extraction and analysis
        combined_prompt = f"""
        You are an expert RFP analyst for OPF with deep knowledge of the company's capabilities, projects, and expertise. You will perform TWO tasks in a single response:

        1. EXTRACT METADATA from the RFP
        2. ANALYZE the RFP against OPF's specific capabilities

        RFP DETAILS:
        - Project Name: {rfp_metadata.get('project_name', 'N/A')}
        - Organization: {rfp_metadata.get('organization_group', 'N/A')}
        - Project Focus: {rfp_metadata.get('project_focus', 'N/A')}
        - RFP Content: {rfp_text}

        OPF COMPANY CAPABILITIES AND EXPERIENCE:
        {context}

        TASK 1: METADATA EXTRACTION
        Extract ONLY information that is explicitly stated or clearly implied in the RFP text. Use your knowledge of OPF to understand context and terminology when extracting OPF-specific information.

        TASK 2: RFP ANALYSIS
        Analyze this RFP against OPF's SPECIFIC capabilities and experience from the context above.

        CRITICAL REQUIREMENTS FOR ANALYSIS:
        1. Reference SPECIFIC projects, clients, or capabilities from OPF's context above
        2. Use actual company names, project examples, and specific expertise mentioned
        3. Avoid generic statements - be specific about OPF's actual experience
        4. When mentioning capabilities, reference where they come from in the context
        5. Use your understanding of OPF from the knowledge base to provide insightful analysis

        Return a SINGLE JSON response with this exact structure:
        {{
            "extracted_metadata": {{
                "organization_group": "The organization or group issuing the RFP (if clearly stated)",
                "country": "The country where the project will be implemented (if clearly stated)",
                "region": "The region or geographic area (if clearly stated)",
                "industry": "The industry sector (if clearly stated)",
                "project_focus": "The main focus or objective of the project (if clearly stated)",
                "opf_gap_size": "The size or scope of OPF gaps mentioned (if clearly stated)",
                "opf_gaps": "Specific OPF gaps or areas mentioned (if clearly stated)",
                "deliverables": "The expected deliverables (if clearly stated)",
                "posting_contact": "Contact information for the posting (if clearly stated)",
                "potential_experts": "Required expertise or expert profiles (if clearly stated)",
                "project_cost": "The project budget or cost (if clearly stated, as a number only)",
                "currency": "The currency for the project cost (if clearly stated)",
                "specific_staffing_needs": "Specific staffing requirements (if clearly stated)",
                "due_date": "The project due date (if clearly stated, in YYYY-MM-DD format)"
            }},
            "analysis": {{
                "fit_assessment": "High/Medium/Low - based on OPF's specific capabilities with detailed reasoning",
                "key_strengths": "Specific OPF projects, clients, or expertise that directly relate to this RFP with examples",
                "gaps_challenges": "Specific areas where OPF may need additional resources or expertise, based on actual capabilities",
                "recommendations": "Specific recommendations based on OPF's actual experience and capabilities",
                "resource_requirements": "Specific team members or resources OPF would need, based on current capabilities",
                "risk_assessment": "Specific risks based on OPF's actual experience and capabilities",
                "competitive_position": "How OPF specifically compares based on actual projects and expertise"
            }}
        }}

        METADATA EXTRACTION GUIDELINES:
        - Only extract information that is EXPLICITLY stated in the text
        - If a field is not mentioned or unclear, use null
        - For dates, use FULL YYYY-MM-DD format (e.g., '2029-12-31', not just '2029')
        - If only year is given, use YYYY-01-01 format
        - If year and month are given, use YYYY-MM-01 format
        - For costs, extract only the numeric value
        - Use your OPF knowledge to better understand OPF-specific terminology

        ANALYSIS GUIDELINES:
        - Every analysis point must reference specific information from OPF's context above
        - Provide detailed, comprehensive responses using the increased token limit
        - Be specific about OPF's actual experience, not generic consulting capabilities
        - Reference specific client names, project types, and outcomes when relevant
        """
        
        # Debug: Write prompts to output.txt for debugging
        try:
            # Get the absolute path to the project root directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_file_path = os.path.join(current_dir, "output.txt")
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write("=== DEBUG: OpenAI Combined Prompt and Context ===\n\n")
                f.write("=== COMBINED METADATA EXTRACTION & ANALYSIS PROMPT ===\n")
                f.write(combined_prompt)
                f.write("\n\n=== KNOWLEDGE BASE CONTEXT (First 8000 chars) ===\n")
                f.write(context[:8000])
                if len(context) > 8000:
                    f.write(f"\n... (truncated, full context is {len(context)} characters)")
                f.write("\n\n=== RFP TEXT (First 5000 chars) ===\n")
                f.write(rfp_text[:5000])
                if len(rfp_text) > 5000:
                    f.write(f"\n... (truncated, full RFP text is {len(rfp_text)} characters)")
                f.write("\n\n=== END DEBUG INFO ===\n")
            print(f"Debug information written to: {output_file_path}")
        except Exception as debug_e:
            print(f"Warning: Could not write debug output: {debug_e}")
        
        # Call OpenAI API with combined prompt for both analysis and metadata extraction
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Single API call for both metadata extraction and analysis
        try:
            # Try with GPT-4o first
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert RFP analyst for OPF with deep knowledge of the company. You will extract metadata and analyze RFPs against OPF's specific capabilities in a single comprehensive response. Always return valid JSON with the exact structure requested."},
                    {"role": "user", "content": combined_prompt}
                ],
                temperature=0.2,  # Lower temperature for consistent, specific responses
                max_tokens=6000  # Increased for combined response
            )
        except Exception as e:
            if "context_length_exceeded" in str(e):
                # Fallback to GPT-4 if context is too long
                print("Context too long for GPT-4o, falling back to GPT-4")
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert RFP analyst for OPF with deep knowledge of the company. You will extract metadata and analyze RFPs against OPF's specific capabilities in a single comprehensive response. Always return valid JSON with the exact structure requested."},
                        {"role": "user", "content": combined_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=6000
                )
            else:
                raise e
        
        # Parse the combined response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            import json
            # Try to parse the response directly
            combined_result = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the response
            try:
                # Look for JSON-like content between curly braces
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    # Try to complete the JSON if it's truncated
                    if not json_str.endswith('}'):
                        # Find the last complete key-value pair
                        last_comma = json_str.rfind(',')
                        if last_comma != -1:
                            json_str = json_str[:last_comma] + '}'
                    combined_result = json.loads(json_str)
                else:
                    raise Exception("No JSON found in response")
            except Exception as e:
                # If all else fails, return the raw analysis with structure
                print(f"JSON parsing failed: {e}")
                print(f"Raw response: {response_text}")
                
                combined_result = {
                    "extracted_metadata": {},
                    "analysis": {
                        "fit_assessment": "Analysis completed - see full response",
                        "key_strengths": "See full analysis below",
                        "gaps_challenges": "See full analysis below", 
                        "recommendations": "See full analysis below",
                        "resource_requirements": "See full analysis below",
                        "risk_assessment": "See full analysis below",
                        "competitive_position": "See full analysis below",
                        "full_analysis": response_text
                    }
                }
        
        # Ensure proper structure - extract analysis and metadata sections
        analysis = combined_result.get("analysis", {})
        extracted_metadata = combined_result.get("extracted_metadata", {})
        
        # Add extracted metadata to analysis for backward compatibility
        if extracted_metadata:
            analysis['extracted_metadata'] = extracted_metadata
        
        return analysis
