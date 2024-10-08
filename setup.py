from setuptools import setup,find_packages
from typing import List
with open('README.md','r',encoding='utf-8') as f:
    long_description = f.read()

__version__='0.0.1'
REPO_NAME='Agrisarathi'
PKG_NAME='Agrisarathinewsscrapper'
AUTHOR_USER_NAME='accessassist-admin'
AUTHOR_EMAIL = "keshabchandra.mandal@accessassist.in"
setup(
    name=PKG_NAME,
    version=__version__,
    author=AUTHOR_USER_NAME,
    author_email=AUTHOR_EMAIL,
    description="A python package for scrapping Agricultural News Data from sources like ABP News,Krishi Jagran,Krishi Jagat,Kisantak",
    long_description=long_description,
    long_description_content="text/markdown",
    url=f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}",
    project_urls={
        "Bug Tracker": f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}/issues",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "tldextract",
    ],
    )
