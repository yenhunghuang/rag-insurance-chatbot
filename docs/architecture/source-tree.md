# Source Code Organization

## 📁 Project Structure Overview

```
rag-insurance-chatbot/
├── 📄 README.md                    # 專案說明與快速開始指南
├── 📄 requirements.txt             # Python依賴清單  
├── 📄 .env.example                 # 環境變數範例
├── 📄 .gitignore                   # Git忽略檔案設定
├── 📄 Dockerfile                   # Docker容器化設定
├── 📄 docker-compose.yml           # 本地開發環境編排
├── 📄 setup.py                     # 套件安裝設定
│
├── 📁 src/                         # 主要源碼目錄
│   ├── 📄 __init__.py
│   ├── 📄 config.py                # 全域配置管理
│   ├── 📄 models.py                # 資料模型與型別定義
│   ├── 📄 exceptions.py            # 自定義例外類別
│   ├── 📄 utils.py                 # 通用工具函式
│   ├── 📄 main.py                  # FastAPI應用程式進入點
│   │
│   ├── 📁 processing/              # 文檔處理模組
│   │   ├── 📄 __init__.py
│   │   ├── 📄 document_processor.py    # 條款文檔處理邏輯
│   │   ├── 📄 text_cleaner.py          # 文本清理與正規化  
│   │   └── 📄 chunking_strategy.py     # 文檔分塊策略
│   │
│   ├── 📁 retrieval/               # 檢索系統模組
│   │   ├── 📄 __init__.py
│   │   ├── 📄 retriever.py             # 主要檢索引擎
│   │   ├── 📄 vector_store.py          # 向量資料庫封裝
│   │   ├── 📄 embedding_engine.py      # 文本嵌入生成
│   │   └── 📄 ranking_engine.py        # 檢索結果排序
│   │
│   ├── 📁 generation/              # 生成系統模組  
│   │   ├── 📄 __init__.py
│   │   ├── 📄 generator.py             # 主要回答生成器
│   │   ├── 📄 prompt_templates.py      # 提示詞模板管理
│   │   ├── 📄 llm_interface.py         # LLM API介面封裝
│   │   └── 📄 response_processor.py    # 回答後處理邏輯
│   │
│   ├── 📁 api/                     # API服務模組
│   │   ├── 📄 __init__.py
│   │   ├── 📄 routes.py                # API路由定義
│   │   ├── 📄 middleware.py            # 中介軟體 (CORS, 日誌等)
│   │   ├── 📄 dependencies.py          # 依賴注入管理
│   │   └── 📄 schemas.py               # API輸入輸出模式
│   │
│   └── 📁 evaluation/              # 評估與測試模組
│       ├── 📄 __init__.py
│       ├── 📄 evaluator.py             # 系統評估邏輯
│       ├── 📄 metrics.py               # 評估指標計算
│       └── 📄 benchmark.py             # 基準測試工具
│
├── 📁 data/                        # 資料檔案目錄
│   ├── 📁 raw/                     # 原始資料
│   │   ├── 📄 insurance_clauses.txt    # 原始保險條款
│   │   └── 📄 terms_glossary.json      # 專業術語詞彙表
│   ├── 📁 processed/               # 處理後資料
│   │   ├── 📄 chunks.json              # 分塊後的條款片段
│   │   └── 📄 embeddings.npy           # 預計算的嵌入向量
│   ├── 📁 indices/                 # 索引檔案
│   │   ├── 📄 faiss_index.bin          # Faiss向量索引
│   │   └── 📄 metadata.json            # 索引元資料
│   └── 📁 test/                    # 測試資料
│       ├── 📄 test_questions.json      # 標準測試問題集
│       └── 📄 expected_answers.json    # 預期答案
│
├── 📁 tests/                       # 測試程式目錄
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py                  # pytest配置與fixtures
│   ├── 📁 unit/                    # 單元測試
│   │   ├── 📄 test_document_processor.py
│   │   ├── 📄 test_retriever.py
│   │   ├── 📄 test_generator.py
│   │   └── 📄 test_api_routes.py
│   ├── 📁 integration/             # 整合測試
│   │   ├── 📄 test_rag_pipeline.py
│   │   └── 📄 test_api_integration.py
│   └── 📁 e2e/                     # 端對端測試
│       └── 📄 test_full_system.py
│
├── 📁 scripts/                     # 工具腳本目錄
│   ├── 📄 setup_environment.py         # 環境初始化腳本
│   ├── 📄 build_index.py              # 索引建構腳本  
│   ├── 📄 run_evaluation.py           # 評估執行腳本
│   ├── 📄 data_preparation.py         # 資料準備腳本
│   └── 📄 demo_server.py              # 演示服務器啟動腳本
│
├── 📁 notebooks/                   # Jupyter筆記本 (可選)
│   ├── 📄 data_exploration.ipynb      # 資料探索分析
│   ├── 📄 model_evaluation.ipynb      # 模型效果評估  
│   └── 📄 system_demo.ipynb           # 系統演示筆記本
│
├── 📁 docs/                        # 文檔目錄
│   ├── 📄 prd.md                      # 產品需求文檔
│   ├── 📄 architecture.md             # 系統架構文檔
│   ├── 📁 architecture/            # 詳細架構文檔
│   │   ├── 📄 tech-stack.md
│   │   ├── 📄 source-tree.md
│   │   └── 📄 coding-standards.md
│   ├── 📁 api/                     # API文檔
│   │   └── 📄 openapi.json
│   └── 📁 guides/                  # 使用指南
│       ├── 📄 quick-start.md
│       └── 📄 development-guide.md
│
├── 📁 frontend/                    # 前端界面 (Streamlit)
│   ├── 📄 app.py                      # Streamlit主應用
│   ├── 📄 components.py               # UI元件
│   ├── 📄 styles.css                  # 自定義樣式
│   └── 📁 pages/                   # 多頁面應用
│       ├── 📄 chat.py                 # 問答頁面
│       └── 📄 admin.py                # 管理頁面
│
└── 📁 deployment/                  # 部署相關檔案
    ├── 📄 docker-compose.prod.yml     # 生產環境編排
    ├── 📁 k8s/                     # Kubernetes配置 (未來使用)
    └── 📁 scripts/                 # 部署腳本
        ├── 📄 deploy.sh
        └── 📄 health_check.py
```

## 📋 Key Directories Explained

### `/src` - 核心業務邏輯
```
責任分離原則:
├── config.py: 全域設定，環境變數管理
├── models.py: 型別安全，資料結構定義  
├── processing/: 資料預處理，文檔分塊
├── retrieval/: 向量檢索，相似度計算
├── generation/: 自然語言生成，回答合成
└── api/: HTTP介面，請求路由
```

### `/data` - 資料管理
```
資料生命週期:
├── raw/: 原始輸入資料 (不可修改)
├── processed/: 清理後的中間資料
├── indices/: 建構完成的檢索索引
└── test/: 驗證與測試資料集
```

### `/tests` - 測試策略
```
測試金字塔:
├── unit/: 單一功能測試 (70%)
├── integration/: 模組間整合測試 (20%)  
└── e2e/: 完整系統測試 (10%)
```

## 🔧 Module Dependencies

### Import Hierarchy
```python
# 依賴層級 (由上到下)
Level 1: External Libraries
├── fastapi, openai, faiss, sentence-transformers
└── streamlit, pandas, numpy

Level 2: Core Infrastructure  
├── src.config (全域配置)
├── src.models (型別定義)  
├── src.exceptions (錯誤處理)
└── src.utils (工具函式)

Level 3: Business Logic
├── src.processing (資料處理)
├── src.retrieval (檢索邏輯)
└── src.generation (生成邏輯)

Level 4: Application Layer
├── src.api (HTTP服務)  
└── src.evaluation (系統評估)

Level 5: User Interface
└── frontend.app (使用者介面)
```

### Module Interaction Rules
```
✅ 允許的依賴方向:
- 上層模組 → 下層模組
- 同層模組 → 核心infrastructure模組  
- 業務邏輯 → 基礎設施

❌ 禁止的依賴方向:
- 下層模組 → 上層模組
- 基礎設施 → 業務邏輯
- 橫向業務模組互相依賴 (processing ↔ retrieval)
```

## 📝 File Naming Conventions

### Python Modules
```
模組命名: snake_case
├── document_processor.py ✅
├── documentProcessor.py ❌  
├── vector_store.py ✅
└── VectorStore.py ❌

類別命名: PascalCase
├── class DocumentProcessor ✅
├── class documentProcessor ❌
├── class VectorStore ✅  
└── class vector_store ❌

函式命名: snake_case
├── def process_document() ✅
├── def processDocument() ❌
├── def build_faiss_index() ✅
└── def buildFaissIndex() ❌
```

### Configuration Files
```
設定檔命名: kebab-case
├── docker-compose.yml ✅
├── requirements.txt ✅
├── coding-standards.md ✅
└── tech_stack.md ❌
```

### Data Files
```
資料檔命名: snake_case
├── insurance_clauses.txt ✅
├── test_questions.json ✅  
├── faiss_index.bin ✅
└── insuranceClauses.txt ❌
```

## 🏗️ Code Organization Principles

### Single Responsibility Principle
```python
# ✅ 良好的職責分離
class DocumentProcessor:
    def chunk_document(self): pass
    def extract_metadata(self): pass
    
class EmbeddingEngine:  
    def generate_embeddings(self): pass
    def batch_encode(self): pass

# ❌ 職責混合的反例
class DocumentHandler:
    def chunk_document(self): pass
    def generate_embeddings(self): pass  # 應該分離
    def search_similar(self): pass       # 應該分離
```

### Interface Segregation
```python
# ✅ 精確的介面定義
class VectorStoreInterface:
    def add_documents(self) -> None: pass
    def search(self) -> List[Document]: pass
    
class LLMInterface:
    def generate_response(self) -> str: pass
    def estimate_tokens(self) -> int: pass

# ❌ 肥大介面的反例  
class AIServiceInterface:
    def add_documents(self): pass    # 向量資料庫操作
    def generate_response(self): pass # LLM操作  
    def evaluate_quality(self): pass  # 評估操作
```

### Dependency Inversion
```python
# ✅ 依賴抽象而非具體實現
class RAGEngine:
    def __init__(self, 
                 retriever: RetrieverInterface,
                 generator: GeneratorInterface):
        self.retriever = retriever
        self.generator = generator

# ❌ 依賴具體實現的反例
class RAGEngine:
    def __init__(self):
        self.retriever = FaissRetriever()    # 硬編碼依賴
        self.generator = OpenAIGenerator()   # 硬編碼依賴
```

## 📦 Package Management Strategy

### Internal Packages
```python
# 核心套件結構
rag_chatbot/
├── __init__.py
├── core/           # 核心基礎設施
├── processing/     # 資料處理
├── retrieval/      # 檢索系統
├── generation/     # 生成系統  
└── evaluation/     # 評估工具
```

### Import Strategy
```python
# ✅ 推薦的import模式
from rag_chatbot.core import Config
from rag_chatbot.retrieval import Retriever
from rag_chatbot.generation import Generator

# ✅ 相對import (模組內)  
from .models import Document
from .exceptions import RetrieverError

# ❌ 避免的import模式
import rag_chatbot.retrieval.vector_store.faiss_impl  # 過深
from rag_chatbot import *                             # 星號導入
```

---

_Source code organization follows clean architecture principles and facilitates maintainable, testable, and scalable development._