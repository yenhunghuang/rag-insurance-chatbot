# Contributing to RAG Insurance Chatbot

Thank you for your interest in contributing to the RAG Insurance Chatbot project! This document provides guidelines and instructions for contributors.

## 🎯 Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## 🏗️ Development Setup

### Prerequisites

- Python 3.8+
- Git
- Docker (recommended)
- OpenAI API key for testing

### Local Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/rag-insurance-chatbot.git
   cd rag-insurance-chatbot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Create environment file**
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY and other configuration
   ```

6. **Verify setup**
   ```bash
   python scripts/check_code_quality.py
   python scripts/validate_dependencies.py
   ```

## 📝 Coding Standards

We maintain high code quality standards following PEP 8 and project-specific guidelines.

### Code Style

- **Formatter**: Black with 88-character line limit
- **Import sorting**: isort with Black profile
- **Linting**: Flake8 with custom rules
- **Type checking**: MyPy for static analysis
- **Security**: Bandit for security scanning

### Documentation Standards

```python
def process_query(query: str, top_k: int = 5) -> QueryResult:
    """Process user query and return relevant documents.
    
    Args:
        query: User's natural language question.
        top_k: Maximum number of documents to return.
        
    Returns:
        QueryResult containing documents and similarity scores.
        
    Raises:
        ValidationError: If query is empty or invalid.
        RetrievalError: If document search fails.
        
    Example:
        >>> result = process_query("什麼是旅遊保險？")
        >>> print(f"Found {len(result.documents)} relevant clauses")
    """
```

### Architecture Principles

Follow the established patterns:

```python
# ✅ Good: Dependency injection
class RAGEngine:
    def __init__(self, retriever: RetrieverInterface, generator: GeneratorInterface):
        self.retriever = retriever
        self.generator = generator

# ❌ Bad: Hard-coded dependencies  
class RAGEngine:
    def __init__(self):
        self.retriever = FaissRetriever()  # Tightly coupled
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests (70%)
├── integration/    # Component interaction tests (20%)  
└── e2e/           # Full system tests (10%)
```

### Writing Tests

```python
# tests/unit/test_document_processor.py
import pytest
from src.processing import DocumentProcessor
from src.exceptions import ProcessingError

class TestDocumentProcessor:
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()
        self.sample_text = "第3.1條 旅程延誤保障..."
    
    def test_chunk_document_success(self):
        """Test successful document chunking."""
        # Arrange
        expected_chunks = 2
        
        # Act
        result = self.processor.chunk_document(self.sample_text)
        
        # Assert  
        assert len(result) == expected_chunks
        assert all(chunk.content for chunk in result)
    
    def test_chunk_document_empty_input(self):
        """Test error handling for empty input."""
        with pytest.raises(ProcessingError, match="Empty document"):
            self.processor.chunk_document("")
```

### Test Categories

Mark your tests appropriately:

```python
@pytest.mark.unit
def test_basic_functionality():
    """Unit test for core functionality."""
    pass

@pytest.mark.integration  
def test_component_interaction():
    """Integration test between components."""
    pass

@pytest.mark.slow
def test_external_api():
    """Test requiring external API calls."""
    pass
```

## 🔀 Git Workflow

### Branch Naming

- **Features**: `feature/add-multilingual-support`
- **Bug fixes**: `bugfix/fix-embedding-cache`  
- **Documentation**: `docs/update-api-guide`
- **Refactoring**: `refactor/simplify-config-loading`

### Commit Messages

Follow conventional commits format:

```
feat: add multilingual embedding support

- Implement language detection for queries
- Add support for Chinese and English models
- Update configuration for language-specific settings

Closes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   python scripts/check_code_quality.py
   pytest tests/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Use descriptive title and description
   - Reference related issues
   - Include testing details
   - Add screenshots for UI changes

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change  
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## 🐛 Bug Reports

When reporting bugs, include:

1. **Environment details** (Python version, OS, Docker, etc.)
2. **Steps to reproduce** the issue
3. **Expected vs actual behavior**
4. **Error messages** and logs
5. **Configuration** (anonymized .env values)

### Bug Report Template

```markdown
**Environment:**
- Python Version: 3.11
- OS: macOS 13.0
- Docker: Yes/No
- OpenAI Model: gpt-3.5-turbo

**Bug Description:**
Clear description of what the bug is.

**Steps to Reproduce:**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Logs:**
```
Error logs here
```

**Additional Context:**
Any other context about the problem.
```

## 💡 Feature Requests

For new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and problem it solves
3. **Provide examples** of how it would work
4. **Consider backwards compatibility**

## 🔍 Code Review Guidelines

### For Reviewers

- **Be constructive** and respectful
- **Focus on code quality** and maintainability
- **Check for security** issues
- **Verify tests** are adequate
- **Ensure documentation** is updated

### Review Checklist

- [ ] Code follows project conventions
- [ ] Tests are comprehensive and pass
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance implications considered
- [ ] Error handling is appropriate
- [ ] Logging is meaningful

## 📚 Resources

- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Pytest Documentation](https://docs.pytest.org/)

## 🤝 Community

- **GitHub Discussions**: For general questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions

## ⚡ Quick Commands

```bash
# Quality checks
python scripts/check_code_quality.py --fix

# Run tests
pytest tests/ -v

# Update dependencies
pip-compile requirements.in

# Build documentation
mkdocs serve

# Docker development
docker-compose up --build -d
```

Thank you for contributing to the RAG Insurance Chatbot! 🎉