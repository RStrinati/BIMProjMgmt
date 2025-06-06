# ui/__init__.py
# Initializes the UI module and exposes a helper to launch the
# tabbed interface.  The individual tab builders live in the
# submodules within this package.

from .base_layout import build_main_ui
from .tab_project import build_project_tab
from .tab_data_imports import build_data_imports_tab
from .tab_review import build_review_tab
from .tab_validation import build_validation_tab


def launch_ui():
    """Convenience helper used by the demo ``app-sss.py`` script."""

    root, notebook, tabs, status_var = build_main_ui()
    build_project_tab(tabs["Project Setup"], status_var)
    build_data_imports_tab(tabs["Data Imports"], status_var)
    build_review_tab(tabs["Review Management"], status_var)
    build_validation_tab(tabs["Validation & Results"], status_var)

    root.mainloop()

