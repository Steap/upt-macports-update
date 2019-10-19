import os
import re
import sys

import upt
from upt_pypi.upt_pypi import PyPIFrontend


class UptDiff(object):
    def __init__(self, old, new):
        self.old = old
        self.new = new

    @property
    def new_version(self):
        return self.new.version

    @property
    def new_requirements(self):
        # TODO
        return []

    @property
    def updated_requirements(self):
        # TODO
        return []

    @property
    def deleted_requirements(self):
        # TODO
        return []


def _clean_depends_line(line):
    if line.endswith('\n'):
        line = line[:-1]
    if line.endswith('\\'):
        line = line[:-1]
    return line.strip()


def update(portfile_path, pypi_name, old_version):
    print(f'[+] Updating {pypi_name} (currently at version {old_version})')
    frontend = PyPIFrontend()
    old = frontend.parse(pypi_name, old_version)
    new = frontend.parse(pypi_name)
    if old.version == new.version:
        print(f'{pypi_name} is already at the latest version')
        sys.exit(0)
    pdiff = UptDiff(old, new)

    new_lines = []
    in_depends_lib = False
    old_depends_lib = []
    depend_libs_indent = 0
    old_depends_lineno = None
    with open(portfile_path) as f:
        for lineno, line in enumerate(f.readlines()):
            m = re.match('(\s+)depends_lib-append(\s+)(.*)', line)
            if m:
                depend_libs_indent = m.group(1)
                in_depends_lib = True
                line = f'{m.group(3)}\n'
                old_depends_lineno = lineno

            if in_depends_lib:
                old_depends_lib.append(_clean_depends_line(line))
                if not line.endswith('\\\n'):
                    in_depends_lib = False
                continue

            # Update version
            m = re.match('^version(\s+)(.*)\n$', line)
            if m:
                line = f'version{m.group(1)}{pdiff.new_version}\n'

            # Reset revision to 0
            m = re.match('^revision(\s+).*', line)
            if m:
                line = f'revision{m.group(1)}0\n'

            # Update rmd160
            m = re.match('^(.*)rmd160(\s+)[0-9a-f]{40}(.*)$', line)
            if m:
                rmd = new.get_archive().rmd160
                line = f'{m.group(1)}rmd160{m.group(2)}{rmd}{m.group(3)}\n'

            # Update sha256
            m = re.match('^(.*)sha256(\s+)[0-9a-f]{64}(.*)$', line)
            if m:
                sha = new.get_archive().sha256
                line = f'{m.group(1)}sha256{m.group(2)}{sha}{m.group(3)}\n'

            # Update size
            m = re.match('^(.*)size(\s+)\d+(.*)$', line)
            if m:
                size = new.get_archive().size
                line = f'{m.group(1)}size{m.group(2)}{size}{m.group(3)}\n'
            new_lines.append(line)

    # Handle dependencies
    old_depends_lib.extend([
        f'port-py${{python.version}}-{req.name}'
        for req in pdiff.new_requirements
    ])

    new_depends_lib = [
        f'{depend_libs_indent}depends_lib-append  {lib}' if i == 0
        else f'{" " * (len(depend_libs_indent) + len("depends_lib-append  "))}'
             f'{lib}'
        for i, lib in enumerate(old_depends_lib)
    ]

    # Create the new Portfile
    new_file = ''.join(new_lines[:old_depends_lineno])
    new_file += ' \\\n'.join(new_depends_lib) + '\n'
    new_file += ''.join(new_lines[old_depends_lineno:])
    print(new_file)


def main():
    pypi_name = sys.argv[1]
    portfile_path = f'py-{pypi_name.lower()}/Portfile'
    old_version = None
    with open(portfile_path) as f:
        for line in f.readlines():
            m = re.match('^version\s+(.*)\n', line)
            if m:
                old_version = m.group(1)
                break
        else:
            print(f'Could not find current version for {pypi_name}')
    update(portfile_path, pypi_name, old_version)


if __name__ == '__main__':
    main()
