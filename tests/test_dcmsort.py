import pathlib

import pytest

import dcmsort.dcmsort as dcmsort

THIS_DIR = pathlib.Path(__file__).resolve().parent
TEST_DATA_DIR = THIS_DIR / "test_data"


@pytest.mark.parametrize(
    "args, expected_output",
    [
        ([0, 10, "doing thing"], "doing thing [  0%]\r"),
        ([5, 10], " [ 50%]\r"),
        ([10, 10], " [100%]\n"),
    ],
)
def test_progress(capsys, args, expected_output):
    dcmsort.progress(*args)
    captured = capsys.readouterr()
    assert captured.out == expected_output


@pytest.mark.parametrize(
    "test_name, expected_output",
    [("a", "a"), ("a_b", "a_b"), (" __a^ b^__ ", "a_b"), (",.;:=%_&()_+-a", "__-a")],
)
def test_simplify_under(test_name, expected_output):
    assert dcmsort.simplify_under(test_name)


@pytest.mark.parametrize(
    "test_description, expected_output",
    [
        ("a", "a"),
        ("a_b", "a_b"),
        (" __a^ b^__ ", "___a__b____"),
        (",.;:=%^&()_+-a", "__-a"),
    ],
)
def test_simplify_series(test_description, expected_output):
    assert dcmsort.simplify_series(test_description) == expected_output


@pytest.mark.parametrize(
    "test_series_num, test_modality, test_clean_desc," "expected_output",
    [
        (1, "MR", "abc", "00001-MR-abc"),
        (5, "CT", "efg", "00005-CT-efg"),
        (2345, "US", "xyz", "02345-US-xyz"),
    ],
)
def test_default_series_dir(
    test_series_num, test_modality, test_clean_desc, expected_output
):
    assert (
        dcmsort.default_series_dir(test_series_num, test_modality, test_clean_desc)
        == expected_output
    )


def test_default_study_dir():
    assert (
        dcmsort.default_study_dir("20200101.120000", "bloggs_joe")
        == "20200101.120000-bloggs_joe"
    )


@pytest.mark.parametrize(
    "test_echo, test_instance_num, test_dup_num, " "expected_output",
    [
        (1, 1, 0, "00001.dcm"),
        (5, 2, 0, "00002-echo00005.dcm"),
        (1, 2345, 1, "02345-dup00001.dcm"),
        (5, 2345, 1, "02345-echo00005-dup00001.dcm"),
    ],
)
def test_make_filename(test_echo, test_instance_num, test_dup_num, expected_output):
    assert (
        dcmsort.make_filename(test_echo, test_instance_num, test_dup_num)
        == expected_output
    )


"""
Need to test 4 different tags:
1. Siemens CoilString (0x0051100f)
    a. Test images I0, I1, I2, I3 and I4
2. InstanceCreationTime (0x00080013)
    a. Test images I0, I1, I7, I8 and I9
3. ContentTime (0x00080033)
    a. Test images I0, I1, I12, I13 and I14
4. ImageType (0x00080008)
    a. Test images I0, I1, I17, I18 and I19

There are 5 scenarios (i.e. 5 test DICOM files) for each:
1. The tag is present in both files and the values are equal, then are_different
returns None (e.g. I0 and I1)
2. The tag is present in both files and the values are different, then
are_different returns True (e.g. I0 and I2)
3. The tag is missing from both files, then are_different returns None
(e.g. I3 and I4)
4. The tag is missing from the first file, then are_different returns True
(e.g. I3 and I1)
5. The tag is missing from the second file, then are_different returns True
(e.g. I0 and I4)
"""


@pytest.mark.parametrize(
    "test_fn1, test_fn2, expected_output",
    [
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I1", None),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I2", True),
        (TEST_DATA_DIR / "I3", TEST_DATA_DIR / "I4", None),
        (TEST_DATA_DIR / "I3", TEST_DATA_DIR / "I1", True),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I4", True),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I7", True),
        (TEST_DATA_DIR / "I8", TEST_DATA_DIR / "I9", None),
        (TEST_DATA_DIR / "I8", TEST_DATA_DIR / "I1", True),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I9", True),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I12", True),
        (TEST_DATA_DIR / "I13", TEST_DATA_DIR / "I14", None),
        (TEST_DATA_DIR / "I13", TEST_DATA_DIR / "I1", True),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I14", True),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I17", True),
        (TEST_DATA_DIR / "I18", TEST_DATA_DIR / "I19", None),
        (TEST_DATA_DIR / "I18", TEST_DATA_DIR / "I1", True),
        (TEST_DATA_DIR / "I0", TEST_DATA_DIR / "I19", True),
    ],
)
def test_are_different(test_fn1, test_fn2, expected_output):
    assert dcmsort.are_different(test_fn1, test_fn2) == expected_output


def test_scan_for_dicom():
    scan_dir = TEST_DATA_DIR / "dir1"

    assert dcmsort.scan_for_dicom(scan_dir) == [
        pathlib.Path(TEST_DATA_DIR / "dir1/DICOMDIR"),
        pathlib.Path(TEST_DATA_DIR / "dir1/I0"),
        pathlib.Path(TEST_DATA_DIR / "dir1/I0_copy"),
        pathlib.Path(TEST_DATA_DIR / "dir1/dir2/I2"),
        pathlib.Path(TEST_DATA_DIR / "dir1/dir2/dir3" "/I3"),
    ]


def test_sort_dicom(tmp_path):
    dcmsort.sort_dicom(
        tmp_path,
        [
            pathlib.Path(TEST_DATA_DIR / "dir1/I0"),
            pathlib.Path(TEST_DATA_DIR / "dir1/dir2/I2"),
            pathlib.Path(TEST_DATA_DIR / "dir1/dir2/dir3/I3"),
        ],
    )

    study_directory = tmp_path / "20201110.150633-unidentified_person"
    series_directory = study_directory / "02000-MR-SeriesA"
    image_1 = series_directory / "00001.dcm"
    image_2 = series_directory / "00001-dup00001.dcm"
    image_3 = series_directory / "00001-dup00002.dcm"
    assert study_directory.is_dir()
    assert series_directory.is_dir()
    assert image_1.is_file()
    assert image_2.is_file()
    assert image_3.is_file()


def test_shorten_path():

    assert dcmsort.shorten_path(pathlib.Path("a/b/c")) == "a/b/c"
    assert (
        len(
            dcmsort.shorten_path(
                pathlib.Path("/aaa/bbb/ccc/ddd/eee/fff/ggg/hhh/iii/jjj/kkk/lll")
            )
        )
        <= 40
    )
    assert (
        dcmsort.shorten_path(
            pathlib.Path("/aaa/bbb/ccc/ddd/eee/fff/ggg/hhh/iii/jjj/kkk/lll")
        )
        == "/aaa/bbb/ccc/ddd/.../hhh/iii/jjj/kkk/lll"
    )


SCRIPT_NAME = "dcmsort"
SCRIPT_USAGE = f"usage: {SCRIPT_NAME} [-h] [-o output_folder] [--version] i [i ...]"


def test_prints_help_1(script_runner):
    result = script_runner.run(SCRIPT_NAME)
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_2(script_runner):
    result = script_runner.run(SCRIPT_NAME, "-h")
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_for_invalid_option(script_runner):
    result = script_runner.run(SCRIPT_NAME, "-!")
    assert not result.success
    assert result.stderr.startswith(SCRIPT_USAGE)


def test_sorts_files(script_runner, tmp_path):
    result = script_runner.run(
        SCRIPT_NAME,
        "-o",
        str(tmp_path),
        str(TEST_DATA_DIR / "dir1"),
        str(TEST_DATA_DIR / "dir2"),
        str(TEST_DATA_DIR / "dir2/dir3"),
    )
    assert result.success

    study_directory = tmp_path / "20201110.150633-unidentified_person"
    series_directory = study_directory / "02000-MR-SeriesA"
    image_1 = series_directory / "00001.dcm"
    image_2 = series_directory / "00001-dup00001.dcm"
    image_3 = series_directory / "00001-dup00002.dcm"
    assert study_directory.is_dir()
    assert series_directory.is_dir()
    assert image_1.is_file()
    assert image_2.is_file()
    assert image_3.is_file()
