# Purpose

This Python package can be used to download files from the Cencora (formerly
Amerisource) secure file transfer site for ingest into clinical data systems.

Downloads are performed from the web-based secure site located at
https://secure.amerisourcebergen.com/. FTP is not supported. (There are many
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

A list of files is automatically downloaded at connection time. Filenames are stored as
a list in the `files` variable.

```python
print(con.files)
# ['039A_012345678_0101.TXT', '077AXM0123456780101.TXT', ...]
```

Any individual file can be downloaded using the `get_file` method.

```python
con.get_file('039A_012345678_0101.TXT', save_dir='C:\\Users\\yourname\\Downloads\\')
```

The file is saved in the path specified by `save_dir`. If this is left blank, it will
default to the current working directory. The local filepath will be returned as a
pathlib Path.

# Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what
you would like to change.

# License

This software is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).

# Disclaimer

This package and its authors are not afiliated, associated, authorized, or endorsed by
Cencora, Inc. All names and brands are properties of their respective owners.