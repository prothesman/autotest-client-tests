# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging

from autotest.client import test, utils
from autotest.client.shared import error



class libdrm(test.test):
    version = 1
    _services = None

    def run_once(self):
        num_errors = 0
        keyvals = {}

        # These are tests to run for all platforms.
        tests_common = ['modetest']
        tests = tests_common + ['kmstest']

        for test in tests:
            # Make sure the test exists on this system.  Not all tests may be
            # present on a given system.
            if utils.system('which %s' % test):
                logging.error('Could not find test %s.', test)
                keyvals[test] = 'NOT FOUND'
                num_errors += 1
                continue

            # Run the test and check for success based on return value.
            return_value = utils.system(test)
            if return_value:
                logging.error('%s returned %d', test, return_value)
                num_errors += 1
                keyvals[test] = 'FAILED'
            else:
                keyvals[test] = 'PASSED'

        self.write_perf_keyval(keyvals)

        if num_errors > 0:
            raise error.TestFail('Failed: %d libdrm tests failed.' % num_errors)
