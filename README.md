# Victoria Urban Planning - Urban Streetscape Intervention Analysis

This repository is for the SIT Capstone "Chameleon Project" in partnership with Infrastructure Victoria.

## Table of Contents
1. Project Overview
2. Business Problem & Research Question
3. Stream Structure
4. Tech Stack
5. Data Sources & CRS Warning
6. Directory Structure
7. Installation & Setup
8. Git Workflow & Collaboration Guide
9. Coding Standards

## Project Overview
Infrastructure Victoria is an independent advisory body providing evidence-based research to the Victorian Government. This project evaluates the real-world impacts of streetscape interventions (like new bike lanes, road reallocations, and pedestrian upgrades) on transport efficiency, sustainability, and livability. 

The goal is to develop a repeatable analytical framework to deliver clear, decision-ready insights for future infrastructure investments.

**Team & Roles:**
- **Product Owners:** Matthew Raisbeck & Danielle Rebbechi (Infrastructure Victoria)
- **Mentor:** Scott West
- **Company Director:** Sing
- **Tools:** Microsoft Teams (communication) and Microsoft Planner (project management)

## Business Problem & Research Question
Understanding the impacts on businesses, parking utilization, and movement patterns when road space is reallocated is complex. We are leveraging public datasets to provide data-driven evidence of these impacts, accounting for challenges like COVID-19 behavioral shifts.

**Research Question:**
> How does parking use change with bike lanes constructed?

- **Null Hypothesis:** There has been no change in parking capacity or utilization.
- **Scope:** Metropolitan Melbourne and Regional Victoria, prioritizing protected bike lanes datasets.
- **Objective:** Understand how many people are using parking spaces before and after bike lane interventions, and the economic/social impacts of those changes.

## Stream Structure
The project is divided into four stakeholder-focused streams:
1. Cycling and public transport mode shift
2. Traffic volumes and parking
3. Pedestrian counts
4. Temporal patterns

**Note:** All streams must share the same foundational tech stack and methodology to avoid sprawl and ensure the final insights are cohesive.

## Tech Stack
- **Languages:** Python and R (both confirmed)
- **Python Libraries:** pandas, numpy, statsmodels, geopandas, shapely, matplotlib, plotly (and JupyterLab)
- **Visualization:** Power BI or Tableau (to be confirmed with POs), or potentially a custom React UI
- **GIS Tools:** QGIS or ArcGIS

## Data Sources & CRS Warning
We are using public datasets from:
- Data.vic.gov.au
- Open Data Transport Victoria (opendata.transport.vic.gov.au)
- VicRoads datasets
- Public Transport Victoria (PTV) data
- Google Maps / Street View / aerial imagery

**Important CRS Warning:**
Datasets from different sources (e.g., VicRoads vs. PTV) are unlikely to share the same spatial coordinate systems (CRS). You must define and document CRS reprojections in your notebooks/scripts. Do not assume all datasets share the same ground truth.

*Note: ABS Census data releases in August. Population data integration will be deferred until after the release to avoid mid-sprint disruption. Use proxy labeling approaches where ground truth is absent, and document proxy methods in the `src/` directory.*

## Directory Structure
Please adhere to this structure to keep the repo organized and facilitate code sharing:

```
Victoria-Urban-Planning/
├── data/
│   ├── raw/            # Original, untouched datasets
│   └── processed/      # Cleaned and transformed datasets
├── notebooks/          # Notebooks organized by stream or task
├── src/                # Shared Python/R modules and utilities
├── project_description.md
├── requirements.txt
├── CODING_STANDARDS.md
└── README.md
```

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Chameleon-company/Victoria-Urban-Planning.git
   cd Victoria-Urban-Planning
   ```

2. **Set Up Python Virtual Environment:**
   - On macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - On Windows:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch JupyterLab:**
   ```bash
   jupyter lab
   ```

## Git Workflow & Collaboration Guide

### Rules
1. Never commit directly to the `main` branch.
2. Use the Branch Naming Convention.
3. PRs with merge conflicts will not be approved or merged. You are responsible for resolving conflicts locally.

### Branch Naming Convention
Branches must use the following format:
- `feature/<your-initials>/<description>`
- `bugfix/<your-initials>/<description>`

Examples:
- `feature/sz/add-traffic-pipeline`
- `bugfix/sz/fix-crs-reprojection`

### Step-by-Step Workflow

**1. Start Fresh**
Always create your branch from the latest `main`:
```bash
git checkout main
git pull origin main
git checkout -b feature/<your-initials>/<description>
```

**2. Work and Commit**
Make your changes, then add and commit with a clear message:
```bash
git add .
git commit -m "Add traffic volume parsing for Metro Melbourne"
```

**3. Rebase Against `main`**
Before pushing, you must rebase on top of the latest `main` to pull in changes and resolve conflicts locally:
```bash
git fetch origin
git rebase origin/main
```
If there are merge conflicts, Git will pause. Open the files, fix the issues, and run:
```bash
git add <fixed-files>
git rebase --continue
```

**4. Push and Open a PR**
Push your branch and open a PR on GitHub:
```bash
git push -u origin <your-branch-name>
```
*(If you already pushed before rebasing, use `git push --force-with-lease origin <your-branch-name>`)*

**5. Review and Merge**
Assign reviewers from your stream. Once approved, the PR can be merged.

## Coding Standards
All contributors are expected to follow our shared coding standards covering PEP 8, Tidyverse, docstrings, and security. Please read the full [Coding Standards & Best Practices Guide](CODING_STANDARDS.md) before writing code.
