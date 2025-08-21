<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

- [x] Verify that the copilot-instructions.md file in the .github directory is created.

- [x] Clarify Project Requirements
      ETF Portfolio Dashboard with HERC/HRP algorithms, Streamlit interface, real-time data download

- [x] Scaffold the Project
      Python project with Streamlit dashboard for financial analysis

- [x] Customize the Project
      Implement HERC/HRP algorithms, ETF data processing, interactive dashboard

- [x] Install Required Extensions
      Install Python and related extensions if needed

- [x] Compile the Project
      Install dependencies and verify setup

- [x] Create and Run Task
      Create Streamlit run task

- [x] Launch the Project
      Launch Streamlit dashboard

- [x] Ensure Documentation is Complete
      Complete README and documentation

## ETF Portfolio Dashboard

A professional dashboard for ETF portfolio analysis using HERC and HRP algorithms.

### Features Implemented:

- ✅ Real-time ETF data download from Yahoo Finance
- ✅ HERC (Hierarchical Equal Risk Contribution) algorithm
- ✅ HRP (Hierarchical Risk Parity) algorithm
- ✅ Interactive Streamlit dashboard
- ✅ Performance metrics calculation
- ✅ Risk analysis and drawdown charts
- ✅ Portfolio weights visualization
- ✅ Data export functionality
- ✅ Professional UI with minimal design

### Usage:

1. Run `streamlit run app.py` or use the task runner
2. Select ETFs from the sidebar
3. Choose analysis period
4. Download historical data
5. Run optimization (HERC or HRP)
6. Analyze results in the interactive dashboard

### Architecture:

- `app.py`: Main Streamlit application
- `src/data_loader.py`: ETF data management
- `src/portfolio_optimizer.py`: HERC/HRP algorithms
- `src/metrics.py`: Performance calculations
- `src/utils.py`: Visualization utilities
