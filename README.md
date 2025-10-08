# RFP Processing Pipeline

A streamlined FastAPI-based pipeline that processes RFP (Request for Proposal) PDF documents using Docling for parsing and Azure OpenAI for intelligent information extraction.

## Features

- **PDF Parsing**: Convert RFP PDFs to structured markdown using Docling
- **Intelligent Extraction**: Extract specific information using Azure OpenAI:
  - Bill of Quantities (BOQ)
  - Prequalification Criteria (PQ)
  - Technical Qualification (TQ)
  - RFP Summary
  - Payment Terms
- **Combined Excel Output**: Single Excel file with all extracted data in separate sheets
- **RESTful API**: Simple FastAPI endpoint for processing
- **Automatic Cleanup**: Temporary files cleaned up after processing
- **Sequential Processing**: Rate-limited API calls to avoid throttling

## Project Structure

```
NEW_DOCLING/
├── main.py                          # FastAPI application
├── run_server.py                    # Server runner script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment configuration template
└── src/                             # Source code modules
    ├── pipeline/                    # Processing pipeline modules
    │   ├── __init__.py
    │   ├── rfp_processor.py        # Main processor orchestrator
    │   └── utils.py                 # Utility functions
    ├── llm_extractor/               # LLM extraction modules
    │   ├── __init__.py
    │   ├── llm_extract_boq.py      # BOQ extraction
    │   ├── llm_extract_pq.py       # Prequalification extraction
    │   ├── llm_extract_pure_tq.py  # Technical qualification extraction
    │   ├── rfp_llm_summary.py      # RFP summary extraction
    │   └── llm_extract_payment_terms.py # Payment terms extraction
    └── excel_convertor/             # Excel conversion modules
        ├── __init__.py
        ├── boq_to_excel.py         # BOQ to Excel converter
        ├── pq_to_excel.py          # PQ to Excel converter
        ├── pure_tq_to_excel.py     # TQ to Excel converter
        ├── rfp_summary_to_excel.py # Summary to Excel converter
        └── payment_terms_to_excel.py # Payment terms to Excel converter
```

## Quick Start

### Manual Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and add: AZURE_OPENAI_API_KEY=your_actual_api_key_here
```

3. **Run Server**
```bash
python run_server.py
```

Server starts at `http://localhost:8000`

## API Usage

### Process RFP PDF

```bash
curl -X POST "http://localhost:8000/process-rfp/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_rfp.pdf" \
     --output "rfp_analysis.xlsx"
```

The API directly returns a combined Excel file containing all extracted information in separate sheets:
- **BOQ** - Bill of Quantities
- **Prequalification** - Prequalification criteria
- **Technical_Qualification** - Technical qualification criteria
- **Summary** - RFP key details summary
- **Payment_Terms** - Payment terms and conditions

### API Root

```bash
curl -X GET "http://localhost:8000/"
```

Returns API information and version.

## Output

The API returns a single Excel file with multiple sheets containing all extracted RFP information:

- **BOQ Sheet**: Bill of Quantities with items, quantities, and specifications
- **Prequalification Sheet**: Eligibility criteria and requirements
- **Technical_Qualification Sheet**: Technical evaluation criteria and scoring
- **Summary Sheet**: Key RFP details, dates, and contact information
- **Payment_Terms Sheet**: Payment schedule, milestones, and conditions

## Processing Pipeline

1. **PDF Parsing**: Docling converts PDF to structured markdown (~14 min for large files)
2. **Concurrent Extraction**: 5 parallel Azure OpenAI extractions (BOQ, PQ, TQ, Summary, Payment Terms)
3. **Excel Conversion**: Specialized converters create formatted Excel sheets
4. **Session Management**: Files organized by unique session IDs
5. **Auto Cleanup**: Temporary files automatically removed

### Recent Fixes
- ✅ **Proxy Issue Resolved**: Fixed Azure OpenAI client initialization conflicts
- ✅ **Unicode Encoding**: Fixed Windows console display issues
- ✅ **Error Handling**: Improved robustness for production use

## Interactive Documentation

Access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

- PDF format validation
- Azure OpenAI API error handling with proxy conflict resolution
- Automatic cleanup on processing failures
- Concurrent processing with individual module error isolation
- Windows console Unicode encoding fixes

## Performance

- **Concurrent LLM processing**: 5 parallel extractions for faster results
- **Async operations**: Non-blocking file I/O and API calls
- **Thread pool execution**: CPU-intensive tasks use separate threads
- **Session-based processing**: Multiple users can process simultaneously
- **Memory efficient**: Streaming file operations

## Requirements

- Python 3.8+
- Azure OpenAI API access
- Sufficient disk space for temporary files
- Internet connection for API calls