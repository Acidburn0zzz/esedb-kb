#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Installation and deployment script."""

from __future__ import print_function

import glob
import locale
import os
import sys

try:
  from setuptools import find_packages, setup
except ImportError:
  from distutils.core import find_packages, setup

try:
  from distutils.command.bdist_msi import bdist_msi
except ImportError:
  bdist_msi = None

try:
  from distutils.command.bdist_rpm import bdist_rpm
except ImportError:
  bdist_rpm = None

version_tuple = (sys.version_info[0], sys.version_info[1])
if version_tuple[0] not in (2, 3):
  print('Unsupported Python version: {0:s}.'.format(sys.version))
  sys.exit(1)

elif version_tuple[0] == 2 and version_tuple < (2, 7):
  print((
      'Unsupported Python 2 version: {0:s}, version 2.7 or higher '
      'required.').format(sys.version))
  sys.exit(1)

elif version_tuple[0] == 3 and version_tuple < (3, 4):
  print((
      'Unsupported Python 3 version: {0:s}, version 3.4 or higher '
      'required.').format(sys.version))
  sys.exit(1)

# Change PYTHONPATH to include esedbrc so that we can get the version.
sys.path.insert(0, '.')

import esedbrc  # pylint: disable=wrong-import-position


if not bdist_msi:
  BdistMSICommand = None
else:
  class BdistMSICommand(bdist_msi):
    """Custom handler for the bdist_msi command."""

    def run(self):
      """Builds an MSI."""
      # Command bdist_msi does not support the library version, neither a date
      # as a version but if we suffix it with .1 everything is fine.
      self.distribution.metadata.version += '.1'

      bdist_msi.run(self)


if not bdist_rpm:
  BdistRPMCommand = None
else:
  class BdistRPMCommand(bdist_rpm):
    """Custom handler for the bdist_rpm command."""

    def _make_spec_file(self):
      """Generates the text of an RPM spec file.

      Returns:
        list[str]: lines of the RPM spec file.
      """
      # Note that bdist_rpm can be an old style class.
      if issubclass(BdistRPMCommand, object):
        spec_file = super(BdistRPMCommand, self)._make_spec_file()
      else:
        spec_file = bdist_rpm._make_spec_file(self)

      if sys.version_info[0] < 3:
        python_package = 'python2'
      else:
        python_package = 'python3'

      description = []
      requires = ''
      summary = ''
      in_description = False

      python_spec_file = []
      for line in iter(spec_file):
        if line.startswith('Summary: '):
          summary = line[9:]

        elif line.startswith('BuildRequires: '):
          line = 'BuildRequires: {0:s}-setuptools, {0:s}-devel'.format(
              python_package)

        elif line.startswith('Requires: '):
          requires = line[10:]
          if python_package == 'python3':
            requires = requires.replace('python-', 'python3-')
            requires = requires.replace('python2-', 'python3-')
          continue

        elif line.startswith('%description'):
          in_description = True

        elif line.startswith('python setup.py build'):
          if python_package == 'python3':
            line = '%py3_build'
          else:
            line = '%py2_build'

        elif line.startswith('python setup.py install'):
          if python_package == 'python3':
            line = '%py3_install'
          else:
            line = '%py2_install'

        elif line.startswith('%files'):
          lines = [
              '%files -n {0:s}-%{{name}}'.format(python_package),
              '%defattr(644,root,root,755)',
              '%license LICENSE',
              '%doc README']

          if python_package == 'python3':
            lines.extend([
                '%{python3_sitelib}/esedbrc/*.py',
                '%{python3_sitelib}/esedbrc*.egg-info/*',
                '',
                '%exclude %{_prefix}/share/doc/*',
                '%exclude %{python3_sitelib}/esedbrc/__pycache__/*',
                '%exclude %{_bindir}/*.py'])

          else:
            lines.extend([
                '%{python2_sitelib}/esedbrc/*.py',
                '%{python2_sitelib}/esedbrc*.egg-info/*',
                '',
                '%exclude %{_prefix}/share/doc/*',
                '%exclude %{python2_sitelib}/esedbrc/*.pyc',
                '%exclude %{python2_sitelib}/esedbrc/*.pyo',
                '%exclude %{_bindir}/*.py'])

          python_spec_file.extend(lines)
          break

        elif line.startswith('%prep'):
          in_description = False

          python_spec_file.append(
              '%package -n {0:s}-%{{name}}'.format(python_package))
          if python_package == 'python2':
            python_spec_file.extend([
                'Obsoletes: python-esedbrc < %{version}',
                'Provides: python-esedbrc = %{version}'])
            python_summary = 'Python 2 module of {0:s}'.format(summary)
          else:
            python_summary = 'Python 3 module of {0:s}'.format(summary)

          if requires:
            python_spec_file.append('Requires: {0:s}'.format(requires))

          python_spec_file.extend([
              'Summary: {0:s}'.format(python_summary),
              '',
              '%description -n {0:s}-%{{name}}'.format(python_package)])

          python_spec_file.extend(description)

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and not line:
            continue

          description.append(line)

        python_spec_file.append(line)

      return python_spec_file


if version_tuple[0] == 2:
  encoding = sys.stdin.encoding  # pylint: disable=invalid-name

  # Note that sys.stdin.encoding can be None.
  if not encoding:
    encoding = locale.getpreferredencoding()

  # Make sure the default encoding is set correctly otherwise on Python 2
  # setup.py sdist will fail to include filenames with Unicode characters.
  reload(sys)  # pylint: disable=undefined-variable

  sys.setdefaultencoding(encoding)  # pylint: disable=no-member


esedbrc_description = (
    'Extensible Storage Engine (ESE) Database resources (esedbrc)')

esedbrc_long_description = (
    'esedbrc is a Python module part of esedb-kb to allow reuse of Extensible '
    'Storage Engine (ESE) Database resources.')

setup(
    name='esedbrc',
    version=esedbrc.__version__,
    description=esedbrc_description,
    long_description=esedbrc_long_description,
    license='Apache License, Version 2.0',
    url='https://github.com/libyal/esedb-kb',
    maintainer='Joachim Metz',
    maintainer_email='joachim.metz@gmail.com',
    cmdclass={
        'bdist_msi': BdistMSICommand,
        'bdist_rpm': BdistRPMCommand},
    classifiers=[
        '',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages('.', exclude=[
        'scripts', 'tests', 'tests.*', 'utils']),
    package_dir={
        'esedbrc': 'esedbrc'
    },
    scripts=glob.glob(os.path.join('scripts', '[a-z]*.py')),
    data_files=[
        ('share/doc/esedbrc', [
            'LICENSE', 'README']),
    ],
)
