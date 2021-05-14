from utils import *
import pytest
import subprocess as sp


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


def test_check_script_ver(tmp_path, capsys):

    script_fp = tmp_path / 'test_script.py'

    # script release check fail and exit
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        check_script_ver(script_fp, False)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == "** FAIL %s not tagged as a clean release " \
                           "(version %s)\n" % (script_fp.name, 'unknown')
    assert captured.err == "** exiting\n"

    # script check fail and don't exit
    check_script_ver(script_fp, True)
    captured = capsys.readouterr()
    assert captured.out == "** FAIL %s not tagged as a clean release " \
                           "(version %s)\n" % (script_fp.name, 'unknown')

    # script check pass and don't exit
    # Set up a mock git repo
    sp.run(['git', 'init'], check=True, text=True, cwd=tmp_path)

    script_fp.touch()

    # Add the file to the repo
    sp.run(['git', 'add', script_fp], check=True, text=True, cwd=tmp_path)

    # Commit changes
    sp.run(['git', 'commit', '-a', '-m', '"Mock commit"'],
           check=True, text=True, cwd=tmp_path)

    # Tag as release
    sp.run(['git', 'tag', '-a', 'release-1.0.0', '-m', '"Release 1.0.0"'],
           check=True, text=True, cwd=tmp_path)

    check_script_ver(script_fp, True)
    captured = capsys.readouterr()
    assert captured.out == "** PASS release check on %s (%s)\n" \
           % (script_fp.name, 'release-1.0.0')


def test_check_lib_ver(capsys):

    # Library check fail and exit
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        check_lib_ver('lib_a', '2.0.0', ['1.0.0', '1.0.1'], False)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == "** FAIL using non-validated lib_a version\n*** " \
                           "expected 1.0.0 or 1.0.1, got 2.0.0\n"
    assert captured.err == "** exiting\n"

    # Library check fail and don't exit
    check_lib_ver('lib_a', '2.0.0', ['1.0.0', '1.0.1'], True)
    captured = capsys.readouterr()
    assert captured.out == "** FAIL using non-validated lib_a version\n*** " \
                           "expected 1.0.0 or 1.0.1, got 2.0.0\n"

    # Library check pass and don't exit
    check_lib_ver('lib_a', '2.0.0', ['1.0.0', '2.0.0'], True)
    captured = capsys.readouterr()
    assert captured.out == "** PASS version check on lib_a (2.0.0)\n"


def test_shorten_path():

    assert shorten_path(pathlib.Path('a/b/c')) == 'a/b/c'
    assert len(shorten_path(
        pathlib.Path('/aaa/bbb/ccc/ddd/eee/fff/ggg/hhh/iii/jjj/kkk/lll'))) <= 40
    assert shorten_path(
        pathlib.Path('/aaa/bbb/ccc/ddd/eee/fff/ggg/hhh/iii/jjj/kkk/lll')) == \
           '/aaa/bbb/ccc/ddd/.../hhh/iii/jjj/kkk/lll'

