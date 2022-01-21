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
1. Create a directory to store the package e.g.:

    ```bash
    mkdir dcmsort
    ```

2. Create a new virtual environment in which to install `dcmsort`:

    ```bash
    python3 -m venv dcmsort-env
    ```
   
3. Activate the virtual environment:

    ```bash
    source dcmsort-env/bin/activate
    ```

4. Upgrade `pip` and `build`:

    ```bash
    pip install --upgrade pip
    pip install --upgrade build
    ```

5. Install using `pip`:
    ```bash
    pip install git+https://github.com/SWastling/dcmsort.git
    ```

## License
See [MIT license](./LICENSE)


## Authors and Acknowledgements
Dr Stephen Wastling 
([stephen.wastling@nhs.net](mailto:stephen.wastling@nhs.net))  based on 
some functions from other applications by by Mark White 
([mark@celos.net](mailto:mark@celos.net)).