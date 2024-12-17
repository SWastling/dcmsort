import pathlib

import pytest
import importlib.metadata

import dcmsort.dcmsort as dcmsort

THIS_DIR = pathlib.Path(__file__).resolve().parent
TEST_DATA_DIR = THIS_DIR / "test_data"


__version__ = importlib.metadata.version("dcmsort")


@pytest.mark.parametrize(
    "test_fp, expected_output",
    [
        (pathlib.Path("a/b/c"), "a/b/c"),
        (
            pathlib.Path("/aaa/bbb/ccc/ddd/eee/fff/ggg/hhh/iii/jjj/kkk/lll"),
            "/aaa/bbb/ccc/ddd/.../hhh/iii/jjj/kkk/lll",
        ),
    ],
)
def test_shorten_path(test_fp, expected_output):
    out_str = dcmsort.shorten_path(test_fp)
    assert out_str == expected_output
    assert len(out_str) <= 40


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
    "test_description, expected_output",
    [
        ("a", "a"),
        ("a_b", "a_b"),
        (" __a^ b^__ ", "___a__b____"),
        (",.;:=%^&()_+-a", "__-a"),
    ],
)
def test_simplify_description(test_description, expected_output):
    assert dcmsort.simplify_description(test_description) == expected_output


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

    patient_dp = tmp_path / "UNIDENTIFIED_Person-DB2566436380"
    assert patient_dp.is_dir()

    study_dp = patient_dp / "20201110.150633-DB9374925401-Synthetic"
    assert study_dp.is_dir()

    series_dp = study_dp / "02000-MR-SeriesA"
    assert series_dp.is_dir()

    image_1 = (
        series_dp / "1.2.826.0.1.1844281.0.721476.7787.20201110150633750.895456.dcm"
    )
    assert image_1.is_file()


SCRIPT_NAME = "dcmsort"
SCRIPT_USAGE = f"usage: {SCRIPT_NAME} [-h] [-o output_folder] [--version] i [i ...]"


def test_prints_help_1(script_runner):
    result = script_runner.run([SCRIPT_NAME])
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_2(script_runner):
    result = script_runner.run([SCRIPT_NAME, "-h"])
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_for_invalid_option(script_runner):
    result = script_runner.run([SCRIPT_NAME, "-!"])
    assert not result.success
    assert result.stderr.startswith(SCRIPT_USAGE)


def test_prints_version(script_runner):
    result = script_runner.run([SCRIPT_NAME, "--version"])
    assert result.success
    expected_version_output = SCRIPT_NAME + " " + __version__ + "\n"
    assert result.stdout == expected_version_output


def test_sorts_files(script_runner, tmp_path):
    result = script_runner.run(
        [
            SCRIPT_NAME,
            "-o",
            str(tmp_path),
            str(TEST_DATA_DIR / "dir1"),
            str(TEST_DATA_DIR / "dir2"),
            str(TEST_DATA_DIR / "dir2/dir3"),
        ]
    )
    assert result.success

    patient_dp = tmp_path / "UNIDENTIFIED_Person-DB2566436380"
    assert patient_dp.is_dir()

    study_dp = patient_dp / "20201110.150633-DB9374925401-Synthetic"
    assert study_dp.is_dir()

    series_dp = study_dp / "02000-MR-SeriesA"
    assert series_dp.is_dir()

    image_1 = (
        series_dp / "1.2.826.0.1.1844281.0.721476.7787.20201110150633750.895456.dcm"
    )
    assert image_1.is_file()


def test_sorts_files_no_DICOM(script_runner, tmp_path):
    result = script_runner.run([SCRIPT_NAME, "-o", str(tmp_path), str(tmp_path)])
    assert result.success
