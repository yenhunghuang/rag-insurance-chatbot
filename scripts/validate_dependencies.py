#!/usr/bin/env python3
"""
Dependency validation script for RAG Insurance Chatbot.

This script validates that all required dependencies can be imported correctly.
"""

import sys
from typing import List, Tuple


def validate_core_dependencies() -> List[Tuple[str, bool, str]]:
    """Validate core AI/ML dependencies."""
    results = []
    
    # AI/ML Core
    try:
        import faiss
        results.append(("faiss-cpu", True, f"Version: {faiss.__version__}"))
    except ImportError as e:
        results.append(("faiss-cpu", False, str(e)))
    
    try:
        import sentence_transformers
        results.append(("sentence-transformers", True, f"Version: {sentence_transformers.__version__}"))
    except ImportError as e:
        results.append(("sentence-transformers", False, str(e)))
    
    try:
        import openai
        results.append(("openai", True, f"Version: {openai.__version__}"))
    except ImportError as e:
        results.append(("openai", False, str(e)))
    
    try:
        import numpy as np
        results.append(("numpy", True, f"Version: {np.__version__}"))
    except ImportError as e:
        results.append(("numpy", False, str(e)))
    
    try:
        import pandas as pd
        results.append(("pandas", True, f"Version: {pd.__version__}"))
    except ImportError as e:
        results.append(("pandas", False, str(e)))
    
    return results


def validate_web_dependencies() -> List[Tuple[str, bool, str]]:
    """Validate web framework dependencies."""
    results = []
    
    try:
        import fastapi
        results.append(("fastapi", True, f"Version: {fastapi.__version__}"))
    except ImportError as e:
        results.append(("fastapi", False, str(e)))
    
    try:
        import uvicorn
        results.append(("uvicorn", True, f"Version: {uvicorn.__version__}"))
    except ImportError as e:
        results.append(("uvicorn", False, str(e)))
    
    try:
        import streamlit
        results.append(("streamlit", True, f"Version: {streamlit.__version__}"))
    except ImportError as e:
        results.append(("streamlit", False, str(e)))
    
    return results


def validate_utility_dependencies() -> List[Tuple[str, bool, str]]:
    """Validate utility dependencies."""
    results = []
    
    try:
        import dotenv
        results.append(("python-dotenv", True, "Loaded successfully"))
    except ImportError as e:
        results.append(("python-dotenv", False, str(e)))
    
    try:
        import yaml
        results.append(("pyyaml", True, "Loaded successfully"))
    except ImportError as e:
        results.append(("pyyaml", False, str(e)))
    
    try:
        import pydantic
        results.append(("pydantic", True, f"Version: {pydantic.__version__}"))
    except ImportError as e:
        results.append(("pydantic", False, str(e)))
    
    return results


def main():
    """Run dependency validation."""
    print("🔍 Validating RAG Insurance Chatbot Dependencies\n")
    
    all_results = []
    
    print("📦 Core AI/ML Dependencies:")
    core_results = validate_core_dependencies()
    all_results.extend(core_results)
    for name, success, info in core_results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}: {info}")
    
    print("\n🌐 Web Framework Dependencies:")
    web_results = validate_web_dependencies()
    all_results.extend(web_results)
    for name, success, info in web_results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}: {info}")
    
    print("\n🔧 Utility Dependencies:")
    utility_results = validate_utility_dependencies()
    all_results.extend(utility_results)
    for name, success, info in utility_results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}: {info}")
    
    # Summary
    successful = sum(1 for _, success, _ in all_results if success)
    total = len(all_results)
    
    print(f"\n📊 Summary: {successful}/{total} dependencies validated successfully")
    
    if successful == total:
        print("🎉 All dependencies are available!")
        return 0
    else:
        print("⚠️  Some dependencies are missing. Please install them using:")
        print("   pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())