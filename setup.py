import setuptools
from pathlib import Path

with open("README.md", "r") as fh:
    long_description = fh.read()


file_path = Path(__file__).absolute().parent / "requirements.txt"
requirements = file_path.read_text().split("\n")

setuptools.setup(
    name="py-track",
    version="0.0.1",
    author="Fabian Zills",
    author_email="fabian.zills@web.de",
    description="A python package for parameter and data version control with DVC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zincware/py-track",
    download_url="https://github.com/zincware/py-track/archive/beta.tar.gz",
    keywords=['dvc', 'machine learning', 'parameter tracking'],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=requirements
)
