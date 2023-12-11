# ShareCareData Provider Details Extraction

## Introduction

This guide outlines the step-by-step process to extract provider details data from the ShareCareData repository. The data extraction is focused on obtaining information about healthcare providers in the United States.

## Prerequisites

Before you begin, make sure you have the following installed:

- [Git](https://git-scm.com/)
- [Python](https://www.python.org/) (version 3.x recommended)
- [pip](https://pip.pypa.io/en/stable/)

## Clone the Repository

Clone the ShareCareData repository using the following command:

```bash
git clone https://github.com/BhavanSai12/ShareCareData
```
Alternatively, you can download the zip file from this link and extract it to your desired location.

## Install Dependencies
Navigate to the project directory and install the required dependencies:
```bash
pip install openpyxl pandas beautifulsoup4 requests
```

## Update USA.json
Locate the USA.json file in the project directory and update it with the specific state details you want to extract.
Modify the file to include the relevant information for your extraction.

Run the Extraction Script
Execute the extraction script to obtain provider details:
```bash
python main.py
```

## Output
The extracted data will be stored in a suitable format (Excel) in the project directory.
