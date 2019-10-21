import unittest

import upt
import upt_macports_update as umu


class TestUptDiff(unittest.TestCase):
    def test_requirements(self):
        old = upt.Package('foo', '1.0')
        old.requirements = {
            'run': [
                upt.PackageRequirement('bar'),
            ]
        }
        new = upt.Package('foo', '1.0')
        new.requirements = {
            'run': [
                upt.PackageRequirement('baz'),
            ]
        }
        pdiff = umu.UptDiff(old, new)

        self.assertEqual(pdiff.new_requirements,
                         [upt.PackageRequirement('baz')])
        self.assertEqual(pdiff.deleted_requirements,
                         [upt.PackageRequirement('bar')])


class TestPrototype(unittest.TestCase):
    def test_upgrade_depends(self):
        old = upt.Package('foo', '1.0')
        old.requirements = {
            'run': [
                upt.PackageRequirement('bar'),
            ]
        }
        new = upt.Package('foo', '1.1')
        new.requirements = {
            'run': [
                upt.PackageRequirement('baz'),
            ]
        }
        pdiff = umu.UptDiff(old, new)
        old_depends = [
            'port:py${python.version}-bar',
        ]
        new_depends = umu._upgrade_depends(old_depends, pdiff)
        expected = [
            'port:py${python.version}-baz',
        ]
        self.assertEqual(new_depends, expected)


if __name__ == '__main__':
    unittest.main()
