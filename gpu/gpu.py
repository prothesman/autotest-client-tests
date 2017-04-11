import logging
import os
import re
import string
import subprocess
import time

from autotest.client import test, utils
from autotest.client.shared import error

GLMARK2_TEST_RE = (
    r'^\[(?P<scene>.*)\] (?P<options>.*): FPS: (?P<fps>\d+) FrameTime: '
    r'(?P<frametime>\d+.\d+) ms$')
GLMARK2_SCORE_RE = r'glmark2 Score: (\d+)'

# perf value description strings may only contain letters, numbers, periods,
# dashes and underscores.
# But glmark2 test names are usually in the form:
#   scene-name:opt=val:opt=v1,v2;v3,v4 or scene:<default>
# which we convert to:
#   scene-name.opt_val.opt_v1-v2_v3-v4 or scene.default
description_table = string.maketrans(':,=;', '.-__')
description_delete = '<>'

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

class gpu(test.test):
    version = 1

    def run_once(self, size='1920x1080', stress=False, offscreen=True, stress_length=100):

        execute_cnt = 0
        options = []

        options.append('--size %s' % size)
        if offscreen:
            options.append('--off-screen')

        if cmd_exists("glmark2-es2"):
            cmd = "glmark2-es2" + ' ' + ' '.join(options)
        else:
            cmd = "glmark2-es2-drm" + ' ' + ' '.join(options)

        while True:

            # In this test we are manually handling stderr, so expected=True.
            # Strangely autotest takes CmdError/CmdTimeoutError as warning only.
            try:
                result = utils.run(cmd)
            except error.CmdError:
                raise error.TestFail('Failed: CmdError running %s' % cmd)
            except error.CmdTimeoutError:
                raise error.TestFail('Failed: CmdTimeout running %s' % cmd)

            logging.info(result)
            for line in result.stderr.splitlines():
                if line.startswith('Error:'):
                    # Line already starts with 'Error: ", not need to prepend.
                    raise error.TestFail(line)

            if not stress:
                break
            else:
                # usually 500min
                execute_cnt += 1
                if execute_cnt > stress_length:
                    break;

        # Numbers in hasty mode are not as reliable, so don't send them to
        # the dashboard etc.
        if not stress:
            keyvals = {}
            score = None
            test_re = re.compile(GLMARK2_TEST_RE)
            for line in result.stdout.splitlines():
                match = test_re.match(line)
                if match:
                    test = '%s.%s' % (match.group('scene'),
                                      match.group('options'))
                    test = test.translate(description_table, description_delete)
                    frame_time = match.group('frametime')
                    keyvals[test] = frame_time
                else:
                    # glmark2 output the final performance score as:
                    #  glmark2 Score: 530
                    match = re.findall(GLMARK2_SCORE_RE, line)
                    if match:
                        score = int(match[0])
            if score is None:
                raise error.TestFail('Failed: Unable to read benchmark score')
            # Output numbers for plotting by harness.
            logging.info('GLMark2 score: %d', score)
            keyvals['glmark2_score'] = score
            self.write_perf_keyval(keyvals)
