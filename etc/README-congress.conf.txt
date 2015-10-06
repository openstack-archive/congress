To generate the sample congress.conf file, run the following
command from the top level of the congress directory (may need root
privilege):

tox -egenconfig #Generates etc/congress.conf.sample

If tox is not installed, you may install it as follows:

$ sudo pip install tox==2.1.1

If you experience error(s) generating a sample conf file
you may be able to resolve them by installing the following
tested versions:

$ sudo pip install -I virtualenv==13.1.2
$ sudo pip install -I setuptools==18.3.2
$ sudo pip install -I tox==2.1.1
