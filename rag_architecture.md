# Veterinary Chat Assistance System

# Production-Grade Core Architecture Documentation (Technical Specification v2)

This document defines the complete system-level technical architecture, execution logic, runtime behavior, orchestration rules, and production specifications for the Veterinary Chat Assistance chatbot.

This version expands the architecture into an implementation-ready blueprint suitable for backend engineers, AI engineers, and system architects.

---

# 1. System Scope

## 1.1 Functional Scope
The system provides:
- Veterinary symptom guidance
- Emergency detection & escalation
- Vaccination and preventive care information
- Clinic locator via Google Maps redirect
- Retrieval-grounded responses
- Controlled live search augmentation

## 1.2 Out of Scope
- Ad-hoc RAG document ingestion
- UI styling and visual design implementation
- Appointment booking integration (future)

---

# 2. High-Level Architecture Overview

```mermaid
flowchart TD

    User --> UI[Streamlit UI Layer]
    UI --> API[Backend Application Layer]

    API --> ORCH[Chat Assistant Core]

    ORCH --> INTENT[Hybrid Intent Engine]
    ORCH --> ROUTER[Deterministic Routing Engine]

    ROUTER --> RAG[RAG Retrieval Pipeline]
    ROUTER --> QENG[Question Engine]
    ROUTER --> MAP[Map Locator Service]
    ROUTER --> EMERG[Emergency Override Service]
    ROUTER --> LIVE[Live Search Module]

    RAG --> VDB[(ChromaDB)]
    VDB --> EMB[BAAI BGE Embeddings]

    RAG --> LLM[Gemini LLM Layer]
    QENG --> LLM
    LIVE --> LLM

    LLM --> RESP[Structured Response Composer]
    RESP --> VALID[Output Validator]
    VALID --> CITE[Citation Generator]
    CITE --> UI

    ORCH --> MEM[(Hybrid Memory Layer)]

```

---

# 3. Layer-by-Layer Technical Specification

---

# 3.1 Presentation Layer (UI - Separate Implementation)

⚠️ IMPORTANT:
The UI design, layout, animations, styling, and user interaction visuals are NOT part of this architecture.

The UI must be built separately and consume backend API responses.

### UI Responsibilities
- Send user message to backend
- Render structured response
- Display citations
- Display Google Maps redirect links
- Maintain visual chat history

### UI Restrictions
- Must NOT modify backend state
- Must NOT perform AI inference
- Must NOT store medical decisions

---

# 3.2 Backend Application Layer

This layer exposes endpoints:

POST /chat
POST /location
GET /health

Handles:
- Session creation
- Request validation
- Error handling
- Logging

---

# 3.3 Chat Assistant Core (Orchestration Engine)

## Responsibilities
- Preprocessing
- Intent detection
- Context injection
- Routing decision
- Memory update

## Deterministic Routing Pseudocode

```
def handle_message(message, session_state):
    preprocessed = preprocess(message)
    intent, confidence = detect_intent(preprocessed)

    emergency_score = compute_emergency_score(preprocessed)

    if emergency_score >= EMERGENCY_THRESHOLD:
        return emergency_flow(preprocessed)

    if intent == "clinic_locator":
        return map_flow(preprocessed)

    if intent == "symptom_inquiry":
        return rag_flow(preprocessed)

    if intent == "missing_info":
        return clarification_flow(preprocessed)

    return fallback_flow(preprocessed)
```

---

# 3.4 Hybrid Intent Detection Engine

## Detection Order
1. Rule-based pattern match
2. Embedding similarity classification
3. LLM classification fallback

## Confidence Calculation

Embedding similarity scoring:

```
confidence = cosine_similarity(query_vector, intent_centroid)
```

### Thresholds

- confidence >= 0.82 → High
- 0.65–0.81 → Medium
- < 0.65 → Low

Routing Strategy:

- High → route directly
- Medium → validate with context
- Low → LLM classification

---

# 3.5 Retrieval Confidence & Live Search Logic

## Retrieval Scoring

For RAG:

```
top_score = max(similarity_scores)
avg_top_k = mean(top_k_scores)
```

Decision Matrix:

| top_score | Action |
|------------|--------|
| > 0.82 | Use KB |
| 0.70–0.82 | Ask clarification |
| < 0.70 | Trigger live search |

If live search fails:
- Provide general safe fallback guidance
- Recommend veterinary consultation

---

# 3.6 RAG Retrieval Pipeline

1. Embed query using BAAI BGE
2. Query ChromaDB
3. Filter by metadata (species, severity)
4. Select top_k = 5
5. Pass context to LLM

### Metadata Schema

```
{
  species: string,
  category: string,
  severity: string,
  emergency_flag: boolean,
  source: string,
  year: int
}
```

---

# 3.7 LLM Invocation Architecture

## LLM Call Types

1. Intent fallback classification
2. RAG answer generation
3. Clarification question generation
4. Emergency response formatting
5. Live search summarization

## Configuration

- Temperature: 0.2 (deterministic)
- Max tokens: 512
- Top_p: 0.9
- Stop sequences enforced

## Rate Limit Handling

- Retry with exponential backoff (max 3 attempts)
- Fallback to cached response if available

---

# 3.8 Structured Output Validation

All LLM outputs must conform to schema:

```
class VetResponse(BaseModel):
    answer: str
    possible_causes: str
    warning_signs: str
    vet_visit_guidance: str
    care_tips: Optional[str]
    citations: List[str]
```

Validation failure → regenerate once → fallback template

---

# 3.9 Emergency Detection Engine

## Severity Score Formula

```
score = sum(keyword_weight) + duration_weight + combination_bonus
```

Threshold = 8

High-risk keywords weighted 3–5 points.

Immediate override if:
- breathing difficulty
- seizure
- collapse
- poisoning

---

# 3.10 Live Search Module

## Trigger Conditions
- top_score < 0.70
- User explicitly requests latest guidance
- Regulatory or outbreak topic

## Source Filtering
Allow only:
- Official veterinary bodies
- Government advisories
- Peer-reviewed sources

Reject:
- Blogs
- Forums
- Social media

---

# 3.11 Hybrid Memory Architecture

## Session Memory
- conversation_history
- last_intent
- emergency_flag

## Structured Memory
- pet_species
- age
- medical_conditions

## Retrieval Memory
- last_retrieved_chunks
- last_similarity_scores

Memory stored per session_id.

Session expiration: 30 minutes inactivity.

---

# 3.12 Error Handling Model

| Failure | Action |
|----------|--------|
| Vector DB unavailable | fallback general guidance |
| LLM timeout | retry 3x then fallback |
| Live search failure | fallback safe guidance |
| Location unavailable | ask user to enter city |

All errors logged.

---

# 3.13 Caching Strategy

- Embedding cache (query hash → vector)
- Retrieval cache (query hash → top_k results)
- Response cache (normalized query → response)
- LLM output cache (temperature=0.2 only)

TTL = 1 hour.

---

# 3.14 Concurrency & Scaling

- Each session isolated via session_id
- Stateless API layer
- ChromaDB connection pooled
- Async LLM calls
- Horizontal scaling supported

---

# 3.15 Security & Privacy

- No permanent storage of medical data
- Session data auto-cleared
- API keys stored in environment variables
- Location permission required
- Logs anonymized

---

# 3.16 Observability & Monitoring

Logs capture:
- Intent classification result
- Emergency score
- Retrieval scores
- LLM latency
- Token usage
- Errors

Metrics:
- Average response time
- Emergency detection rate
- Live search frequency

---

# 3.17 Full End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant Core
    participant Intent
    participant Router
    participant RAG
    participant LLM
    participant Validator

    User->>UI: Message
    UI->>API: POST /chat
    API->>Core: handle_message
    Core->>Intent: detect_intent
    Intent-->>Core: intent + confidence
    Core->>Router: routing decision
    Router-->>RAG: if medical
    RAG->>LLM: generate answer
    LLM->>Validator: structured output
    Validator->>API: validated response
    API->>UI: JSON response
    UI->>User: Rendered output
```

---

# 3.18 Non-Functional Requirements

Performance:
- P95 latency < 3s

Reliability:
- 99% uptime

Safety:
- 0 dosage hallucinations

Scalability:
- 100+ concurrent sessions

---

# 4. Final Architecture Guarantees

This system ensures:

✔ Deterministic routing  
✔ Controlled live search  
✔ Retrieval-grounded answers  
✔ Emergency-first override  
✔ Structured validated outputs  
✔ Modular replaceable components  
✔ Clear separation of UI and backend  

---

---

# 5. Prompt Engineering & Structured LLM Specifications

This section defines the exact prompt templates, structural constraints, and orchestration logic used for all LLM interactions. These prompts are mandatory and version-controlled.

All prompts inherit constraints from the Master System Prompt.

---

# 5.1 Master System Prompt (Global Behavioral Contract)

## Purpose
Defines tone, safety guardrails, and response structure.

```
You are a veterinary assistance AI.

OBJECTIVES:
- Provide safe, clear, evidence-based guidance.
- Do not provide medication dosages.
- Do not make definitive diagnoses.
- Always highlight emergency warning signs.
- Encourage veterinary consultation when appropriate.

RESPONSE STYLE:
- Calm and reassuring.
- Simple language.
- Short paragraphs.
- Structured output only.

If information is missing, ask clarifying questions.
If uncertain, say so.
```

Temperature: 0.2  
Max Tokens: 512  

---

# 5.2 RAG Prompt (Knowledge-Based Response Template)

## Used When
Vector retrieval confidence ≥ threshold.

## Inputs
- user_question
- retrieved_context
- pet_type
- conversation_context

## Template

```
Use ONLY the provided veterinary knowledge.

USER QUESTION:
{user_question}

PET TYPE:
{pet_type}

RETRIEVED CONTEXT:
{retrieved_context}

CONVERSATION CONTEXT:
{conversation_context}

INSTRUCTIONS:
- Base your answer strictly on retrieved context.
- Do not invent facts.
- If context insufficient, say so.

FORMAT:

Answer:

Possible Causes:

Warning Signs:

When to See a Vet:

Care Tips:
```

---

# 5.3 Question Engine Prompt (Clarification Flow)

## Used When
Intent confidence medium OR missing required fields.

## Inputs
- user_input
- missing_fields
- suspected_intent

## Template

```
The user's message lacks required details.

USER MESSAGE:
{user_input}

MISSING INFORMATION:
{missing_fields}

SUSPECTED INTENT:
{suspected_intent}

Ask 2–4 essential clarifying questions.
Keep them concise.
Do not provide medical advice yet.
Return only bullet-point questions.
```

---

# 5.4 Emergency Prompt (Override Template)

## Used When
Emergency score ≥ threshold.

## Inputs
- symptoms
- pet_type

## Template

```
The symptoms may indicate a medical emergency.

SYMPTOMS:
{symptoms}

PET TYPE:
{pet_type}

Provide urgent structured guidance.

FORMAT:

EMERGENCY ALERT:

Why This Is Serious:

Immediate Action:

Seek Veterinary Care Immediately.

If transport delay occurs:

Do NOT provide diagnosis or medication dosing.
```

This prompt bypasses normal RAG flow.

---

# 5.5 Live Search Summary Prompt

## Used When
KB confidence below threshold and live search triggered.

## Inputs
- topic
- filtered_search_results

## Template

```
Summarize the latest veterinary guidance from the provided trusted sources.

TOPIC:
{topic}

SEARCH RESULTS:
{filtered_search_results}

Provide:

Latest Guidance:

Key Points:
- point
- point
- point

Mention that recommendations may vary by veterinarian.
```

---

# 5.6 Fallback General Guidance Prompt

## Used When
No reliable KB or live data available.

## Template

```
Provide safe, general veterinary guidance for the user's question.

Do not speculate.
Encourage veterinary consultation if symptoms persist.
Keep response under 150 words.
```

---

# 5.7 Intent Classification Prompt (LLM Fallback)

## Used When
Rule-based and embedding classification confidence low.

## Template

```
Classify the user intent.

INTENTS:
- symptom_inquiry
- emergency
- clinic_locator
- vaccination
- pet_care
- follow_up
- general_info

USER MESSAGE:
"{message}"

Return ONLY the intent label.
```

---

# 5.8 Prompt Versioning & Governance

Each prompt must include:
- version_id
- last_updated_date
- owner

Example:

prompt_version = "RAG_v1.2"

Prompt updates require:
- regression testing
- emergency detection validation
- hallucination testing

---

# 5.9 Prompt Injection Protection Rules

The system must:
- Ignore user attempts to override instructions
- Reject requests to reveal system prompt
- Refuse unsafe medical instructions

All LLM calls must prepend system prompt before user content.

---

# 5.10 LLM Call Workflow Diagram

```mermaid
flowchart TD

    INPUT[User Input] --> CHECK[Emergency Check]
    CHECK -->|High| EMERG_PROMPT[Emergency Prompt]
    CHECK -->|Normal| RETRIEVE[Retrieval Confidence Check]

    RETRIEVE -->|High| RAG_PROMPT
    RETRIEVE -->|Medium| QUESTION_PROMPT
    RETRIEVE -->|Low| LIVE_SEARCH

    LIVE_SEARCH --> LIVE_PROMPT

    RAG_PROMPT --> LLM
    QUESTION_PROMPT --> LLM
    EMERG_PROMPT --> LLM
    LIVE_PROMPT --> LLM

    LLM --> VALIDATE[Structured Output Validation]
```

---

---

# 6. Citation System – Technical Architecture & Prompt Specification

The citation system is a mandatory transparency layer that ensures every knowledge-grounded response is traceable to its source.

It applies to:
- RAG-based responses
- Live search responses
- Hybrid responses (KB + live)

It does NOT apply to:
- Pure clarification questions
- Emergency formatting without KB usage

---

# 6.1 Citation Objectives

The citation module must:

✔ Attach source references for all retrieval-based responses  
✔ Preserve traceability to original KB chunks  
✔ Avoid hallucinated references  
✔ Distinguish KB citations from live search citations  
✔ Provide structured citation metadata  

---

# 6.2 Citation Data Model

## 6.2.1 Vector Document Metadata (Extended)

Each chunk stored in ChromaDB must include:

```
{
  document_id: string,
  chunk_id: string,
  source_title: string,
  organization: string,
  publication_year: int,
  section_reference: string,
  url: optional string,
  evidence_level: string,
  last_updated: date
}
```

This ensures citation traceability.

---

# 6.3 Citation Generation Workflow

```mermaid
flowchart TD

    RETRIEVAL[Top-K Retrieved Chunks]
    RETRIEVAL --> FILTER[Remove Low Score Chunks]
    FILTER --> UNIQUE[Deduplicate by document_id]
    UNIQUE --> FORMAT[Format Citation Objects]
    FORMAT --> ATTACH[Attach to Response JSON]
```

---

# 6.4 Citation Confidence Threshold

Only chunks meeting:

```
similarity_score >= 0.75
```

are eligible for citation.

If no chunk exceeds threshold:
- No citation attached
- Response labeled as general guidance

---

# 6.5 Citation JSON Output Contract

All RAG responses must return:

```
{
  answer: string,
  possible_causes: string,
  warning_signs: string,
  vet_visit_guidance: string,
  care_tips: string,
  citations: [
    {
      source_title: string,
      organization: string,
      publication_year: int,
      section_reference: string,
      url: optional string
    }
  ]
}
```

UI renders citation list separately.

---

# 6.6 RAG Citation Prompt Addendum

The RAG prompt must instruct the LLM:

```
At the end of your response, include citation references ONLY from the retrieved context.
Do not fabricate sources.
Use the metadata fields exactly as provided.
If context insufficient, do not create citations.
```

The LLM must not invent new citation entries.

---

# 6.7 Live Search Citation Prompt

## Inputs
- filtered_search_results (structured metadata)

## Template

```
Summarize the provided trusted veterinary sources.

At the end, list citations in the format:

Sources:
- Source Title | Organization | Year

Do not fabricate sources.
Use only provided metadata.
```

---

# 6.8 Citation Deduplication Rules

If multiple chunks originate from same document:

- Only one citation entry allowed
- Merge section references

Example:

"Section 3.1, 4.2"

---

# 6.9 Hallucination Prevention Rules (Citation Layer)

The system must:

- Reject any citation not present in retrieved metadata
- Validate citation list against retrieved document_ids
- Remove citations if mismatch detected
- Regenerate response once if hallucination detected

---

# 6.10 Citation Logging & Auditing

For each response log:

- retrieved document_ids
- similarity scores
- attached citation list
- live search source domains

Used for:
- Audit trail
- Medical reliability verification
- Regulatory compliance

---

# 6.11 Citation Failure Handling

| Failure | Action |
|----------|--------|
| No eligible chunks | Return response without citations |
| Metadata missing | Exclude chunk |
| LLM fabricates citation | Regenerate response |

---

# 6.12 Citation UI Separation Rule

Backend returns citations in structured JSON.
UI responsibility:
- Render citation panel
- Display expandable source list
- Provide clickable URLs if available

UI must NOT:
- Modify citation content
- Add or remove references

---

# 6.13 End-to-End Citation Flow Diagram

```mermaid
sequenceDiagram
    participant RAG
    participant Metadata
    participant LLM
    participant Validator
    participant API
    participant UI

    RAG->>Metadata: Retrieve chunks + metadata
    Metadata->>LLM: Inject context + metadata
    LLM->>Validator: Structured response + citations
    Validator->>API: Verified citation list
    API->>UI: JSON with citations
    UI->>User: Displayed citation panel
```

---

# 6.14 Citation Integrity Guarantees

The citation system guarantees:

✔ Every citation is traceable to stored KB metadata  
✔ No hallucinated references  
✔ Confidence-based inclusion  
✔ Structured JSON validation  
✔ Audit-ready logging  

---

# 7. Final Guarantee

With prompt structuring integrated, the system now ensures:

✔ Deterministic routing logic  
✔ Strict prompt governance  
✔ Emergency-first override handling  
✔ Retrieval-grounded answers only  
✔ Structured validated outputs  
✔ Injection-resistant prompt control  
✔ Full production-ready AI orchestration  

---

END OF PRODUCTION ARCHITECTURE DOCUMENT

---------------------------------------

## Architecture Update - 1

# 8. Hybrid Partial Response Mode – Architectural Amendment

This section introduces a controlled Hybrid Partial Response Mode to resolve over-restrictive clarification behavior for general informational queries (e.g., vaccination schedules) while preserving medical safety.

This amendment modifies behavior in the following layers:
- 3.3 Chat Assistant Core (Routing Logic)
- 3.5 Retrieval Confidence & Live Search Logic
- 5.1 Master System Prompt
- 5.3 Question Engine Prompt
- 5.10 LLM Call Workflow Diagram

No other architectural components are altered.

---

## 8.1 Amendment to 3.5 Retrieval Confidence & Live Search Logic

### Updated Decision Matrix

| top_score | Intent Type | Action |
|------------|-------------|--------|
| > 0.82 | Any | FULL_RAG |
| 0.70–0.82 | vaccination / pet_care / general_info | HYBRID_PARTIAL |
| 0.70–0.82 | symptom_inquiry | CLARIFICATION_REQUIRED |
| < 0.70 | Any | LIVE_SEARCH |

---

## 8.2 Amendment to 3.3 Chat Assistant Core (Routing Engine)

```
def determine_response_mode(intent, retrieval_score, emergency_score):

    if emergency_score >= EMERGENCY_THRESHOLD:
        return "EMERGENCY"

    if retrieval_score > 0.82:
        return "FULL_RAG"

    if 0.70 <= retrieval_score <= 0.82:
        if intent in ["vaccination", "pet_care", "general_info"]:
            return "HYBRID_PARTIAL"
        if intent == "symptom_inquiry":
            return "CLARIFICATION_REQUIRED"

    return "LIVE_SEARCH"
```

Routing Replacement:

```
response_mode = determine_response_mode(intent, retrieval_score, emergency_score)

if response_mode == "FULL_RAG":
    return rag_flow(preprocessed)

if response_mode == "HYBRID_PARTIAL":
    answer = rag_flow(preprocessed)
    questions = clarification_flow(preprocessed)
    return merge(answer, questions)

if response_mode == "CLARIFICATION_REQUIRED":
    return clarification_flow(preprocessed)

if response_mode == "LIVE_SEARCH":
    return live_search_flow(preprocessed)
```

---

## 8.3 Amendment to 5.1 Master System Prompt

Replace:

"If information is missing, ask clarifying questions."

With:

"If partial information is available, provide safe general guidance first.
Ask clarifying questions only when missing details significantly affect safety or accuracy."

---

## 8.4 Amendment to 5.3 Question Engine Prompt

Replace:

"Do not provide medical advice yet."

With:

"Only avoid providing guidance if missing information prevents safe advice.
If safe general guidance is possible, provide it before asking clarifications."

---

## 8.5 Amendment to 5.10 LLM Call Workflow Diagram

```mermaid
flowchart TD

    INPUT[User Input] --> CHECK[Emergency Check]
    CHECK -->|High| EMERG_PROMPT[Emergency Prompt]
    CHECK -->|Normal| RETRIEVE[Retrieval Confidence Check]

    RETRIEVE -->|High| RAG_PROMPT
    RETRIEVE -->|Medium + Informational| HYBRID_FLOW
    RETRIEVE -->|Medium + Symptom| QUESTION_PROMPT
    RETRIEVE -->|Low| LIVE_SEARCH

    HYBRID_FLOW --> RAG_PROMPT
    HYBRID_FLOW --> QUESTION_PROMPT

    RAG_PROMPT --> LLM
    QUESTION_PROMPT --> LLM
    EMERG_PROMPT --> LLM
    LIVE_SEARCH --> LIVE_PROMPT
    LIVE_PROMPT --> LLM

    LLM --> VALIDATE[Structured Output Validation]
```

---

## 8.6 Safety Preservation Rule

HYBRID_PARTIAL mode is prohibited when:
- emergency_score >= threshold
- dosage-related queries
- toxic exposure queries
- seizure / collapse / respiratory distress indicators

---

## 8.7 Expected Behavioral Outcome

Example Query:
"3 month old cat vaccination schedule"

System Output:
- Explanation of vaccination
- General kitten vaccination schedule
- Follow-up questions about prior doses
- Indoor/outdoor status clarification

---

END OF ARCHITECTURAL UPDATE - 1

---
# 8. Hybrid Partial Response Mode – Architectural Amendment (v2.1)

This section introduces a controlled Hybrid Partial Response Mode to resolve over-restrictive clarification behavior for general informational queries (e.g., vaccination schedules) while preserving medical safety.

This amendment modifies behavior in the following layers:
- 3.3 Chat Assistant Core (Routing Logic)
- 3.5 Retrieval Confidence & Live Search Logic
- 5.1 Master System Prompt
- 5.3 Question Engine Prompt
- 5.10 LLM Call Workflow Diagram

No other architectural components are altered.

---

## 8.1 Amendment to 3.5 Retrieval Confidence & Live Search Logic

### Updated Decision Matrix

| top_score | Intent Type | Action |
|------------|-------------|--------|
| > 0.82 | Any | FULL_RAG |
| 0.70–0.82 | vaccination / pet_care / general_info | HYBRID_PARTIAL |
| 0.70–0.82 | symptom_inquiry | CLARIFICATION_REQUIRED |
| < 0.70 | Any | LIVE_SEARCH |

---

## 8.2 Amendment to 3.3 Chat Assistant Core (Routing Engine)

```
def determine_response_mode(intent, retrieval_score, emergency_score):

    if emergency_score >= EMERGENCY_THRESHOLD:
        return "EMERGENCY"

    if retrieval_score > 0.82:
        return "FULL_RAG"

    if 0.70 <= retrieval_score <= 0.82:
        if intent in ["vaccination", "pet_care", "general_info"]:
            return "HYBRID_PARTIAL"
        if intent == "symptom_inquiry":
            return "CLARIFICATION_REQUIRED"

    return "LIVE_SEARCH"
```

Routing Replacement:

```
response_mode = determine_response_mode(intent, retrieval_score, emergency_score)

if response_mode == "FULL_RAG":
    return rag_flow(preprocessed)

if response_mode == "HYBRID_PARTIAL":
    answer = rag_flow(preprocessed)
    questions = clarification_flow(preprocessed)
    return merge(answer, questions)

if response_mode == "CLARIFICATION_REQUIRED":
    return clarification_flow(preprocessed)

if response_mode == "LIVE_SEARCH":
    return live_search_flow(preprocessed)
```

---

## 8.3 Amendment to 5.1 Master System Prompt

Replace:

"If information is missing, ask clarifying questions."

With:

"If partial information is available, provide safe general guidance first.
Ask clarifying questions only when missing details significantly affect safety or accuracy."

---

## 8.4 Amendment to 5.3 Question Engine Prompt

Replace:

"Do not provide medical advice yet."

With:

"Only avoid providing guidance if missing information prevents safe advice.
If safe general guidance is possible, provide it before asking clarifications."

---

## 8.5 Amendment to 5.10 LLM Call Workflow Diagram

```mermaid
flowchart TD

    INPUT[User Input] --> CHECK[Emergency Check]
    CHECK -->|High| EMERG_PROMPT[Emergency Prompt]
    CHECK -->|Normal| RETRIEVE[Retrieval Confidence Check]

    RETRIEVE -->|High| RAG_PROMPT
    RETRIEVE -->|Medium + Informational| HYBRID_FLOW
    RETRIEVE -->|Medium + Symptom| QUESTION_PROMPT
    RETRIEVE -->|Low| LIVE_SEARCH

    HYBRID_FLOW --> RAG_PROMPT
    HYBRID_FLOW --> QUESTION_PROMPT

    RAG_PROMPT --> LLM
    QUESTION_PROMPT --> LLM
    EMERG_PROMPT --> LLM
    LIVE_SEARCH --> LIVE_PROMPT
    LIVE_PROMPT --> LLM

    LLM --> VALIDATE[Structured Output Validation]
```

---

## 8.6 Safety Preservation Rule

HYBRID_PARTIAL mode is prohibited when:
- emergency_score >= threshold
- dosage-related queries
- toxic exposure queries
- seizure / collapse / respiratory distress indicators

---

## 8.7 Expected Behavioral Outcome

Example Query:
"3 month old cat vaccination schedule"

System Output:
- Explanation of vaccination
- General kitten vaccination schedule
- Follow-up questions about prior doses
- Indoor/outdoor status clarification

---

END OF ARCHITECTURAL AMENDMENT v2.1

---

# 9. Corrective Amendment – Hybrid Partial Response (Append-Only Update)

This section appends precise behavioral modifications without rewriting any previously documented layer content.

The following layers are amended:
- 3.3 Chat Assistant Core
- 3.5 Retrieval Confidence & Live Search Logic
- 5.1 Master System Prompt
- 5.3 Question Engine Prompt
- 5.10 LLM Call Workflow Diagram

No structural relocation or deletion of existing documentation is performed.

---

## 9.1 Modification to Layer 3.5 (Retrieval Confidence Logic)

Replace the existing medium-confidence action:

"0.70–0.82 → Ask clarification"

With conditional routing:

If 0.70–0.82 AND intent in [vaccination, pet_care, general_info]
→ HYBRID_PARTIAL

If 0.70–0.82 AND intent == symptom_inquiry
→ CLARIFICATION_REQUIRED

All other thresholds remain unchanged.

---

## 9.2 Modification to Layer 3.3 (Routing Logic)

Introduce response_mode evaluation before clarification routing.

Add logical evaluation:

- FULL_RAG
- HYBRID_PARTIAL
- CLARIFICATION_REQUIRED
- LIVE_SEARCH

HYBRID_PARTIAL must:
1. Execute rag_flow()
2. Execute clarification question generation
3. Merge outputs
4. Return structured answer + follow_up_questions

Remove any direct unconditional routing to clarification_flow based solely on medium confidence.

---

## 9.3 Modification to Layer 5.1 (Master System Prompt)

Replace:
"If information is missing, ask clarifying questions."

With:
"If partial information is available, provide safe general guidance first. Ask clarifying questions only when missing details significantly affect safety or accuracy."

---

## 9.4 Modification to Layer 5.3 (Question Engine Prompt)

Replace:
"Do not provide medical advice yet."

With:
"Only avoid providing guidance if missing information prevents safe advice. If safe general guidance is possible, provide it before asking clarifications."

---

## 9.5 Modification to Layer 5.10 (LLM Workflow)

Update medium-confidence branch to:

Medium + Informational Intent → HYBRID_FLOW
Medium + Symptom Intent → QUESTION_PROMPT

HYBRID_FLOW executes:
- RAG_PROMPT
- QUESTION_PROMPT
- Merge before validation

---

## 9.6 Safety Constraint

HYBRID_PARTIAL is prohibited when:
- emergency_score ≥ threshold
- dosage-related queries
- toxic exposure
- respiratory distress, seizure, collapse

Emergency and high-risk overrides remain unchanged.

---

END OF CORRECTIVE APPEND UPDATE



---

# Architecture Update - 2

# 9. Response Style Switching – Educational vs Clinical Mode

This amendment introduces a Response Style Layer that separates:

- Clinical Structured Responses  
- Educational Natural Responses  

This ensures general conceptual queries are answered in a user-friendly conversational format, while sensitive or case-specific queries remain strictly structured and retrieval-grounded.

This amendment modifies behavior in the following layers:

- 3.3 Chat Assistant Core (Routing Logic)
- 3.7 LLM Invocation Architecture
- 3.8 Structured Output Validation
- 5.1 Master System Prompt
- 5.10 LLM Call Workflow Diagram

No other architectural components are altered.

---

## 9.1 New Concept: Response Style Classification

Introduce a new independent decision:

```
response_style = determine_response_style(intent, query, emergency_score)
```

This operates independently from `response_mode`.

---

## 9.2 Educational Style Trigger Conditions

Educational style MUST activate when:

- intent in ["vaccination", "pet_care", "general_info"]
- emergency_score < threshold
- NOT dosage-related
- NOT toxic exposure related
- NOT symptom-specific
- Query is conceptual (starts with: why, what, how, explain, tell me about)

Example conceptual starters:

```
("why", "what", "how", "explain", "tell me about")
```

If conditions satisfied:

```
return "EDUCATIONAL"
```

Else:

```
return "CLINICAL"
```

---

## 9.3 Modification to Layer 3.3 (Chat Assistant Core)

After determining `response_mode`, also determine:

```
response_style = determine_response_style(intent, query, emergency_score)
```

Routing logic becomes two-dimensional:

- response_mode (full_rag / hybrid_partial / clarification / live_search)
- response_style (educational / clinical)

If:

```
response_style == "EDUCATIONAL"
```

Then:

- Skip structured RAG template formatting
- Skip VetResponse schema validation
- Generate natural explanation
- Do NOT enforce section headers (Answer, Possible Causes, etc.)
- Optionally append gentle follow-up question

If:

```
response_style == "CLINICAL"
```

Then existing structured flow remains unchanged.

---

## 9.4 Educational Response Execution Rules

When response_style == "EDUCATIONAL":

1. Use a new prompt template:  
   `prompts/educational_prompt.txt`

2. Do NOT use structured format sections.
3. Do NOT force:
   - Possible Causes
   - Warning Signs
   - When to See a Vet
   - Care Tips
4. Return plain conversational text.
5. Optionally include a single friendly follow-up question.

Educational responses must NOT require high retrieval similarity threshold.

Retrieval may optionally be used, but confidence failure must NOT block explanation.

---

## 9.5 Amendment to 3.7 LLM Invocation Architecture

Add new LLM call type:

6. Educational Concept Explanation

Configuration:

- Temperature: 0.4
- Max tokens: 600
- No structured output enforcement

This mode bypasses structured schema validation.

---

## 9.6 Amendment to 3.8 Structured Output Validation

Structured schema validation applies ONLY when:

```
response_style == "CLINICAL"
```

Educational responses bypass VetResponse schema validation.

They return:

```
ChatResponse(
    text: str,
    follow_up_questions: optional,
    citations: optional
)
```

No mandatory structured fields.

---

## 9.7 Amendment to 5.1 Master System Prompt

Add:

```
If the query is general and conceptual (educational in nature),
respond in a natural, conversational style without structured medical sections.

Use structured clinical format only for case-specific or health-risk queries.
```

---

## 9.8 Amendment to 5.10 LLM Workflow Diagram

```mermaid
flowchart TD

    INPUT[User Input] --> CHECK[Emergency Check]
    CHECK -->|High| EMERG_PROMPT

    CHECK -->|Normal| STYLE[Determine Response Style]

    STYLE -->|Educational| EDUCATIONAL_PROMPT
    STYLE -->|Clinical| RETRIEVE

    RETRIEVE -->|High| RAG_PROMPT
    RETRIEVE -->|Medium + Informational| HYBRID_FLOW
    RETRIEVE -->|Medium + Symptom| QUESTION_PROMPT
    RETRIEVE -->|Low| LIVE_SEARCH

    EDUCATIONAL_PROMPT --> LLM

    RAG_PROMPT --> LLM
    QUESTION_PROMPT --> LLM
    LIVE_SEARCH --> LIVE_PROMPT
    LIVE_PROMPT --> LLM

    LLM --> VALIDATE[Structured Validation if Clinical Only]
```

---

## 9.9 Safety Preservation Rule

Educational mode is strictly prohibited when:

- emergency_score ≥ threshold
- dosage-related queries
- toxic exposure
- symptom-specific clinical assessment
- lab value interpretation
- medication advice

In such cases, system must revert to CLINICAL structured flow.

---

## 9.10 Expected Behavioral Outcome

Query:
"Why do we vaccinate animals?"

System Output:

- Explanation of what vaccines are
- Why vaccination is important
- How schedules vary by species and age
- Friendly follow-up question
- No structured medical sections

Query:
"My dog has vomiting and diarrhea."

System Output:

- Structured clinical response
- Warning signs
- Vet guidance
- Citations if applicable

---

END OF ARCHITECTURAL UPDATE - 2

------

# Architecture Update - 3

# 10. Context-Aware Academic vs Clinical Restriction Model

This amendment corrects a foundational architectural limitation: the system previously assumed all dosage and treatment queries occur in a clinical context.

The updated model introduces Context Classification to distinguish between:

- ACADEMIC (educational / veterinary student intent)
- GENERAL (conceptual, non-case-specific)
- CLINICAL\_SPECIFIC (active pet-specific medical scenario)

This ensures dosage and treatment information can be explained safely in academic/general contexts while remaining restricted in pet-specific cases.

This amendment modifies behavior in the following layers:

- 3.3 Chat Assistant Core (Orchestration Engine)
- 3.4 Hybrid Intent Detection Engine
- 3.7 LLM Invocation Architecture
- 3.8 Structured Output Validation
- 3.9 Emergency Detection Engine
- 5.1 Master System Prompt
- 5.2 RAG Prompt
- 5.6 Fallback General Guidance Prompt
- 5.10 LLM Workflow Diagram

No previously defined safety guarantees are removed. Restrictions are now context-dependent rather than keyword-only.

---

## 10.1 New Layer: Query Context Classification

Before determining response\_mode or response\_style, introduce:

```
query_context = determine_query_context(query, pet_profile)
```

Return one of:

- "ACADEMIC"
- "GENERAL"
- "CLINICAL\_SPECIFIC"

This classification operates independently of intent and retrieval confidence.

---

## 10.2 Context Classification Rules

### CLINICAL\_SPECIFIC

Trigger if ANY of the following are detected:

- Mentions "my dog", "my cat", "my puppy", etc.
- Includes weight (kg, lbs)
- Includes age of specific pet
- Describes active symptoms
- Requests calculation ("how much should I give")
- Time-sensitive framing ("right now", "immediately")

This context implies real-world application risk.

---

### ACADEMIC

Trigger if:

- No specific pet described
- No weight or age mentioned
- No active symptoms
- Phrases such as:
  - "standard dosage"
  - "usual dose"
  - "recommended mg/kg"
  - "in veterinary medicine"
  - "for academic purpose"

This context implies informational learning.

---

### GENERAL

Trigger if:

- Conceptual question
- No specific pet
- No real-time medical scenario

Example: "How does amoxicillin work in dogs?"

---

## 10.3 Dosage & Treatment Handling Matrix

Replace previous binary restriction rule.

New logic:

```
if dosage_pattern and query_context == "CLINICAL_SPECIFIC":
    enforce_strict_clinical_restriction()

elif dosage_pattern and query_context in {"ACADEMIC", "GENERAL"}:
    allow_general_range_only()
    prohibit_specific_calculation()
```

---

### Allowed in ACADEMIC / GENERAL:

- Provide standard mg/kg range
- Explain therapeutic indications
- Explain mechanism of action
- Include safety note that dosing must be determined by veterinarian

### Prohibited in ACADEMIC / GENERAL:

- Calculating dose for specific weight
- Giving step-by-step treatment plan for specific case

---

## 10.4 Modification to Layer 3.3 (Chat Assistant Core)

Update orchestration pseudocode:

```
preprocessed = preprocess(message)
intent, confidence = detect_intent(preprocessed)
emergency_score = compute_emergency_score(preprocessed)
query_context = determine_query_context(preprocessed, session.pet_profile)
response_style = determine_response_style(intent, preprocessed, emergency_score)
response_mode = determine_response_mode(intent, retrieval_score, emergency_score)
```

Safety gating must now evaluate BOTH:

- query\_context
- dosage\_pattern
- emergency\_score

---

## 10.5 Structured vs Educational Output Refinement

Educational responses must now support structured narrative formatting.

Instead of rigid schema blocks, educational responses should use soft structured sections:

Recommended structure for educational responses:

- "What it is"
- "Why it matters"
- "How it works"
- "Differences by species or age"
- "General dosage range" (if applicable)
- Gentle follow-up question

This preserves clarity while remaining user-friendly.

---

## 10.6 Amendment to 3.7 LLM Invocation Architecture

Add new LLM call subtype:

7. Educational Academic Explanation with Controlled Dosage Range

Configuration:

- Temperature: 0.35–0.45
- Max tokens: 700
- Structured narrative guidance
- Explicit prohibition of individualized dosing

---

## 10.7 Amendment to 3.8 Structured Output Validation

Structured VetResponse schema remains mandatory ONLY for:

- CLINICAL\_SPECIFIC context
- Symptom-based queries
- Lab interpretation
- Emergency scenarios

Educational and Academic contexts bypass strict schema.

However:

Educational responses must still pass:

- Injection protection validation
- Citation validation if retrieval used
- Safety keyword audit

---

## 10.8 Amendment to 3.9 Emergency Detection

Emergency override remains absolute.

Even in ACADEMIC context:

If emergency\_score ≥ threshold → EMERGENCY flow overrides all other context.

---

## 10.9 Amendment to 5.1 Master System Prompt

Add:

```
The system serves both educational and clinical support purposes.

If the query is academic or general and not tied to a specific pet case,
you may explain dosage ranges and treatment principles in general terms.

Never calculate or prescribe medication amounts for a specific animal.

If the query involves a specific pet and treatment decision,
follow strict clinical structured mode.
```

---

## 10.10 Amendment to 5.2 RAG Prompt

Add instruction:

```
If the query is educational or academic in nature,
you may provide general dosage ranges but must not compute dose for a specific animal.
```

---

## 10.11 Amendment to 5.6 Fallback General Guidance Prompt

Update:

Remove hard prohibition of dosage mention.

Replace with:

```
You may explain standard dosage ranges in general educational context.
Do not calculate or prescribe individualized dosing.
```

---

## 10.12 Updated Workflow Diagram

```mermaid
flowchart TD

    INPUT --> CHECK_EMERGENCY
    CHECK_EMERGENCY -->|High| EMERG_PROMPT
    CHECK_EMERGENCY -->|Normal| CONTEXT

    CONTEXT --> STYLE
    STYLE --> RETRIEVE

    RETRIEVE --> RESPONSE_MODE
    RESPONSE_MODE --> LLM_CALL

    LLM_CALL --> VALIDATE
```

Where VALIDATE applies structured schema only if:

```
query_context == "CLINICAL_SPECIFIC"
```

---

## 10.13 Safety Guarantees Preserved

The updated architecture guarantees:

✔ No individualized dosage hallucinations\
✔ No emergency override bypass\
✔ Academic dosage explanation allowed\
✔ Clinical-specific dosing restricted\
✔ Structured medical formatting preserved where required\
✔ Educational conversational tone enabled where appropriate

---

END OF ARCHITECTURE UPDATE - 3

