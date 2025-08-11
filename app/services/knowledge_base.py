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
        
    def process_knowledge_base(self, documents_path: str):
        """
        Process company knowledge base documents and store in vector database
        """
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
                raise Exception(f"Knowledge base not initialized and could not be loaded: {e}. Please process company documents first.")
        
        # Retrieve more specific context (increased to 8 for better coverage)
        relevant_docs = self.vector_store.similarity_search(rfp_text, k=8)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Truncate RFP text if it's too long (keep first 2000 characters)
        if len(rfp_text) > 2000:
            rfp_text = rfp_text[:2000] + "... [truncated]"
        
        # Truncate context if it's too long (keep first 4000 characters for more detail)
        if len(context) > 4000:
            context = context[:4000] + "... [truncated]"
        
        # Create analysis prompt with specific company focus and metadata extraction
        prompt = f"""
        You are an expert RFP analyst for OPF. Analyze this RFP against our SPECIFIC company capabilities and past projects.

        RFP DETAILS:
        - Project Name: {rfp_metadata.get('project_name', 'N/A')}
        - Organization: {rfp_metadata.get('organization_group', 'N/A')}
        - Project Focus: {rfp_metadata.get('project_focus', 'N/A')}
        - RFP Content: {rfp_text[:1500]}

        OUR COMPANY CAPABILITIES AND EXPERIENCE:
        {context[:3500]}

        CRITICAL REQUIREMENTS:
        1. Reference SPECIFIC projects, clients, or capabilities from our company context above
        2. Use actual company names, project examples, and specific expertise mentioned
        3. Avoid generic statements - be specific about our actual experience
        4. If you mention capabilities, reference where they come from in our context

        Provide detailed JSON analysis with these keys:
        {{
            "fit_assessment": "High/Medium/Low - based on our specific capabilities",
            "key_strengths": "Specific projects, clients, or expertise from our company context that directly relate to this RFP",
            "gaps_challenges": "Specific areas where we may need additional resources or expertise, based on our actual capabilities",
            "recommendations": "Specific recommendation based on our actual experience and capabilities",
            "resource_requirements": "Specific team members or resources we would need, based on our current capabilities",
            "risk_assessment": "Specific risks based on our actual experience and capabilities",
            "competitive_position": "How we specifically compare based on our actual projects and expertise"
        }}

        IMPORTANT: Every point must reference specific information from our company context above. Do not make generic statements.
        """

        # Create metadata extraction prompt
        metadata_prompt = f"""
        You are an expert at extracting structured information from RFP documents. Extract ONLY the information that is clearly stated in the RFP text below.

        RFP TEXT TO ANALYZE:
        {rfp_text[:2000]}

        Extract ONLY information that is explicitly stated or clearly implied. If information is not present or unclear, return null for that field.

        Return JSON with these fields:
        {{
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
        }}

        IMPORTANT: 
        - Only extract information that is EXPLICITLY stated in the text
        - If a field is not mentioned or unclear, use null
        - For dates, you MUST use FULL YYYY-MM-DD format (e.g., '2029-12-31', not just '2029')
        - If only year is given, use YYYY-01-01 format
        - If year and month are given, use YYYY-MM-01 format
        - For costs, extract only the numeric value
        - Be conservative - it's better to return null than to guess
        """
        
        # Call OpenAI API for both analysis and metadata extraction
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        # First, extract metadata from RFP text
        try:
            metadata_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from RFP documents. Extract ONLY information that is explicitly stated."},
                    {"role": "user", "content": metadata_prompt}
                ],
                temperature=0.1,  # Very low temperature for consistent extraction
                max_tokens=1000
            )
            extracted_metadata = metadata_response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            extracted_metadata = "{}"
        
        # Then, perform the main analysis
        try:
            # Try with GPT-4 first
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert RFP analyst for OPF. You must reference SPECIFIC company information, projects, clients, and capabilities from the provided context. Avoid generic statements - be specific about actual company experience and capabilities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent, specific responses
                max_tokens=2500
            )
        except Exception as e:
            if "context_length_exceeded" in str(e):
                # Fallback to GPT-3.5-turbo if context is too long
                print("Context too long for GPT-4, falling back to GPT-3.5-turbo")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert RFP analyst for OPF. You must reference SPECIFIC company information, projects, clients, and capabilities from the provided context. Avoid generic statements - be specific about actual company experience and capabilities."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2500
                )
            else:
                raise e
        
        # Parse and return analysis
        analysis_text = response.choices[0].message.content.strip()
        
        # Parse extracted metadata
        extracted_metadata_dict = {}
        try:
            import json
            extracted_metadata_dict = json.loads(extracted_metadata)
        except json.JSONDecodeError:
            print(f"Metadata JSON parsing failed: {extracted_metadata}")
            extracted_metadata_dict = {}
        
        # Try to extract JSON from the analysis response
        try:
            import json
            # Try to parse the response directly
            analysis = json.loads(analysis_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the response
            try:
                # Look for JSON-like content between curly braces
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    # Try to complete the JSON if it's truncated
                    if not json_str.endswith('}'):
                        # Find the last complete key-value pair
                        last_comma = json_str.rfind(',')
                        if last_comma != -1:
                            json_str = json_str[:last_comma] + '}'
                    analysis = json.loads(json_str)
                else:
                    raise Exception("No JSON found in response")
            except Exception as e:
                # If all else fails, return the raw analysis
                print(f"JSON parsing failed: {e}")
                print(f"Raw response: {analysis_text}")
                
                # Try to extract what we can from the partial response
                analysis = {
                    "fit_assessment": "Analysis completed",
                    "key_strengths": "See full analysis below",
                    "gaps_challenges": "See full analysis below", 
                    "recommendations": "See full analysis below",
                    "resource_requirements": "See full analysis below",
                    "risk_assessment": "See full analysis below",
                    "competitive_position": "See full analysis below",
                    "full_analysis": analysis_text
                }
                
                # Try to extract any partial information
                if '"fit_assessment"' in analysis_text:
                    try:
                        fit_match = re.search(r'"fit_assessment":\s*"([^"]+)"', analysis_text)
                        if fit_match:
                            analysis["fit_assessment"] = fit_match.group(1)
                    except:
                        pass
                
                if '"key_strengths"' in analysis_text:
                    try:
                        strengths_match = re.search(r'"key_strengths":\s*"([^"]+)"', analysis_text)
                        if strengths_match:
                            analysis["key_strengths"] = strengths_match.group(1)
                    except:
                        pass
        
        # Add extracted metadata to the analysis results
        if extracted_metadata_dict:
            analysis['extracted_metadata'] = extracted_metadata_dict
        
        return analysis
