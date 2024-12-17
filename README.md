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
the Study Root Information Model i.e. it makes: 
 - Patient level directories based on the patient's family and given names and 
 their Patient ID of the form: `FamilyName_GivenName-PatientID`
 - Study level directories based on the study date, study time, study ID and 
 study description and patient name of the form: 
 `StudyDate.StudyTime-StudyID-StudyDescription`
 - Series level directories based on the series number, modality and series 
 description of the form: `SeriesNumber-Modality-SeriesDescription`

The `SOPInstanceUID` with the suffix `.dcm` is used as the filename.

## Installing
1. Create a new virtual environment in which to install `dcmsort`:

    ```bash
    uv venv dcmsort-venv
    ```
   
2. Activate the virtual environment:

    ```bash
    source dcmsort-venv/bin/activate
    ```

4. Install using `uv pip`:
    ```bash
    uv pip install git+https://github.com/SWastling/dcmsort.git
    ```
   
> [!TIP]
> You can also run `dcmsort` without installing it using 
>[uvx](https://docs.astral.sh/uv/guides/tools/) i.e. with the command 
>`uvx --from  git+https://github.com/SWastling/dcmsort.git dcmsort`

## License
See [MIT license](./LICENSE)

## Authors and Acknowledgements
Written by [Stephen Wastling](mailto:stephen.wastling@nhs.net) using some 
functions from other applications by by Mark White.