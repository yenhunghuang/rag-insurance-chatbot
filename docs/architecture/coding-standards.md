# Coding Standards & Best Practices

## 🎯 Development Philosophy
**"寫給人看的代碼，順便給機器執行"**
- 程式碼可讀性優於聰明技巧
- 明確勝過隱含
- 簡單勝過複雜  
- 一致性勝過個人偏好

---

## 📝 Python Code Style

### PEP 8 Compliance + Project Extensions

#### Naming Conventions
```python
# ✅ 變數與函式: snake_case
user_query = "什麼情況下可以申請旅遊延誤賠償？"
embedding_vector = generate_embedding(user_query)

def process_insurance_document(document: str) -> List[Chunk]:
    """處理保險文檔並返回分塊結果"""
    pass

# ✅ 類別: PascalCase
class DocumentProcessor:
    """負責處理保險條款文檔的類別"""
    pass

class RAGEngine:
    """檢索增強生成引擎的主要實作"""
    pass

# ✅ 常數: SCREAMING_SNAKE_CASE
MAX_CHUNK_SIZE = 256
OPENAI_MODEL_NAME = "gpt-3.5-turbo"
DEFAULT_SIMILARITY_THRESHOLD = 0.8

# ✅ 私有成員: 前綴單底線
class VectorStore:
    def __init__(self):
        self._index = None
        self._documents = []
    
    def _build_index(self):
        """私有方法用於建構索引"""
        pass

# ✅ 模組級私有: 前綴單底線
_DEFAULT_CONFIG = {...}

def _internal_helper_function():
    """模組內部使用的輔助函式"""
    pass
```

#### Line Length & Formatting
```python
# ✅ 行長度限制: 88字元 (Black格式化工具標準)
def search_relevant_clauses(
    query: str, 
    top_k: int = 5, 
    similarity_threshold: float = 0.8
) -> List[Document]:
    """搜尋相關的保險條款"""
    pass

# ✅ 長字符串處理
error_message = (
    "檢索系統發生錯誤：無法在指定的相似度閾值下找到相關條款。"
    "請嘗試調整查詢內容或降低相似度要求。"
)

# ✅ 複雜表達式換行
result = some_complex_function(
    parameter_one=value_one,
    parameter_two=value_two,
    parameter_three=very_long_value_that_exceeds_line_limit
)
```

### Type Annotations (強制要求)
```python
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass

# ✅ 函式型別標註
def generate_embeddings(texts: List[str]) -> np.ndarray:
    """為文本列表生成嵌入向量"""
    pass

def search_documents(
    query: str, 
    top_k: int = 5
) -> List[Document]:
    """搜尋相關文檔"""
    pass

# ✅ 複雜型別定義
QueryResult = Dict[str, Union[str, float, List[Document]]]

def process_query(query: str) -> QueryResult:
    """處理用戶查詢並返回結構化結果"""
    pass

# ✅ 類別屬性型別標註  
@dataclass
class Document:
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    chunk_id: Optional[str] = None

# ✅ 可選型別處理
def load_config(config_path: Optional[str] = None) -> Config:
    """載入配置，如果路徑為空則使用預設"""
    if config_path is None:
        config_path = "default_config.yaml"
    # 實作邏輯
    pass
```

---

## 🏗️ Architecture Patterns

### Dependency Injection Pattern
```python
# ✅ 抽象介面定義
from abc import ABC, abstractmethod

class RetrieverInterface(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int) -> List[Document]:
        pass

class GeneratorInterface(ABC):
    @abstractmethod  
    def generate_response(self, context: str, query: str) -> str:
        pass

# ✅ 依賴注入實作
class RAGEngine:
    def __init__(
        self,
        retriever: RetrieverInterface,
        generator: GeneratorInterface,
        config: Config
    ):
        self.retriever = retriever
        self.generator = generator
        self.config = config
    
    def process_query(self, query: str) -> ChatbotResponse:
        # 業務邏輯不依賴具體實作
        documents = self.retriever.search(query, self.config.top_k)
        context = self._build_context(documents)
        answer = self.generator.generate_response(context, query)
        return ChatbotResponse(answer=answer, sources=documents)

# ✅ Factory Pattern for DI
class ComponentFactory:
    @staticmethod
    def create_retriever(config: Config) -> RetrieverInterface:
        if config.retriever_type == "faiss":
            return FaissRetriever(config)
        elif config.retriever_type == "pinecone":
            return PineconeRetriever(config)
        else:
            raise ValueError(f"Unknown retriever type: {config.retriever_type}")
```

### Error Handling Strategy
```python
# ✅ 自定義例外類別層次結構
class RAGSystemError(Exception):
    """RAG系統基礎例外類別"""
    pass

class RetrievalError(RAGSystemError):
    """檢索相關錯誤"""
    pass

class GenerationError(RAGSystemError):
    """生成相關錯誤"""
    pass

class ConfigurationError(RAGSystemError):
    """配置相關錯誤"""
    pass

# ✅ 錯誤處理最佳實踐
import logging

logger = logging.getLogger(__name__)

def search_documents(query: str) -> List[Document]:
    try:
        # 檢索邏輯
        results = perform_vector_search(query)
        if not results:
            logger.warning(f"No documents found for query: {query}")
            return []
        return results
        
    except ConnectionError as e:
        logger.error(f"Vector database connection failed: {e}")
        raise RetrievalError(f"檢索服務暫時無法使用: {e}") from e
        
    except ValueError as e:
        logger.error(f"Invalid query format: {e}")
        raise RetrievalError(f"查詢格式錯誤: {e}") from e
        
    except Exception as e:
        logger.exception(f"Unexpected error in document search: {e}")
        raise RAGSystemError(f"系統發生未預期錯誤") from e

# ✅ Context Manager for Resource Management  
from contextlib import contextmanager

@contextmanager
def vector_store_connection(config: Config):
    """向量資料庫連線的上下文管理器"""
    store = None
    try:
        store = VectorStore(config)
        store.connect()
        yield store
    except Exception as e:
        logger.error(f"Vector store connection error: {e}")
        raise
    finally:
        if store:
            store.disconnect()
```

### Configuration Management
```python
# ✅ 結構化配置類別
from dataclasses import dataclass, field
from typing import List
import os

@dataclass
class EmbeddingConfig:
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 32
    max_length: int = 512

@dataclass  
class RetrievalConfig:
    top_k: int = 5
    similarity_threshold: float = 0.8
    index_type: str = "faiss"

@dataclass
class GenerationConfig:
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.1
    max_tokens: int = 500
    
@dataclass
class AppConfig:
    # 環境變數整合
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    # 子配置組合
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)  
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    
    # 驗證方法
    def __post_init__(self):
        if not self.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY environment variable is required")
        
        if self.retrieval.top_k <= 0:
            raise ConfigurationError("retrieval.top_k must be positive")

# ✅ 配置載入工廠
class ConfigFactory:
    @staticmethod
    def load_from_env() -> AppConfig:
        """從環境變數載入配置"""
        return AppConfig()
    
    @staticmethod
    def load_from_file(config_path: str) -> AppConfig:
        """從YAML檔案載入配置"""
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        return AppConfig(**data)
```

---

## 🧪 Testing Standards

### Test Organization
```python
# tests/unit/test_document_processor.py
import pytest
from unittest.mock import Mock, patch
from src.processing import DocumentProcessor
from src.models import Document

class TestDocumentProcessor:
    """DocumentProcessor的單元測試"""
    
    def setup_method(self):
        """每個測試方法執行前的設置"""
        self.processor = DocumentProcessor()
        self.sample_text = "第3.1條 旅程延誤保障：被保險人之原定搭乘班機..."
    
    def test_chunk_document_basic(self):
        """測試基本文檔分塊功能"""
        # Arrange
        expected_chunks = 2
        
        # Act  
        result = self.processor.chunk_document(self.sample_text)
        
        # Assert
        assert len(result) == expected_chunks
        assert all(isinstance(chunk, Document) for chunk in result)
        assert all(chunk.content for chunk in result)
    
    def test_chunk_document_empty_input(self):
        """測試空輸入的邊界情況"""
        # Act & Assert
        with pytest.raises(ValueError, match="文檔內容不能為空"):
            self.processor.chunk_document("")
    
    @patch('src.processing.document_processor.extract_metadata')
    def test_chunk_with_metadata(self, mock_extract):
        """測試帶有元數據的分塊"""
        # Arrange
        mock_extract.return_value = {"article": "3.1", "type": "coverage"}
        
        # Act
        result = self.processor.chunk_document(self.sample_text)
        
        # Assert  
        mock_extract.assert_called_once()
        assert result[0].metadata["article"] == "3.1"

# ✅ Integration Test Example
# tests/integration/test_rag_pipeline.py
class TestRAGPipeline:
    """RAG系統整合測試"""
    
    @pytest.fixture
    def rag_system(self):
        """RAG系統測試裝置"""
        config = AppConfig()
        retriever = FaissRetriever(config)
        generator = OpenAIGenerator(config)
        return RAGEngine(retriever, generator, config)
    
    def test_end_to_end_query(self, rag_system):
        """端到端查詢測試"""
        # Arrange
        test_query = "什麼情況下可以申請旅遊延誤賠償？"
        
        # Act
        response = rag_system.process_query(test_query)
        
        # Assert
        assert response.answer
        assert len(response.sources) > 0
        assert response.confidence > 0.5
        assert "延誤" in response.answer
```

### Test Data Management
```python
# tests/conftest.py - 共用測試設備
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """測試數據目錄"""
    return Path(__file__).parent / "data"

@pytest.fixture(scope="session") 
def sample_insurance_clauses(test_data_dir):
    """樣本保險條款"""
    with open(test_data_dir / "sample_clauses.json") as f:
        return json.load(f)

@pytest.fixture(scope="function")
def mock_openai_response():
    """模擬OpenAI API回應"""
    return {
        "choices": [{
            "message": {
                "content": "根據第3.1條規定，當班機延誤達4小時以上時..."
            }
        }]
    }

# ✅ Test Categories
"""
測試分類標記:
@pytest.mark.unit       - 單元測試  
@pytest.mark.integration - 整合測試
@pytest.mark.e2e        - 端到端測試
@pytest.mark.slow       - 慢速測試 (需要外部API)
@pytest.mark.gpu        - 需要GPU的測試
"""

@pytest.mark.slow
@pytest.mark.integration
def test_openai_api_integration():
    """測試OpenAI API整合 (需要實際API調用)"""
    pass
```

---

## 📚 Documentation Standards

### Docstring Conventions (Google Style)
```python
def search_insurance_clauses(
    query: str,
    clause_types: List[str] = None,
    similarity_threshold: float = 0.8,
    max_results: int = 5
) -> List[Document]:
    """搜尋相關的保險條款。
    
    根據用戶查詢在保險條款資料庫中搜尋相關內容，支援條款類型過濾
    和相似度閾值設定。
    
    Args:
        query: 用戶查詢文本，例如"什麼情況可以申請延誤賠償？"
        clause_types: 限制搜尋的條款類型列表，可選值包括:
            - "coverage": 保障條款
            - "exclusion": 免責條款  
            - "procedure": 申請程序
            預設為None表示搜尋所有類型。
        similarity_threshold: 相似度最小閾值，範圍0.0-1.0，
            預設0.8表示只返回高相關性結果。
        max_results: 最大返回結果數量，預設5。
    
    Returns:
        按相關性排序的Document列表，每個Document包含:
        - content: 條款內容文本
        - metadata: 包含條款編號、類型等資訊
        - similarity_score: 與查詢的相似度分數
    
    Raises:
        RetrievalError: 當檢索系統無法連線或查詢格式錯誤時。
        ValueError: 當參數值超出有效範圍時。
    
    Example:
        >>> searcher = ClauseSearcher()
        >>> results = searcher.search_insurance_clauses(
        ...     "行李遺失理賠",
        ...     clause_types=["coverage", "procedure"],
        ...     max_results=3
        ... )
        >>> print(f"找到 {len(results)} 個相關條款")
        找到 3 個相關條款
    
    Note:
        此函式會記錄查詢統計資訊用於系統監控和性能分析。
        對於相同查詢，結果會被緩存30分鐘以提升回應速度。
    """
    # 實作邏輯...
    pass

# ✅ 類別文檔標準
class RAGEngine:
    """檢索增強生成(RAG)引擎的核心實作。
    
    RAGEngine整合了文檔檢索和語言生成功能，為保險條款查詢
    提供智能問答服務。系統採用語義檢索配合GPT模型生成，
    確保回答準確性和可追溯性。
    
    Attributes:
        retriever: 文檔檢索器實例，負責找尋相關條款。
        generator: 回答生成器實例，負責合成自然語言回答。
        config: 系統配置物件，包含模型參數和業務規則。
    
    Example:
        >>> config = AppConfig()
        >>> retriever = FaissRetriever(config)
        >>> generator = OpenAIGenerator(config)
        >>> rag = RAGEngine(retriever, generator, config)
        >>> 
        >>> response = rag.process_query("什麼情況可以申請延誤賠償？")
        >>> print(response.answer)
        根據第3.1條規定，當班機因天候因素延誤達4小時以上時...
    """
    
    def __init__(self, retriever: RetrieverInterface, ...):
        """初始化RAG引擎。
        
        Args:
            retriever: 實作RetrieverInterface的檢索器
            generator: 實作GeneratorInterface的生成器  
            config: 系統配置物件
        """
        pass
```

### Code Comments Guidelines
```python
# ✅ 適當的註解使用
class DocumentProcessor:
    def chunk_document(self, text: str) -> List[Document]:
        # Step 1: 清理文本格式和特殊字符
        cleaned_text = self._clean_text(text)
        
        # Step 2: 按語義邊界分割條款
        # 保險條款通常以"第X條"或"第X.Y條"開始
        clause_boundaries = self._find_clause_boundaries(cleaned_text)
        
        chunks = []
        for i, boundary in enumerate(clause_boundaries):
            # Step 3: 提取每個條款的內容和編號
            clause_content = self._extract_clause_content(
                cleaned_text, 
                boundary, 
                clause_boundaries[i+1] if i+1 < len(clause_boundaries) else None
            )
            
            # Step 4: 為每個chunk生成結構化元數據
            metadata = self._extract_metadata(clause_content)
            
            chunk = Document(
                content=clause_content,
                metadata=metadata,
                chunk_id=f"clause_{i}"
            )
            chunks.append(chunk)
        
        return chunks

# ❌ 避免的註解模式
def add_numbers(a, b):
    # 將 a 和 b 相加    <- 冗餘註解
    return a + b        

x = x + 1  # 將x增加1      <- 顯而易見的註解

# TODO: 修復這個bug     <- 模糊的TODO
# HACK: 暫時的解決方案  <- 沒有說明原因和替代方案

# ✅ 有價值的註解
def calculate_similarity_threshold(user_expertise_level: str) -> float:
    """根據用戶專業程度動態調整相似度閾值"""
    # 保險專業人士可以接受更低相似度的結果，
    # 因為他們具備足夠知識判斷相關性
    if user_expertise_level == "expert":
        return 0.6
    # 一般消費者需要更高相似度確保答案準確性
    elif user_expertise_level == "consumer":  
        return 0.85
    else:
        return 0.8  # 預設中等閾值

    # FIXME: 需要優化大型文檔的分塊策略
    # 當前實作在處理>1MB文檔時會有記憶體問題
    # 替代方案: 考慮使用streaming或lazy loading
    # GitHub Issue: #123
```

---

## 🔍 Code Review Checklist

### Pre-Review Requirements
```
✅ 自我檢查清單:
- [ ] 所有函式都有型別標註和docstring
- [ ] 單元測試覆蓋率 ≥ 80%
- [ ] Black格式化已執行  
- [ ] Flake8檢查通過
- [ ] 沒有明顯的代碼重複
- [ ] 錯誤處理適當且具體
- [ ] 敏感資訊已移除 (API keys, passwords)
- [ ] Import順序符合規範
```

### Review Focus Areas
```python
# 🔍 審查重點 1: 錯誤處理
def risky_function():
    try:
        result = external_api_call()
        return result
    except Exception:  # ❌ 過於寬泛的例外捕捉
        pass           # ❌ 靜默忽略錯誤
        
# ✅ 改進版本        
def improved_function():
    try:
        result = external_api_call()
        return result
    except requests.ConnectionError as e:
        logger.error(f"API connection failed: {e}")
        raise RetrievalError("檢索服務暫時無法使用") from e
    except requests.Timeout as e:
        logger.warning(f"API timeout: {e}")
        raise RetrievalError("檢索服務回應超時") from e

# 🔍 審查重點 2: 資源管理
class VectorStore:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        self.connection = create_connection()
    
    # ❌ 沒有明確的資源清理
    def __del__(self):  # ❌ 不可靠的資源清理方式
        if self.connection:
            self.connection.close()

# ✅ 改進版本
class VectorStore:
    def __enter__(self):
        self.connection = create_connection()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
    
    # 或者提供明確的清理方法
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

# 🔍 審查重點 3: 性能考慮
def process_documents(documents):
    results = []
    for doc in documents:  # ❌ 順序處理，效率低
        embedding = generate_embedding(doc.content)  # ❌ 重複的模型載入
        results.append(embedding)
    return results

# ✅ 改進版本
def process_documents(documents):
    # 批量處理提升效率
    contents = [doc.content for doc in documents]
    embeddings = generate_embeddings_batch(contents)
    return embeddings
```

---

## 🚀 Performance Guidelines

### Memory Management
```python
# ✅ 記憶體效率的設計
class EmbeddingCache:
    def __init__(self, max_size: int = 1000):
        from collections import OrderedDict
        self._cache = OrderedDict()
        self._max_size = max_size
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        if text in self._cache:
            # LRU: 移動到最後表示最近使用
            self._cache.move_to_end(text)
            return self._cache[text]
        return None
    
    def set_embedding(self, text: str, embedding: np.ndarray):
        self._cache[text] = embedding
        self._cache.move_to_end(text)
        
        # 維持緩存大小限制
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

# ✅ Generator用於大型數據處理
def load_documents(file_path: str) -> Iterator[Document]:
    """使用generator避免一次性載入大量文檔到記憶體"""
    with open(file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            yield Document(
                content=data['content'],
                metadata=data['metadata']
            )

# ✅ 適當的資料結構選擇
class DocumentIndex:
    def __init__(self):
        # 使用set進行快速成員檢查
        self._processed_ids = set()
        # 使用dict進行快速ID查找
        self._id_to_document = {}
        # 使用deque進行高效佇列操作
        from collections import deque
        self._processing_queue = deque()
```

### Async Programming Standards  
```python
import asyncio
import aiohttp
from typing import List

# ✅ 異步API呼叫
class AsyncLLMClient:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def generate_response(self, prompt: str) -> str:
        """異步生成回答"""
        async with self.session.post(
            'https://api.openai.com/v1/chat/completions',
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': prompt}]
            }
        ) as response:
            data = await response.json()
            return data['choices'][0]['message']['content']

# ✅ 批量異步處理
async def process_multiple_queries(queries: List[str]) -> List[str]:
    """並行處理多個查詢以提升throughput"""
    async with AsyncLLMClient() as client:
        tasks = [
            client.generate_response(query) 
            for query in queries
        ]
        results = await asyncio.gather(*tasks)
        return results
```

---

_This coding standards document ensures consistent, maintainable, and performant code across the RAG system implementation._