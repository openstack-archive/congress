To generate the sample congress.conf file, run the following
command from the top level of the congress directory (may need root
privilege):

tox -egenconfig #Generates etc/congress.conf.sample

If tox is not installed, you may install it as follows:

$ sudo pip install tox

If you experience error(s) generating a sample conf file
you may be able to resolve them by ensuring you have
virtualenv version 12.0.0 or higher installed.

$ virtualenv --version # check virtualenv version
