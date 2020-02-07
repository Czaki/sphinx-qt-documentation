import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    install_requires=['sphinx'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
)
