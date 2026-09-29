# AI-Powered Architectural Blueprint & Construction Cost Intelligence Engine

> An AI-assisted Python system for parsing digital architectural blueprints and unstructured construction logs, converting extracted information into structured project data, automating material takeoffs, comparing planned quantities with actual site consumption, and generating financial reports.

---

## 1. Project Overview

This project is a prototype for an **AI-assisted construction quantity takeoff and financial reporting system**.

The system accepts two major classes of input:

1. **Architectural documents**
   - Floor plans
   - Sections
   - Elevations
   - Door/window schedules
   - Other drawing PDFs
   - Rasterized blueprint images

2. **Unstructured project/site records**
   - Construction site logs
   - Daily reports
   - Material delivery records
   - Material consumption records
   - Labour records
   - Progress notes
   - Invoices or cost records

The system uses AI/multimodal document understanding where appropriate to extract information from unstructured documents. It then passes the extracted information into deterministic Python calculation engines.

The central design principle is:

> **Use AI for interpretation and extraction; use deterministic Python logic for calculations, quantities, costing, validation, and reporting.**

This separation is critical. An LLM should not be responsible for inventing or silently changing engineering formulas.

---

# 2. Problem Statement

Architectural and construction projects generate large amounts of information across drawings, schedules, site reports, delivery notes, and financial records.

Traditionally, quantity takeoff and cost monitoring can require substantial manual work:

- Reading drawings
- Identifying rooms and building elements
- Measuring dimensions
- Calculating areas and volumes
- Estimating material quantities
- Applying wastage factors
- Recording site consumption
- Comparing estimated quantities with actual usage
- Calculating material costs
- Preparing financial summaries

The goal of this project is to create a prototype that demonstrates how these workflows can be partially automated.

The system should ultimately answer questions such as:

- What spaces and measurable elements are present in this drawing?
- What quantities can be reliably extracted?
- What materials are required?
- How much of each material is estimated?
- What has actually been consumed on site?
- Where are there significant quantity variances?
- What is the estimated material cost?
- How does actual expenditure compare with the planned budget?
- What should be included in a project financial report?

---

# 3. Prototype Scope

The first version should **not attempt to solve every possible construction quantity takeoff problem**.

The MVP should focus on demonstrating the complete pipeline:

```text
Upload Documents
       |
       v
Document Processing
       |
       v
AI-Assisted Extraction
       |
       v
Structured Project Data
       |
       v
Deterministic Quantity Calculations
       |
       v
Material Takeoff
       |
       v
Cost Calculation
       |
       v
Actual Site Log Processing
       |
       v
Planned vs Actual Analysis
       |
       v
Financial / Project Report
```

The prototype will use **Streamlit** as the user interface.

FastAPI is intentionally not required for the first prototype. The internal application modules should nevertheless be designed so that the processing logic can later be exposed through FastAPI endpoints.

---

# 4. High-Level Architecture

```text
                         STREAMLIT UI
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
      Blueprint Upload                  Site Log Upload
             |                                 |
             v                                 v
      Document Processor                Log Processor
             |                                 |
             v                                 v
      AI/Multimodal Extraction       AI/Text Extraction
             |                                 |
             +----------------+----------------+
                              |
                              v
                    Structured Project Data
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          Quantity Engine             Validation
                 |                         |
                 v                         |
          Material Takeoff <--------------+
                 |
                 v
           Cost Engine
                 |
                 v
       Planned vs Actual Engine
                 |
                 v
          Reporting Engine
                 |
                 v
             Streamlit
                 |
       +---------+----------+
       |         |          |
       v         v          v
    Tables     Charts    Downloads
```

---

# 5. Recommended Technology Stack

## Core

- Python 3.11+
- Streamlit
- Pydantic
- pandas
- NumPy

## Document Processing

Depending on document type:

- PyMuPDF / `fitz`
- Pillow
- pdfplumber where useful
- OCR engine where required

## AI / Multimodal Processing

The implementation should abstract the provider behind an internal interface.

Possible providers include:

- Google Gemini
- OpenAI
- Other multimodal models

The application should not scatter provider-specific API calls throughout the project.

Use an abstraction such as:

```text
AIProvider
   |
   +-- GeminiProvider
   |
   +-- OpenAIProvider
```

## Visualization

- Streamlit native charts
- Plotly where interactive charts provide value
- pandas for tabular analysis

## Data Storage for MVP

The MVP can begin with:

- JSON
- CSV
- SQLite

For the first version, SQLite is recommended if persistent project data is required.

## Future Production Infrastructure

The eventual production system may use:

- FastAPI
- PostgreSQL
- Redis
- Celery or another job queue
- Object storage
- Docker
- Authentication
- Background workers

---

# 6. Recommended Project Structure

```text
arcparser/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   ├── uploads/
│   ├── processed/
│   └── sample/
├── app/
│   ├── models.py
│   ├── config.py
│   ├── document_processing.py
│   ├── extraction.py
│   ├── takeoff.py
│   ├── costing.py
│   ├── logs.py
│   └── reporting.py
└── tests/
    ├── test_takeoff.py
    ├── test_costing.py
    └── test_logs.py
```

---

# 7. Separation of Responsibilities

Do not place the entire application inside `app.py`.

`app.py` should primarily:

- initialize Streamlit
- create navigation
- collect user input
- invoke application services
- display results

Business logic should live elsewhere.

For example:

```python
# Good

results = takeoff_engine.calculate(project_data)
st.dataframe(results)
```

Avoid:

```python
# Bad

# Hundreds of lines of quantity formulas
# directly inside Streamlit callbacks
```

This separation will make the future FastAPI migration much easier.

---

# 8. Core Data Models

Pydantic models should define the contracts between processing stages.

## Project

```python
class Project:
    id: str
    name: str
    project_type: str
    currency: str
    location: str | None
```

## Drawing

```python
class Drawing:
    id: str
    filename: str
    drawing_type: str
    page_number: int | None
    source_path: str
```

## Room

```python
class Room:
    name: str
    length_m: float | None
    width_m: float | None
    height_m: float | None
    area_m2: float | None
```

## Building Element

```python
class BuildingElement:
    element_type: str
    quantity: float
    unit: str
    dimensions: dict
```

## Material

```python
class Material:
    name: str
    quantity: float
    unit: str
    wastage_percent: float
    final_quantity: float
```

## Site Log Entry

```python
class SiteLogEntry:
    date: str
    activity: str
    material: str | None
    quantity: float | None
    unit: str | None
    workers: int | None
    notes: str | None
```

---

# 9. Document Processing Pipeline

The system should not immediately send every file directly to an LLM.

The pipeline should be:

```text
Uploaded File
     |
     v
Identify File Type
     |
     +---- PDF ----> PDF Processor
     |
     +---- Image --> Image Processor
     |
     +---- TXT ----> Text Processor
     |
     +---- CSV ----> Tabular Processor
     |
     v
Normalize
     |
     v
Extract Text / Images / Metadata
     |
     v
AI Extraction where required
```

The processor should produce a normalized intermediate representation.

---

# 10. Blueprint Processing

Blueprints are more difficult than ordinary text documents.

A drawing may contain:

- lines
- dimensions
- room labels
- symbols
- doors
- windows
- stairs
- annotations
- title blocks
- scales
- hatching
- legends

The MVP should therefore support two levels of extraction.

## Level 1 — AI-Assisted Visual Interpretation

Send the relevant drawing image/page to a multimodal model.

Ask it to identify:

- drawing type
- room labels
- visible dimensions
- doors
- windows
- stairs
- major building elements
- drawing scale if visible
- important annotations

Return structured JSON.

## Level 2 — Deterministic Processing

Use Python to:

- validate numeric values
- calculate areas
- calculate volumes
- apply formulas
- detect missing values
- apply wastage
- calculate costs

The AI output should never automatically be trusted.

---

# 11. Example Blueprint Extraction

Input:

```text
Ground Floor Plan
```

Possible extracted representation:

```json
{
  "drawing_type": "floor_plan",
  "scale": "1:100",
  "rooms": [
    {
      "name": "Living Room",
      "length_m": 6.2,
      "width_m": 4.5
    },
    {
      "name": "Bedroom 1",
      "length_m": 4.2,
      "width_m": 3.8
    }
  ],
  "doors": {
    "internal": 6,
    "external": 2
  },
  "windows": 10
}
```

The exact schema should evolve as the prototype encounters real drawings.

---

# 12. Important Limitation: Measurement Accuracy

The prototype must clearly distinguish between:

1. **Explicit dimensions found in the drawing**
2. **Dimensions inferred from scale**
3. **Dimensions estimated by AI**
4. **Dimensions calculated from other known information**

Every extracted measurement should ideally carry a confidence/source field.

Example:

```json
{
  "value": 6.2,
  "unit": "m",
  "source": "drawing_dimension",
  "confidence": 0.98
}
```

Do not present uncertain AI estimates as surveyed measurements.

For production use, quantities derived from drawings should be reviewed by a qualified quantity surveyor, architect, engineer, or other appropriate professional.

---

# 13. Construction Log Processing

Construction logs are usually easier to process than drawings.

Example:

```text
Date: 02/09/2026

Activity:
Blockwork

Workers:
12

Materials Used:
Cement - 8 bags
Blocks - 650 pcs
Sand - 3 m3

Remarks:
External walls completed.
```

The parser should normalize this into:

```json
{
  "date": "2026-09-02",
  "activity": "Blockwork",
  "workers": 12,
  "materials": [
    {
      "name": "cement",
      "quantity": 8,
      "unit": "bag"
    },
    {
      "name": "blocks",
      "quantity": 650,
      "unit": "pcs"
    },
    {
      "name": "sand",
      "quantity": 3,
      "unit": "m3"
    }
  ]
}
```

---

# 14. Material Takeoff Engine

The takeoff engine is the heart of the deterministic calculation layer.

It should receive structured building information and return material quantities.

Example:

```text
Building Elements
       |
       v
Geometry
       |
       v
Measured Quantities
       |
       v
Construction Rules
       |
       v
Material Requirements
```

The system should support formulas such as:

```text
Area = Length × Width

Wall Area = Wall Length × Wall Height

Volume = Length × Width × Height

Net Quantity = Calculated Quantity

Final Quantity =
    Net Quantity × (1 + Wastage %)
```

The exact construction formulas should be configurable rather than hard-coded everywhere.

---

# 15. Material Rules

A material rule can define how a construction element maps to materials.

Example:

```python
{
    "element": "block_wall",
    "materials": [
        {
            "material": "blocks",
            "consumption_rate": 10.0,
            "unit": "pcs/m2"
        },
        {
            "material": "cement",
            "consumption_rate": 0.15,
            "unit": "bag/m2"
        }
    ]
}
```

This allows the same quantity engine to support different construction assumptions.

The MVP should clearly document that these rates are **project assumptions**, not universal engineering constants.

---

# 16. Wastage

Wastage should be explicit.

Example:

```text
Net blocks = 4,000

Wastage = 5%

Final quantity =
4,000 × 1.05
= 4,200 blocks
```

Represent it separately:

```python
{
    "material": "blocks",
    "net_quantity": 4000,
    "wastage_percent": 5,
    "final_quantity": 4200
}
```

Do not hide wastage inside unexplained formulas.

---

# 17. Cost Engine

The cost engine converts quantities into financial values.

Example price book:

```python
{
    "cement": {
        "unit": "bag",
        "unit_price": 12000
    },
    "blocks": {
        "unit": "pcs",
        "unit_price": 750
    }
}
```

Calculation:

```text
Total Cost =
Quantity × Unit Price
```

Example:

```text
Cement
195 bags × ₦12,000
= ₦2,340,000
```

---

# 18. Price Book

The prototype should allow prices to be changed without modifying Python formulas.

For example:

```text
Material        Unit       Price
----------------------------------
Cement          bag        ₦12,000
Blocks          pcs        ₦750
Sand            m3         ₦85,000
Steel           kg         ₦2,200
Tiles           m2         ₦8,500
```

Possible MVP implementation:

```text
data/price_book.csv
```

Later this can become a database table.

Prices should have:

- material name
- unit
- unit price
- currency
- effective date
- optional supplier
- optional location

---

# 19. Planned vs Actual

One of the most valuable features is comparing the estimated takeoff with actual site records.

Example:

```text
Material: Cement

Planned:
200 bags

Actual:
230 bags

Variance:
30 bags

Variance %:
15%
```

Formula:

```text
Variance =
Actual - Planned

Variance % =
((Actual - Planned) / Planned) × 100
```

The system should classify results:

```text
UNDER BUDGET
ON TRACK
OVER CONSUMPTION
```

Thresholds should be configurable.

Example:

```text
0–5%       = Normal
5–10%      = Attention
>10%       = Significant variance
```

These thresholds are project-management assumptions and should be configurable.

---

# 20. Financial Dashboard

The Streamlit dashboard should contain:

## Project Summary

```text
Project
Estimated Material Cost
Actual Material Cost
Estimated Total Materials
Number of Drawings
Number of Site Logs
```

## Material Summary

```text
Material | Planned | Actual | Variance | Cost
```

## Charts

Recommended charts:

- Planned vs actual quantity
- Planned vs actual cost
- Cost by material
- Quantity variance
- Material consumption over time
- Daily/weekly expenditure

---

# 21. Streamlit Pages

Recommended navigation:

## 1. Dashboard

Displays:

- project summary
- cost summary
- material summary
- key warnings
- charts

## 2. Project Setup

Allows users to specify:

- project name
- project type
- location
- currency
- project assumptions

## 3. Upload Documents

Allows:

- blueprint upload
- site log upload
- price book upload

## 4. Blueprint Analysis

Displays:

- uploaded drawing
- extracted information
- rooms
- dimensions
- doors
- windows
- confidence/source
- extraction warnings

## 5. Material Takeoff

Displays:

- building elements
- calculated quantities
- materials
- wastage
- final quantities

## 6. Cost Analysis

Displays:

- unit prices
- material costs
- total estimated cost
- actual cost
- variance

## 7. Reports

Allows export of:

- CSV
- Excel
- JSON
- PDF summary where implemented

---

# 22. AI Prompt Design

Prompts should be stored centrally.

Do not write long prompts directly inside UI functions.

Example:

```python
BLUEPRINT_EXTRACTION_PROMPT = """
You are analyzing an architectural drawing.

Extract only information that is explicitly visible
or reasonably identifiable.

Return structured JSON containing:

- drawing type
- rooms
- dimensions
- doors
- windows
- stairs
- annotations

Do not invent dimensions.

For every uncertain value, indicate uncertainty.
"""
```

The application should request structured output wherever the provider supports it.

---

# 23. AI Provider Abstraction

Create an interface:

```python
class AIProvider:
    def analyze_image(self, image, prompt):
        raise NotImplementedError

    def analyze_text(self, text, prompt):
        raise NotImplementedError
```

Then implement:

```text
AIProvider
   |
   +--- GeminiProvider
   |
   +--- OpenAIProvider
```

The rest of the application should call:

```python
provider.analyze_image(...)
```

rather than:

```python
genai.Client(...)
```

everywhere.

This makes it possible to change providers later.

---

# 24. Error Handling

Every processing stage should handle failures gracefully.

Examples:

```text
Invalid PDF
Unsupported image
OCR failure
AI API timeout
Invalid AI JSON
Missing dimension
Missing material price
Malformed site log
Calculation error
```

The UI should show a useful message instead of crashing.

Example:

```text
⚠ Blueprint analysis completed with warnings.

3 dimensions could not be confidently extracted.

Please review the highlighted fields before generating
the final material takeoff.
```

---

# 25. Validation

Validation should occur at multiple levels.

## Input validation

Check:

- file extension
- file size
- required project information

## AI output validation

Use Pydantic models to validate AI responses.

If the model returns:

```json
{
    "length": "six metres"
}
```

when a float is expected, the system should reject or normalize it rather than blindly continuing.

## Calculation validation

Check:

- negative quantities
- zero dimensions
- impossible values
- missing units
- missing prices

---

# 26. Auditability

Every important calculated result should be traceable.

For example:

```text
Final Blocks: 4,200 pcs

Source:
Ground Floor Plan

Calculation:
Wall Area = 400 m2
Block Rate = 10 pcs/m2
Net Blocks = 4,000
Wastage = 5%
Final = 4,200
```

This is extremely important for a construction-related system.

The user should be able to understand **why** the system produced a number.

---

# 27. Intermediate Data

Do not immediately throw away extraction results.

Save intermediate structured outputs.

Example:

```text
data/processed/
    project_001/
        drawings/
            ground_floor.json
            first_floor.json
        logs/
            week_01.json
        takeoff.json
        costs.json
```

This makes debugging much easier.

---

# 28. Example End-to-End Scenario

Assume the user creates:

```text
Project:
3 Bedroom Residential Building
```

They upload:

```text
ground_floor.pdf
first_floor.pdf
site_log_week_01.pdf
site_log_week_02.pdf
price_book.csv
```

The application performs:

### Step 1

Identify documents.

```text
ground_floor.pdf → floor plan
first_floor.pdf → floor plan
site_log_week_01.pdf → construction log
site_log_week_02.pdf → construction log
price_book.csv → price book
```

### Step 2

Extract blueprint information.

```text
Rooms
Dimensions
Doors
Windows
Walls
Other identifiable elements
```

### Step 3

Validate extracted information.

```text
Dimensions → Pydantic validation
Missing values → warnings
Uncertain values → review
```

### Step 4

Calculate measurable quantities.

```text
Room areas
Wall areas
Floor areas
Other supported quantities
```

### Step 5

Generate material takeoff.

```text
Cement
Blocks
Sand
Steel
Tiles
Paint
etc.
```

### Step 6

Apply wastage.

```text
Net Quantity
+
Wastage
=
Final Quantity
```

### Step 7

Apply prices.

```text
Quantity × Unit Price
```

### Step 8

Parse construction logs.

```text
Actual material usage
Actual labour
Deliveries
Activities
```

### Step 9

Compare:

```text
Planned vs Actual
```

### Step 10

Generate report.

```text
Project Summary
Material Takeoff
Cost Summary
Variance Analysis
Warnings
Assumptions
```

---

# 29. Example Output

A final takeoff might look like:

| Material | Planned Qty | Wastage | Final Qty | Unit Price | Estimated Cost |
|---|---:|---:|---:|---:|---:|
| Cement | 185 | 5% | 195 | ₦12,000 | ₦2,340,000 |
| Blocks | 3,850 | 5% | 4,043 | ₦750 | ₦3,032,250 |
| Sand | 24 | 5% | 25.2 | ₦85,000 | ₦2,142,000 |
| Steel | 2,450 | 7% | 2,622 | ₦2,200 | ₦5,768,400 |

The exact numbers above are illustrative only.

---

# 30. Database Strategy

The MVP does not need a complex database.

Recommended progression:

```text
Version 1
JSON / CSV
     ↓
Version 2
SQLite
     ↓
Production
PostgreSQL
```

Potential production entities:

```text
projects
documents
drawings
rooms
building_elements
materials
takeoff_items
site_logs
material_consumption
price_books
cost_records
reports
```

---

# 31. Security

Even for the prototype:

- never hard-code API keys
- use `.env`
- never commit `.env`
- validate uploaded files
- restrict file sizes
- sanitize filenames
- avoid exposing internal exceptions
- do not log API keys
- do not store sensitive documents unnecessarily

Example:

```text
.env

AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

And:

```text
.env
```

must be included in `.gitignore`.

Provide:

```text
.env.example
```

with placeholder values.

---

# 32. Configuration

Use environment variables for secrets and environment-specific settings.

Example:

```python
AI_PROVIDER=gemini
MODEL_NAME=...
MAX_UPLOAD_SIZE_MB=100
CURRENCY=NGN
```

Application configuration should be separated from business rules.

For example:

```text
config.py
    application configuration

takeoff/formulas.py
    calculation rules

price_book.csv
    material prices
```

---

# 33. Testing Strategy

The most important parts to test are the deterministic calculation engines.

Example:

```python
def test_wall_area():
    assert calculate_wall_area(20, 3) == 60
```

Wastage:

```python
def test_wastage():
    assert apply_wastage(4000, 5) == 4200
```

Variance:

```python
def test_variance():
    assert calculate_variance(200, 230) == 30
```

Also test:

- malformed AI responses
- missing dimensions
- missing prices
- invalid units
- empty documents
- unsupported files

AI outputs should have integration tests with representative fixtures where practical.

---

# 34. Logging

Use Python's `logging` module.

Log events such as:

```text
INFO  Project created
INFO  Blueprint uploaded
INFO  Blueprint converted to image
INFO  AI extraction started
INFO  AI extraction completed
WARNING Missing dimension detected
ERROR AI provider failed
INFO  Takeoff calculation completed
```

Do not log:

- API keys
- sensitive document contents unnecessarily
- credentials

---

# 35. Performance

The prototype can process documents synchronously.

For example:

```text
Upload
  ↓
Process
  ↓
Show spinner
  ↓
Return result
```

Streamlit can display:

```python
with st.spinner("Analyzing blueprint..."):
    result = analyze_blueprint(file)
```

For large documents, the future architecture should move expensive work into background jobs.

---

# 36. Future FastAPI Architecture

Once the prototype works, separate the UI from the backend.

Future architecture:

```text
                    React / Web UI
                           |
                           v
                        FastAPI
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
     Document API     Takeoff API      Reporting API
          |                |                |
          +----------------+----------------+
                           |
                    Service Layer
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
   AI Service         Takeoff Engine       Cost Engine
       |                   |                   |
       +-------------------+-------------------+
                           |
                      PostgreSQL
                           |
                        Redis
                           |
                    Background Workers
```

Possible API endpoints:

```text
POST /projects
GET  /projects/{project_id}

POST /projects/{project_id}/documents

POST /projects/{project_id}/analyze

GET  /projects/{project_id}/drawings

GET  /projects/{project_id}/takeoff

GET  /projects/{project_id}/costs

GET  /projects/{project_id}/variance

POST /projects/{project_id}/reports

GET  /projects/{project_id}/reports/{report_id}
```

---

# 37. Background Processing in Production

Blueprint processing can become expensive.

Instead of:

```text
HTTP Request
   ↓
Analyze 100-page PDF
   ↓
Wait
   ↓
Response
```

Use:

```text
Upload
   ↓
FastAPI
   ↓
Create Job
   ↓
Redis / Queue
   ↓
Worker
   ↓
AI Processing
   ↓
Store Results
   ↓
Update Job Status
```

The frontend can poll:

```text
GET /jobs/{job_id}
```

and display:

```text
Processing: 65%
```

---

# 38. Production Storage

Uploaded documents should eventually be stored in object storage rather than directly on the application server.

For example:

```text
User
 |
 v
FastAPI
 |
 v
Object Storage
 |
 +-- project_001/
 |     +-- drawings/
 |     +-- logs/
 |     +-- reports/
 |
 v
Database
```

The database stores metadata and references to files.

---

# 39. RAG / Knowledge Base

A future version can include a construction knowledge base.

Potential documents:

- project specifications
- construction standards
- company estimating rules
- material specifications
- approved pricing rules
- internal quantity-surveying guidelines

Then a RAG system can answer questions such as:

> Why was this material quantity calculated using this rate?

or:

> What project rule was used for the wastage allowance?

However, RAG should support the calculation engine rather than replace deterministic calculations.

---

# 40. LLM Responsibilities vs Python Responsibilities

This distinction should remain explicit throughout development.

## AI / LLM

Good uses:

```text
Document interpretation
Text extraction
Visual classification
Room identification
Symbol interpretation
Unstructured log extraction
Natural-language explanations
Report narrative
```

## Python

Good uses:

```text
Geometry
Arithmetic
Unit conversion
Quantity calculations
Wastage
Pricing
Variance
Aggregation
Validation
Database operations
Business rules
```

Avoid asking the LLM:

```text
"Calculate the final project cost."
```

when Python can reliably perform:

```python
total = quantity * unit_price
```

The LLM can explain the result, but the calculation should come from deterministic code.

---

# 41. Confidence and Human Review

The system should not pretend that AI extraction is perfect.

Each extraction should ideally include:

```text
value
source
confidence
review_required
```

Example:

```json
{
  "element": "living_room_length",
  "value": 6.2,
  "unit": "m",
  "source": "explicit_dimension",
  "confidence": 0.97,
  "review_required": false
}
```

For uncertain extraction:

```json
{
  "element": "wall_length",
  "value": 8.4,
  "unit": "m",
  "source": "scale_estimation",
  "confidence": 0.62,
  "review_required": true
}
```

The Streamlit UI should allow users to review and edit uncertain values before generating the final takeoff.

---

# 42. MVP Acceptance Criteria

The prototype should be considered successful if it can:

- [ ] Create a project
- [ ] Upload architectural PDFs/images
- [ ] Upload construction logs
- [ ] Process PDFs
- [ ] Render blueprint pages
- [ ] Extract basic drawing information
- [ ] Extract basic dimensions where available
- [ ] Extract rooms
- [ ] Extract basic building elements
- [ ] Validate extracted information
- [ ] Calculate supported quantities
- [ ] Apply configurable wastage
- [ ] Generate material takeoff
- [ ] Load material prices
- [ ] Calculate estimated material costs
- [ ] Parse site logs
- [ ] Calculate actual material consumption
- [ ] Compare planned vs actual
- [ ] Display variance
- [ ] Show dashboard charts
- [ ] Export results
- [ ] Preserve intermediate processing results
- [ ] Handle errors without crashing

---

# 43. Development Order

Build the application in this order.

## Stage 1 — Project Skeleton

Create:

```text
app.py
config.py
app/
data/
tests/
```

Make sure Streamlit launches.

---

## Stage 2 — Project Setup

Implement:

- project creation
- project metadata
- session/project state

---

## Stage 3 — File Upload

Implement:

- PDF upload
- image upload
- text upload
- CSV upload
- file validation
- storage

---

## Stage 4 — PDF/Image Processing

Implement:

- PDF page extraction
- PDF-to-image conversion
- image normalization
- metadata extraction

Do this before integrating AI.

---

## Stage 5 — AI Extraction

Implement:

```text
AIProvider
GeminiProvider
Prompt templates
Pydantic output schemas
```

Start with simple blueprint extraction.

---

## Stage 6 — Blueprint Structured Data

Implement:

- rooms
- dimensions
- doors
- windows
- building elements
- confidence
- source

---

## Stage 7 — Quantity Engine

Implement deterministic formulas.

Start with a small number of supported elements.

Do not attempt to support every construction material immediately.

---

## Stage 8 — Material Takeoff

Map quantities to materials.

Implement:

- consumption rates
- wastage
- units
- validation

---

## Stage 9 — Cost Engine

Implement:

- price book
- unit prices
- estimated costs
- total costs

---

## Stage 10 — Construction Logs

Implement:

- text extraction
- AI parsing where required
- normalization
- actual consumption

---

## Stage 11 — Variance Analysis

Implement:

```text
planned
actual
variance
variance %
status
```

---

## Stage 12 — Dashboard

Build:

- project overview
- takeoff table
- cost table
- variance charts
- warnings

---

## Stage 13 — Reporting

Implement exports:

```text
CSV
Excel
JSON
PDF
```

---

## Stage 14 — Testing

Write tests around:

- models
- formulas
- wastage
- costing
- variance
- validation

---

## Stage 15 — Refactor for FastAPI

Once the Streamlit prototype is stable:

```text
Streamlit UI
      |
      v
Service Layer
      |
      +---- AI
      +---- Takeoff
      +---- Cost
      +---- Reports
```

The service layer becomes the foundation for FastAPI.

---

# 44. Coding Principles for Codex

When implementing this repository, follow these rules.

### Rule 1

Do not put business logic in Streamlit UI files.

### Rule 2

Do not hard-code API keys.

### Rule 3

Do not let AI output directly determine financial calculations without validation.

### Rule 4

Use Pydantic models for structured AI outputs and internal contracts.

### Rule 5

Keep calculation functions deterministic and unit-testable.

### Rule 6

Keep prompts in dedicated files.

### Rule 7

Use type hints throughout the codebase.

### Rule 8

Use meaningful exceptions.

### Rule 9

Add logging around document and AI processing.

### Rule 10

Preserve intermediate outputs for debugging.

### Rule 11

Make assumptions configurable.

### Rule 12

Do not implement unsupported engineering calculations merely to make the demo appear complete.

If a calculation is not sufficiently defined, display:

```text
Not enough information available.
```

rather than inventing a value.

---

# 45. Suggested Initial Dependencies

A starting `requirements.txt` may include:

```text
streamlit
pydantic
pydantic-settings
python-dotenv
pandas
numpy
pymupdf
pillow
plotly
openpyxl
reportlab
google-genai
pytest
```

Additional OCR or document-processing packages should be added only when actually required.

---

# 46. Environment Setup

Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env`:

```text
AI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
MODEL_NAME=your_model_name
MAX_UPLOAD_SIZE_MB=100
DEFAULT_CURRENCY=NGN
```

Run:

```cmd
streamlit run app.py
```

---

# 47. `.gitignore`

The repository should ignore:

```text
.venv/
.env
__pycache__/
*.pyc
.pytest_cache/

data/uploads/
data/processed/
data/outputs/

.streamlit/secrets.toml
```

Sample files can live under:

```text
data/sample/
```

if they are safe to distribute.

---

# 48. Recommended First Demo

The first demonstration should use a relatively simple residential floor plan.

Example:

```text
3 Bedroom House
|
+-- Living Room
+-- Dining
+-- Kitchen
+-- 3 Bedrooms
+-- Bathrooms
+-- Circulation
```

The demo should show:

```text
1. Upload floor plan
2. AI identifies rooms
3. Dimensions are extracted
4. Areas are calculated
5. Wall/floor quantities are calculated
6. Materials are estimated
7. Wastage is applied
8. Prices are applied
9. Cost summary is produced
10. Site log is uploaded
11. Actual consumption is extracted
12. Planned vs actual is displayed
```

This provides a much stronger demonstration than attempting to process a highly complex commercial building on day one.

---

# 49. Important Product Boundary

This prototype is an **AI-assisted estimation and reporting tool**, not a replacement for professional quantity surveying, engineering review, or construction supervision.

The application should clearly identify:

- assumptions
- estimated values
- AI-derived values
- user-entered values
- calculated values
- values requiring review

This is especially important when results could influence construction procurement or financial decisions.

---

# 50. Final Target Architecture

The long-term system should evolve toward:

```text
                         WEB / MOBILE CLIENT
                                  |
                                  v
                              FASTAPI
                                  |
              +-------------------+-------------------+
              |                   |                   |
              v                   v                   v
        Project Service     Document Service     Report Service
              |                   |
              |                   v
              |            Document Pipeline
              |                   |
              |        +----------+----------+
              |        |                     |
              |        v                     v
              |   OCR / Parsing       Multimodal AI
              |                              |
              +--------------+---------------+
                             |
                             v
                     Structured Data
                             |
                +------------+------------+
                |            |            |
                v            v            v
          Quantity Engine Cost Engine Variance Engine
                |            |            |
                +------------+------------+
                             |
                             v
                         PostgreSQL
                             |
                       +-----+-----+
                       |           |
                     Redis       Object
                       |          Storage
                       v
                  Background
                    Workers
```

The Streamlit MVP is therefore not a disposable demo. It should be treated as the **first implementation of the core domain logic**.

The main objective is to get the following pipeline working reliably:

```text
ARCHITECTURAL DOCUMENTS
          +
CONSTRUCTION LOGS
          +
PROJECT ASSUMPTIONS
          +
MATERIAL PRICES
          |
          v
    AI EXTRACTION
          |
          v
 STRUCTURED PROJECT DATA
          |
          v
 DETERMINISTIC CALCULATION
          |
          v
 MATERIAL TAKEOFF
          |
          v
 COST ESTIMATION
          |
          v
 PLANNED vs ACTUAL
          |
          v
 FINANCIAL REPORTING
```

Once that pipeline is reliable, the application can be migrated from Streamlit to a production architecture without rewriting the fundamental calculation and AI-processing logic.
