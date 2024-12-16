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
Written by [Stephen Wastling](mailto:stephen.wastling@nhs.net) based on 
some functions from other applications by by Mark White.