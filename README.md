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

## Establishing a connection

Import the SecureSite class from the medberg module.

```python
from medberg import SecureSite
```

Initialize a connection to the secure site by providing a username and password.

```python
con = SecureSite(username='yourname', password='yourpassword')
```

## Reviewing files

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

The library will attempt to automatically extract additional metadata from the
filename describing account type (e.g., 340B, GPO, WAC), file specification
(e.g., 037, 039), and account number.

```python
print(con.files[0].account_type)
# 340B

print(con.files[0].specification)
# 037AM

print(con.files[0].account_number)
# 123456789
```

If the metadata is not present in the filename, the corresponding property will
simply evaluate to None.

## Downloading files

Any individual file can be downloaded using the `get()` method of the File class.
By default, the file contents will be saved to `File.contents`. Optional parameters
can be specified for the save directory (`save_dir`) and local filename (`save_name`).
If these are included, the file will also be saved to disk. Five attempts will be
made to download the file by default. This can be overriden with the `max_tries`
parameter.

```python
con.files[0].get(save_dir='C:\\Users\\yourname\\Downloads\\',
                 save_name='new_filename.txt',
                 max_tries=10)
```

Files can also be downloaded using the `get_file()` method of the SecureSite
class. In this case, the file to download must be specified in the first
parameter as either an instance of the File class or a string containing the
filename as it appears on the remote site. This method returns a bytes object
instead of the string saved to `File.contents`.

```python
# Using a File object
file_to_get = con.files[0]
con.get_file(file_to_get)

# Using a string filename
con.get_file('039A_012345678_0101.TXT')
```

## Filtering files

The list of files obtained from the server can be filtered using the
`match_files()` method, which can take any number of arguments in the format
file_property=filter_value. For example, to retrieve all files with account
number 123456789, you can call `match_files(account_number="123456789")`. The
result will be a list of File objects matching the specified arguments.

```python
con.match_files(account_number="123456789")
# [File(name=340B037AM1234567890330.TXT, filesize=self.filesize='1.3MB', date='03/30/2025'),  ...]
```

Files can be matched on any attribute. In cases where the file property type
differs from the filter value type, the filter value will be converted to the
correct type automatically. For example, the account number above was filtered
using a string (as account_number is stored in the file class), but it can just
as well be filtered using an integer:

```python
con.match_files(account_number=123456789)
# [File(name=340B037AM1234567890330.TXT, filesize=self.filesize='1.3MB', date='03/30/2025'),  ...]
```

String filter values can contain a wildcard (&ast;) at the beginning or end of
the filter. For example, `match_files(file_specification="039*")` will match
"039", "039A", "039AM", etc.

List and tuple filters will cause a match if any one of the inner values
matches. Effectively, this acts as a nested OR filter.

Callables can also be passed to allow for more complex filtering. For example,
we can get all files from the current month as follows:

```python
from datetime import datetime

current_month = datetime.now().month
current_year = datetime.now().year
con.match_files(date=lambda x: x >= datetime(current_year, current_month, 1))
```

Multiple filter arguments can be passed together to create a more specific
filter.

To get a single file with the most recent upload time that matches a filter or
series of filters, use `match_latest_file()`. This method takes the same
arguments as the `match_files()` method.

## Manipulating files

Once files are downloaded, you can perform row-level manipulations using the
`File.filter_()` method. To do this, you must have already downloaded the target
file using `get()`, otherwise this will be performed for you using the default
parameters.

Next, a row pattern must be present in `File.row_pattern`. This is essentially a
regex that defines the named capture groups of each line within the file. When
the file is downloaded, the library will attempt to match a row pattern based on
the parsed specification. If this fails, you must set it manually, e.g.:

```python
file.row_pattern = RowPattern.ICS_039A
```

Filters are defined as lambda functions based on row properies. Each Row object
contains two properties: `raw`, which is simply a raw string representation of
the row from the file, and `parts`, which contains the parsed elements from the
row in a dictionary. Take the following row as an example:

```text
11111111111222222  333333333444444444
```

When parsed with the ICS_039A row pattern, `parts` results as the following:

```python
{
    "ndc11": "11111111111",
    "item_id": "222222",
    "price": "333333333",
    "pack_size": "444444444"
}
```

You could filter **in** rows that contain an NDC-11 beginning with 11111 with
the following lambda:

```python
file.filter_(lambda row: row.parts['ndc11'].startswith("11111"))
```

If called as a standalone function, `filter_()` will open the file, filter rows,
and save the result on its own. This happens locally inside the `File.contents`
variable. If the file was saved to disk, the file referenced by the path in
`File.location` will be updated also. If multiple applications of `filter_()`
need to be performed, it's recommended to use a `with` block, which buffers and
saves the file at the beginning and end of the block, respectively.

```python
with file as f:
    # Writing to object and disk occurs only after the final filter is applied
    f.filter_(lambda row: row.parts['ndc11'].startswith("11111"))
    f.filter_(lambda row: int(row.parts['price']) / 1000 > 100)
```

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