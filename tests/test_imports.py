#!/usr/bin/env python3
"""Step-by-step import test"""

print("Testing individual imports...")

try:
    import tkinter as tk
    print("✅ tkinter imported")
except Exception as e:
    print(f"❌ tkinter failed: {e}")

try:
    from tkinter import ttk, messagebox, filedialog
    print("✅ tkinter submodules imported")
except Exception as e:
    print(f"❌ tkinter submodules failed: {e}")

try:
    from tkcalendar import DateEntry
    print("✅ tkcalendar imported")
except Exception as e:
    print(f"❌ tkcalendar failed: {e}")

try:
    from datetime import datetime, timedelta
    print("✅ datetime imported")
except Exception as e:
    print(f"❌ datetime failed: {e}")

try:
    import threading
    print("✅ threading imported")
except Exception as e:
    print(f"❌ threading failed: {e}")

try:
    import os
    print("✅ os imported")
except Exception as e:
    print(f"❌ os failed: {e}")

try:
    import pandas as pd
    print("✅ pandas imported")
except Exception as e:
    print(f"❌ pandas failed: {e}")

try:
    from phase1_enhanced_database import (
        EnhancedTaskManager, MilestoneManager, ResourceManager, ProjectTemplateManager
    )
    print("✅ phase1_enhanced_database imported")
except Exception as e:
    print(f"❌ phase1_enhanced_database failed: {e}")

try:
    from database import get_projects
    print("✅ database module imported")
except Exception as e:
    print(f"❌ database module failed: {e}")
