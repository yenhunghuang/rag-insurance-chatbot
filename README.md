# 海外旅行不便險 RAG 智能客服系統

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![OpenAI](https://img.shields.io/badge/OpenAI-1.105.0-green)
![Pinecone](https://img.shields.io/badge/Pinecone-3.0.0-orange)
![Status](https://img.shields.io/badge/status-production--ready-green)

一個專為**海外旅行不便險條款諮詢**設計的智能RAG系統。使用先進的向量檢索和GPT生成技術，提供準確、上下文相關的保險條款解答服務。

**🎯 專案狀態**: 開發完成 - 已實現完整的RAG pipeline，支援中文保險條款查詢

## 🌟 核心功能

- **🧠 智能查詢處理**: 支援中文自然語言理解，精確解析保險相關問題
- **📄 文檔檢索系統**: 基於OpenAI text-embedding-3-small的向量檢索，語義搜尋保險條款
- **💬 上下文回答生成**: GPT-3.5-turbo驅動的專業保險諮詢，附帶來源引用
- **🗄️ 向量數據庫**: Pinecone雲端向量存儲，快速高效的相似性搜索
- **🔧 RESTful API**: FastAPI框架，自動生成API文檔，支援交互式測試
- **🛡️ 安全性保障**: 完整的輸入驗證、PII保護和安全審計
- **⚡ 生產就緒**: 完整的錯誤處理、日誌系統和性能監控

## 🎯 已實現的系統能力

- ✅ **文檔處理**: 成功處理43個海外旅行不便險條款chunk
- ✅ **向量嵌入**: 1536維向量生成，支援中文語義理解  
- ✅ **智能檢索**: Pinecone向量數據庫整合，相似性閾值過濾
- ✅ **回答生成**: GPT-3.5-turbo專業保險領域回答
- ✅ **API服務**: 完整的FastAPI端點和文檔
- ✅ **測試驗證**: 集成測試和功能驗證完成

## 🏗️ 系統架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   中文查詢問題    │───▶│  RAG處理pipeline │───▶│   智能回答結果   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │      核心組件架構        │
                    ├─────────────────────────┤
                    │ • 文檔處理 (PDF→chunk)   │
                    │ • 向量存儲 (Pinecone)    │
                    │ • 嵌入引擎 (OpenAI)      │
                    │ • LLM生成 (GPT-3.5)     │
                    │ • API服務 (FastAPI)     │
                    │ • 安全層 (驗證&審計)     │
                    └─────────────────────────┘
```

### 技術棧詳情

**核心AI服務**:
- 📊 **向量嵌入**: OpenAI text-embedding-3-small (1536維)
- 🤖 **語言生成**: OpenAI GPT-3.5-turbo
- 🗄️ **向量數據庫**: Pinecone (雲端託管)
- 🔍 **相似性搜索**: 餘弦相似度 (閾值0.8)

**應用架構**:
- 🚀 **Web框架**: FastAPI 0.104.1
- 🐍 **運行環境**: Python 3.11+
- 📝 **文檔格式**: PDF → TXT → 結構化chunk
- 🔐 **安全框架**: 輸入驗證 + PII保護 + 審計日誌

## 🚀 快速開始

### 🔧 系統需求

- **Python 3.11+**
- **OpenAI API Key** (GPT-3.5-turbo + text-embedding-3-small)
- **Pinecone API Key** (向量數據庫服務)

### ⚡ 本地開發設置

1. **環境準備**
   ```bash
   # 創建虛擬環境
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   
   # 安裝依賴
   pip install -r requirements.txt
   ```

2. **配置環境變量**
   ```bash
   # 複製並編輯環境配置
   cp .env.example .env
   ```
   
   在 `.env` 文件中設置：
   ```bash
   # OpenAI 配置
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Pinecone 配置  
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=us-east-1
   PINECONE_INDEX_NAME=your_index_name
   
   # 模型配置
   EMBEDDING_MODEL=text-embedding-3-small
   VECTOR_DIMENSION=1536
   ```

3. **系統測試**
   ```bash
   # 執行整合測試
   python test_system.py
   ```

4. **啟動API服務**
   ```bash
   # 啟動FastAPI伺服器
   python -m src.main
   
   # 訪問API文檔: http://localhost:8000/docs
   # 健康檢查: http://localhost:8000/health
   ```

5. **網頁界面 (可選)**
   ```bash
   # 啟動Streamlit演示界面
   streamlit run streamlit_demo.py
   
   # 訪問: http://localhost:8501
   ```

## 📖 使用指南

### 🔌 API端點

系統提供完整的RESTful API服務：

```bash
# 健康檢查
curl -X GET "http://localhost:8000/health"

# 查詢保險條款
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "班機延誤超過幾小時可以申請賠償？",
    "top_k": 5,
    "threshold": 0.8
  }'
```

### 💬 查詢範例

**Python客戶端**:
```python
import requests

# 查詢海外旅行不便險條款
response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "query": "行李延誤超過多久可以申請賠償？",
        "top_k": 5,
        "threshold": 0.8
    }
)

result = response.json()
print(f"回答: {result['answer']}")
print(f"信心度: {result['confidence_score']}")
print(f"來源文檔: {len(result['sources'])}")
```

**JavaScript客戶端**:
```javascript
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: '颱風導致班機取消，可以申請哪些賠償？',
    top_k: 5,
    threshold: 0.8
  })
});

const result = await response.json();
console.log('AI回答:', result.answer);
```

### 🎯 典型查詢場景

- **班機延誤**: "班機延誤超過6小時可以申請多少賠償？"
- **行李問題**: "行李遺失或延誤的賠償標準是什麼？"
- **醫療費用**: "海外就醫費用申請需要哪些文件？"
- **旅程變更**: "因不可抗力因素導致行程變更如何申請補償？"

## 🛠️ Development

### Code Quality

This project maintains high code quality standards:

```bash
# Run all quality checks
python scripts/check_code_quality.py

# Auto-fix formatting issues
python scripts/check_code_quality.py --fix

# Individual checks
black src/ tests/ scripts/
flake8 src/ tests/ scripts/
mypy src/
pytest tests/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Project Structure

```
rag-insurance-chatbot/
├── src/                     # Main source code
│   ├── processing/          # Document processing
│   ├── retrieval/          # Vector search
│   ├── generation/         # Response generation
│   ├── api/               # FastAPI routes
│   └── evaluation/        # System evaluation
├── data/                   # Data files
│   ├── raw/               # Original documents
│   ├── processed/         # Processed chunks
│   └── indices/          # Vector indices
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/             # End-to-end tests
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── frontend/             # Streamlit UI
└── deployment/          # Deployment files
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories  
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m e2e          # End-to-end tests
```

## 📊 性能指標

基於實際測試結果的系統性能數據：

- **⚡ 查詢響應時間**: < 3秒 (端到端處理)
- **🔍 向量搜索速度**: ~2秒 (Pinecone雲端檢索)
- **📝 文檔處理能力**: 43個chunk成功索引
- **🧠 嵌入生成**: 43個文檔批量處理 ~3秒
- **💾 向量維度**: 1536維 (OpenAI text-embedding-3-small)
- **🎯 相似性閾值**: 0.8 (可配置)
- **📚 知識庫規模**: 海外旅行不便險完整條款

### 系統資源使用

- **內存使用**: ~2GB (包含模型加載)
- **存儲需求**: ~50MB (處理後的chunk數據)
- **API併發**: 支援同時查詢處理
- **可擴展性**: 支援更多保險產品文檔擴展

## 🔧 配置說明

### 主要配置項 (.env 文件)

```bash
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
MAX_TOKENS=500
TEMPERATURE=0.1

# Pinecone 向量數據庫配置
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=0903practice
PINECONE_NAMESPACE=travel-insurance

# 嵌入模型配置
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DIMENSION=1536

# 檢索參數
TOP_K=5
SIMILARITY_THRESHOLD=0.8
CHUNK_SIZE=256
CHUNK_OVERLAP=26

# 應用程式配置
LOG_LEVEL=INFO
API_HOST=localhost
API_PORT=8000
ENVIRONMENT=development
```

### 關鍵配置說明

- **EMBEDDING_MODEL**: 使用OpenAI最新的embedding模型
- **VECTOR_DIMENSION**: 1536維向量確保最佳語義理解
- **SIMILARITY_THRESHOLD**: 0.8閾值平衡精確度與召回率
- **CHUNK_SIZE/OVERLAP**: 優化後的chunk參數適合中文保險條款

## 🚦 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   export ENVIRONMENT=production
   export LOG_LEVEL=INFO
   ```

2. **Docker Production Build**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
   ```

3. **Health Monitoring**
   - Health endpoint: `/health`
   - Metrics: Available in logs
   - Error tracking: Structured JSON logging

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes following our coding standards
4. Run quality checks: `python scripts/check_code_quality.py`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See `/docs` directory for detailed guides
- **Issues**: Create GitHub issues for bugs and feature requests
- **Development Guide**: See [docs/guides/development-guide.md](docs/guides/development-guide.md)

## 📈 Roadmap

- [ ] Advanced query preprocessing
- [ ] Multiple document format support
- [ ] Performance optimization
- [ ] Multi-tenant architecture
- [ ] Advanced analytics and monitoring
- [ ] Mobile-responsive UI

---

**Built with ❤️ for intelligent insurance assistance**