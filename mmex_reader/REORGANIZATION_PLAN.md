# MMEX Reader Reorganization Plan (OpenSpec Style)

## 1. Specification (Target State)

The `mmex_reader` project shall be organized into modular packages to ensure maintainability and separation of concerns. All source files should be under 1200 lines.

### 1.1. Directory Structure
```
mmex_reader/
├── main.py                     # Application entry point (was mmex_kivy_app_main.py)
├── app_layout.py               # Main layout composition
├── __main__.py                 # Module entry point for python -m mmex_reader
├── ui/                         # [NEW] UI Package
│   ├── __init__.py             # Exports public UI components
│   ├── config.py               # Configuration & Constants (from ui_config_new.py)
│   ├── base.py                 # Base classes (from base_ui_component_new.py)
│   ├── widgets.py              # Generic widgets (DatePicker etc.)
│   ├── transaction.py          # Transaction-related components
│   └── account.py              # Account-related components
├── visualization/              # [NEW] Visualization Package
│   ├── __init__.py             # Exports public visualization components
│   ├── charts.py               # Chart generation logic
│   ├── view.py                 # Kivy UI for visualizations
│   ├── cache.py                # Caching logic
│   └── utils.py                # Helper functions
└── ... (other utility modules like db_utils.py, async_utils.py remain as is)
```

### 1.2. Constraints
- **No temporary files**: Files named `*_new.py`, `*_bak.py`, or `*_refactored.py` shall not exist in the final state.
- **Backward Compatibility**: `ui/__init__.py` and `visualization/__init__.py` must expose the same classes as the current `*_new.py` files to minimize refactoring in `app_layout.py`.

---

## 2. Change Proposal (Execution Plan)

### Phase 1: UI Module Restructuring
**Goal**: Consolidate `*_new.py` UI files into `ui/` package and remove `ui_components.py`.

1.  **Create Package**: `mmex_reader/ui/`
2.  **Migrate Files**:
    - `ui_config_new.py` -> `ui/config.py`
    - `base_ui_component_new.py` -> `ui/base.py`
    - `date_components_new.py` -> `ui/widgets.py` (rename class if needed)
    - `transaction_components_new.py` -> `ui/transaction.py`
    - `account_components_new.py` -> `ui/account.py`
3.  **Create Interface**: `ui/__init__.py` re-exporting all moved components.
4.  **Update Consumers**: Update `app_layout.py` and `mmex_kivy_app.py` to import from `ui.*` instead of `*_new`.
5.  **Cleanup**: Delete `ui_components.py`, `ui_components_new.py`, `ui_components_refactored.py`, `ui_components_backup_original.py`, and source `*_new.py` files.

### Phase 2: Visualization Module Restructuring
**Goal**: Consolidate `visualization_*_new.py` files into `visualization/` package and remove `visualization.py`.

1.  **Create Package**: `mmex_reader/visualization/`
2.  **Migrate Files**:
    - `visualization_charts_new.py` -> `visualization/charts.py`
    - `visualization_tab_new.py` -> `visualization/view.py`
    - `visualization_cache_new.py` -> `visualization/cache.py`
    - `visualization_utils_new.py` -> `visualization/utils.py`
    - `visualization_errors_new.py` -> `visualization/errors.py`
3.  **Create Interface**: `visualization/__init__.py` re-exporting components.
4.  **Update Consumers**: Update imports in `app_layout.py`.
5.  **Cleanup**: Delete `visualization.py`, `visualization_refactored.py`, and source `visualization_*_new.py` files.

### Phase 3: Core App Structure Finalization
**Goal**: Finalize entry point and remove legacy app file.

1.  **Finalize Main**: Rename `mmex_kivy_app_main.py` to `main.py`.
2.  **Create Module Entry**: Add `__main__.py` for `python -m mmex_reader` support.
3.  **Verify Layout**: Ensure `app_layout.py` is self-contained.
4.  **Cleanup**: Delete `mmex_kivy_app.py` (legacy monolithic file) and `mmex_kivy_app_bak.py`.

### Phase 4: Final Validation
1.  **Dependency Check**: Run `python -m compileall mmex_reader` to ensure no missing imports.
2.  **Runtime Check**: Launch application to verify functionality.
