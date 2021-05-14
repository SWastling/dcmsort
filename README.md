# dcmsort

## Synopsis
Sort DICOM files into study/series directories

## Usage

```bash
dcmsort.py [-h] [-o] [--any-version] i
```
- `i`: List of input directories

## Description
This script attempts to find and then sort DICOM files into directories based on 
study date, study time, patient name, series number and series description i.e. 
output directory names will be of the form:

`StudyDate.StudyTime-PatientName/SeriesNumber-Modality-SeriesDescription`

The version of `dcmsort`, as stored by `git`, and of the `pydicom` library are 
verified at runtime

## Options
- `-h`: display help message
- `-o`: output directory (default ./dcm)
- `--any-version`: don't abort if version checks fail

## Requirements
__Software__
- `git`
- `python3`

__Python libraries__
- `argparse`
- `os`
- `pathlib`
- `pydicom` (version 2.0.0)
- `re`
- `shutil`
- `subprocess`
- `sys`   

__Testing__
- `pytest` 

## Updating Code

1. Make a local copy of the repository
   ```bash
    cp -r /store/apps/dcmsort your_directory
   ```
2. Make changes to the python code as required

3. Update the necessary unit tests in `test_dcmsort.py` and 
the data stored in `test_data` directory

4. Run the unit tests and check they pass

    ```bash
    pytest-3 -v
    ```

5. Commit changes to git repository

    ```bash
    git commit -a
    ```

6. Tag the latest commit as a release

    ```bash
    git tag -a release-1.0.0 -m "release 1.0.0"
    ```

7. Push the changes to the github repository
    ```bash
    git push -u origin master --follow-tags
    ```

8. Copy the modified directory back into `/store/apps`

    ```bash
    sudo cp -r your_directory /store/apps/dcmsort
    ```
## Authors and Acknowledgements
Dr Stephen Wastling 
([stephen.wastling@nhs.net](mailto:stephen.wastling@nhs.net))  based on 
functions from other applications by Dr Mark White.