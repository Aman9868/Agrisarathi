import os
from pathlib import Path
list_of_files=[
    ".github/workflows/ci.yaml",
    ".github/workflows/python-publish.yaml",
    "test/__init__.py",
    "test/unit/__init__.py",
    "news_scraper/__init__.py",
    "news_scraper/scraper.py",
    "news_scraper/utils.py",
    "test/unit/unit.py",
    "test/integration/__init__.py",
    "test/integration/integration.py",
    "init_setup.sh",
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    "tox.ini",
    "experiments/experiments.ipynb", 
]
for i in list_of_files:
    file_path=Path(i)
    file_dir,filename=os.path.split(file_path)
    if file_dir!="":
        os.makedirs(file_dir, exist_ok=True)
    if (not os.path.exists(file_path)) or (os.path.getsize(file_path)==0):
        with open(file_path, "w"): 
            pass