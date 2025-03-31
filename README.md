# Purpose

This Python package can be used to download files from the Cencora (formerly
Amerisource) secure file transfer site for ingest into clinical data systems.

Downloads are performed from the web-based secure site located
at https://secure.amerisourcebergen.com/. FTP is not supported. (There are many
easier ways to automate FTP-based downloads.)

# Requirements

- Python 3.10 or newer

# Installation

Use [pip](https://pip.pypa.io/en/stable/) to install the medberg package.

```bash
pip install medberg
```

# Usage

Import the SecureSite class from the medberg module.

```python
from medberg import SecureSite
```

Initialize a connection to the secure site by providing a username and password.

```python
con = SecureSite(username='yourname', password='yourpassword')
```

A list of files is automatically downloaded at connection time and stored in the
`files` variable. Files are represented by objects comprising a name, filesize,
and upload date.

```python
print(con.files)
# [File(name=340B037AM1234567890330.TXT, filesize=self.filesize='1.3MB', date='03/30/2025'),  ...]

print(con.files[0].name)
# 340B037AM1234567890330.TXT

print(con.files[0].filesize)
# 1.3MB

print(con.files[0].date)
# datetime.datetime(2025, 3, 30, 8, 13, 58)
```

Any individual file can be downloaded using the `get` method of the File class.
Optional parameters can be specified for the save directory (`save_dir`) and
local filename (`save_name`). If these are omitted, the file will be saved in
the current working directory using the original filename by default.

```python
con.files[0].get(save_dir='C:\\Users\\yourname\\Downloads\\',
                 save_name='new_filename.txt')
```

Files can also be downloaded using the `get_file` method of the SecureSite
class. In this case, the file to download must be specified in the first
parameter as either an instance of the File class or a string containing the
filename as it appears on the remote site. The optional `save_dir` and
`save_name` parameters are again available as with the `File.get` method.

```python
# Using a File object
file_to_get = con.files[0]
con.get_file(file_to_get)

# Using a string filename
con.get_file('039A_012345678_0101.TXT')
```

When a file is downloaded using either of the methods above, the return value
will be a pathlib Path object pointing to the local file.

# Contributing

Pull requests are welcome. Please ensure all code submitted is formatted
with [Black](https://pypi.org/project/black/) and tested
with [pytest](https://docs.pytest.org/en/stable/). For major changes, please
open an issue first to discuss what you would like to change.

When editing the codebase locally, you may install medberg
in [development mode](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#working-in-development-mode)
to use it in REPLs:

```bash
pip install -e '.[dev]'
```

# License

This software is licensed under
the [MIT License](https://choosealicense.com/licenses/mit/).

# Disclaimer

This package and its authors are not afiliated, associated, authorized, or
endorsed by Cencora, Inc. All names and brands are properties of their
respective owners.