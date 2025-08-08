#!/usr/bin/env python3
"""
Script to initialize the knowledge base with company documents
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.knowledge_base import KnowledgeBaseService

def main():
    # Path to your company documents
    documents_path = input("Enter the path to your company documents folder: ").strip()
    
    if not os.path.exists(documents_path):
        print(f"Error: Path '{documents_path}' does not exist")
        return
    
    print(f"Processing documents from: {documents_path}")
    
    try:
        # Initialize knowledge base service
        kb_service = KnowledgeBaseService()
        
        # Process documents
        num_chunks = kb_service.process_knowledge_base(documents_path)
        
        print(f"✅ Successfully processed {num_chunks} document chunks")
        print("Knowledge base is ready for AI analysis!")
        
    except Exception as e:
        print(f"❌ Error processing documents: {str(e)}")
        print("\nMake sure you have:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Installed required dependencies: pip install chromadb langchain openai tiktoken docx2txt")
        print("3. Valid PDF/DOCX files in the documents folder")

if __name__ == "__main__":
    main()
