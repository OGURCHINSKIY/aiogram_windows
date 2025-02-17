import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aiogram_windows",
    version="0.0.1a",
    author="ogurchinskiy",
    description="windows for aiogram",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OGURCHINSKIY/aiogram_windows",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)