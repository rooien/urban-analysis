## Description
<!-- Provide a brief summary of the changes and the business problem or stream task it addresses. -->

## Type of Change
- [ ] New feature (adds functionality)
- [ ] Bug fix (fixes an issue)
- [ ] Refactoring / Code cleanup
- [ ] Documentation update

## Checklist
Please ensure all of the following are checked before requesting a review.

### Coding Standards
- [ ] Code follows PEP 8 (Python) or Tidyverse (R) style guidelines.
- [ ] Functions and shared scripts include proper docstrings/documentation.
- [ ] Notebooks run sequentially without errors and have been cleared of large debug outputs.
- [ ] No secrets, API keys, or absolute file paths are included (relative paths used throughout).
- [ ] Code avoids duplication and leverages existing libraries or `src/` modules where possible.

### Git & Collaboration
- [ ] Branch follows the naming convention (`feature/initials/description` or `bugfix/initials/description`).
- [ ] Branch has been rebased against the latest `main`.
- [ ] **I confirm there are no merge conflicts** (PRs with conflicts will not be approved).

## Testing & Verification
<!-- Describe how you tested your changes. Include any plots or terminal outputs if relevant. -->
- [ ] Notebook/Script runs successfully from top to bottom.
- [ ] Verified spatial data outputs (e.g., correct CRS reprojection).
