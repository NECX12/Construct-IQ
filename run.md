# Running ConstructIQ

ConstructIQ is a Streamlit MVP for blueprint review, material takeoff, construction-log parsing, costing, and planned-versus-actual analysis.

## 1. Prerequisites

Install:

- Python 3.11 or newer
- VS Code with the Python extension

Open a terminal in the project root:

```text
cd C:\path\to\ConstructIQ
```

## 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

If PowerShell blocks activation, run this once in PowerShell as your normal user:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Configure environment values

Copy `.env.example` to `.env` if you want to prepare environment settings:

```powershell
Copy-Item .env.example .env
```

Gemini extraction requires a key. Set these values in your local `.env` file:

```text
AI_PROVIDER=gemini
MODEL_NAME=gemini-2.5-flash
GEMINI_API_KEY=your_key_here
```

Never commit `.env` or share the API key. A `.json` blueprint upload can still provide structured extraction data without making an AI request.

## 5. Run the tests

```powershell
python -m pytest -q
```

The tests cover:

- Quantity and wastage calculations
- Material costing
- Planned-versus-actual variance
- Construction-log parsing

## 6. Start Streamlit

```powershell
python -m streamlit run app.py
```

Streamlit normally opens the application at:

```text
http://localhost:8501
```

Stop the application with `Ctrl+C` in the terminal.

## 7. Use the application

1. Confirm `AI_PROVIDER=gemini`, `MODEL_NAME`, and `GEMINI_API_KEY` are set in `.env`.
2. Open **Project setup** and enter the project name, currency, wastage, and variance threshold.
3. Open **Upload documents**.
4. Upload a blueprint as PDF, PNG, JPG, or JSON.
5. Click **Process blueprint**. PDF/image files are sent to Gemini; JSON files are validated locally.
6. Open **Blueprint analysis** and review the extracted rooms and building elements.
7. Edit the element quantities when required, then click **Apply reviewed elements**.
8. Upload a site log as TXT, MD, or CSV text and click **Process site log**.
9. Open **Takeoff and costs** to inspect quantities, prices, variance, and charts.
10. Download the JSON or Excel report.

## 8. Supported blueprint JSON format

A JSON upload is useful for testing deterministic calculations before an AI provider is connected:

```json
{
  "drawing_type": "floor_plan",
  "rooms": [
    {
      "name": "Living Room",
      "length_m": 6.2,
      "width_m": 4.5,
      "area_m2": 27.9
    }
  ],
  "building_elements": [
    {
      "element_type": "block_wall",
      "quantity": 120,
      "unit": "m2",
      "dimensions": {"area_m2": 120},
      "source": "explicit_dimension",
      "confidence": 0.98
    },
    {
      "element_type": "floor_area",
      "quantity": 27.9,
      "unit": "m2",
      "dimensions": {"area_m2": 27.9},
      "source": "explicit_dimension",
      "confidence": 0.98
    }
  ]
}
```

The filename should end in `.json`. The application validates this data with Pydantic before using it.

## 9. Supported site-log format

The simple parser recognizes lines such as:

```text
Date: 02/09/2026
Activity: Blockwork
Workers: 12
Cement - 8 bags
Blocks - 650 pcs
Sand - 3 m3
```

Material names are normalized to lowercase. Actual quantities are aggregated by material name.

## 10. Price book CSV format

Upload a CSV with these columns:

```text
material,unit,unit_price,currency
blocks,pcs,750,NGN
cement,bag,12000,NGN
sand,m3,85000,NGN
tiles,m2,8500,NGN
```

If `currency` is omitted, the project currency is used.

## 11. Gemini extraction behavior

PDF and image uploads are sent to the configured Gemini model with a structured JSON response schema. The response is validated with Pydantic before it reaches the calculation engine. Gemini is asked to identify rooms, visible dimensions, doors, windows, and supported building elements such as wall and floor areas.

If Gemini is unavailable, the UI displays an error and does not silently substitute invented measurements. Quantity, wastage, costing, and variance calculations remain deterministic in Python.

The Gemini implementation is in `app/extraction.py`; configuration is loaded in `app/config.py`, and the extraction prompt is in `app/prompts.py`.

## 12. Project structure

```text
ConstructIQ/
├── app.py
├── requirements.txt
├── .env.example
├── run.md
├── data/
│   ├── uploads/
│   ├── processed/
│   └── sample/
├── app/
│   ├── models.py
│   ├── document_processing.py
│   ├── extraction.py
│   ├── logs.py
│   ├── takeoff.py
│   ├── costing.py
│   └── reporting.py
└── tests/
    ├── test_takeoff.py
    ├── test_costing.py
    └── test_logs.py
```
