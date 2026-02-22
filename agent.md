# Agent Runbook - Veterinary Chat Assistance

- Purpose & Scope: Provide safe, retrieval-grounded veterinary guidance for pet owners; assist with symptom severity and routing to care; maintain conversational continuity with hybrid memory.

- System Objectives: Safety-first guidance; evidence-backed responses; modular and extensible architecture; controlled AI behavior; transparent citations.

- Core Modules & Responsibilities: Chat Assistant Core orchestrates preprocessing, intent detection, classification, routing, memory, and response composition; UI is a separate layer that only renders outputs and collects input.

- Routing & Decision Logic: Rule-based intent triggers first, then embedding similarity, then LLM fallback; route to RAG for medical queries, Question Engine for missing info, Map Locator for clinic search, Emergency Override for severe symptoms, FAQ/Fallback for general info.

- Intent Confidence Thresholds: confidence >= 0.82 route directly; 0.65–0.81 validate with context; < 0.65 use LLM classification fallback.

- Retrieval & Data Sources: Chroma vector DB + BAAI BGE embeddings; query embedding -> similarity search -> metadata filtering -> top-K retrieval; sources include vet guidelines, symptom references, vaccination schedules, FAQs, clinic datasets.

- Retrieval Confidence Matrix: top_score > 0.82 use KB; 0.70–0.82 ask clarification; < 0.70 trigger live search.

- Safety & Guardrails: Do not provide medication dosages or definitive diagnoses; always highlight emergency signs and recommend vet consultation when appropriate; emergency override can interrupt pipeline at any stage.

- LLM Invocation: Temperature 0.2, max tokens 512, top_p 0.9, stop sequences; retry with exponential backoff up to 3 attempts.

- Structured Output Validation: `VetResponse` schema (answer, possible_causes, warning_signs, vet_visit_guidance, care_tips, citations); regenerate once on failure, then fallback template.

- Response Structure & Citations: Responses follow direct answer, possible causes, warning signs, when to visit vet, care tips; include citations with structured metadata and do not fabricate sources.

- Emergency Override Flow: Severity scoring formula includes keyword weights + duration + combination bonus; threshold score 8; immediate override for breathing difficulty, seizure, collapse, poisoning.

- Live Search Control: Trigger when top_score < 0.70, user requests latest guidance, or regulatory/outbreak topics; allow official/gov/vet bodies; reject blogs/forums/social.
- API Layer: Backend exposes `POST /chat`, `POST /location`, `GET /health`; validates requests, handles errors, logs key events.

- Memory Model: Session memory stores conversation history, last intent, severity flag; structured memory stores pet profile; retrieval memory caches recent KB context and semantic matches.

- Session Expiration: Auto-clear session data after 30 minutes of inactivity.
- Error Handling: Vector DB unavailable -> fallback guidance; LLM timeout -> retry 3x then fallback; live search failure -> safe guidance; location unavailable -> ask for city.

- Caching: Embedding, retrieval, response, and LLM output caches; TTL 1 hour.

- Concurrency & Scaling: Stateless API layer, pooled DB connections, async LLM calls, horizontal scaling supported.

- Security & Privacy: No permanent medical data storage; anonymized logs; location permission required; API keys via env vars.

- Observability: Log intent, emergency score, retrieval scores, LLM latency, token usage, and errors; track response time and live search frequency.

- Prompt Governance: Master system prompt + per-flow prompts; version_id/owner/last_updated required; regression tests for prompt updates; injection protection rules enforced.

- Citation System: Extended metadata (document_id, chunk_id, source_title, organization, year, section_reference, url, evidence_level, last_updated); include only similarity_score >= 0.75; dedup by document_id; validate citations against retrieved metadata; log citation audit trail.

- Non-Functional Requirements: Response latency < 3 seconds; retrieval latency < 500 ms; reliability via emergency priority routing and graceful fallbacks; modular replaceable LLM provider.

- Testing Focus Areas: Intent routing accuracy; emergency detection reliability; hallucination prevention; response format and citation presence.

# Plan Log

## 2026-02-21 17:02 - Add Plan Log to agent.md
- Scope: Add a Plan Log section to track plans over time.
- Format: Append entries (do not replace).
- Entry Detail: Concise summary (5-10 bullets).
- Timestamp: Date + time to the minute.
- Tests: Verify Plan Log exists and entry format is correct.
- Assumptions: Use local time for timestamps; append future plans.

## 2026-02-21 17:18 - Build Backend Chatbot MVP (Library)
- Scope: Backend-only library with ingestion, routing, RAG, and live search.
- Stack: Python library, Gemini LLM, BAAI BGE embeddings, ChromaDB.
- Live Search: Google Custom Search API with allowlist from domain.txt.
- Routing: Emergency, clinic search, missing info, medical query.
- Safety: No dosages or definitive diagnoses; emergency warnings.
- Tests: Basic emergency scoring test.

## 2026-02-22 12:54 - Align agent.md with rag_architecture.md
- Scope: Expand runbook to match production-grade RAG spec.
- Added: API endpoints, intent/retrieval thresholds, emergency threshold 8.
- Added: LLM config and retry policy.
- Added: Structured output validation schema.
- Added: Error handling and caching strategies.
- Added: Security, privacy, observability, scaling.
- Added: Prompt governance and citation system requirements.

## 2026-02-22 15:40 - Implement Hybrid Partial Response Mode
- Scope: Apply Architecture Update - 1 for HYBRID_PARTIAL routing.
- Added: pet_care intent support (exemplars, rule-based, LLM mapping).
- Added: hybrid eligibility gate for dosage/toxic/respiratory/emergency exclusions.
- Added: response_mode routing for full RAG, hybrid partial, clarification, live search.
- Added: live search override for "latest/recent" queries.
- Updated: master and question prompts for partial guidance before clarifications.
- Updated: question engine to parse JSON guidance + questions.
- Tests: Added hybrid partial, live search override, and hybrid block tests; all tests passing.

## 2026-02-22 16:18 - Implement Educational Style + Context-Aware Dosage
- Scope: Apply Architecture Updates 2 and 3 (educational vs clinical, context-aware dosing).
- Added: query_context classification (ACADEMIC/GENERAL/CLINICAL_SPECIFIC).
- Added: response_style routing with educational prompt for conceptual informational queries.
- Added: educational prompt and context-aware dosage guidance rules.
- Updated: rag and fallback prompts with query_context handling.
- Updated: LLM client to support per-call generation overrides.
- Tests: Added educational response style test; full suite passing.

## 2026-02-22 22:58 - Streamlit UI Integration (Spec v1.0)
- Scope: Implement Streamlit UI per ui_architecture_spec.md.
- Added: ui/app.py with full UI layout, state handling, and API integration.
- Added: UI state rendering for emergency, clinical, educational, hybrid, clarification, live search.
- Added: Sidebar pet profile, file upload placeholder, session controls.
- Added: Top nav status indicator and disclaimer panel.
- Updated: API response includes response_mode/style/query_context/live_search_flag.
- Updated: requirements.txt with streamlit dependency.
