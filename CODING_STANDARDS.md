# Coding Standards & Best Practices

Welcome to the Victoria Urban Planning project! To ensure our codebase remains clean, readable, and maintainable across all 4 streams and 30+ contributors, we adhere to the following coding standards.

> [!IMPORTANT]
> **PR Checks:** Compliance with these standards will be reviewed by mentors and stream leads as part of the Pull Request (PR) process. Code that severely violates these standards will need to be refactored before being approved and merged into `main`.

---

## 📖 Table of Contents
1. [General Principles](#general-principles)
2. [Python Standards (PEP 8)](#python-standards-pep-8)
3. [R Standards (Tidyverse)](#r-standards-tidyverse)
4. [Documentation & Docstrings](#documentation--docstrings)
5. [Notebook Hygiene](#notebook-hygiene)
6. [Security: No Secrets in Code](#security-no-secrets-in-code)
7. [Code Reuse & Library Usage](#code-reuse--library-usage)

---

## 🌟 General Principles
- **Readability counts:** Write code for humans first, computers second. Use descriptive names and comments.
- **KISS (Keep It Simple, Stupid):** Avoid overly complex one-liners. Break complex logic into smaller, testable functions.
- **DRY (Don me Repeat Yourself):** If you find yourself copy-pasting code across notebooks or scripts, move it to the `src/` directory as a shared utility.

---

## 🐍 Python Standards (PEP 8)
We follow the standard [PEP 8](https://peps.python.org/pep-0008/) style guide for Python.
- **Naming Conventions:**
  - Variables & Functions: `snake_case` (e.g., `calculate_parking_utilization`, `raw_data_path`)
  - Classes: `PascalCase` (e.g., `TrafficDataParser`)
  - Constants: `ALL_CAPS` (e.g., `MELBOURNE_CRS = "EPSG:7899"`)
- **Spacing:** Use 4 spaces per indentation level. Do not mix tabs and spaces.

---

## 📊 R Standards (Tidyverse)
We follow the [Tidyverse Style Guide](https://style.tidyverse.org/) for R.
- **Naming Conventions:**
  - Variables & Functions: `snake_case` (e.g., `calculate_parking_utilization`, `raw_data_path`)
  - Constants: `ALL_CAPS`
- **Spacing:** Place a space after commas, and use `<-` for assignment (not `=`).

---

## 📝 Documentation & Docstrings
Every function, class, and shared script in the `src/` directory must be documented.
- **Python:** Use triple-quotes docstrings explaining the purpose, parameters, and return values (Google or NumPy style).
  ```python
  def reproject_dataframe(df: pd.DataFrame, target_crs: str) -> pd.DataFrame:
      """
      Reprojects a GeoDataFrame to the specified Target CRS.

      Parameters:
          df (pd.DataFrame): The input GeoDataFrame.
          target_crs (str): The CRS string (e.g., 'EPSG:7899').

      Returns:
          pd.DataFrame: The reprojected GeoDataFrame.
      """
      return df.to_crs(target_crs)
  ```
- **R:** Use `roxygen2` comments (`#'`) for functions.

---

## 📓 Notebook Hygiene
Notebooks are great for exploration, but can easily become messy and hard to version control.
- **Sequential Execution:** Before committing a notebook, ensure it can run from top to bottom without errors (`Restart Kernel and Run All Cells`). Execution counts should be sequential (e.g., `[1]`, `[2]`, `[3]`).
- **Remove Debugging Artifacts:** Remove `print(df.head())`, large data dumps, or temporary variables before committing, unless they are part of the final narrative or visualization.
- **Use Markdown Cells:** Use headers and markdown cells to explain *why* you are doing something, not just *what* the code does. A notebook should read like a report.

---

## 🔒 Security: No Secrets & Absolute Paths
**Never hardcode credentials, API keys, or personal paths in the repository.**

### 1. API Keys & Passwords
Use environment variables to store sensitive information (e.g., Google Maps API keys).
- Store them in a `.env` file locally.
- **Do not commit the `.env` file.** (It is already added to our `.gitignore`).
- Use the `python-dotenv` package or R's `Sys.getenv()` to load them.

### 2. Personal/Absolute Paths
Never use absolute file paths like `C:/Users/JohnDoe/Documents/data.csv`. These will break when your teammates try to run your code.
- **Always use relative paths** starting from the project root.
- Example: `pd.read_csv("data/raw/traffic_data.csv")`

---

## ♻️ Code Reuse & Library Usage
- **Leverage Existing Libraries:** Before writing a complex geometric intersection function or statistical test, check the documentation for `geopandas`, `shapely`, `scipy`, or `statsmodels`. Chances are, a well-optimized, built-in function already exists.
- **Share via `src/`:** If two streams are working on similar tasks (e.g., CRS reprojection, reading specific PTV formats, proxy labeling), collaborate to write a shared module in the `src/` directory rather than duplicating code in separate notebooks.

---

*If you have any questions about these standards or need help refactoring your code, please reach out in the Microsoft Teams channel or ask your stream lead.*
