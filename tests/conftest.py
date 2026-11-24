"""Load the repository root as the mm_modem package during tests."""

import importlib.util
import sys
from pathlib import Path


integration_root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mm_modem",
    integration_root / "__init__.py",
    submodule_search_locations=[str(integration_root)],
)
module = importlib.util.module_from_spec(spec)
sys.modules["mm_modem"] = module
spec.loader.exec_module(module)
