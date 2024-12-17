"""Sort DICOM files using the Study Root Information Model"""

import argparse
import os
import pathlib
import re
import shutil
import sys

import importlib.metadata
import pydicom

# useful patterns for simplifying study and series descriptions
under = re.compile(r"[\s/^]")
remove = re.compile(r"[^A-Za-z0-9_-]")

__version__ = importlib.metadata.version("dcmsort")


def shorten_path(fp):
    """
    Shorten a pathlib.Path object to a 40-character string so it's easier to display on stdout.

    :param fp: path
    :type fp: pathlib.Path
    :return: truncated path
    :rtype: str
    """
    fp_str = str(fp)
    if len(fp_str) >= 40:
        fp_str = fp_str[0:17] + "..." + fp_str[-20:]

    return fp_str


def progress(count, total, message=None):
    """
    Print percentage progress to stdout during loop.

    :param count: Loop counter
    :type count: int
    :param total: Total number of iterations of loop
    :type total: str
    :param message: Optional message to accompany % progress
    :type message: str
    """
    if message is None:
        message = ""

    percents = round(100.0 * count / float(total), 1)

    if total == count:
        print("%s [%3d%%]" % (message, percents))
    else:
        print("%s [%3d%%]" % (message, percents), end="\r")


def simplify_description(desc):
    """
    Simplify study or series description.

    :param desc: description
    :type desc: str
    :return: simplified description
    :rtype: str
    """
    s = under.subn("_", desc)[0]
    s = remove.subn("", s)[0]
    return s


def sort_dicom(out_dp, in_fps):
    """
    Sort DICOM files into directories.

    :param out_dp: output directory
    :type out_dp: pathlib.Path
    :param in_fps: list of DICOM files to sort
    :type in_fps: list
    """
    for ctr, in_fp in enumerate(in_fps, 1):
        # Update progress bar
        progress(
            ctr,
            len(in_fps),
            "* sorting %d DICOM files" % len(in_fps),
        )

        # Load the DICOM file
        ds = pydicom.dcmread(in_fp, stop_before_pixels=True)

        # Ignore DICOMDIR files i.e. Media Storage Directory Storage
        sop_class = ds.file_meta.get("MediaStorageSOPClassUID", None)
        if sop_class == "1.2.840.10008.1.3.10":
            continue

        # Extract the relevant metadata
        PatientName = ds.get("PatientName", "unknownPatientName")
        PatientID = ds.get("PatientID", "unknown_PatientID")
        StudyDate = ds.get("StudyDate", 20000101)
        StudyTime = ds.get("StudyTime", 120000.00).split(".")[0]
        StudyID = ds.get("StudyID", "unknown_StudyID")
        StudyDescription = ds.get("StudyDescription", "unknown_StudyDescription")
        SeriesNumber = ds.get("SeriesNumber", 1)
        Modality = ds.get("Modality", "unknown_Modality")
        SeriesDescription = ds.get("SeriesDescription", "SeriesDescription")
        SOPInstanceUID = ds.get("SOPInstanceUID", "unknown_SOPInstanceUID")

        cleanStudyDescription = simplify_description(StudyDescription)
        cleanSeriesDescription = simplify_description(SeriesDescription)

        # create the sorted filepath
        out_fp = (
            out_dp
            / f"{PatientName.family_name.upper()}_{PatientName.given_name.capitalize()}-{PatientID}"
            / f"{StudyDate}.{StudyTime}-{StudyID}-{cleanStudyDescription}"
            / f"{SeriesNumber:05}-{Modality}-{cleanSeriesDescription}"
            / f"{SOPInstanceUID}.dcm"
        )

        # copy the file to the new hierarchical directory structure
        pathlib.Path.mkdir(out_fp.parent, parents=True, exist_ok=True)
        shutil.copy(in_fp, out_fp)


def scan_for_dicom(dp, to_sort=[]):
    """
    Scan a directory recursively for DICOM files.

    :param dp: Directory to scan
    :type dp: pathlib.Path
    :param to_sort: List of DICOM file to append to
    :type to_sort: list
    :return: List of DICOM filepaths
    :rtype: list
    """
    for root, _, files in os.walk(dp):
        for file_counter, fn in enumerate(files, 1):
            fp = pathlib.Path(root) / fn
            if pydicom.misc.is_dicom(fp):
                to_sort.append(fp)

    return to_sort


def main():
    parser = argparse.ArgumentParser(
        description="Sort DICOM files into directories using the Study Root "
        "Information Model i.e. 'FamilyName_GivenName-PatientID/"
        "StudyDate.StudyTime-StudyID-StudyDescription/"
        "SeriesNumber-Modality-SeriesDescription/SOPInstanceUID.dcm'"
    )

    parser.add_argument(
        "i",
        help="list of input directories to search for DICOM files",
        nargs="+",
        type=pathlib.Path,
    )

    parser.add_argument(
        "-o",
        default="./dcm",
        help="output directory (default %(default)s)",
        metavar="output_folder",
        type=pathlib.Path,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()

    out_dir = args.o.resolve()

    to_sort = []
    for item in args.i:
        print("* scanning for DICOM files in %s" % shorten_path(item))
        to_sort = scan_for_dicom(item, to_sort)

    if len(to_sort) > 0:
        sort_dicom(out_dir, to_sort)


if __name__ == "__main__":  # pragma: no cover
    main()
