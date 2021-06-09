import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytrack",
    version="0.0.1",
    author="Fabian Zills",
    author_email="fabian.zills@web.de",
    description="A python package for parameter and data version control with DVC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zincware/DVC_Op",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'dvc',
        'pytest',
        'PyYAML'
    ],
)
