# Quick Start Guide

Get the RAG Insurance Chatbot up and running in minutes with this step-by-step guide.

## 🎯 What You'll Build

By the end of this guide, you'll have:
- A running RAG chatbot API server
- Vector search capabilities for insurance documents  
- GPT-powered response generation
- Interactive API documentation

## ⚡ 5-Minute Setup (Docker)

### Step 1: Get the Code
```bash
git clone <repository-url>
cd rag-insurance-chatbot
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit the .env file and add your OpenAI API key
# Required: OPENAI_API_KEY=your_key_here
```

### Step 3: Start the Application
```bash
# Build and run with Docker Compose
docker-compose up --build

# Wait for startup logs to show "Application startup complete"
```

### Step 4: Test the API
Visit http://localhost:8000/docs for interactive API documentation, or test with curl:

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "environment": "development", 
  "version": "1.0.0"
}
```

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- 4GB+ RAM recommended

### Step 1: Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\\Scripts\\activate
```

### Step 2: Install Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Development tools (optional)
pip install -r requirements-dev.txt
```

### Step 3: Validate Setup
```bash
# Check all dependencies
python scripts/validate_dependencies.py

# Should show all ✅ for required packages
```

### Step 4: Configure Application
```bash
# Copy example configuration
cp .env.example .env
```

Edit `.env` file with your settings:
```bash
# Required - Get from OpenAI
OPENAI_API_KEY=sk-your-key-here

# Optional customizations
LOG_LEVEL=INFO
API_PORT=8000
CHUNK_SIZE=256
TOP_K=5
TEMPERATURE=0.1
```

### Step 5: Run the Application
```bash
# Start the FastAPI server
python -m src.main

# Server will start on http://localhost:8000
```

## 📋 First API Calls

### Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### Basic Query (When Implemented)
```bash
curl -X POST "http://localhost:8000/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "什麼情況下可以申請延誤賠償？",
    "top_k": 3
  }'
```

## 🎮 Interactive Testing

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Using Swagger UI
1. Open http://localhost:8000/docs
2. Expand endpoint sections
3. Click "Try it out" on any endpoint
4. Fill in parameters and click "Execute"
5. View responses and example code

## 📊 Monitoring Your Application

### Log Files
```bash
# Application logs
tail -f logs/rag_chatbot_development.log

# Error logs only  
tail -f logs/rag_chatbot_errors_development.log
```

### Docker Logs
```bash
# Follow container logs
docker-compose logs -f rag-chatbot

# Show last 100 lines
docker-compose logs --tail=100 rag-chatbot
```

### Health Monitoring
The `/health` endpoint provides system status:
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0"
}
```

## 🔧 Common Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | OpenAI API key for GPT |
| `LOG_LEVEL` | INFO | Logging level (DEBUG/INFO/WARNING) |
| `API_PORT` | 8000 | Port for FastAPI server |
| `ENVIRONMENT` | development | Environment (development/production) |
| `TOP_K` | 5 | Number of documents to retrieve |
| `TEMPERATURE` | 0.1 | LLM temperature (0.0-2.0) |
| `MAX_TOKENS` | 500 | Maximum response tokens |

### Port Configuration
- **API Server**: 8000 (configurable via API_PORT)
- **Streamlit UI**: 8501 (when using frontend profile)
- **Development**: 8001 (docker-compose dev profile)

## 🚨 Troubleshooting

### Common Issues

**1. "Configuration not initialized" error**
```bash
# Check your .env file exists and has OPENAI_API_KEY
cat .env | grep OPENAI_API_KEY
```

**2. "Module not found" errors**
```bash
# Ensure you're in project directory and virtual environment is active
pwd
which python
pip list | grep fastapi
```

**3. Port already in use**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in .env
echo "API_PORT=8001" >> .env
```

**4. Docker build fails**
```bash
# Clean Docker cache
docker system prune -f

# Rebuild without cache
docker-compose build --no-cache
```

**5. OpenAI API errors**
```bash
# Test API key manually
curl https://api.openai.com/v1/models \\
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Getting Help

1. **Check logs** first for specific error messages
2. **Verify configuration** with validation script
3. **Test dependencies** individually  
4. **Create GitHub issue** with error details and environment info

## ✨ Next Steps

Once you have the basic system running:

1. **Explore the API** using Swagger UI
2. **Add insurance documents** to the data/raw/ directory
3. **Run code quality checks** with `python scripts/check_code_quality.py`
4. **Read the development guide** for advanced usage
5. **Set up the Streamlit frontend** for visual testing

## 📚 Additional Resources

- [Development Guide](development-guide.md) - Detailed development setup
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Architecture Overview](../architecture.md) - System design details
- [Contributing Guidelines](../../CONTRIBUTING.md) - How to contribute

---

**🎉 Congratulations!** You now have a running RAG insurance chatbot. The system is ready for document processing, vector search, and intelligent query responses.