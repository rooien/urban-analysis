# Victoria Urban Planning - Urban Streetscape Intervention Analysis

Welcome to the **Urban Streetscape Intervention Analysis** repository. This project is a SIT Capstone "Chameleon Project" in partnership with **Infrastructure Victoria**.

---

## 📖 Table of Contents
1. [Project Overview](#-project-overview)
2. [Business Problem & Research Question](#-business-problem--research-question)
3. [Stream Structure](#-stream-structure)
4. [Tech Stack](#-tech-stack)
5. [Data Sources & CRS Warning](#-data-sources--crs-warning)
6. [Directory Structure](#-directory-structure)
7. [Installation & Setup](#-installation--setup)
8. [Git Workflow & Collaboration Guide](#-git-workflow--collaboration-guide)

---

## 🎯 Project Overview
Infrastructure Victoria is an independent advisory body providing evidence-based research to the Victorian Government. This project aims to evaluate the real-world impacts of streetscape interventions—such as new bike lanes, road reallocations, and pedestrian upgrades—on transport efficiency, sustainability, and livability.

The goal is to develop a **repeatable analytical framework** that delivers clear, decision-ready insights to inform future infrastructure investments.

**Key Stakeholders & Team:**
- **Product Owners (POs):** Matthew Raisbeck & Danielle Rebbechi (Infrastructure Victoria)
- **Mentor:** Scott West
- **Company Director:** Sing
- **Project Management:** Microsoft Planner
- **Communication:** Microsoft Teams

---

## 📈 Business Problem & Research Question
Understanding what happens to businesses, parking utilization, and movement patterns when road space is reallocated is complex. This project leverages publicly available datasets to provide data-driven evidence of these impacts, accounting for challenges like COVID-19 behavioral shifts and stakeholder sentiment.

### Primary Research Question
> **"How does parking use change with bike lanes constructed?"**

- **Null Hypothesis:** There has been no change in parking capacity or utilization.
- **Scope:** Metropolitan Melbourne and Regional Victoria, with a priority on **protected bike lanes** datasets.
- **Objective:** Understand how many people are using parking spaces before and after bike lane interventions, and the economic/social impacts of those changes.

---

## 👥 Stream Structure
To tackle this problem comprehensively without creating silos, the project is divided into four stakeholder-focused streams:

1. **Cycling and public transport mode shift**
2. **Traffic volumes and parking**
3. **Pedestrian counts**
4. **Temporal patterns**

> [!IMPORTANT]
> **Key Alignment Rule:** All streams must share the same foundational tech stack and methodology to avoid sprawl and ensure the final insights are cohesive.

---

## 🛠 Tech Stack
- **Core Languages:** Python and R (both confirmed).
- **Python Libraries:** pandas, numpy, statsmodels, geopandas, shapely, matplotlib, plotly (and JupyterLab for interactive development).
- **Visualization:** Power BI or Tableau (to be confirmed with POs), with the potential to build a custom UI (e.g., React) if required.
- **GIS Tools:** QGIS or ArcGIS for spatial analysis.

---

## 📊 Data Sources & CRS Warning
We will be utilizing publicly available datasets from the following sources:
- Data.vic.gov.au
- Open Data Transport Victoria (opendata.transport.vic.gov.au)
- VicRoads datasets
- Public Transport Victoria (PTV) data
- Google Maps / Street View / aerial imagery

> [!WARNING]
> **Coordinate Reference System (CRS) Reprojection:**
> Datasets from different sources (e.g., VicRoads vs. PTV) are unlikely to share the same spatial coordinate systems. You **must** define and document CRS reprojections in your notebooks/scripts. Do not assume all datasets share the same ground truth.

*(Note: The ABS Census data releases in August. To avoid mid-sprint disruption, population data integration will be deferred until after the release. In the meantime, use proxy labeling approaches where ground truth is absent, documenting the proxy methods clearly in the `src/` directory.)*

---

## 📁 Directory Structure
To keep the repository organized and facilitate code sharing across the 30+ team members, please adhere to the following structure:

```
Victoria-Urban-Planning/
├── data/
│   ├── raw/            # Untouched, original datasets (do NOT commit large files)
│   └── processed/      # Cleaned and transformed datasets ready for analysis
├── notebooks/          # Jupyter notebooks organized by stream or task
├── src/                # Shared Python/R modules and utilities (to avoid rewriting code)
├── project_description.md
├── requirements.txt
└── README.md
```

---

## 🚀 Installation & Setup
Follow these steps to set up your local development environment.

### 1. Clone the Repository
```bash
git clone https://github.com/Chameleon-company/Victoria-Urban-Planning.git
cd Victoria-Urban-Planning
```

### 2. Set Up a Python Virtual Environment
*(Highly recommended to keep your dependencies isolated)*

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch JupyterLab (Optional but recommended)
```bash
jupyter lab
```

---

## 🤝 Git Workflow & Collaboration Guide
With 30+ contributors, maintaining a clean and working `main` branch is critical. Please follow this strict workflow for all changes.

### The Golden Rules
1. **Never commit directly to the `main` branch.**
2. **Use the Branch Naming Convention.**
3. **Resolve all merge conflicts locally.** PRs with conflicts will **not** be approved or merged.

### Branch Naming Convention
Branches must be named using the following format:
- `feature/<your-initials>/<descriptive-name>`
- `bugfix/<your-initials>/<descriptive-name>`

**Examples:**
- `feature/sz/add-traffic-pipeline`
- `bugfix/sz/fix-crs-reprojection`

### Step-by-Step Workflow

#### Step 1: Start Fresh
Always create your branch from the latest version of `main`.
```bash
git checkout main
git pull origin main
git checkout -b feature/<your-initials>/<descriptive-name>
```

#### Step 2: Work and Commit
Make your changes, then add and commit them with a clear message.
```bash
git add .
git commit -m "Add traffic volume parsing for Metro Melbourne"
```

#### Step 3: Rebase Against `main`
Before pushing, you **must** rebase your branch on top of the latest `main` to pull in changes from other streams and resolve conflicts locally.
```bash
git fetch origin
git rebase origin/main
```

> [!NOTE]
> **Handling Merge Conflicts During Rebase:**
> If Git pauses and reports conflicts, open the conflicting files, resolve the issues, and run:
> ```bash
> git add <fixed-files>
> git rebase --continue
> ```

#### Step 4: Push and Open a Pull Request (PR)
Once the rebase is complete, push your branch and open a PR on GitHub.
```bash
git push -u origin <your-branch-name>
```
*(If you have already pushed your branch previously before rebasing, you will need to force-push using `git push --force-with-lease origin <your-branch-name>`.)*

#### Step 5: Review and Merge
Assign reviewers from your stream and tag the POs/Mentor if needed. Once approved and checks pass, your PR can be merged into `main`.
