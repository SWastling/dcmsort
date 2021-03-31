#!/usr/bin/env python3
"""
Sort DICOM files into directories
e.g.
StudyDate.StudyTime-PatientName/SeriesNumber-Modality-SeriesDescription"
"""

__author__ = "Stephen Wastling"

import argparse
import os
import pathlib
import pydicom
import re
import shutil
import subprocess as sp
import sys

# useful patterns for simplifying names
under = re.compile(r'[\s/^]')
underb = re.compile(r'^_+')
underrep = re.compile(r'_{2,}')
undere = re.compile(r'_+$')
remove = re.compile(r'[^A-Za-z0-9_-]')
removep = re.compile(r'[^A-Za-z0-9,.;:=%^&()_+-]')

# tested versions of external libraries
PYDICOM_VERSIONS = ['2.0.0', ]


def progress(count, total, message=None):
    """
    Print percentage progress to stdout during loop

    :param count: Loop counter
    :type count: int
    :param total: Total number of iterations of loop
    :type total: str
    :param message: Optional message to accompany % progress
    :type message: str
    """

    if message is None:
        message = ''

    percents = round(100.0 * count / float(total), 1)

    if total == count:
        print('%s [%3d%%]' % (message, percents))
    else:
        print('%s [%3d%%]' % (message, percents), end='\r')


def git_version(srcdir):
    """
    Determine if we are running a release and if so what version

    :param srcdir: Directory containing git repo
    :type srcdir: pathlib.Path
    :return: ver, release
    """

    git_dir = srcdir / '.git'

    if git_dir.is_dir():
        # Are there any tags with the prefix release-
        sp_out = sp.run(['git', 'tag', '-l', 'release-*'], check=True,
                        capture_output=True, text=True, cwd=srcdir)

        tag_list = sp_out.stdout.strip()
        if tag_list:
            sp_out = sp.run(['git', 'describe', '--tags', '--long',
                             '--dirty=+'], check=True, capture_output=True,
                            text=True, cwd=srcdir)
            ver_long = sp_out.stdout.strip()
            ver_components = ver_long.split('-')

            # If a tag has been defined the output of git describe is
            # tag-commits_ontop-git_sha e.g.

            # Case 1
            # release-1.0.0-0-4609e1a is clean with no commits on top the tag
            # so version = release-1.0.0 and release = True

            # Case 2
            # release-1.0.0-0-4609e1a+ is dirty so release is False

            # Case 3
            # release-1.0.0-1-4609e1a has 1 further commit on top the tag
            # so release is False

            # Case 4
            # release-1.0.0-2-4609e1a+ has 2 further commits on top the tag and
            # it's dirty so release is False

            git_sha = ver_components.pop()
            commits_ontop = int(ver_components.pop())
            ver = "-".join(ver_components)

            if re.match(r'release-', ver) and commits_ontop == 0 \
                    and git_sha[-1] is not '+':
                release = True
            else:
                # Show user long version of tag so they can see why the version
                # check failed i.e. commits on top or dirty repo
                ver = ver + '-' + str(commits_ontop) + '-' + git_sha
                release = False
        else:
            # No tags with prefix release-
            ver = 'unknown'
            release = False
    else:
        # No .git directory
        ver = 'unknown'
        release = False

    return ver, release


def check_lib_ver(lib_name, lib_ver, expected_lib_ver_list, bad_ver):
    """
    Compare the actual library version to the expected version

    :param lib_name: name of library
    :type lib_name: str
    :param lib_ver: version of library
    :type lib_ver: str
    :param expected_lib_ver_list: expected version of library
    :type expected_lib_ver_list: list
    :param bad_ver: Boolean to True if lib_ver != expected_lib_ver
    :type bad_ver: bool
    :return: bad_ver
    :type: bool
    """
    if lib_ver not in expected_lib_ver_list:
        print("** FAIL using non-validated %s version" % lib_name)
        print("*** expected %s, got %s" % (' or '.join(expected_lib_ver_list),
                                           lib_ver))
        bad_ver = True
    else:
        print("** PASS version check on %s (%s)" % (lib_name, lib_ver))

    return bad_ver


def simplify_under(name):
    """
    Turn spaces and carets into underscores, and tidy up repeated or
    leading/trailing underscores

    :param name: string to be cleaned of spaces, carets and repeated underscores
    :type name: str
    :return: s - simplified name
    :type: str
    """

    s = under.subn("_", name)[0]
    s = underb.subn("", s)[0]
    s = undere.subn("", s)[0]
    s = underrep.subn("_", s)[0]
    s = remove.subn("", s)[0]

    return s


def simplify_series(desc):
    """
    Simplify series description

    :param desc: series description
    :type desc: str
    :return: s
    """
    s = under.subn("_", desc)[0]
    s = remove.subn("", s)[0]
    return s


def default_series_dir(series_num, modality, clean_desc):
    """
    Generate series directory name

    :param series_num: series number
    :type series_num: int
    :param modality: DICOM modality e.g. MR
    :type modality: str
    :param clean_desc: cleaned series description
    :type clean_desc: str
    :return: series directory name
    :type: str
    """
    return "%05d-%s-%s" % (series_num, modality, clean_desc)


def default_study_dir(study_dts, clean_pt_name):
    """
    Generate receiving study directory name

    :param study_dts: study date and time string
    :type study_dts: str
    :param clean_pt_name: cleaned patient name
    :type clean_pt_name: str
    :return: study directory name
    :type: str
    """
    return "%s-%s" % (study_dts, clean_pt_name)


def make_filename(echo, inst_num, dup_number):
    """
    Generate filename

    :param echo: echo number
    :type echo: int
    :param inst_num: instance number
    :type inst_num: int
    :param dup_number: duplicate number
    :type dup_number: int
    :return: DICOM filename
    :type: str
    """
    if dup_number == 0:
        if echo == 1:
            instance_fn = "%05d.dcm" % (inst_num,)
        else:
            instance_fn = "%05d-echo%05d.dcm" % (inst_num, echo,)
    else:
        if echo == 1:
            instance_fn = "%05d-dup%05d.dcm" % \
                (inst_num, dup_number,)
        else:
            instance_fn = "%05d-echo%05d-dup%05d.dcm" % \
                (inst_num, echo, dup_number,)

    return instance_fn


def are_different(fp1, fp2):
    """
    Check if two DICOM files are different

    :param fp1: filepath of 1st file
    :type fp1: pathlib.Path or str
    :param fp2: filepath of 2nd file
    :type fp2: pathlib.Path or str
    :return: Boolean, true if different, false if same
    :type: bool
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

    if single_key_differs(0x0051100f):
        return True  # siemens coil id
    if single_key_differs(0x00080013):
        return True  # instance time
    if single_key_differs(0x00080033):
        return True  # content time
    if single_key_differs(0x00080008):
        return True  # image type


def sort_dicom(output_dir, dcm_filelist):
    """
    Sort DICOM files into directories e.g.
    StudyDate.StudyTime-PatientName/SeriesNumber-Modality-SeriesDescription"

    :param output_dir: output directory
    :type output_dir: pathlib.Path
    :param dcm_filelist: list of DICOM files to sort
    :type dcm_filelist: list
    """
    for dcm_counter, dcm_file in enumerate(dcm_filelist, 1):

        # Update progress bar
        progress(dcm_counter, len(dcm_filelist),
                 '* sorting %d DICOM files' % len(dcm_filelist))

        # Load the DICOM file
        ds = pydicom.dcmread(dcm_file, stop_before_pixels=True)

        # Ignore DICOMDIR files i.e. Media Storage Directory Storage
        if ds.file_meta.MediaStorageSOPClassUID.name == \
                'Media Storage Directory Storage':
            continue

        pt_name = str(ds.get('PatientName', 'unknown'))

        study_date = str(ds.get('StudyDate', 20000101))

        study_time = str(ds.get('StudyTime', 120000.00)).split(".")[0]

        modality = str(ds.get('Modality', 'unknown'))

        series_num = int(ds.get('SeriesNumber', 1))

        series_desc = str(ds.get('SeriesDescription', 'unknown'))

        echo = int(ds.get('EchoNumbers', 1))

        inst_num = int(ds.get('InstanceNumber', 1))

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
    Scan a directory recursively for DICOM files

    :param a: Directory to scan
    :type a: pathlib.Path
    :return: List of files
    :type: list
    """

    to_sort = []
    for root, _, files in os.walk(a):
        for file_counter, fn in enumerate(files, 1):
            fp = pathlib.Path(root) / fn
            if pydicom.misc.is_dicom(fp):
                to_sort.append(fp)

    return to_sort


def main():
    parser = argparse.ArgumentParser(
        description="Sort DICOM files into directories "
                    "e.g. StudyDate.StudyTime-PatientName/"
                    "SeriesNumber-Modality-SeriesDescription")

    parser.add_argument("i", help="list of input directories to search for DICOM"
                                  " files", nargs='+', type=pathlib.Path)
    parser.add_argument("-o", default='./dcm',
                        help="output directory (default %(default)s)",
                        metavar='output_folder', type=pathlib.Path)
    parser.add_argument('--any-version', dest='any_version', default=False,
                        action="store_true",
                        help="don't abort if version checks fail")

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()

    script_fp = pathlib.Path(__file__).resolve()
    script_fn = script_fp.name
    version, release = git_version(script_fp.parent)

    print("* checking version of %s and libraries" % script_fn)
    bad_version = False
    if not release:
        print("** FAIL %s not tagged as a clean release (%s)"
              % (script_fn, version))
        bad_version = True
    else:
        print("** PASS release check on %s (%s)" % (script_fn, version))

    bad_version = check_lib_ver('pydicom', pydicom.__version__,
                                PYDICOM_VERSIONS, bad_version)

    if bad_version and not args.any_version:
        print("** Aborting because of version check failure")
        sys.exit(1)

    out_dir = args.o.resolve()

    for item in args.i:
        print('* scanning for DICOM files in %s' % item)
        to_sort = scan_for_dicom(item)

        if len(to_sort) > 0:
            sort_dicom(out_dir, to_sort)


if __name__ == "__main__":
    main()

