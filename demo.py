#!/usr/bin/env python3
"""RAG System Demo Script

Interactive demonstration of the RAG insurance chatbot system
for showcasing core functionality and capabilities.
"""

import os
import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import ConfigFactory, set_config
from src.logging_config import setup_logging
from src.generation import RAGSystem


def print_header():
    """Print demo header."""
    print("🏨 RAG Insurance Chatbot Demo")
    print("=" * 50)
    print("🎯 Purpose: Travel Insurance Query Assistant")
    print("📚 Data: 海外旅行不便險條款 (Travel Inconvenience Insurance)")
    print("🤖 Technology: RAG (Retrieval-Augmented Generation)")
    print("=" * 50)


def print_section(title: str):
    """Print section header."""
    print(f"\n{'─' * 20} {title} {'─' * 20}")


def demo_initialization(rag_system: RAGSystem) -> bool:
    """Demonstrate system initialization."""
    print_section("System Initialization")
    
    print("🔧 Initializing RAG system components...")
    
    # Check document availability
    doc_path = "data/raw/海外旅行不便險條款.txt"
    if not os.path.exists(doc_path):
        print(f"❌ Document not found: {doc_path}")
        print("   Please run PDF processing first.")
        return False
    
    print(f"📄 Found insurance document: {doc_path}")
    
    # Initialize system
    print("🚀 Processing and indexing documents...")
    start_time = time.time()
    
    try:
        result = rag_system.initialize_system(doc_path)
        end_time = time.time()
        
        if result["initialized"]:
            stats = result["indexing_results"]
            print(f"✅ Initialization completed in {end_time - start_time:.1f}s")
            print(f"   📊 Statistics:")
            print(f"      - Document chunks: {stats.get('total_chunks', 0)}")
            print(f"      - Embeddings generated: {stats.get('embeddings_generated', 0)}")
            print(f"      - Vectors indexed: {stats.get('vectors_indexed', 0)}")
            print(f"      - Embedding dimension: {stats.get('embedding_dimension', 0)}")
            return True
        else:
            print("❌ Initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


def demo_queries(rag_system: RAGSystem):
    """Demonstrate query processing."""
    print_section("Query Demonstration")
    
    # Sample queries
    queries = [
        {
            "query": "班機延誤超過幾小時可以申請賠償？",
            "description": "Flight Delay Compensation"
        },
        {
            "query": "行李遺失後應該如何申請理賠？", 
            "description": "Lost Luggage Claims Process"
        },
        {
            "query": "哪些情況下旅遊不便險不會理賠？",
            "description": "Insurance Exclusions"
        }
    ]
    
    for i, item in enumerate(queries, 1):
        query = item["query"]
        description = item["description"]
        
        print(f"\n💬 Query {i}: {description}")
        print(f"   Question: {query}")
        
        try:
            start_time = time.time()
            response = rag_system.query(query, top_k=3)
            end_time = time.time()
            
            print(f"   ⚡ Response time: {end_time - start_time:.2f}s")
            print(f"   🎯 Confidence: {response.confidence_score:.2f}")
            print(f"   📚 Sources: {len(response.sources)} relevant clauses")
            
            # Display answer
            print(f"\n   📝 Answer:")
            answer_lines = response.answer.split('\n')
            for line in answer_lines[:5]:  # Show first 5 lines
                if line.strip():
                    print(f"      {line}")
            
            if len(answer_lines) > 5:
                print(f"      ... ({len(answer_lines) - 5} more lines)")
            
            # Display top source
            if response.sources:
                top_source = response.sources[0]
                print(f"\n   📋 Top Source:")
                print(f"      Clause: {top_source.get('clause_number', 'N/A')}")
                print(f"      Relevance: {top_source.get('relevance_score', 0):.2f}")
                snippet = top_source.get('content_snippet', '')[:100]
                print(f"      Content: {snippet}...")
            
            print("   ✅ Query processed successfully")
            
        except Exception as e:
            print(f"   ❌ Query failed: {e}")


def demo_system_stats(rag_system: RAGSystem):
    """Show system statistics."""
    print_section("System Statistics")
    
    try:
        status = rag_system.get_system_status()
        
        print(f"🏥 Overall Health: {status.get('overall_status', 'unknown')}")
        print(f"🔄 System Ready: {status.get('system_initialized', False)}")
        
        # Component status
        components = status.get('components', {})
        if components:
            print(f"\n🔧 Component Status:")
            for name, info in components.items():
                component_status = info.get('status', 'unknown')
                print(f"   - {name.title()}: {component_status}")
        
        # Configuration
        config = status.get('configuration', {})
        if config:
            print(f"\n⚙️ Configuration:")
            retrieval_cfg = config.get('retrieval', {})
            if retrieval_cfg:
                print(f"   - Top K: {retrieval_cfg.get('top_k', 'N/A')}")
                print(f"   - Similarity Threshold: {retrieval_cfg.get('similarity_threshold', 'N/A')}")
                print(f"   - Index Type: {retrieval_cfg.get('index_type', 'N/A')}")
            
            generation_cfg = config.get('generation', {})
            if generation_cfg:
                print(f"   - Model: {generation_cfg.get('model', 'N/A')}")
                print(f"   - Temperature: {generation_cfg.get('temperature', 'N/A')}")
                print(f"   - Max Tokens: {generation_cfg.get('max_tokens', 'N/A')}")
        
        # Vector store stats
        stats = status.get('statistics', {})
        vector_stats = stats.get('retrieval', {}).get('vector_store', {})
        if vector_stats:
            print(f"\n📊 Vector Store:")
            print(f"   - Total Vectors: {vector_stats.get('total_vectors', 0)}")
            print(f"   - Namespace Vectors: {vector_stats.get('namespace_vectors', 0)}")
            print(f"   - Dimension: {vector_stats.get('dimension', 0)}")
            print(f"   - Index: {vector_stats.get('index_name', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Failed to get system stats: {e}")


def main():
    """Run the demo."""
    print_header()
    
    try:
        # Setup
        print("\n🔧 Setting up demo environment...")
        config = ConfigFactory.load_from_env()
        set_config(config)
        setup_logging("WARNING", config.environment)  # Reduce log noise for demo
        
        # Initialize RAG system
        rag_system = RAGSystem()
        
        # Demo flow
        if not demo_initialization(rag_system):
            print("\n❌ Demo failed during initialization")
            return
        
        demo_queries(rag_system)
        demo_system_stats(rag_system)
        
        # Demo conclusion
        print_section("Demo Complete")
        print("🎉 RAG Insurance Chatbot demo completed successfully!")
        print("\n📋 Key Features Demonstrated:")
        print("   ✅ PDF document processing and indexing")
        print("   ✅ Vector embedding generation")
        print("   ✅ Semantic search and retrieval") 
        print("   ✅ Contextual response generation")
        print("   ✅ Source citation and traceability")
        print("   ✅ Multi-language support (Chinese)")
        
        print("\n🚀 Ready for Production:")
        print("   - API Server: python -m src.main")
        print("   - Documentation: http://localhost:8000/docs")
        print("   - Health Check: http://localhost:8000/api/v1/health")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()