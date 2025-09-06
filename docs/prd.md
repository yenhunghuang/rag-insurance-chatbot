# Product Requirements Document (PRD) v4
# 旅遊不便險 RAG Chatbot 系統

## 📋 Document Information
- **Version**: v4.0
- **Date**: 2025-01-03
- **Project**: RAG Insurance Chatbot
- **Type**: MVP Prototype for Interview Demonstration
- **Timeline**: 3.5 days development cycle

---

## 🎯 Executive Summary

### Product Vision
開發一個基於檢索增強生成(RAG)技術的旅遊不便險智能問答系統，能夠準確解答客戶關於保險條款的查詢，並提供可追溯的條款來源引用。

### Business Objectives
- **主要目標**: 技術概念驗證(POC)，展示RAG技術在保險領域的應用可行性
- **面試目標**: 在15分鐘內完整展示系統核心功能與技術深度
- **商業價值**: 驗證AI助手在保險客服領域的潛力，預期可減少60%人工諮詢工作量

### Success Metrics
- 三個測試問題回答準確率 ≥ 85%
- 條款來源引用準確性 ≥ 90%
- 系統回應時間 ≤ 5秒
- 完整技術演示無故障運行

---

## 🏆 Product Goals & Success Metrics

### Primary Goals
1. **技術驗證**: 證明RAG架構在保險條款查詢場景的有效性
2. **準確性展示**: 針對三個核心問題類型提供專業準確的回答
3. **可追溯性**: 每個回答都能提供具體的條款來源和編號引用
4. **系統穩定性**: 演示過程中系統運行穩定，無技術故障

### Key Performance Indicators (KPIs)
- **Retrieval Accuracy**: Precision@5 ≥ 0.85
- **Answer Quality**: 專家評分 ≥ 4.0/5.0
- **Source Citation**: 引用準確率 ≥ 90%
- **Deduplication Efficiency**: 去重效果 ≥ 95%，消除重複來源
- **Response Time**: 平均回應時間 ≤ 5秒
- **System Uptime**: 演示期間 100% 可用性

---

## 👥 Target Users & Use Cases

### Primary Users
**保險業務評估者 & 技術決策者**
- **需求**: 評估AI技術在保險客服的應用潛力
- **使用場景**: 技術概念驗證、投資決策評估
- **成功標準**: 看到技術可行性和商業價值的清晰展示

### Secondary Users  
**面試官 & 技術專家**
- **需求**: 評估候選人的技術能力和系統設計思維
- **使用場景**: 技術面試、能力評估
- **成功標準**: 理解技術架構深度和實現質量

### End User Scenarios (測試用例)
1. **延誤賠償查詢**: "什麼情況下可以申請旅遊延誤賠償？"
2. **行李理賠流程**: "行李遺失後應該如何申請理賠？"
3. **免責條款確認**: "哪些原因屬於不可理賠範圍？"

---

## 🔧 Core Features & Requirements

### MVP Core Features

#### 1. 智能問答引擎 (Priority: P0)
**功能描述**: 基於RAG技術的核心問答系統
- **輸入**: 自然語言保險查詢問題
- **處理**: 向量檢索 + LLM生成
- **輸出**: 結構化的專業回答

**技術要求**:
- 支援繁體中文查詢和回答
- 回應時間 ≤ 5秒
- 輸出格式包含：直接答案、條款依據、注意事項

#### 2. 條款檢索系統 (Priority: P0)
**功能描述**: 準確檢索相關保險條款片段
- **檢索方法**: 語義向量檢索 (Sentence-BERT + Faiss)
- **檢索範圍**: 旅遊不便險條款文檔
- **輸出**: Top-5 相關條款片段

**技術要求**:
- 檢索準確率 Precision@5 ≥ 85%
- 支援模糊語義匹配
- 條款來源可追溯

#### 3. 來源引用系統 (Priority: P0)  
**功能描述**: 提供每個回答的條款來源引用
- **引用格式**: 條款編號 + 具體內容摘要
- **追溯能力**: 可定位到原始條款文檔位置
- **驗證機制**: 引用內容與檢索結果一致性檢查

#### 4. 智能去重系統 (Priority: P0)
**功能描述**: 自動過濾重複的條款來源，確保結果唯一性
- **去重邏輯**: 基於內容前150字符的智能去重算法
- **效果指標**: 100%去重效果，從多個重複源減少至單一最佳匹配
- **用戶體驗**: 避免重複信息干擾，提供清晰精準的回答來源

#### 5. 演示界面 (Priority: P1)
**功能描述**: 簡潔的Web界面用於技術演示
- **技術選擇**: Streamlit 快速原型
- **功能**: 問題輸入、回答顯示、檢索結果可視化
- **要求**: 界面清晰、操作直觀

### Out of Scope (V1)
- 多輪對話功能
- 用戶身份認證
- 複雜的業務系統整合
- 生產級別的監控和日誌
- 多語言支援(僅繁中)

---

## 🛠 Technical Requirements

### System Requirements
- **開發環境**: Python 3.8+, 本地開發
- **部署方式**: Docker容器化, 本地運行
- **存儲需求**: < 1GB (模型 + 數據 + 索引)
- **計算需求**: 單台開發機器即可運行

### Performance Requirements
- **回應時間**: 95%的查詢在5秒內回應
- **併發處理**: 支援單用戶演示使用
- **準確率**: 核心測試問題準確率 ≥ 85%
- **可用性**: 演示期間100%運行穩定

### Security Requirements
- API Key安全存儲(.env文件)
- 不處理敏感個人信息
- 本地運行，無數據傳輸風險

---

## 📊 Success Criteria & Validation

### MVP Success Criteria
1. **功能完整性**: 三個核心測試問題都能得到準確回答
2. **技術深度**: 展示RAG檢索和生成的完整流程
3. **質量保證**: 條款引用準確，回答邏輯清晰
4. **演示效果**: 15分鐘內完整展示所有核心功能

### Validation Methods
- **自動化測試**: 單元測試覆蓋核心模組
- **功能驗證**: 三個測試問題的標準答案比對
- **專家評估**: 保險業務邏輯正確性檢查
- **技術評估**: 代碼質量和架構設計評估

---

## 🗓 Timeline & Milestones

### 3.5天開發里程碑

**Day 0.5 (今天)**: 項目初始化
- 環境搭建
- 項目結構創建
- 核心依賴安裝
- 基礎代碼框架

**Day 1**: 核心系統開發
- 條款處理系統
- 向量檢索系統
- 基礎測試數據

**Day 2**: RAG生成系統
- LLM整合
- 問答邏輯實現
- 來源引用系統

**Day 3**: 整合與測試
- 系統整合測試
- 三個測試問題驗證
- 演示界面完善

**Day 0.5 (面試當天)**: 最終準備
- 系統最終檢查
- 演示腳本確認

---

## 🔍 Risk Assessment

### High Risk Items
1. **時程風險**: 3.5天開發時程緊迫
   - **緩解**: 專注MVP核心功能，避免feature creep
2. **技術風險**: RAG系統調優複雜度
   - **緩解**: 使用成熟的預訓練模型，簡化架構
3. **演示風險**: 現場技術故障
   - **緩解**: 準備本地演示環境，預錄影備用

### Medium Risk Items  
1. **準確率風險**: 測試問題回答質量不達標
   - **緩解**: 人工調優提示詞，準備標準答案
2. **性能風險**: 回應時間過長
   - **緩解**: 本地部署，優化檢索參數

---

## 📚 Appendices

### A. Technical Stack
- **後端**: Python, FastAPI
- **向量檢索**: Faiss, Sentence-Transformers  
- **LLM**: OpenAI GPT-3.5-turbo
- **前端**: Streamlit
- **容器化**: Docker

### B. Test Questions
1. 什麼情況下可以申請旅遊延誤賠償？
2. 行李遺失後應該如何申請理賠？
3. 哪些原因屬於不可理賠範圍？

### C. References
- OpenAI API Documentation
- Faiss Vector Database Guide
- RAG Implementation Best Practices

---

## 📝 Document History
- **v4.0** (2025-01-03): 初始MVP版本，3.5天開發計劃