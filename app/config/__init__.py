import os
import importlib.util
import sys

# Get the current module (app.config)
current_module = sys.modules[__name__]

# Load default settings
from . import settings

# Expose default settings
for setting in dir(settings):
    if setting.isupper():
        setattr(current_module, setting, getattr(settings, setting))

# Check for and load local settings override
local_settings_path = os.path.join(os.path.dirname(__file__), 'settings_local.py')

if os.path.exists(local_settings_path):
    spec = importlib.util.spec_from_file_location('settings_local', local_settings_path)
    settings_local = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings_local)

    # Override with local settings
    for setting in dir(settings_local):
        if setting.isupper():
            setattr(current_module, setting, getattr(settings_local, setting))