# RAG Insurance Chatbot

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
![License](https://img.shields.io/badge/license-MIT-blue)

A **Retrieval-Augmented Generation (RAG)** system for intelligent insurance policy queries. This system helps users understand insurance clauses through natural language queries with contextual, accurate responses backed by source documents.

## 🌟 Features

- **Intelligent Query Processing**: Natural language understanding for insurance-related questions
- **Document Retrieval**: Vector-based semantic search through insurance clauses
- **Contextual Responses**: GPT-powered responses with source attribution
- **Multilingual Support**: Optimized for Chinese and English insurance terminology
- **RESTful API**: FastAPI-based service with automatic documentation
- **Demo Interface**: Streamlit-based user interface for testing
- **Production Ready**: Docker containerization with monitoring and logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  RAG Pipeline   │───▶│   AI Response   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │    Core Components      │
                    ├─────────────────────────┤
                    │ • Document Processing   │
                    │ • Vector Store (Faiss)  │
                    │ • Embedding Engine      │
                    │ • LLM Integration       │
                    │ • API Service           │
                    └─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** 
- **Docker** (recommended for easy setup)
- **OpenAI API Key** (for GPT integration)

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rag-insurance-chatbot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file and add your OPENAI_API_KEY
   ```

3. **Build and run with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Streamlit UI: http://localhost:8501 (if using frontend profile)

### Option 2: Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. **Run the application**
   ```bash
   python -m src.main
   ```

## 📖 Usage

### API Endpoints

Once running, access the interactive API documentation at `/docs`:

```bash
curl -X GET "http://localhost:8000/health"
```

### Example Query

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "什麼情況下可以申請旅遊延誤賠償？",
        "top_k": 5
    }
)
print(response.json())
```

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

## 📊 Performance

- **Query Response Time**: < 3 seconds (P95)
- **Embedding Generation**: ~100 docs/second
- **Vector Search**: < 50ms locally
- **Memory Usage**: ~4GB total system
- **Supported Concurrency**: Optimized for 1 user (MVP)

## 🔧 Configuration

Key configuration options in `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_key_here
MAX_TOKENS=500
TEMPERATURE=0.1

# Vector Search
TOP_K=5
SIMILARITY_THRESHOLD=0.8
CHUNK_SIZE=256

# Application
LOG_LEVEL=INFO
API_PORT=8000
ENVIRONMENT=development
```

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