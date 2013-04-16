# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Jan Safranek <jsafrane@redhat.com>
# -*- coding: utf-8 -*-

from openlmi.storage.StorageConfiguration import StorageConfiguration
import openlmi.common.cmpi_logging as cmpi_logging
import unittest

import sys
import StringIO

class CMPILoggerMock(object):
    """ Mockup of cmpi_bindings_pywbem Logger and env."""
    def __init__(self, stream):
        self.stream = stream

    def get_logger(self):
        return self

    def log_error(self, msg):
        self.stream.write("E:" + msg)

    def log_warn(self, msg):
        self.stream.write("W:" + msg)

    def log_info(self, msg):
        self.stream.write("I:" + msg)

    def log_debug(self, msg):
        self.stream.write("D:" + msg)

    def trace_warn(self, component, msg):
        self.stream.write("w:" + msg)

    def trace_info(self, component, msg):
        self.stream.write("i:" + msg)

    def trace_verbose(self, component, msg):
        self.stream.write("v:" + msg)

class TestLogging(unittest.TestCase):
    """
        Test logging with various configurations + also with dynamic
        configuration updates.
        
        This test is very fragile, it depends on trace messages in LogManager
        and StorageConfiguration.
    """
    def setUp(self):
        self.cmpi_stream = StringIO.StringIO()
        self.stderr_stream = StringIO.StringIO()
        # override stderr
        self.oldstderr = sys.stderr
        sys.stderr = self.stderr_stream

        self.cmpi_logger = CMPILoggerMock(self.cmpi_stream)
        self.logmgr = cmpi_logging.LogManager(self.cmpi_logger)
        self.logger = cmpi_logging.logger

    def test_default(self):
        """
            Test default configuration
            - INFO goes to CMPI.
            - nothing goes to stderr
        """
        StorageConfiguration.CONFIG_PATH = "/"
        StorageConfiguration.CONFIG_FILE = "/configs/not-existing.conf"
        cfg = StorageConfiguration()
        self.logmgr.set_config(cfg)

        # log at various log levels)
        self.logger.error("E1")
        self.logger.warn("W1")
        self.logger.info("I1")
        self.logger.debug("D1")
        self.logger.trace_warn("w1")
        self.logger.trace_info("i1")
        self.logger.trace_verbose("v1")

        # check that the messages went through CMPILoggerMock
        cmpi = self.cmpi_stream.getvalue()
        stderr = self.stderr_stream.getvalue()
        self.assertEqual(cmpi, "I:INFO: CMPI log startedE:ERROR: E1W:WARNING: W1I:INFO: I1")
        self.assertEqual(stderr, "")

    def test_tracing(self):
        """
            Test with enabled tracing
            - DEBUG and TRACE goes to CMPI.
            - nothing goes to stderr
        """
        StorageConfiguration.CONFIG_PATH = "/"
        StorageConfiguration.CONFIG_FILE = "/configs/not-existing.conf"
        cfg = StorageConfiguration()
        cfg.config.set("Log", "Debug", "true")
        self.logmgr.set_config(cfg)

        # log at various log levels)
        self.logger.error("E1")
        self.logger.warn("W1")
        self.logger.info("I1")
        self.logger.debug("D1")
        self.logger.trace_warn("w1")
        self.logger.trace_info("i1")
        self.logger.trace_verbose("v1")

        # check that the messages went through CMPILoggerMock
        cmpi = self.cmpi_stream.getvalue()
        stderr = self.stderr_stream.getvalue()
        self.assertEqual(cmpi, "I:INFO: CMPI log startedv:DEBUG: Exiting LogManager._config_changedv:DEBUG: Exiting LogManager.set_configE:ERROR: E1W:WARNING: W1I:INFO: I1v:DEBUG: D1w:Level 19: w1i:Level 18: i1v:DEBUG: v1")
        self.assertEqual(stderr, "")

    def test_stderr(self):
        """
            Test with enabled stderr
            - INFO goes to CMPI.
            - INFO goes to CMPI.
        """
        StorageConfiguration.CONFIG_PATH = "/"
        StorageConfiguration.CONFIG_FILE = "/configs/not-existing.conf"
        cfg = StorageConfiguration()
        cfg.config.set("Log", "Stderr", "true")

        self.logmgr.set_config(cfg)

        # log at various log levels)
        self.logger.error("E1")
        self.logger.warn("W1")
        self.logger.info("I1")
        self.logger.debug("D1")
        self.logger.trace_warn("w1")
        self.logger.trace_info("i1")
        self.logger.trace_verbose("v1")

        # check that the messages went through CMPILoggerMock
        cmpi = self.cmpi_stream.getvalue()
        stderr = self.stderr_stream.getvalue()
        self.assertEqual(cmpi, "I:INFO: CMPI log startedI:INFO: Started logging to stderr.E:ERROR: E1W:WARNING: W1I:INFO: I1")
        self.assertEqual(stderr, "INFO: Started logging to stderr.\nERROR: E1\nWARNING: W1\nINFO: I1\n")

    def test_tracing_stderr(self):
        """
            Test with enabled tracing and stderr
            - DEBUG and TRACE goes to CMPI.
            - DEBUG and TRACE goes to stderr.
        """
        StorageConfiguration.CONFIG_PATH = "/"
        StorageConfiguration.CONFIG_FILE = "/configs/not-existing.conf"
        cfg = StorageConfiguration()
        cfg.config.set("Log", "Debug", "true")
        cfg.config.set("Log", "Stderr", "true")
        self.logmgr.set_config(cfg)

        # log at various log levels)
        self.logger.error("E1")
        self.logger.warn("W1")
        self.logger.info("I1")
        self.logger.debug("D1")
        self.logger.trace_warn("w1")
        self.logger.trace_info("i1")
        self.logger.trace_verbose("v1")

        # check that the messages went through CMPILoggerMock
        cmpi = self.cmpi_stream.getvalue()
        stderr = self.stderr_stream.getvalue()
        self.assertEqual(cmpi, "I:INFO: CMPI log startedI:INFO: Started logging to stderr.v:DEBUG: Exiting LogManager._config_changedv:DEBUG: Exiting LogManager.set_configE:ERROR: E1W:WARNING: W1I:INFO: I1v:DEBUG: D1w:Level 19: w1i:Level 18: i1v:DEBUG: v1")
        self.assertEqual(stderr, "INFO: Started logging to stderr.\nDEBUG: Exiting LogManager._config_changed\nDEBUG: Exiting LogManager.set_config\nERROR: E1\nWARNING: W1\nINFO: I1\nDEBUG: D1\nLevel 19: w1\nLevel 18: i1\nDEBUG: v1\n")

    def test_dynamic_change(self):
        """
            Test with changing configuration
        """
        # start with the default on
        StorageConfiguration.CONFIG_PATH = "/"
        StorageConfiguration.CONFIG_FILE = "/configs/not-existing.conf"
        cfg = StorageConfiguration()
        self.logmgr.set_config(cfg)

        # log at various log levels)
        self.logger.error("E1")
        self.logger.warn("W1")
        self.logger.info("I1")
        self.logger.debug("D1")
        self.logger.trace_warn("w1")
        self.logger.trace_info("i1")
        self.logger.trace_verbose("v1")

        # enable tracing and stderr
        cfg.config.set("Log", "Debug", "true")
        cfg.config.set("Log", "Stderr", "true")
        cfg._call_listeners()

        # log at various log levels)
        self.logger.error("E2")
        self.logger.warn("W2")
        self.logger.info("I2")
        self.logger.debug("D2")
        self.logger.trace_warn("w2")
        self.logger.trace_info("i2")
        self.logger.trace_verbose("v2")

        # disable tracing and stderr
        cfg.config.set("Log", "Debug", "false")
        cfg.config.set("Log", "Stderr", "false")
        cfg._call_listeners()

        # log at various log levels)
        self.logger.error("E3")
        self.logger.warn("W3")
        self.logger.info("I3")
        self.logger.debug("D3")
        self.logger.trace_warn("w3")
        self.logger.trace_info("i3")
        self.logger.trace_verbose("v3")

        # check that the messages went through CMPILoggerMock
        cmpi = self.cmpi_stream.getvalue()
        stderr = self.stderr_stream.getvalue()
        self.assertEqual(cmpi, "I:INFO: CMPI log startedE:ERROR: E1W:WARNING: W1I:INFO: I1I:INFO: Started logging to stderr.v:DEBUG: Exiting LogManager._config_changedv:DEBUG: Exiting StorageConfiguration._call_listenersE:ERROR: E2W:WARNING: W2I:INFO: I2v:DEBUG: D2w:Level 19: w2i:Level 18: i2v:DEBUG: v2v:DEBUG: Entering StorageConfiguration._call_listenersv:DEBUG: Entering LogManager._config_changedI:INFO: Stopped logging to stderr.E:ERROR: E3W:WARNING: W3I:INFO: I3")
        self.assertEqual(stderr, "INFO: Started logging to stderr.\nDEBUG: Exiting LogManager._config_changed\nDEBUG: Exiting StorageConfiguration._call_listeners\nERROR: E2\nWARNING: W2\nINFO: I2\nDEBUG: D2\nLevel 19: w2\nLevel 18: i2\nDEBUG: v2\nDEBUG: Entering StorageConfiguration._call_listeners\nDEBUG: Entering LogManager._config_changed\nINFO: Stopped logging to stderr.\n")

    def tearDown(self):
        self.logmgr.destroy()
        # restore old stderr
        sys.stderr = self.oldstderr
        # and print all messages to it, we want asserts there
        sys.stderr.write(self.stderr_stream.getvalue())


if __name__ == '__main__':
    unittest.main()
