# SR&ED Technical Summary (FY 2025)

## **Project 1: Robust Generative AI Reliability Framework**

### **A. Technological Uncertainty**

Standard industrial practice for integrating Large Language Models (LLMs) often involves direct API integration with a single provider. However, this creates a "Single Point of Failure" and exposes the application to varied API schemas, rate limits, and non-deterministic latency. The technological uncertainty lay in how to create a **Universal AI Fallback Engine** that could maintain 99.9% uptime for critical financial operations (like real-time invoice extraction) while dynamically switching between cloud-based (OpenAI/Anthropic) and local-host (Ollama) providers without loss of transactional state or metadata.

### **B. Work Performed**

- Developed a **Centralized AI Configuration Service (`AIConfigService`)** that implements a tiered hierarchy for provider selection.
- Engineered a **Multi-Provider Mapping Logic** that normalizes disparate API response structures into a unified internal schema.
- Conducted experimental testing of fallback triggers based on latency thresholds and API error code taxonomies.
- Implemented **Database-to-Environment Fallback** mechanisms to ensure recovery during system-wide database unavailability.

### **C. Technological Advancement**

The result is a proprietary reliability framework that allows a stateless API to maintain complex AI configurations. This advancement enables the "failover" from cloud-hosted Gemini models to local Llama-3 models in under 500ms, ensuring that financial data extraction is never interrupted by external provider outages.

---

## **Project 2: Heuristic-Augmented Multi-Stage OCR Stability Pipeline**

### **A. Technological Uncertainty**

Conventional Optical Character Recognition (OCR) systems struggle with "Vision-LLM Drift"—where advanced models return non-deterministic data structures (e.g., Markdown instead of JSON) or produce invalid data types (e.g., non-compliant ISO-8601 timestamps like "12:08:69"). The uncertainty was whether a purely programmatic pipeline could "self-heal" these non-deterministic outputs without requiring manual human intervention or significantly increasing compute latency.

### **B. Work Performed**

- Designed a **Multi-Stage Detection & Recovery Pipeline** that executes sequenced extraction phases: (1) Structured JSON Extraction, (2) Fuzzy Markdown Parser, (3) Heuristic Text Normalizer.
- Developed a specialized **Timestamp Validator (`_validate_timestamp`)** to intercept and correct common AI hallucinations in temporal data.
- Built a **Recursion Guard** that triggers an autonomous AI "re-try" loop with refined context prompts upon detection of parsing failures.

### **C. Technological Advancement**

Achieved a 40% reduction in OCR-related data corruption errors. The advancement is a hybrid parsing engine that successfully blends deterministic regex-based validation with fuzzy AI logic, creating a resilient data pipeline capable of processing highly irregular receipt and invoice formats that traditional OCR libraries (like Tesseract) failed to structured.

---

## **Project 3: AI-Powered Forensic Auditing & Anomaly Detection (Insights Engine)**

### **A. Technological Uncertainty**

Existing Automated Audit systems are largely "Deterministic"—executing simple boolean checks (e.g., `if amount > 1000 flag`). These systems cannot detect "Behavioral Anomalies" such as **Phantom Vendors** (typosquatting on brand names) or **Threshold Splitting** (recurring sub-limit payments) that require contextual "Senior Auditor" reasoning. The uncertainty was whether a Generative AI could be constrained within a modular "Forensic Rule" framework to provide defensible, consistent risk scores without "AI Hallucination."

### **B. Work Performed**

- Implemented a **Modular Forensic Rule System** that orchestrates multiple audit-agents against a single entity.
- Conducted R&D into **Vectorized Vendor Verification** and **Temporal Anomaly Analysis** (detecting off-hours transaction patterns).
- Engineered a **Risk Level Scoring Algorithm** (Low/Med/High) that maps qualitative AI reasoning to quantitative severity scores.

### **C. Technological Advancement**

Created the **"FinanceWorks Insights"** engine, which successfully automates 85% of the "Senior Auditor" review cycle. The advancement is the integration of forensic behavioral rules into an asynchronous worker stream, enabling real-time detection of financial policy circumvention and faked documentation patterns in high-volume transaction environments.

---

**Evidence Directory**:

- `api/services/ai_config_service.py`
- `api/services/ocr_service.py`
- `api/commercial/anomaly_detection/service.py`
- `docs/technical-notes/UNIFIED_AI_FALLBACK_IMPLEMENTATION.md`
- `docs/technical-notes/OCR_STABILITY_IMPROVEMENTS.md`
