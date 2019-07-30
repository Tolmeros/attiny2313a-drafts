#!/usr/bin/env python

import argparse
import re

#import pavrasm


out_dir = 'tmp/'

command_start_re = r'^ ?#'
command_end_re = r' ?$'
ivect_re = command_start_re + r'ivect +([a-zA-Z0-9_]*) +([a-zA-Z0-9_]*)' + command_end_re

asm_directive_cseg_re = r'^ ?\.cseg ?$'

def p_warning(text):
    print('WARNING: %s' % (text,))

def parse_ivect(scope, param):
    if param[0] in scope.ivect:
        p_warning('redefinition ivect `%s`.' % (param[0],))
    scope.ivect[param[0]] = param[1]
    pass


def parse_device(scope, param):
    scope.device = param[0]

class DraftPreproc(object):
    devices = {
        'attiny2313a':{
            'interrupt_vector':('RESET', 'INT0', 'INT1', 'ICP1', 'OC1A', 'OVF1',
                                'OVF0', 'URXC', 'UDRE', 'UTXC', 'ACI', 'PCI',
                                'OC1B', 'OC0A', 'OC0B', 'USI_START', 'USI_OVF',
                                'ERDY', 'WDT'),
            'interrupt_vector_size':'INT_VECTORS_SIZE'
        }
    }
    """docstring for DraftPreproc"""
    def __init__(self, in_filename, out_filename):
        #super(DraftPreproc, self).__init__()
        self.in_filename = in_filename
        self.out_filename = out_filename
        self.device = '';
        self.ivect = {}
        self.stage_1_directives = {}
        self.add_stage_1_directive(
                'device',
                parse_device,
                command_start_re + r'device +([a-zA-Z0-9_]*)' + command_end_re
            )

    def __decode_stage_1(self, line, line_number, filename):
        for key, values in self.stage_1_directives.items():
            match = re.search(values['re'], line)
            if match:
                values['function'](scope=self, param=match.groups())
                break

    def __is_directive(self, line):
        for key, values in self.stage_1_directives.items():
            match = re.search(values['re'], line)
            if match:
                return True
                break

        return False



    def add_stage_1_directive(self, name, function, re):
        self.stage_1_directives[name] = {
            'function': function,
            're': re,
        }

    def first_pass(self):
        with open(self.in_filename) as infile:
            line = infile.readline()
            cnt = 1
            while line:
                self.__decode_stage_1(line, cnt, self.in_filename)
                line = infile.readline()
                cnt += 1

    def __make_ivect(self):
        asm_code = ['.org 0']
        for ivect_name in self.devices[self.device]['interrupt_vector']:
            print(ivect_name)
            if ivect_name in self.ivect:
                asm_code.append('rjmp %s' % (self.ivect[ivect_name]))
            else:
                asm_code.append('reti')

        # как это сделать красиво?
        if 'interrupt_vector_size' in self.devices[self.device]:
            asm_code.append('')
            asm_code.append('.org %s' % (self.devices[self.device]['interrupt_vector_size']))

        asm_code.append('')
        return '\n'.join(asm_code)

    def last_pass(self):
        with open(self.in_filename) as infile, open(self.out_filename, 'w') as outfile:
            line = infile.readline()
            cnt = 1

            while line:
                if not self.__is_directive(line):
                    outfile.write(line)
                    if re.match(asm_directive_cseg_re, line, re.IGNORECASE):
                        outfile.write(self.__make_ivect())

                line = infile.readline()
                cnt += 1


        


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filename',
        help='Input file name.'
    )

    args = parser.parse_args()

    preproc = DraftPreproc(args.filename, out_dir+args.filename)
    preproc.add_stage_1_directive('ivect', parse_ivect, ivect_re)
    preproc.first_pass()


    print(preproc.device)
    print(preproc.ivect)

    preproc.last_pass()

    '''
    with open(args.filename) as infile, open(out_dir+args.filename, 'w') as outfile:
        line = infile.readline()
        cnt = 1
        while line:
            print("Line {}: {}".format(cnt, line.strip()))
            line = infile.readline()
            cnt += 1
    '''




if __name__=='__main__':
    main()
