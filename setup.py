import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zntrack",
    version="0.1.2",
    author="Zincware",
    author_email="zincwarecode@gmail.com",
    description="A python package for parameter and data version control with DVC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zincware/ZnTrack",
    download_url="https://github.com/zincware/ZnTrack/archive/beta.tar.gz",
    keywords=["dvc", "machine learning", "parameter tracking"],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=["dvc", "PyYAML"],
)
