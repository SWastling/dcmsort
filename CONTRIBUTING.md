# Contributing

This is a personal project, I'm not expecting contributions. This guide is intended to be a reference for myself.

## Developing

1. Activate the virtual environment in which tox is installed

    ```bash
    source dcmsort-env/bin/activate
    ```
   
2. Before making any modification call tox to run the linters 
(isort, black and flake8) then the tests, and coverage:

    ```bash
    tox
    ```

3. Make your changes

4. After making any modifications auto-format the code with with the tox format 
option which in this case calls isort and black:

    ```bash
    tox -e format
    ```

5. Create and activate a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) for [development](https://tox.readthedocs.io/en/latest/example/devenv.html):

    ```bash
    tox --devenv venv
    source venv/bin/activate
    ```

5. Run the tests:

    ```bash
    pytest -v
    ```

6. If all the tests pass re-activate the the virtual environment in which tox 
is installed

    ```bash
    source dcmsort-env/bin/activate
    ```

7. Re-run tox to run the linters 
(isort, black and flake8) then the tests, and coverage:

    ```bash
    tox
    ```



## Releasing

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [PEP 440](https://www.python.org/dev/peps/pep-0440/), and uses [setuptools_scm](https://pypi.org/project/setuptools-scm/) to determine the version from the latest `git` tag.

1. Commit your changes

    ```bash
    git commit -a
    ```

2. Choose a version number:

    ```bash
    version=0.2.0
    ```

3. Update the [changelog](./CHANGELOG.md):

    ```bash
    git commit -a -m "Update changelog for $version"
    ```

4. Tag the release:

    ```bash
    git tag -a $version -m "release $version"
    ```

5. Push the changes to the github repository

    ```bash
    git push -u origin main --follow-tags
    ```

6. Create the [source distribution](https://packaging.python.org/glossary/#term-Source-Distribution-or-sdist) and [wheel](https://packaging.python.org/glossary/#term-Built-Distribution) packages, then publish the release to [PyPI](https://pypi.org/project/dcmsort/):

    ```bash
    tox -e release
    ```