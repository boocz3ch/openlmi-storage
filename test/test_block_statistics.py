#!/usr/bin/python
# -*- Coding:utf-8 -*-
#
# Copyright (C) 2013 Red Hat, Inc.  All rights reserved.
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

from test_base import StorageTestBase
import unittest
import pywbem
import subprocess

class TestBlockStatistics(StorageTestBase):
    """
    Test that statistics provided by LMI_BlockStatisticsData and
    LMI_BlockStatisticsService are roughly accurate.
    """

    def _write_data(self, kbytes, device):
        """
        Write given nr. of kilobytes to given device.
        :param kbytes: ``int`` Nr. of kilobybytes to write.
        :param device: ``string`` Name of the device file.
        """
        subprocess.call(["dd", "if=/dev/zero", "of=" + device, "bs=1024",
                "count=%d" % (kbytes)])

    def _read_data(self, kbytes, device):
        """
        Read given nr. of kilobytes from given device.
        :param kbytes: ``int`` Nr. of kilobybytes to read.
        :param device: ``string`` Name of the device file.
        """
        subprocess.call(["dd", "if=" + device, "of=/dev/zero", "bs=1024",
                "count=%d" % (kbytes)])

    def test_data(self):
        """
        Test LMI_BlockStatisticsData.
        """
        # Load LMI_BlockStatisticsData of each partition.
        initial_stats = []
        for partition in self.partition_names:
            stats = self.wbemconnection.Associators(
                    partition,
                    ResultClass="LMI_BlockStorageStatisticalData")
            self.assertEquals(len(stats), 1)
            stat = stats[0]
            initial_stats.append(stat)

        # Generate some load
        for part in self.partitions:
            self._read_data(1024, part)
            self._write_data(2048, part)

        i = 0
        for partition in self.partition_names:
            stats = self.wbemconnection.Associators(
                    partition,
                    ResultClass="LMI_BlockStorageStatisticalData")
            self.assertEquals(len(stats), 1)
            stat = stats[0]
            initial_stat = initial_stats[i]

            # Just common sense tests.
            self.assertEquals(stat['InstanceID'], initial_stat['InstanceID'])
            self.assertEquals(stat['ElementName'], initial_stat['ElementName'])
            self.assertEquals(stat['ElementType'], initial_stat['ElementType'])
            self.assertEquals(stat['ElementType'], 9)  # Extent
            self.assertGreater(
                    stat['IOTimeCounter'], initial_stat['IOTimeCounter'])
            self.assertGreater(
                    stat['KBytesWritten'], initial_stat['KBytesWritten'])
            self.assertGreater(
                    stat['KBytesWritten'], initial_stat['KBytesWritten'])
            self.assertGreater(stat['ReadIOs'], initial_stat['ReadIOs'])
            self.assertGreater(stat['TotalIOs'], initial_stat['TotalIOs'])
            self.assertGreater(stat['WriteIOs'], initial_stat['WriteIOs'])
            self.assertGreater(
                    stat['KBytesTransferred'],
                    initial_stat['KBytesTransferred'])

            # Test that the counter have expected values
            # From some reason, the read counter includes also writes...
            self.assertAlmostEquals(
                    stat['KBytesRead'],
                    initial_stat['KBytesRead'] + 1024 + 2048,
                    delta=3 * 256)
            self.assertAlmostEquals(
                    stat['KBytesWritten'],
                    initial_stat['KBytesWritten'] + 2048,
                    delta=256)

            # Check the counters match each other
            self.assertEquals(stat['TotalIOs'],
                    stat['ReadIOs'] + stat['WriteIOs'])
            self.assertEquals(stat['KBytesTransferred'],
                    stat['KBytesWritten'] + stat['KBytesRead'])

            i += 1

    def test_get_collection(self):
        """
        Test LMI_BlockStatisticsService.GetStatisticsCollection
        """
        service = self.wbemconnection.EnumerateInstanceNames(
                "LMI_BlockStatisticsService")[0]

        # load the stats
        (ret, outparams) = self.wbemconnection.InvokeMethod(
                "GetStatisticsCollection",
                service)
        self.assertEquals(ret, 0)
        self.assertEquals(len(outparams), 1)
        # Join all statistics[] into one string
        stats = "\n".join(outparams['statistics'])

        self.assertGreater(len(stats), 0)

        # Load and parse the column headers
        manifest = self.wbemconnection.EnumerateInstances(
                "LMI_BlockStatisticsManifest")[0]
        columns = manifest['CSVSequence']

        # The first column must be InstanceID
        self.assertEquals(columns[0], "InstanceID")


        # Check all the lines have the same value as related
        # LMI_BlockStorageStatisticalData instance
        for line in stats.split("\n"):
            try:
                i = None
                if line == '':
                    continue
                # Parse the line
                values = line.split(";")
                self.assertEquals(len(columns), len(values))

                # Get the LMI_BlockStorageStatisticalData
                instanceid = values[0]
                path = pywbem.CIMInstanceName(
                        classname="LMI_BlockStorageStatisticalData",
                        namespace="root/cimv2",
                        keybindings={ 'InstanceID': instanceid})
                stats = self.wbemconnection.GetInstance(path)

                # Finally, check all columns except StatisticsTime
                for i in xrange(len(columns)):
                    if columns[i] == "StatisticTime":
                        continue
                    value = stats[columns[i]]
                    if isinstance(value, pywbem.Uint64):
                        # Compare counters with grain of salt, e.g. system disk
                        # can be busy. Use 1% as tolerance
                        self.assertAlmostEquals(int(values[i]), value,
                                delta=value * 0.01)
                    else:
                        self.assertEquals(values[i], str(value))
            except Exception:
                # Print something useful and not generic 'xyz' != 'abc'
                if i is not None:
                    column_name = columns[i]
                else:
                    column_name = ""
                print "Error on line: '%s', column %d(%s)" % (line, i,
                        column_name)
                raise


if __name__ == '__main__':
    unittest.main()
