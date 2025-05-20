# PriceSage – Project Overview

**"Track. Analyze. Buy Smart."**  
An end-to-end system to track, analyze, alert, and eventually predict Finasteride price trends from local distributors.

---

## 🔍 Problem Statement

Manually checking price fluctuations for Finasteride is inefficient and error-prone. PriceSage automates this process, stores historical data, visualizes trends, sends alerts for smart buying, and will eventually use machine learning to predict optimal purchase windows.

---

## 🧭 Phased Roadmap

### **Stage 1 – MVP Web Scraper**

**Goal**: Automate daily collection of price data for two brands.  
**Tools**: Python, Selenium, pandas, CSV (temp), PostgreSQL (target), Docker  

**Enhancements**:
- Scraper containerized for repeatable execution
- Temporary output to CSV while PostgreSQL schema is validated
- `Makefile` automates dev tasks and container commands
- Unit + smoke tests for selectors and response format

**Milestones**:
- Create scraper module using Selenium
- Write CSV output with timestamp
- Scaffold `pytest`-based test suite
- Define PostgreSQL schema for migration

---

### **Stage 2 – Automated Scheduling**

**Goal**: Enable daily autonomous scraping  
**Tools**: cron, Task Scheduler, AWS Lambda + EventBridge  

**Enhancements**:
- GitHub Actions configured to run test suite on push
- Smoke test ensures scraper still produces usable output
- Scheduler calls Dockerized scraper module

**Milestones**:
- Wrap scraper in script for CLI execution
- Schedule task locally and/or in AWS
- Log job results (success/failure)

---

### **Stage 3 – Data Visualization Dashboard**

**Goal**: Create a user-facing dashboard to explore trends  
**Tools**: Streamlit or Dash, pandas, matplotlib, plotly, Docker  

**Enhancements**:
- Dashboard containerized for local/cloud run
- VSCode Dev Container enables instant launch
- Functional test ensures dashboard loads successfully
- Manual QA for chart rendering, filters, and responsiveness

**Milestones**:
- Build chart views (historical trend, highs/lows)
- Add brand/date filters
- Connect PostgreSQL as data source
- Package in Docker

---

### **Stage 4 – Price Alert Notifications**

**Goal**: Send alerts when prices drop below defined thresholds  
**Tools**: smtplib, Twilio (Free Tier), Pushbullet  

**Enhancements**:
- Alert logic isolated for testing
- Mock tests simulate threshold crossing and alert delivery
- Alert triggers query PostgreSQL directly

**Milestones**:
- Define and persist user-configured thresholds
- Match current prices against rules
- Trigger mock alert send and validate formatting

---

### **Stage 5 – Predictive Price Analysis**

**Goal**: Train a basic ML model to estimate future low-price periods  
**Tools**: scikit-learn, pandas, numpy, matplotlib, Jupyter  

**Enhancements**:
- `/notebooks/` folder for EDA, modeling, and evaluation
- Notebook includes metrics (MAE, RMSE) and result plots
- Model sanity checks: leakage detection, bias, accuracy

**Milestones**:
- Clean data and select relevant features
- Run baseline linear regression or time series forecast
- Evaluate accuracy and highlight limitations
- Visualize predictions vs actual

---

### **Stage 6 – Persistent Data Storage Layer**

**Goal**: Store and manage scraped data in PostgreSQL  
**Tools**: PostgreSQL (Docker), SQLAlchemy or psycopg2  

**Enhancements**:
- Dedicated Docker container for PostgreSQL
- Integration tests confirm inserts/queries
- Migration script to import past CSVs

**Milestones**:
- Define schema (brands, prices, timestamps, discounts)
- Connect scraper to write directly into DB
- Confirm dashboard and alerts work off structured data

---

### **Stage 7 – Documentation & Portfolio Finalization**

**Goal**: Wrap project into a portfolio-grade, replicable package  
**Tools**: Markdown, draw.io, GitHub Pages, GanttProject  

**Enhancements**:
- Final Makefile supports full workflow (scrape, test, dashboard)
- Project covered by automated CI testing
- Final pass of test suite for all modules

**Deliverables**:
- `/docs/` folder with all markdown documentation
- `README.md`, `CHANGELOG.md`, LICENSE, architecture diagram
- Polished GitHub repo with proper structure, badges, and demo instructions

---

## ⚙️ Tools & Technologies

| Purpose            | Tool/Service                            |
|--------------------|------------------------------------------|
| Scraping           | Selenium / Playwright                    |
| Data Analysis      | pandas, numpy                            |
| Visualization      | matplotlib, plotly, Streamlit / Dash     |
| Storage            | PostgreSQL (Dockerized), CSV (temp)      |
| Alerts             | SMTP, Twilio API                         |
| ML (future)        | scikit-learn, Jupyter Notebooks          |
| Automation         | cron, AWS Lambda, EventBridge            |
| Deployment         | Docker, Docker Compose                   |
| Dev Workflow       | Makefile, GitHub Actions, VSCode DevContainers |
| Docs/Diagrams      | Markdown, draw.io                        |

---

## 🧪 Testing Strategy

| Module        | Tests Implemented                           |
|---------------|---------------------------------------------|
| Scraper       | Unit tests (selectors), smoke test          |
| Scheduler     | Job result logger, GitHub Actions validation|
| Dashboard     | Functional load test, manual QA             |
| Alerts        | Logic test with mocks, formatting validation|
| ML Pipeline   | MAE/RMSE checks, leakage detection          |
| PostgreSQL    | Insert/query integration tests, CSV migration validation|

---

## 🧰 Free Project Management Tools

| Tool           | Purpose                             |
|----------------|-------------------------------------|
| Trello         | Kanban task board                   |
| GanttProject   | Timeline and milestone planning     |
| Draw.io        | Architecture & data flow diagrams   |
| Markdown       | All internal documentation format   |
| Git            | Version control & collaboration     |

---

## 💡 Extra Enhancements (Mapped to Stages)

| Enhancement             | Stage Introduced | Why It Matters                             |
|-------------------------|------------------|--------------------------------------------|
| Dockerization           | Stage 1          | Portable, reproducible setup               |
| Makefile                | Stage 1          | Easier commands, cleaner workflow          |
| GitHub Actions          | Stage 2–3        | CI automation, health checks               |
| PostgreSQL (Core DB)    | Stage 1–2        | Structured, queryable, professional storage|
| VSCode Dev Containers   | Stage 3+         | Cloud-ready developer workflow             |
| Jupyter Notebooks       | Stage 5          | Transparent ML/EDA and explainability      |

---

## 🧠 Philosophy

PriceSage isn’t just a utility—it’s a demonstration of good software engineering, modular DevOps, data architecture, and continuous learning. Each layer builds on the last, teaching real-world tools and enabling a complete portfolio-ready project.

> Build with purpose. Learn by doing.