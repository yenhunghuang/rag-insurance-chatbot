#!/usr/bin/env python3
"""RAG System Integration Test

Test script to verify the complete RAG system functionality
including document processing, indexing, and query processing.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import ConfigFactory, set_config
from src.logging_config import setup_logging
from src.generation import RAGSystem


def main():
    """Run integration tests for the RAG system."""
    print("🚀 Starting RAG System Integration Test")
    print("=" * 50)
    
    try:
        # Step 1: Initialize configuration
        print("\n📁 Step 1: Loading configuration...")
        config = ConfigFactory.load_from_env()
        set_config(config)
        setup_logging(config.log_level, config.environment)
        
        print(f"✅ Configuration loaded successfully")
        print(f"   - Environment: {config.environment}")
        print(f"   - API Port: {config.api.port}")
        print(f"   - Index Type: {config.retrieval.index_type}")
        
        # Step 2: Initialize RAG system
        print("\n🔧 Step 2: Initializing RAG system...")
        rag_system = RAGSystem()
        print("✅ RAG system components initialized")
        
        # Step 3: Check system health
        print("\n🏥 Step 3: Checking system health...")
        health = rag_system.get_system_status()
        print(f"   - System Status: {health.get('overall_status', 'unknown')}")
        print(f"   - Initialized: {health.get('system_initialized', False)}")
        
        # Step 4: Initialize system with documents
        print("\n📚 Step 4: Initializing system with insurance documents...")
        
        # Check if insurance document exists
        doc_path = "data/raw/海外旅行不便險條款.txt"
        if not os.path.exists(doc_path):
            print(f"❌ Insurance document not found at: {doc_path}")
            print("   Please ensure the PDF has been processed and converted.")
            return False
            
        init_result = rag_system.initialize_system(doc_path)
        
        if init_result["initialized"]:
            print("✅ System initialized successfully")
            stats = init_result["indexing_results"]
            print(f"   - Total chunks: {stats.get('total_chunks', 0)}")
            print(f"   - Embeddings generated: {stats.get('embeddings_generated', 0)}")
            print(f"   - Vectors indexed: {stats.get('vectors_indexed', 0)}")
        else:
            print("❌ System initialization failed")
            return False
        
        # Step 5: Test queries
        print("\n💬 Step 5: Testing sample queries...")
        
        test_queries = [
            "班機延誤超過幾小時可以申請賠償？",
            "行李遺失後應該如何申請理賠？",
            "哪些情況下旅遊不便險不會理賠？"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            try:
                response = rag_system.query(query, top_k=3)
                
                print(f"   ✅ Response generated")
                print(f"      - Answer length: {len(response.answer)} characters")
                print(f"      - Sources found: {len(response.sources)}")
                print(f"      - Confidence: {response.confidence:.2f}")
                print(f"      - Answer preview: {response.answer[:100]}...")
                
                if response.sources:
                    print(f"      - Top source: {response.sources[0].get('clause_number', 'N/A')}")
                
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
                return False
        
        # Step 6: Final system status
        print("\n📊 Step 6: Final system status...")
        final_status = rag_system.get_system_status()
        
        print(f"   - Overall Status: {final_status.get('overall_status', 'unknown')}")
        
        vector_stats = final_status.get('statistics', {}).get('retrieval', {}).get('vector_store', {})
        if vector_stats:
            print(f"   - Indexed vectors: {vector_stats.get('namespace_vectors', 0)}")
            print(f"   - Vector dimension: {vector_stats.get('dimension', 0)}")
        
        print("\n🎉 Integration test completed successfully!")
        print("=" * 50)
        print("\n📋 Next Steps:")
        print("1. Update .env file with your actual API keys:")
        print("   - OPENAI_API_KEY=your_key_here") 
        print("   - PINECONE_API_KEY=your_key_here")
        print("   - PINECONE_ENVIRONMENT=your_environment")
        print("\n2. Start the API server:")
        print("   python -m src.main")
        print("\n3. Access API documentation:")
        print("   http://localhost:8000/docs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)