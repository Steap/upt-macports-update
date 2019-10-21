# Prototype to upgrade PyPI ports in Macports.

This will eventually end up being part of upt itself.

## Usage

$ cd $MACPORTS_DIR/
$ python upt_macports_update.py <pypi name>

## Features
- Update version
- Reset revision to 0
- Update checksums
- Update archive size
- Add new requirements to "depends_lib-append"
- Remove no longer needed requirements from "depends_lib-append"

## Shortcomings
- Only works with PyPI ports
- Does not add new dependencies if there were no dependencies to begin with
