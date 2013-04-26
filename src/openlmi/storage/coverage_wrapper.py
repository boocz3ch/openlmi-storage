# OpenLMI Storage Provider
#
# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
    This is a simple wrapper to gather test coverage of OpenLMI storage
    providers.

    It is special provider module, which starts collecting the coverage
    and just calls cimom_entry provider module functions.
"""

import os

COVERAGE_DIRECTORY = "/var/lib/openlmi-storage/coverage/"
LOGFILE_NAME = COVERAGE_DIRECTORY + "coverage.err"
COVERAGE_FILE = COVERAGE_DIRECTORY + "coverage."

def start_coverage():
    """ Start collecting coverage. """
    # create directory for logs
    if not os.path.isdir(COVERAGE_DIRECTORY):
        os.makedirs(COVERAGE_DIRECTORY)

    # find unused file name
    i = 0
    while os.path.exists(COVERAGE_FILE + str(i)):
        i = i + 1
    coverage_file = COVERAGE_FILE + str(i)

    try:
        print "Loading coverage"
        import coverage
        cov = coverage.coverage(auto_data=True,
                data_file=coverage_file)
        # remove any previous error file
        if os.path.exists(LOGFILE_NAME):
            os.remove(LOGFILE_NAME)
        print "Starting coverage"
        cov.start()
    except ImportError:
        msg = "'import coverage' failed, no coverage report will be generated."
        print(msg)
        log = open(LOGFILE_NAME, "w")
        log.write(msg + "\n")
        log.close()
        cov = None
    return cov

# Pylint expects that only constants are on global level, but we have one
# global variable + we assign also functions below.
# Also we *do* check if the wrapped provider module has all methods
# we access (with hasattr(cimom_entry,...))
# pylint: disable-msg=C0103,E1101

mycoverage = start_coverage()
# import the cimom_entry only when the coverage has started
# (so we can measure the initialization coverage)
import openlmi.storage.cimom_entry as cimom_entry

def shutdown(env):
    """Called from CIMOM on shutdown."""
    if mycoverage:
        print "Stopping coverage"
        mycoverage.stop()
        mycoverage.save()
    if hasattr(cimom_entry, 'shutdown'):
        return cimom_entry.shutdown(env)

# forward all other provider module methods to cmpi_bindings
if hasattr(cimom_entry, 'init'):
    init = cimom_entry.init
if hasattr(cimom_entry, 'get_providers'):
    get_providers = cimom_entry.get_providers
if hasattr(cimom_entry, 'can_unload'):
    can_unload = cimom_entry.can_unload
if hasattr(cimom_entry, 'handle_indication'):
    handle_indication = cimom_entry.handle_indication
if hasattr(cimom_entry, 'authorize_filter'):
    authorize_filter = cimom_entry.authorize_filter
if hasattr(cimom_entry, 'activate_filter'):
    activate_filter = cimom_entry.activate_filter
if hasattr(cimom_entry, 'deactivate_filter'):
    deactivate_filter = cimom_entry.deactivate_filter
if hasattr(cimom_entry, 'enable_indications'):
    enable_indications = cimom_entry.enable_indications
if hasattr(cimom_entry, 'disable_indications'):
    disable_indications = cimom_entry.disable_indications

# pylint: enable-msg=C0103,E1101
