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
        old_names = [req.name for req in self.old.requirements.get('run', [])]
        new_names = [req.name for req in self.new.requirements.get('run', [])]
        added_names = set(new_names) - set(old_names)
        return [
            req for req in self.new.requirements.get('run', [])
            if req.name in added_names
        ]

    @property
    def updated_requirements(self):
        # TODO
        return []

    @property
    def deleted_requirements(self):
        old_names = [req.name for req in self.old.requirements.get('run', [])]
        new_names = [req.name for req in self.new.requirements.get('run', [])]
        deleted_names = set(old_names) - set(new_names)
        return [
            req for req in self.old.requirements.get('run', [])
            if req.name in deleted_names
        ]
        return []


def _reqformat(req):
    return f'port:py${{python.version}}-{req.name.lower()}'


def _clean_depends_line(line):
    if line.endswith('\n'):
        line = line[:-1]
    if line.endswith('\\'):
        line = line[:-1]
    return line.strip()


def _upgrade_depends(old_depends, pdiff, indent=''):
    # Start by removing requirements that are no longer needed
    for deleted_req in pdiff.deleted_requirements:
        try:
            old_depends.remove(_reqformat(deleted_req))
        except ValueError:
            pass

    # Then add new requirements
    old_depends.extend([
        _reqformat(req) for req in pdiff.new_requirements
    ])

    return [
        f'{indent}depends_lib-append  {lib}' if i == 0
        else f'{" " * (len(indent) + len("depends_lib-append  "))}'
             f'{lib}'
        for i, lib in enumerate(old_depends)
    ]


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
    with open(portfile_path) as f:
        for line in f.readlines():
            # TODO: should we also consider depends_lib?
            # NOTE: we only consider 0 or 1 level of indentation. More
            # indentation probably means we are in a special case (typically,
            # for specific versions of Python), and it is too tricky to handle
            # these.
            m = re.match('(    )?depends_lib-append(\s+)(.*)', line)
            if m:
                depend_libs_indent = m.group(1)
                in_depends_lib = True
                line = f'{m.group(3)}\n'

            if in_depends_lib:
                old_depends_lib.append(_clean_depends_line(line))
                if not line.endswith('\\\n'):
                    in_depends_lib = False
                    new_lines.append('DEPENDS_LIB_PLACEHOLDER')
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

    # Upgrade dependencies
    new_depends_lib = _upgrade_depends(old_depends_lib, pdiff,
                                       depend_libs_indent)

    # Create the new Portfile
    new_path = f'python/py-{pypi_name.lower()}/Portfile.new'
    print(f'[+] Writing new Portfile to {new_path}')
    with open(new_path, 'w') as f:
        new_file = ''.join(new_lines)
        new_file = new_file.replace('DEPENDS_LIB_PLACEHOLDER',
                                    ' \\\n'.join(new_depends_lib) + '\n')
        f.write(new_file)


def main():
    pypi_name = sys.argv[1]
    portfile_path = f'python/py-{pypi_name.lower()}/Portfile'
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
