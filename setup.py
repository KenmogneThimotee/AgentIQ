import os
from setuptools import setup, find_packages

setup(
    name="your-project-name",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add your project dependencies here
    ],
    python_requires=">=3.6",
    author="Your Name",
    author_email="your.email@example.com",
    description="A short description of your project",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
) 