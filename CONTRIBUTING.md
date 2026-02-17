# Contributing to Microsoft Fabric Utilities

Thank you for your interest in contributing! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

- Use [GitHub Issues](../../issues) to report bugs or request features
- Search existing issues before creating a new one
- Provide as much detail as possible (Fabric capacity type, runtime version, error messages)

### Submitting Changes

1. **Fork** the repository
2. **Create a feature branch** from `main`

   ```bash
   git checkout -b feature/my-new-utility
   ```

3. **Make your changes** following the guidelines below
4. **Test** your changes in a Fabric workspace
5. **Commit** with clear, descriptive messages

   ```bash
   git commit -m "Add capacity monitoring notebook"
   ```

6. **Push** to your fork and submit a **Pull Request**

### Contribution Guidelines

- **Notebooks** go in `notebooks/` with a descriptive filename (e.g., `fabric-capacity-monitor.ipynb`)
- **Scripts** go in `scripts/python/` or `scripts/powershell/`
- Include a **Markdown header cell** in every notebook explaining purpose, prerequisites, and usage
- Use **Fabric-native libraries** (`sempy`, `mssparkutils`) where possible
- Add **error handling** and **fallback logic** for cross-environment compatibility
- Include **DRY_RUN** mode for any notebook that modifies settings
- Update `README.md` to list new assets in the "What's Included" table

### Code Style

- Python: Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- PowerShell: Follow [PowerShell Best Practices](https://learn.microsoft.com/en-us/powershell/scripting/developer/cmdlet/strongly-encouraged-development-guidelines)
- Use meaningful variable names and inline comments
- Keep cells focused — one logical task per cell

## Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information, see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/)
or contact [opencode@microsoft.com](mailto:opencode@microsoft.com).
