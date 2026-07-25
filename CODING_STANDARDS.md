# Coding Standards & Best Practices

To ensure the codebase remains clean and maintainable across all 4 streams and 30+ contributors, we follow these coding standards. Compliance will be reviewed as part of the Pull Request (PR) process.

## General Principles
- **Readability counts:** Write code for humans first, computers second.
- **KISS (Keep It Simple, Stupid):** Avoid overly complex one-liners. Break complex logic into smaller, testable functions.
- **DRY (Don't Repeat Yourself):** If you find yourself copy-pasting code across notebooks or scripts, move it to the `src/` directory as a shared utility.

## Python Standards (PEP 8)
We follow the standard PEP 8 style guide for Python.
- **Naming Conventions:**
  - Variables & Functions: `snake_case` (e.g., `calculate_parking_utilization`)
  - Classes: `PascalCase` (e.g., `TrafficDataParser`)
  - Constants: `ALL_CAPS` (e.g., `MELBOURNE_CRS = "EPSG:7899"`)
- **Spacing:** Use 4 spaces per indentation level. Do not mix tabs and spaces.

## R Standards (Tidyverse)
We follow the Tidyverse Style Guide for R.
- **Naming Conventions:**
  - Variables & Functions: `snake_case`
  - Constants: `ALL_CAPS`
- **Spacing:** Place a space after commas, and use `<-` for assignment (not `=`).

## Documentation & Docstrings
Every function, class, and shared script in the `src/` directory must be documented.
- **Python:** Use triple-quotes docstrings (Google or NumPy style).
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

## Notebook Hygiene
- **Sequential Execution:** Before committing a notebook, ensure it can run from top to bottom without errors (`Restart Kernel and Run All Cells`). Execution counts should be sequential (e.g., `[1]`, `[2]`, `[3]`).
- **Remove Debugging Artifacts:** Remove `print(df.head())`, large data dumps, or temporary variables before committing, unless they are part of the final narrative or visualization.
- **Use Markdown Cells:** Use headers and markdown cells to explain *why* you are doing something, not just *what* the code does.

## Security: Secrets & Absolute Paths
**Never hardcode credentials, API keys, or personal paths in the repository.**

1. **API Keys & Passwords:** Use environment variables. Store them in a `.env` file locally (do not commit it; it is in `.gitignore`) and load them using `python-dotenv` or `Sys.getenv()`.
2. **Personal/Absolute Paths:** Never use paths like `C:/Users/JohnDoe/Documents/data.csv`. Always use relative paths starting from the project root (e.g., `data/raw/traffic_data.csv`).

## Code Reuse
- **Leverage Existing Libraries:** Before writing complex geometric operations or stats, check `geopandas`, `shapely`, or `scipy`.
- **Share via `src/`:** If streams are working on similar tasks, collaborate to write a shared module in `src/` rather than duplicating code in separate notebooks.
