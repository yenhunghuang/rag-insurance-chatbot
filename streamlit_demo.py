#!/usr/bin/env python3
"""Streamlit Demo Interface

Simple Streamlit web interface for demonstrating the RAG insurance chatbot.
"""

import streamlit as st
import sys
import os
from pathlib import Path
import time
import json
from dotenv import load_dotenv

# Ensure .env is loaded before any imports
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import ConfigFactory, set_config, get_config
from src.generation import RAGSystem


# Page configuration
st.set_page_config(
    page_title="RAG 旅遊不便險諮詢系統",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize system
@st.cache_resource
def initialize_rag_system():
    """Initialize RAG system with caching."""
    try:
        # Debug: Show environment variables
        st.write("🔧 **Debug Info - Environment Variables:**")
        st.write(f"- SIMILARITY_THRESHOLD: {os.getenv('SIMILARITY_THRESHOLD', 'NOT SET')}")
        st.write(f"- TOP_K: {os.getenv('TOP_K', 'NOT SET')}")
        st.write(f"- PINECONE_INDEX_NAME: {os.getenv('PINECONE_INDEX_NAME', 'NOT SET')}")
        
        config = ConfigFactory.load_from_env()
        set_config(config)
        
        # Debug: Show loaded configuration
        st.write("🔧 **Debug Info - Loaded Configuration:**")
        st.write(f"- retrieval.similarity_threshold: {config.retrieval.similarity_threshold}")
        st.write(f"- retrieval.top_k: {config.retrieval.top_k}")
        st.write(f"- pinecone.index_name: {config.pinecone.index_name}")
        
        rag_system = RAGSystem()
        
        # Initialize with insurance documents
        doc_path = "data/raw/海外旅行不便險條款.txt"
        if os.path.exists(doc_path):
            result = rag_system.initialize_system(doc_path)
            if result["initialized"]:
                # Add configuration info to the result
                result["indexing_results"]["debug_config"] = {
                    "similarity_threshold": config.retrieval.similarity_threshold,
                    "top_k": config.retrieval.top_k,
                    "index_name": config.pinecone.index_name
                }
                return rag_system, result["indexing_results"]
            else:
                return None, {"error": "System initialization failed"}
        else:
            return None, {"error": f"Document not found: {doc_path}"}
            
    except Exception as e:
        return None, {"error": str(e)}


# Main interface
def main():
    """Main Streamlit interface."""
    
    # Header
    st.title("🏨 RAG 旅遊不便險諮詢系統")
    st.markdown("基於檢索增強生成 (RAG) 技術的智能保險條款查詢系統")
    
    # Initialize system
    with st.spinner("正在初始化系統..."):
        rag_system, init_info = initialize_rag_system()
    
    if rag_system is None:
        st.error(f"❌ 系統初始化失敗: {init_info.get('error', 'Unknown error')}")
        st.stop()
    
    # Sidebar with system info
    st.sidebar.header("📊 系統資訊")
    
    # Add cache clear button
    if st.sidebar.button("🔄 清除緩存並重新載入"):
        st.cache_resource.clear()
        st.rerun()
    
    if "error" not in init_info:
        st.sidebar.success("✅ 系統已就緒")
        st.sidebar.metric("文件片段", init_info.get("total_chunks", 0))
        st.sidebar.metric("向量索引", init_info.get("vectors_indexed", 0))
        st.sidebar.metric("嵌入維度", init_info.get("embedding_dimension", 0))
        
        # Debug configuration info
        debug_config = init_info.get("debug_config", {})
        if debug_config:
            st.sidebar.header("🔧 配置資訊")
            st.sidebar.write(f"相似度閾值: {debug_config.get('similarity_threshold', 'N/A')}")
            st.sidebar.write(f"檢索數量: {debug_config.get('top_k', 'N/A')}")
            st.sidebar.write(f"索引名稱: {debug_config.get('index_name', 'N/A')}")
    
    # Sample queries
    st.sidebar.header("💡 範例問題")
    sample_queries = [
        "班機延誤超過幾小時可以申請賠償？",
        "行李遺失後應該如何申請理賠？", 
        "哪些情況下旅遊不便險不會理賠？",
        "旅程取消保險的承保範圍有哪些？",
        "行李延誤達到多久才能申請理賠？"
    ]
    
    selected_query = st.sidebar.selectbox(
        "選擇範例問題：",
        [""] + sample_queries
    )
    
    # Main query interface
    st.header("💬 問題查詢")
    
    # Query input
    query_input = st.text_area(
        "請輸入您的保險問題：",
        value=selected_query,
        height=100,
        placeholder="例如：班機延誤超過幾小時可以申請賠償？"
    )
    
    # Query settings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_k = st.slider("檢索文件數量", min_value=1, max_value=10, value=5)
    
    with col2:
        include_sources = st.checkbox("顯示來源引用", value=True)
    
    with col3:
        show_confidence = st.checkbox("顯示信心分數", value=True)
    
    # Process query
    if st.button("🔍 查詢", type="primary", disabled=not query_input.strip()):
        with st.spinner("正在處理查詢..."):
            start_time = time.time()
            
            try:
                response = rag_system.query(
                    question=query_input.strip(),
                    top_k=top_k,
                    include_sources=include_sources
                )
                
                end_time = time.time()
                
                # Display response
                st.header("📝 回答")
                
                # Response metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("回應時間", f"{end_time - start_time:.2f}s")
                
                with col2:
                    if show_confidence:
                        st.metric("信心分數", f"{response.confidence:.2f}")
                
                with col3:
                    st.metric("參考來源", len(response.sources))
                
                with col4:
                    st.metric("回答長度", f"{len(response.answer)}字")
                
                # Main answer
                st.markdown("### 📄 詳細回答")
                st.markdown(response.answer)
                
                # Source citations
                if include_sources and response.sources:
                    st.markdown("### 📚 參考來源")
                    
                    for i, source in enumerate(response.sources, 1):
                        with st.expander(f"來源 {i}: {source.get('clause_number', 'N/A')} (相關度: {source.get('relevance_score', 0):.2f})"):
                            st.markdown(f"**條款編號**: {source.get('clause_number', 'N/A')}")
                            st.markdown(f"**來源文件**: {source.get('source_file', 'N/A')}")
                            st.markdown(f"**相關度分數**: {source.get('relevance_score', 0):.3f}")
                            st.markdown(f"**內容摘要**: {source.get('content_snippet', 'N/A')}")
                
                # Metadata
                if st.checkbox("顯示詳細資訊"):
                    st.markdown("### 🔧 技術資訊")
                    
                    metadata = response.metadata
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.json({
                            "模型": metadata.get("model_used", "N/A"),
                            "生成時間": f"{metadata.get('generation_time', 0)}秒",
                            "完成原因": metadata.get("finish_reason", "N/A"),
                            "時間戳": metadata.get("timestamp", "N/A")
                        })
                    
                    with col2:
                        usage = metadata.get("token_usage", {})
                        st.json({
                            "提示詞Token": usage.get("prompt_tokens", 0),
                            "回答Token": usage.get("completion_tokens", 0),
                            "總Token": usage.get("total_tokens", 0),
                            "平均相關度": f"{metadata.get('average_relevance_score', 0):.3f}"
                        })
                
            except Exception as e:
                st.error(f"❌ 查詢處理失敗: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>🤖 基於 OpenAI GPT + Pinecone + Sentence Transformers 構建</p>
            <p>📚 數據來源：海外旅行不便險條款</p>
        </div>
        """, 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()