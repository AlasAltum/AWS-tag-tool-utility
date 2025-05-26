from setuptools import setup, find_packages

setup(
    name="aws-tagging-tool",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'boto3>=1.26.0',
        'python-dotenv>=0.19.0',
        'colorama>=0.4.4',
    ],
    entry_points={
        'console_scripts': [
            'aws-tagging-tool=tagging_tool:main',
        ],
    },
    python_requires='>=3.7',
    author="Alonso Utreras",
    author_email="alonso.utreras@arquitectosdigital.com",
    description="A tool for automatically tagging AWS resources",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aws-tagging-tool",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
