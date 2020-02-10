import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    setup_requires=['setuptools>=36.0'],
)
