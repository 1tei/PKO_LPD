from setuptools import setup, find_packages

setup(
    name="my_project",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "timefold==1.17.0b0",
        "fastapi==0.111.0",
        "pydantic==2.7.3",
        "uvicorn==0.30.1",
        "pytest==8.2.2"
    ],
)