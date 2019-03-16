import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="statuscope",
    version="0.1.1",
    author="Baris Demiray",
    author_email="baris.demiray@gmail.com",
    description="A package to ease log sending to Statuscope",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/statuscope-io/python-package",
    packages=setuptools.find_packages(),
    install_requires=[
        'requests',
        'simplejson'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
