from dcmsort import *
import pathlib
import pytest
import subprocess as sp


@pytest.mark.parametrize("args, expected_output",
                         [([0, 10, 'doing thing'], "doing thing [  0%]\r"),
                          ([5, 10], " [ 50%]\r"),
                          ([10, 10], " [100%]\n")])
def test_progress(capsys, args, expected_output):
    progress(*args)
    captured = capsys.readouterr()
    assert captured.out == expected_output


def test_git_version(tmp_path):

    assert git_version(tmp_path) == ('unknown', False)

    # Set up a mock git repo
    sp.run(['git', 'init'], check=True, text=True, cwd=tmp_path)

    assert git_version(tmp_path) == ('unknown', False)

    # Add a file to the git repo
    test_fp = tmp_path / 'test.txt'
    test_fp.touch()

    assert git_version(tmp_path) == ('unknown', False)

    # Add the file to the repo
    sp.run(['git', 'add', test_fp], check=True, text=True, cwd=tmp_path)

    assert git_version(tmp_path) == ('unknown', False)

    # Commit changes
    sp.run(['git', 'commit', '-a', '-m', '"Mock commit"'],
           check=True, text=True, cwd=tmp_path)

    assert git_version(tmp_path) == ('unknown', False)

    # Tag as release
    sp.run(['git', 'tag', '-a', 'release-1.0.0', '-m', '"Release 1.0.0"'],
           check=True, text=True, cwd=tmp_path)

    assert git_version(tmp_path) == ('release-1.0.0', True)

    # Make the repo dirty
    test_fp.write_text('Hello')

    sp_out = sp.run(['git', 'describe', '--tags', '--long',
                     '--dirty=+'], check=True, capture_output=True,
                    text=True, cwd=tmp_path)

    assert git_version(tmp_path) == (sp_out.stdout.strip(), False)

    # Commit on top of tag as release
    sp.run(['git', 'commit', '-a', '-m', '"Mock commit 2"'],
           check=True, text=True, cwd=tmp_path)

    sp_out = sp.run(['git', 'describe', '--tags', '--long',
                     '--dirty=+'], check=True, capture_output=True,
                    text=True, cwd=tmp_path)

    assert git_version(tmp_path) == (sp_out.stdout.strip(), False)


@pytest.mark.parametrize("test_name, expected_output",
                         [('a', 'a'), ('a_b', 'a_b'),
                          (' __a^ b^__ ', 'a_b'), (',.;:=%_&()_+-a', '__-a')])
def test_simplify_under(test_name, expected_output):
    assert simplify_under(test_name)


@pytest.mark.parametrize("test_description, expected_output",
                         [('a', 'a'), ('a_b', 'a_b'),
                          (' __a^ b^__ ', '___a__b____'),
                          (',.;:=%^&()_+-a', '__-a')])
def test_simplify_series(test_description, expected_output):
    assert simplify_series(test_description) == expected_output


@pytest.mark.parametrize("test_series_num, test_modality, test_clean_desc,"
                         "expected_output",
                         [(1, 'MR', 'abc', '00001-MR-abc'),
                          (5, 'CT', 'efg', '00005-CT-efg'),
                          (2345, 'US', 'xyz', '02345-US-xyz')])
def test_default_series_dir(test_series_num, test_modality, test_clean_desc,
                            expected_output):
    assert default_series_dir(test_series_num, test_modality,
                              test_clean_desc) == expected_output


def test_default_study_dir():
    assert default_study_dir('20200101.120000', 'bloggs_joe') \
           == '20200101.120000-bloggs_joe'


@pytest.mark.parametrize("test_echo, test_instance_num, test_dup_num, "
                         "expected_output",
                         [(1, 1, 0, '00001.dcm'),
                          (5, 2, 0, '00002-echo00005.dcm'),
                          (1, 2345, 1, '02345-dup00001.dcm'),
                          (5, 2345, 1, '02345-echo00005-dup00001.dcm')])
def test_make_filename(test_echo, test_instance_num, test_dup_num,
                       expected_output):
    assert make_filename(test_echo, test_instance_num, test_dup_num) \
           == expected_output


'''
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
'''


@pytest.mark.parametrize("test_fn1, test_fn2, expected_output",
                         [('test_data/I0', 'test_data/I1', None),
                          ('test_data/I0', 'test_data/I2', True),
                          ('test_data/I3', 'test_data/I4', None),
                          ('test_data/I3', 'test_data/I1', True),
                          ('test_data/I0', 'test_data/I4', True),
                          ('test_data/I0', 'test_data/I7', True),
                          ('test_data/I8', 'test_data/I9', None),
                          ('test_data/I8', 'test_data/I1', True),
                          ('test_data/I0', 'test_data/I9', True),
                          ('test_data/I0', 'test_data/I12', True),
                          ('test_data/I13', 'test_data/I14', None),
                          ('test_data/I13', 'test_data/I1', True),
                          ('test_data/I0', 'test_data/I14', True),
                          ('test_data/I0', 'test_data/I17', True),
                          ('test_data/I18', 'test_data/I19', None),
                          ('test_data/I18', 'test_data/I1', True),
                          ('test_data/I0', 'test_data/I19', True)])
def test_are_different(test_fn1, test_fn2, expected_output):
    assert are_different(test_fn1, test_fn2) == expected_output


def test_scan_for_dicom():
    scan_dir = pathlib.Path('test_data/dir1')

    assert scan_for_dicom(scan_dir) == [pathlib.Path('test_data/dir1/DICOMDIR'),
                                        pathlib.Path('test_data/dir1/I0'),
                                        pathlib.Path('test_data/dir1/dir2/I2'),
                                        pathlib.Path('test_data/dir1/dir2/dir3'
                                                     '/I3')]


def test_sort_dicom(tmp_path):
    sort_dicom(tmp_path, [pathlib.Path('test_data/dir1/I0'),
                          pathlib.Path('test_data/dir1/dir2/I2'),
                          pathlib.Path('test_data/dir1/dir2/dir3/I3')])

    study_directory = tmp_path / '20201110.150633-unidentified_person'
    series_directory = study_directory / '02000-MR-SeriesA'
    image_1 = series_directory / '00001.dcm'
    image_2 = series_directory / '00001-dup00001.dcm'
    image_3 = series_directory / '00001-dup00002.dcm'
    assert study_directory.is_dir()
    assert series_directory.is_dir()
    assert image_1.is_file()
    assert image_2.is_file()
    assert image_3.is_file()


def test_dcmsort(tmp_path):

    sp.run(['./dcmsort.py', '--any-version', '-o', tmp_path, 'test_data/dir1',
            'test_data/dir1/dir2', 'test_data/dir1/dir2/dir3'])

    study_directory = tmp_path / '20201110.150633-unidentified_person'
    series_directory = study_directory / '02000-MR-SeriesA'
    image_1 = series_directory / '00001.dcm'
    image_2 = series_directory / '00001-dup00001.dcm'
    image_3 = series_directory / '00001-dup00002.dcm'
    assert study_directory.is_dir()
    assert series_directory.is_dir()
    assert image_1.is_file()
    assert image_2.is_file()
    assert image_3.is_file()
