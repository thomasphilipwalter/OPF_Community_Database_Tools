import os
import openai
from typing import List, Dict, Any

class KnowledgeBaseService:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
        
        # Get the absolute path to the knowledge_base directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.knowledge_base_path = os.path.join(current_dir, "knowledge_base")
        self.knowledge_base_text = None
        
    def reset_knowledge_base(self):
        """
        Reset the knowledge base by clearing cached text
        """
        try:
            self.knowledge_base_text = None
            print("Cleared cached knowledge base text")
            return True
        except Exception as e:
            print(f"Error resetting knowledge base: {e}")
            return False
    
    def load_knowledge_base(self, documents_path: str = None, force_reset: bool = False):
        """
        Load all knowledge base text files directly into memory
        """
        # Reset if requested
        if force_reset:
            self.reset_knowledge_base()
        
        # Use default path if none provided
        if documents_path is None:
            documents_path = self.knowledge_base_path
        
        # Return cached text if already loaded and not forcing reset
        if self.knowledge_base_text is not None and not force_reset:
            return len(self.knowledge_base_text)
        
        all_text = []
        file_count = 0
        
        # Load all text files directly
        for root, dirs, files in os.walk(documents_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if file.endswith('.txt'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                all_text.append(f"=== {file} ===\n{content}")
                                file_count += 1
                                print(f"Loaded {file}: {len(content)} characters")
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {str(e)}")
                    continue
        
        if not all_text:
            raise Exception("No text files were successfully loaded. Please check your file paths.")
        
        # Combine all text with separators
        self.knowledge_base_text = "\n\n".join(all_text)
        
        print(f"Knowledge base loaded: {file_count} files, {len(self.knowledge_base_text)} total characters")
        return len(self.knowledge_base_text)
    
    def analyze_rfp(self, rfp_text: str, rfp_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze RFP against company knowledge base using direct text approach
        """
        # Load knowledge base if not already loaded
        if self.knowledge_base_text is None:
            try:
                self.load_knowledge_base()
            except Exception as e:
                print(f"Knowledge base not loaded: {e}")
                raise Exception("Knowledge base not available. Please initialize the knowledge base first.")
        
        # Use the complete knowledge base text as context - NO TRUNCATION
        context = self.knowledge_base_text
        print(f"Using complete knowledge base as context: {len(context)} characters")
        print(f"Using complete RFP text: {len(rfp_text)} characters")
        
        # Create comprehensive prompt that combines metadata extraction and analysis
        # IMPORTANT: Pass FULL RFP text and FULL knowledge base - no truncation anywhere
        combined_prompt = f"""
        You are an expert climate consulting business development analyst for OnePointFive, responsible for evaluating Request for Proposals (RFPs) provided by the user. You have access to our company's knowledge base, which includes:
        - Summaries of past proposals (ASME.txt, EDF.txt, EIT.txt, FAI.txt, Kendra_Scott.txt, Sanofi.txt, Sarona_ADI.txt, Sweef_Kinetik.txt, Talon.txt)
        - Summary of the case studies on our website (all_case_studies.txt)
        - Summary of our master slide deck (master_slide_deck.txt)

        Your task is to critically assess the fit of each RFP relative to OnePointFive's capabilities, ensuring that the analysis is both honest and professional. When performing the analysis, consider the following:
        - Be cautious not to overestimate the fit of an RFP. While our capabilities are strong, do not let the marketing content in "all_case_studies.txt" unduly influence the evaluation. This document representss past projects and is intended for promotional purposes, so its content may portray our capabilities too optimistically.
        
        When an RFP is provided, you have two primary tasks:
        1. EXTRACT METADATA from the RFP
        2. ANALYZE the RFP against OPF's specific capabilities

        COMPLETE RFP CONTENT:
        {rfp_text}

        COMPLETE OPF COMPANY CAPABILITIES AND EXPERIENCE:
        {context}

        TASK 1: METADATA EXTRACTION
        Extract information from the RFP text above. For OPF-specific fields, use your knowledge of OPF's capabilities from the knowledge base to assess what gaps exist between what the RFP requires and what OPF can deliver.
        OPF-specific fields include: opf_gap_size, opf_gaps

        CRITICAL FOR OPF-SPECIFIC METADATA:
        - opf_gap_size: Compare RFP requirements against OPF's capabilities to determine the size/scope of gaps
        - opf_gaps: Identify specific areas where OPF lacks capabilities mentioned in the RFP
        - Use the complete OPF knowledge base above to make these assessments

        TASK 2: RFP ANALYSIS
        Analyze this RFP against OPF's SPECIFIC capabilities and experience from the complete knowledge base above.

        CRITICAL REQUIREMENTS FOR ANALYSIS:
        1. Reference SPECIFIC projects, clients, or capabilities from OPF's complete knowledge base
        2. Use actual company names, project examples, and specific expertise mentioned
        3. Avoid generic statements - be specific about OPF's actual experience
        4. When mentioning capabilities, reference where they come from in the knowledge base
        5. Use your complete understanding of OPF from the knowledge base to provide insightful analysis

        Return a SINGLE JSON response with this exact structure:
        {{
            "extracted_metadata": {{
                "organization_group": "The organization or group issuing the RFP (if clearly stated)",
                "country": "The country where the project will be implemented (if clearly stated)",
                "region": "The region or geographic area (if clearly stated)",
                "industry": "The industry sector (if clearly inferrable). Choose from the most appropriate industry(ies) from the following options: Infrastructure, Culture, Recycling, Carbon Systems, Circularity, Food/Agriculture, Finance, Strategy, Energy Environmental, Development, Transportation, Health & Safety. If the project does not fit clearly into one of these categories, provide the best fit.",
                "project_focus": "The main focus or objective of the project (if clearly inferrable). Choose the most appropriate focus area(s) from the following options: Skills Development, Agriculture Systems, Transportation Systems, Broad Sustainability Strategy, Natural Disaster, Investment Strategy, Water Assessment, Environmental Analysis, Climate Risk, Circular Economy, Nature-Based Solutions, Climate Change Policy, Energy Systems. If the project does not fit clearly into one of these categories, use a label outside these options but still provide the best fit.",
                "opf_gap_size": "Assess the size/scope of gaps between RFP requirements and OPF's capabilities from the knowledge base (Small/Medium/Large/None)",
                "opf_gaps": "Identify specific capability gaps by comparing RFP requirements to OPF's knowledge base capabilities",
                "deliverables": "The expected deliverables (if clearly stated)",
                "posting_contact": "Contact information for the posting (if clearly stated)",
                "potential_experts": "Required expertise or expert profiles (if clearly stated)",
                "project_cost": "The project budget or cost (if clearly stated, as a number only)",
                "currency": "The currency for the project cost (if clearly stated)",
                "specific_staffing_needs": "Specific staffing requirements (if clearly stated)",
                "due_date": "The proposal due date (if clearly stated, in YYYY-MM-DD format)"
            }},
            "analysis": {{
                "fit_assessment": "Provide a comprehensive High/Medium/Low assessment with extensive detailed reasoning. Include specific examples from OPF's knowledge base, cite relevant past projects, client work, and capabilities. Explain the reasoning behind the assessment with multiple supporting points and detailed analysis of how OPF's specific experience aligns with or differs from the RFP requirements. This should be a thorough, multi-paragraph analysis.",
                "key_strengths": "Provide an extensive analysis of OPF's key strengths relevant to this RFP. Include specific project examples, client names, methodologies, tools, and outcomes from the knowledge base. Detail how each strength directly addresses RFP requirements. Cite specific case studies, successful implementations, and unique differentiators. This should be comprehensive and detailed, covering all relevant strengths with supporting evidence from the knowledge base.",
                "gaps_challenges": "Conduct a thorough analysis of areas where OPF may face challenges or lack specific expertise required by the RFP. Be detailed about what capabilities are missing, what would need to be developed or acquired, and how significant these gaps are. Include analysis of resource requirements, timeline implications, and potential mitigation strategies. Reference specific requirements from the RFP that may not be fully covered by current OPF capabilities.",
                "recommendations": "Provide comprehensive, actionable recommendations based on OPF's actual experience and capabilities from the knowledge base. Include detailed strategies for approach, methodology, team composition, timeline considerations, and risk mitigation. Reference similar past projects and lessons learned. Provide multiple recommendation categories such as strategic approach, tactical execution, resource allocation, and partnership considerations.",
                "resource_requirements": "Conduct a detailed analysis of specific team members, skill sets, resources, tools, and capabilities OPF would need for this project. Based on the knowledge base, identify existing team members who could contribute and specify additional hires or partnerships needed. Include analysis of budget implications, timeline for resource acquisition, and organizational capacity considerations.",
                "risk_assessment": "Provide a comprehensive risk analysis covering technical, operational, financial, timeline, and strategic risks specific to this RFP and OPF's capabilities. Reference past project experiences from the knowledge base where similar risks were encountered. Include detailed mitigation strategies for each identified risk and contingency planning recommendations.",
                "competitive_position": "Conduct an extensive analysis of how OPF compares to potential competitors for this RFP. Reference specific past wins, losses, and competitive situations from the knowledge base. Detail OPF's unique differentiators, potential weaknesses relative to competitors, and strategic positioning recommendations. Include market analysis and competitive intelligence based on OPF's experience."
            }}
        }}

        METADATA EXTRACTION GUIDELINES:
        - Extract information that is explicitly stated or can be reasonably inferred
        - For OPF-specific fields (opf_gap_size, opf_gaps), analyze the COMPLETE RFP requirements against the COMPLETE OPF knowledge base
        - opf_gap_size: Determine gap size by comparing what RFP needs vs what OPF can deliver based on knowledge base
        - opf_gaps: List specific missing capabilities by analyzing RFP needs against OPF's complete capability set
        - For dates, use FULL YYYY-MM-DD format (e.g., '2029-12-31', not just '2029')
        - If only year is given, use YYYY-01-01 format
        - If year and month are given, use YYYY-MM-01 format
        - For costs, extract only the numeric value
        - If a non-OPF field is not mentioned or unclear, use null

        ANALYSIS GUIDELINES:
        - Every analysis point must reference specific information from the COMPLETE OPF knowledge base
        - Provide EXTENSIVE, DETAILED, COMPREHENSIVE responses - aim for thorough, multi-paragraph analyses for each section
        - Be highly specific about OPF's actual experience from the complete knowledge base, not generic consulting capabilities
        - Reference specific client names, project types, methodologies, tools, outcomes, and lessons learned from the complete knowledge base
        - Use the FULL RFP content and FULL OPF knowledge base for comprehensive analysis
        - Each analysis section should be substantial and detailed - think comprehensive report sections, not brief summaries
        - Include specific examples, case studies, numbers, outcomes, and evidence from the knowledge base wherever possible
        - Provide actionable insights with detailed reasoning and supporting evidence
        - Make each section comprehensive enough to stand alone as a thorough analysis
        """
        
        # Debug: Write prompts to output.txt for debugging
        try:
            # Get the absolute path to the project root directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_file_path = os.path.join(current_dir, "output.txt")
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write("=== DEBUG: OpenAI Combined Prompt and COMPLETE Context ===\n\n")
                f.write(f"PROMPT LENGTH: {len(combined_prompt)} characters\n")
                f.write(f"KNOWLEDGE BASE LENGTH: {len(context)} characters\n")
                f.write(f"RFP TEXT LENGTH: {len(rfp_text)} characters\n")
                f.write(f"TOTAL CONTEXT SIZE: {len(combined_prompt)} characters\n\n")
                
                f.write("=== COMBINED METADATA EXTRACTION & ANALYSIS PROMPT (COMPLETE) ===\n")
                f.write(combined_prompt)
                f.write("\n\n=== COMPLETE KNOWLEDGE BASE CONTEXT (NO TRUNCATION) ===\n")
                f.write(context)
                f.write(f"\n\n=== COMPLETE RFP TEXT (NO TRUNCATION) ===\n")
                f.write(rfp_text)
                f.write("\n\n=== END DEBUG INFO ===\n")
            print(f"Complete debug information written to: {output_file_path}")
            print(f"Total context size being sent to OpenAI: {len(combined_prompt)} characters")
        except Exception as debug_e:
            print(f"Warning: Could not write debug output: {debug_e}")
        
        # Call OpenAI API with combined prompt for both analysis and metadata extraction
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Single API call for both metadata extraction and analysis with COMPLETE context
        try:
            # Try with GPT-4o first - using complete context without any truncation
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert RFP analyst for OPF with complete knowledge of the company. You have access to the COMPLETE RFP content and COMPLETE OPF knowledge base. For OPF-specific metadata fields like opf_gap_size and opf_gaps, you must analyze the complete RFP requirements against OPF's complete capabilities to assess gaps. Provide EXTENSIVE, DETAILED, COMPREHENSIVE analysis for each section - think thorough report sections with multiple paragraphs, specific examples, and detailed reasoning. Always return valid JSON with the exact structure requested."},
                    {"role": "user", "content": combined_prompt}
                ],
                temperature=0.2,  # Lower temperature for consistent, specific responses
                max_tokens=16000  # Significantly increased for extensive, detailed analysis sections
            )
        except Exception as e:
            if "context_length_exceeded" in str(e):
                # If context is too long, we need to handle this differently since we don't want to truncate
                print(f"Context length exceeded. Total prompt size: {len(combined_prompt)} characters")
                print("Consider using a model with larger context window or splitting the analysis")
                raise Exception(f"Context too large ({len(combined_prompt)} characters) for available models. Consider using a model with larger context window.")
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
