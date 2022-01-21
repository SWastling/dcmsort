"""Sort DICOM files using the Study Root Information Model."""

import argparse
import os
import pathlib
import re
import shutil
import sys

import importlib_metadata as metadata
import pydicom

# useful patterns for simplifying names
under = re.compile(r"[\s/^]")
underb = re.compile(r"^_+")
underrep = re.compile(r"_{2,}")
undere = re.compile(r"_+$")
remove = re.compile(r"[^A-Za-z0-9_-]")
removep = re.compile(r"[^A-Za-z0-9,.;:=%^&()_+-]")

try:
    __version__ = metadata.version("dcmsort")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Sort DICOM files into directories using the Study Root "
        "Information Model e.g. StudyDate.StudyTime-PatientName/"
        "SeriesNumber-Modality-SeriesDescription"
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

    for item in args.i:
        print("* scanning for DICOM files in %s" % shorten_path(item))
        to_sort = scan_for_dicom(item)

        if len(to_sort) > 0:
            sort_dicom(out_dir, to_sort)


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


def simplify_under(name):
    """
    Turn spaces and carets into underscores, and tidy up repeated or leading/trailing underscores.

    :param name: string to be cleaned of spaces, carets and repeated underscores
    :type name: str
    :return: s - simplified name
    :rtype: str
    """
    s = under.subn("_", name)[0]
    s = underb.subn("", s)[0]
    s = undere.subn("", s)[0]
    s = underrep.subn("_", s)[0]
    s = remove.subn("", s)[0]

    return s


def simplify_series(desc):
    """
    Simplify series description.

    :param desc: series description
    :type desc: str
    :return: simplified series description
    :rtype: str
    """
    s = under.subn("_", desc)[0]
    s = remove.subn("", s)[0]
    return s


def default_series_dir(series_num, modality, clean_desc):
    """
    Generate series directory name.

    :param series_num: series number
    :type series_num: int
    :param modality: DICOM modality e.g. MR
    :type modality: str
    :param clean_desc: cleaned series description
    :type clean_desc: str
    :return: series directory name
    :rtype: str
    """
    return "%05d-%s-%s" % (series_num, modality, clean_desc)


def default_study_dir(study_dts, clean_pt_name):
    """
    Generate receiving study directory name.

    :param study_dts: study date and time string
    :type study_dts: str
    :param clean_pt_name: cleaned patient name
    :type clean_pt_name: str
    :return: study directory name
    :rtype: str
    """
    return "%s-%s" % (study_dts, clean_pt_name)


def make_filename(echo, inst_num, dup_number):
    """
    Generate filename.

    :param echo: echo number
    :type echo: int
    :param inst_num: instance number
    :type inst_num: int
    :param dup_number: duplicate number
    :type dup_number: int
    :return: DICOM filename
    :rtype: str
    """
    if dup_number == 0:
        if echo == 1:
            instance_fn = "%05d.dcm" % (inst_num,)
        else:
            instance_fn = "%05d-echo%05d.dcm" % (
                inst_num,
                echo,
            )
    else:
        if echo == 1:
            instance_fn = "%05d-dup%05d.dcm" % (
                inst_num,
                dup_number,
            )
        else:
            instance_fn = "%05d-echo%05d-dup%05d.dcm" % (
                inst_num,
                echo,
                dup_number,
            )

    return instance_fn


def are_different(fp1, fp2):
    """
    Check if two DICOM files are different.

    :param fp1: filepath of 1st file
    :type fp1: pathlib.Path or str
    :param fp2: filepath of 2nd file
    :type fp2: pathlib.Path or str
    :return: Boolean, true if different, false if same
    :rtype: bool
    """
    dcm1 = pydicom.dcmread(fp1, stop_before_pixels=True)
    dcm2 = pydicom.dcmread(fp2, stop_before_pixels=True)

    def single_key_differs(key):
        if key in dcm1 and key in dcm2:
            if dcm1[key].value == dcm2[key].value:
                return False
            else:
                return True
        elif not (key in dcm1 or key in dcm2):
            return False
        else:
            # key present in one but not other
            return True

    if single_key_differs(0x0051100F):
        return True  # siemens coil id
    if single_key_differs(0x00080013):
        return True  # instance time
    if single_key_differs(0x00080033):
        return True  # content time
    if single_key_differs(0x00080008):
        return True  # image type


def sort_dicom(output_dir, dcm_filelist):
    """
    Sort DICOM files into directories.

    :param output_dir: output directory
    :type output_dir: pathlib.Path
    :param dcm_filelist: list of DICOM files to sort
    :type dcm_filelist: list
    """
    for dcm_counter, dcm_file in enumerate(dcm_filelist, 1):

        # Update progress bar
        progress(
            dcm_counter,
            len(dcm_filelist),
            "* sorting %d DICOM files" % len(dcm_filelist),
        )

        # Load the DICOM file
        ds = pydicom.dcmread(dcm_file, stop_before_pixels=True)

        # Ignore DICOMDIR files i.e. Media Storage Directory Storage
        sop_class = ds.file_meta.get("MediaStorageSOPClassUID", None)
        if sop_class == "1.2.840.10008.1.3.10":
            continue

        pt_name = str(ds.get("PatientName", "unknown"))

        study_date = str(ds.get("StudyDate", 20000101))

        study_time = str(ds.get("StudyTime", 120000.00)).split(".")[0]

        modality = str(ds.get("Modality", "unknown"))

        series_num = int(ds.get("SeriesNumber", 1))

        series_desc = str(ds.get("SeriesDescription", "unknown"))

        echo = int(ds.get("EchoNumbers", 1))

        inst_num = int(ds.get("InstanceNumber", 1))

        study_dts = study_date + "." + study_time

        clean_pt_name = simplify_under(pt_name.lower())

        clean_series_desc = simplify_series(series_desc)

        study_dir = default_study_dir(study_dts, clean_pt_name)

        series_dir = default_series_dir(series_num, modality, clean_series_desc)

        path = output_dir / study_dir / series_dir

        # create output directory if it doesn't already exist
        if not path.is_dir():
            path.mkdir(parents=True, exist_ok=True)

        instance_fn = make_filename(echo, inst_num, 0)
        new_fp = path / instance_fn

        if new_fp.is_file():
            dup = 0
            while new_fp.is_file() and are_different(dcm_file, new_fp):
                dup += 1
                instance_fn = make_filename(echo, inst_num, dup)
                new_fp = path / instance_fn

            if new_fp.is_file():
                new_fp.unlink()

        shutil.copy(dcm_file, new_fp)


def scan_for_dicom(a):
    """
    Scan a directory recursively for DICOM files.

    :param a: Directory to scan
    :type a: pathlib.Path
    :return: List of DICOM files
    :rtype: list
    """
    to_sort = []
    for root, _, files in os.walk(a):
        for file_counter, fn in enumerate(files, 1):
            fp = pathlib.Path(root) / fn
            if pydicom.misc.is_dicom(fp):
                to_sort.append(fp)

    return to_sort


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


if __name__ == "__main__":  # pragma: no cover
    main()
