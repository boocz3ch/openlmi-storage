#!/bin/bash

#
# Helper script to generate developer documentation in
# doc/devel/modules and index.rst
#

TOPDIR=../..

mkdir $TOPDIR/doc/devel/modules

# index.rst header
cat >$TOPDIR/doc/devel/index.rst <<_EOF_
.. OpenLMI Storage developer documentation

Welcome to OpenLMI Storage developer documentation!
===================================================

Contents:

.. toctree::

_EOF_

# Generate modules/*.rst
for module in $TOPDIR/src/openlmi/storage/*.py; do
    module=`basename $module`
    name=${module%.py}
    out=$name.rst
    len=`echo $name | wc -c`
    len=$(($len-1))
    underline=""
    for i in `seq $len`; do underline="=$underline"; done

    cat >$TOPDIR/doc/devel/modules/$out  <<_EOF_
$name
$underline
.. automodule:: openlmi.storage.$name

_EOF_
    echo >>$TOPDIR/doc/devel/index.rst "    modules/$name"
done

# index.rst footer
cat >>$TOPDIR/doc/devel/index.rst <<_EOF_
    :maxdepth: 2

Indices and tables
==================

* :ref:\`genindex\`
* :ref:\`modindex\`
* :ref:\`search\`

_EOF_
