# 🐾 Veterinary Chat Assistance

# UI Architecture & Design Specification

**Version: 1.0**\
**Scope: Streamlit UI Implementation (Backend-Integrated)**

------------------------------------------------------------------------

# 1. Purpose

This document defines the complete UI design architecture for the
Veterinary Chat Assistance System.

The UI must:

-   Reflect backend routing logic
-   Respect response modes and styles
-   Clearly separate emergency, clinical, and educational flows
-   Render citations properly
-   Maintain structured session state
-   Avoid performing backend logic

⚠️ The UI must NOT: - Modify medical decisions - Perform inference -
Override backend logic - Alter citations

------------------------------------------------------------------------

# 2. High-Level Layout Structure

## Global Layout

  ---------------------------------------------------------
  \| Top Navigation Bar \|
  ---------------------------------------------------------
  \| Sidebar (Memory Panel) \| Main Conversation Area \|

  ---------------------------------------------------------

------------------------------------------------------------------------

# 3. UI State Model

The UI must support the following visual states:

1.  EMPTY_STATE\
2.  ACTIVE_CHAT_STATE\
3.  EMERGENCY_STATE\
4.  CLINICAL_STRUCTURED_STATE\
5.  EDUCATIONAL_STATE\
6.  HYBRID_PARTIAL_STATE\
7.  CLARIFICATION_REQUIRED_STATE\
8.  LIVE_SEARCH_STATE

These states are visual rendering modes driven by backend JSON fields.

------------------------------------------------------------------------

# 4. Top Navigation Bar

## Components

-   Application Title: "Veterinary AI Assistant"
-   System Status Indicator:
    -   🟢 System Ready
    -   🟡 Live Search Active
    -   🔴 Emergency Mode
-   Legal Disclaimer Button
-   Session Timer (optional)
-   About / Info Panel

------------------------------------------------------------------------

# 5. Sidebar (Structured Memory Panel)

The sidebar reflects structured memory.

## 5.1 Pet Profile Form

Fields: - Species (required) - Age - Weight - Breed - Known Medical
Conditions

Display note: "Information is used to personalize responses. Session
data is cleared after inactivity."

This data is sent to backend but not stored permanently.

------------------------------------------------------------------------

## 5.2 File Upload Panel (Future Expansion Ready)

Supported file types: - Vaccine reports - Lab reports - Prescription
text

Current Behavior: - File can be uploaded - File name displayed - Parsing
status placeholder shown

⚠️ Uploading files currently does NOT alter backend behavior. This is
reserved for future expansion.

UI must display: "Document interpretation feature coming soon."

------------------------------------------------------------------------

## 5.3 Session Controls

-   Reset Conversation
-   Clear Pet Profile
-   Clear Uploaded Files
-   Optional: Export Chat

------------------------------------------------------------------------

# 6. Main Conversation Area

## 6.1 EMPTY_STATE (Landing View)

When no chat history exists:

Display:

-   Large App Title
-   Subtitle: "AI-powered veterinary guidance system"
-   Large central input box
-   Suggestion Chips:
    -   Puppy vaccination schedule
    -   My dog is vomiting
    -   Explain rabies vaccine
    -   Emergency signs in cats
-   Legal disclaimer link

------------------------------------------------------------------------

## 6.2 ACTIVE_CHAT_STATE

Layout:

-   Chat history scrollable container
-   Emergency banner (conditional)
-   Streaming markdown rendering
-   Input bar fixed at bottom

------------------------------------------------------------------------

# 7. Response Rendering Rules

The UI must render messages differently based on backend response
metadata.

Backend response includes: - response_mode - response_style -
emergency_flag - citations - follow_up_questions - live_search_flag

------------------------------------------------------------------------

## 7.1 EMERGENCY_STATE

Trigger: emergency_flag == true

UI Behavior:

-   Red banner above response
-   Large header: ⚠️ EMERGENCY ALERT
-   Highlighted sections:
    -   Why This Is Serious
    -   Immediate Action
    -   Seek Veterinary Care Immediately
-   Google Maps redirect button

------------------------------------------------------------------------

## 7.2 CLINICAL_STRUCTURED_STATE

Trigger: response_style == "CLINICAL" AND query_context ==
"CLINICAL_SPECIFIC"

Render as segmented sections:

-   Answer
-   Possible Causes
-   Warning Signs
-   When to See a Vet
-   Care Tips

Below response: Collapsible Citation Panel.

------------------------------------------------------------------------

## 7.3 EDUCATIONAL_STATE

Trigger: response_style == "EDUCATIONAL"

Render as:

-   Conversational markdown block
-   Optional soft headers:
    -   What it is
    -   Why it matters
    -   General dosage range (if academic)
-   Optional gentle follow-up question

------------------------------------------------------------------------

## 7.4 HYBRID_PARTIAL_STATE

Trigger: response_mode == "HYBRID_PARTIAL"

Render in two parts:

Part 1: General guidance response.

Part 2: Highlighted box: "Before giving more specific advice, I need to
know:"

-   Clarifying question 1
-   Clarifying question 2

------------------------------------------------------------------------

## 7.5 CLARIFICATION_REQUIRED_STATE

Trigger: response_mode == "CLARIFICATION_REQUIRED"

Render:

Highlighted "More Information Needed" panel.

Display bullet-point questions only.

------------------------------------------------------------------------

## 7.6 LIVE_SEARCH_STATE

Trigger: live_search_flag == true

Display badge above response:

"Live Search Augmented Response"

------------------------------------------------------------------------

# 8. Citation Panel Design

Citations must:

-   Be displayed separately from main answer
-   Be collapsible
-   Not modify citation content
-   Display:
    -   Source Title
    -   Organization
    -   Publication Year
    -   Section Reference
    -   URL (if available)

If citations list empty: Do not render citation panel.

------------------------------------------------------------------------

# 9. Input Bar

Components:

-   Text input
-   Send button
-   Loading spinner
-   Disable input while processing
-   Streaming markdown rendering

------------------------------------------------------------------------

# 10. Context Transparency Indicators

If backend provides query_context:

Display small badge above response:

-   Educational Context
-   Academic Context
-   Case-Specific Clinical Context

------------------------------------------------------------------------

# 11. Error Handling UI

Handle gracefully:

-   Vector DB unavailable
-   LLM timeout
-   Live search failure
-   Parsing errors

Display safe fallback message:

"Unable to access knowledge sources at the moment. Please consult a
veterinarian if symptoms persist."

Never show raw error logs.

------------------------------------------------------------------------

# 12. Security & Privacy Notice

The UI must clearly state:

-   No permanent storage of medical data
-   Session auto-clears after inactivity
-   Not a substitute for professional veterinary consultation

------------------------------------------------------------------------

# 13. Non-Functional UI Requirements

-   Clean, clinical appearance
-   No playful pet illustrations
-   Minimal color palette (white, soft blue, emergency red)
-   Responsive layout
-   Scrollable chat history
-   Smooth streaming without flicker

------------------------------------------------------------------------

# 14. Explicit Limitations (Current Phase)

-   File uploads do not alter backend logic yet
-   No appointment booking integration
-   No persistent user accounts
-   No dosage calculation UI

Future-ready placeholders may be shown but must not imply active
functionality.

------------------------------------------------------------------------

# 15. Final Implementation Constraint

The UI must remain a presentation layer only.

All decision-making logic remains exclusively in backend orchestration.

The UI renders what backend returns.

------------------------------------------------------------------------

END OF UI ARCHITECTURE SPECIFICATION
