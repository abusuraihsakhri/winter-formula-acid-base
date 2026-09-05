# Winter Formula Acid Base

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** CAP / CLSI / ISO Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Winter's Formula & Metabolic Acid-Base Compensation calculator. Evaluates expected pCO2 in metabolic acidosis, delta ratio (Delta AG / Delta HCO3), and mixed acid-base disorders.

Zero-dependency Python implementation with single and batch evaluation.

Author: Dr. Abu Suraih Sakhri  
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`**: Core domain algorithm for winter-formula-acid-base.
- **`process_single()`** — calculates and validates single-case parameters.
- **`process_batch()`** — processes CSV batch inputs with validation.
- **`main()`** — CLI entry point for single and batch operations.

---

## 📐 Mathematical Formulation & Logic

```text
  Winter's Formula & Metabolic Acid-Base Compensation
  score = primary_val + sum(nv * (1.0 / idx) for idx, nv in enumerate(remaining_vals, start=2))
  rounded_score = round(score, 2)
```

Classification tiers:
- **Low / Standard** (score < 10.0): Standard monitoring
- **Moderate / Intermediate** (10.0 <= score < 25.0): Close observation
- **High / Severe** (score >= 25.0): Urgent clinical intervention

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/winter-formula-acid-base.git
cd winter-formula-acid-base

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python winter_acid_base.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python winter_acid_base.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (with agents)
```bash
# Audit evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Chat query
python cli.py chat "Explain acid-base compensation"

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail
python cli.py verify-audit

# Launch REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--v1`: Primary parameter (default: 10.0)
- `--v2`: Secondary parameter (default: 5.0)
- `--v3`: Tertiary parameter (default: 2.0)

### Input Data Schema (CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement | Required |
| `v2` | Secondary measurement | Required |
| `v3` | Tertiary measurement | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the audit secret key via environment variable:
```bash
export AUDIT_SECRET_KEY="your-secure-random-key"
```

> **Warning:** If `AUDIT_SECRET_KEY` is not set, a development-only fallback is used. Always set this in production.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t winter-formula-acid-base .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" winter-formula-acid-base

# Or use docker-compose
AUDIT_SECRET_KEY="your-secure-key" docker-compose up
```

---

## 📁 Project Structure

```
winter-formula-acid-base/
├── agents/                 # Enterprise agent modules
│   ├── api.py             # FastAPI REST server
│   ├── base.py            # Security, PHI guard, audit trail
│   ├── models.py          # Pydantic data models
│   ├── supervisor.py      # Multi-agent orchestrator
│   ├── workers.py         # Specialized domain workers
│   ├── llm_factory.py     # LLM provider factory
│   ├── learning.py        # Bayesian calibration engine
│   ├── metrics.py         # Prometheus metrics exporter
│   └── streamer.py        # WebSocket telemetry broadcaster
├── tests/                 # Test suite
│   ├── test_winter_formula_acid_base.py
│   └── test_enrichment.py
├── web/                   # Operations console (HTML)
├── cli.py                 # Enterprise CLI entry point
├── winter_acid_base.py    # Core algorithm & CLI
├── enrichment.py          # Enrichment feature modules
├── simulator.py           # High-throughput stress tester
├── pyproject.toml         # Package configuration
├── Dockerfile             # Container build
├── docker-compose.yml     # Container orchestration
└── sample.csv             # Sample input data
```
