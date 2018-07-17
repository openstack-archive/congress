# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('./'))
# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.todo',
    'sphinxcontrib.apidoc',
    'oslo_config.sphinxext',
    'oslo_config.sphinxconfiggen',
]

# Don't use default openstack theme, for readthedocs
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:
    extensions.append('openstackdocstheme')

# openstackdocstheme options
repository_name = 'openstack/congress'
bug_project = 'congress'
bug_tag = ''
# autodoc generation is a bit aggressive and a nuisance when doing heavy
# text edit cycles.
# execute "export SPHINX_DEBUG=1" in your terminal to disable

# sphinxcontrib.apidoc options
apidoc_module_dir = '../../congress'
apidoc_output_dir = 'api'
apidoc_excluded_paths = [
    'datalog/Python2/*',
    'datalog/Python3/*',
    'db/migration/alembic_migrations/*',
    'server/*',
    'tests/*',
    '/dse2/disabled_test_control_bus.py']

apidoc_separate_modules = True

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'congress'
copyright = u'2013, OpenStack Foundation'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of glob-style patterns that should be excluded when looking for
# source files. They are matched against the source file names relative to the
# source directory, using slashes as directory separators on all platforms.
exclude_patterns = ['api/congress.db.migration.alembic_migrations.*',
                    'api/congress.server.*']


# A list of ignored prefixes for module index sorting.
modindex_common_prefix = ['congress.']

autodoc_mock_imports = ['congress.datalog.Python2', 'congress.datalog.Python3',
                        'cloudfoundryclient', 'congress.dse',
                        'monascaclient']

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
# html_theme_path = ["."]
html_theme = 'openstackdocs'
html_static_path = ['_static']

# Output file base name for HTML help builder.
htmlhelp_basename = '%sdoc' % project

html_last_updated_fmt = '%Y-%m-%d %H:%M'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
    ('index',
     '%s.tex' % project,
     u'%s Documentation' % project,
     u'OpenStack Foundation', 'manual'),
]

# Example configuration for intersphinx: refer to the Python standard library.
#intersphinx_mapping = {'http://docs.python.org/': None}

# -- Options for oslo_config.sphinxconfiggen ---------------------------------

config_generator_config_file = [
    ('../../etc/congress-config-generator.conf',
     '_static/congress'),
    ('../../etc/congress-agent-config-generator.conf',
     '_static/congress-agent')
]


[extensions]
todo_include_todos=True
