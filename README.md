# dcmsort

## Synopsis
Sort DICOM files using the Study Root Information Model

## Usage

```bash
dcmsort [-h] [-o] [--version] i
```
- `i`: List of input directories

## Options
- `-h`: display help message
- `-o`: output directory (default ./dcm)
- `--version`: show version

## Description
This package attempts to find and then sort DICOM files into directories using 
the Study Root Information Model i.e. it will create a study directories based 
on study date, study time and patient name of the form: 
`StudyDate.StudyTime-PatientName`
Within each study directory it will create series directories based on series 
number, modality and series description of the form: 
`SeriesNumber-Modality-SeriesDescription`

## Installing
This package requires Python 3.7 or newer. To install the latest version from 
GitHub 

_Note: I strongly recommend creating a venv first, and then installing into it_

```bash
pip install git+https://github.com/SWastling/dcmsort.git
```

## Authors and Acknowledgements
Dr Stephen Wastling 
([stephen.wastling@nhs.net](mailto:stephen.wastling@nhs.net))  based on 
some functions from other applications by Dr Mark White.