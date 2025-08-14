import os
import openai
from typing import List, Dict, Any
from app.services.database import get_database_connection, search_database

class MemberMatcherService:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
    
    def extract_expertise_keywords(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Extract expertise keywords/phrases from RFP analysis that represent gaps
        """
        # Focus on gaps and challenges section to identify missing expertise
        gaps_text = analysis.get('gaps_challenges', '')
        resource_requirements = analysis.get('resource_requirements', '')
        
        # Combine relevant sections
        combined_text = f"{gaps_text}\n\n{resource_requirements}"
        
        if not combined_text.strip():
            return []
        
        # Use OpenAI to extract specific expertise keywords/phrases
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        prompt = f"""
        Based on the following RFP analysis sections that identify gaps and resource requirements, 
        extract specific expertise keywords or phrases that represent areas where the company needs 
        additional expertise or team members.
        
        Focus on:
        - Technical skills and expertise
        - Industry knowledge
        - Specific methodologies or tools
        - Professional roles or positions
        - Domain-specific knowledge
        
        RFP Analysis Text:
        {combined_text}
        
        Return a JSON array of specific expertise keywords/phrases. Each keyword/phrase should be:
        - Specific and actionable (e.g., "carbon accounting", "ESG reporting", "climate risk modeling")
        - Relevant for finding team members or expertise
        - Not too generic (avoid terms like "management" or "leadership" unless very specific)
        
        Limit to 10-15 most important keywords/phrases.
        
        Format: ["keyword1", "keyword2", "keyword3"]
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying specific expertise requirements from business analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            import json
            import re
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON array
            try:
                # Look for array pattern
                array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if array_match:
                    keywords = json.loads(array_match.group())
                    if isinstance(keywords, list):
                        return [kw.strip() for kw in keywords if kw.strip()]
            except:
                pass
            
            # Fallback: extract keywords manually
            keywords = []
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    keyword = line[1:].strip()
                    if keyword and len(keyword) > 2:
                        keywords.append(keyword)
                elif '"' in line:
                    # Extract quoted strings
                    quoted = re.findall(r'"([^"]*)"', line)
                    keywords.extend(quoted)
            
            return keywords[:15]  # Limit to 15 keywords
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def search_members_by_keywords(self, keywords: List[str], max_results: int = 50) -> List[Dict]:
        """
        Search the member database using the extracted keywords
        """
        if not keywords:
            return []
        
        # Join keywords with commas for the search function
        keywords_string = ', '.join(keywords)
        
        try:
            # Use the existing search function
            results = search_database(keywords_string)
            
            # Limit results to avoid overwhelming the API
            if len(results) > max_results:
                results = results[:max_results]
            
            return results
            
        except Exception as e:
            print(f"Error searching members: {e}")
            return []
    
    def rank_members_by_relevance(self, members: List[Dict], rfp_analysis: Dict[str, Any], keywords: List[str]) -> List[Dict]:
        """
        Use OpenAI to rank members by relevance to the RFP requirements
        """
        if not members:
            return []
        
        # Limit to top 20 members for API efficiency
        members_to_rank = members[:20]
        
        # Prepare member data for analysis
        member_data = []
        for member in members_to_rank:
            member_info = {
                'id': member.get('id'),
                'name': f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                'current_job': member.get('current_job', ''),
                'current_company': member.get('current_company', ''),
                'linkedin_summary': member.get('linkedin_summary', ''),
                'executive_summary': member.get('executive_summary', ''),
                'linkedin_skills': member.get('linkedin_skills', ''),
                'key_competencies': member.get('key_competencies', ''),
                'key_sectors': member.get('key_sectors', ''),
                'years_xp': member.get('years_xp', ''),
                'years_sustainability_xp': member.get('years_sustainability_xp', '')
            }
            member_data.append(member_info)
        
        # Create prompt for ranking
        client = openai.OpenAI(api_key=self.openai_api_key)
        
        prompt = f"""
        You are an expert at matching team members to project requirements. 
        
        RFP Requirements and Gaps:
        - Gaps & Challenges: {rfp_analysis.get('gaps_challenges', 'N/A')}
        - Resource Requirements: {rfp_analysis.get('resource_requirements', 'N/A')}
        - Key Strengths: {rfp_analysis.get('key_strengths', 'N/A')}
        
        Expertise Keywords Identified: {', '.join(keywords)}
        
        Available Team Members:
        {member_data}
        
        Rank these team members by their relevance to the RFP requirements. Consider:
        1. Direct match with expertise keywords
        2. Relevant experience in similar projects
        3. Skills that address identified gaps
        4. Industry knowledge alignment
        
        Return a JSON array with the top 10 most relevant members, ranked by relevance score (1-10, where 10 is most relevant).
        Include a brief explanation for each ranking.
        
        Format:
        [
            {{
                "member_id": 123,
                "name": "John Doe",
                "relevance_score": 9,
                "explanation": "Strong match in carbon accounting and ESG reporting",
                "key_skills": ["carbon accounting", "ESG reporting", "sustainability"]
            }}
        ]
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at matching team members to project requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            import json
            import re
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON array
            try:
                array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if array_match:
                    ranked_members = json.loads(array_match.group())
                    if isinstance(ranked_members, list):
                        return ranked_members
            except:
                pass
            
            # Fallback: return original members with basic ranking
            return [
                {
                    'member_id': member.get('id'),
                    'name': f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    'relevance_score': 5,
                    'explanation': 'Member matched by keyword search',
                    'key_skills': keywords[:3]
                }
                for member in members_to_rank[:10]
            ]
            
        except Exception as e:
            print(f"Error ranking members: {e}")
            # Return original members with basic info
            return [
                {
                    'member_id': member.get('id'),
                    'name': f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    'relevance_score': 5,
                    'explanation': 'Member matched by keyword search',
                    'key_skills': keywords[:3]
                }
                for member in members_to_rank[:10]
            ]
    
    def find_relevant_members(self, rfp_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main function to find relevant members for an RFP
        """
        try:
            # Step 1: Extract expertise keywords from analysis
            keywords = self.extract_expertise_keywords(rfp_analysis)
            print(f"Extracted keywords: {keywords}")
            
            if not keywords:
                return {
                    'success': False,
                    'error': 'No expertise keywords could be extracted from the analysis',
                    'keywords': [],
                    'members': []
                }
            
            # Step 2: Search for members matching keywords
            members = self.search_members_by_keywords(keywords)
            print(f"Found {len(members)} members matching keywords")
            
            if not members:
                return {
                    'success': True,
                    'keywords': keywords,
                    'members': [],
                    'message': 'No members found matching the identified expertise requirements'
                }
            
            # Step 3: Rank members by relevance
            ranked_members = self.rank_members_by_relevance(members, rfp_analysis, keywords)
            print(f"Ranked {len(ranked_members)} members by relevance")
            
            return {
                'success': True,
                'keywords': keywords,
                'members': ranked_members,
                'total_members_found': len(members),
                'ranked_members_count': len(ranked_members)
            }
            
        except Exception as e:
            print(f"Error in find_relevant_members: {e}")
            return {
                'success': False,
                'error': f'Error finding relevant members: {str(e)}',
                'keywords': [],
                'members': []
            }

