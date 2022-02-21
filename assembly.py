import argparse
from typing import List, Tuple
import traceback


class Assembler():
    register_types = {"A": 0, "R": 1}

    def __init__(self) -> None:
        self.registers = ["0x0000"] * 9
        self.raw = []
        self.assembled = []
        self.instructions = {"load": ("0000", ('load R0, 5'), self._load),
                             "add": ("0001", ('add R1, R2, 100', 'add R1, R2, R0'), self._add),
                             "sub": ("0010", ('sub R0, R1, 20', 'sub R0, R2, R1'), self._sub),
                             "mul": ("0011", ('mul R3, R2, 4', 'mul R3, R2, R1'), self._mul),
                             "goto": ("0100", ('goto 3'), self._goto),
                             "gotoeq": ("0101", ('gotoeq R1, R0, 4'), self._gotoeq),
                             "gotolt": ("0110", ('gotolt R1, R2, 5'), self._gotolt),
                             "gotogt": ("0111", ('gotogt R2, R3, 12'), self._gotogt),
                             "mv": ("1000", ('mv A0, R1'), self._mv),
                             "system": ("1001", ('system'), self._system)}

    def _translate(self, instruction: str) -> Tuple[str, str]:
        opcode, values = self._split_instruction(instruction)
        opcode = opcode.rstrip()
        values = [value.rstrip() for value in values]
        op = self.instructions[opcode][0]
        values_binary = []

        if opcode =='load':
            assert(len(values) == 2 and self._is_register(values[0]) and not self._is_register(
            values[1])), f'Incorrect values for instruction {opcode}. Use formats {self.instructions[opcode][1]}'
        elif opcode in ('add', 'sub','mul'):
            assert(len(values) == 3 and self._is_register(values[0]) and self._is_register(
            values[1])), f'Incorrect values for instruction {opcode} only value in position 2 can be constant. Use formats {self.instructions[opcode][1]}'
        elif opcode =='goto':
            assert(len(values) == 1 and not self._is_register(
            values[0])), f'Incorrect values for instruction {opcode}. Use formats {self.instructions[opcode][1]}'
            line = int(values[0])
            assert(line >= 1 and line <= len(self.raw)),f"integers must be between 1 and {len(self.raw)}"
        elif opcode in ('gotoeq','gotolt','gotogt'):
            assert(len(values) == 3 and self._is_register(values[0]) and self._is_register(
            values[1]) and not self._is_register(values[2])), f'Incorrect values for instruction {opcode}. Use formats {self.instructions[opcode][1]}'
            line = int(values[2])
            assert(line >= 1 and line <= len(self.raw)),f"integers must be between 1 and {len(self.raw)}"
        elif opcode == 'mv':
            assert(len(values) == 2 and self._is_register(values[0]) and self._is_register(
            values[1])), f'Incorrect values for instruction {opcode}. Use formats {self.instructions[opcode][1]}'
        

        for value in values:
            if self._is_register(value):
                index = int(value[1:]) + Assembler.register_types[value[0]]
                values_binary.append(f'{index:04b}')
            else:
                if value=='':
                    value_int = 0
                else: value_int = int(value)
                assert (value_int >= -32768 and value_int <
                        32768), "integers must be between -32768 and 32767"
                values_binary.append(self._to_twos_complement(value_int))
        values_str = "".join(values_binary)
        assert len(
            values_str) <= 28, f"Invalid instruction, instruction must be of the following formats {self.instructions[opcode][1]}"
        if len(values_str) < 28:
            values_str += '0' * (28-len(values_str))
        op_hex = self._binary_to_hex(op, 1)
        instruction_hex = self._binary_to_hex(values_str, 7)
        return op_hex, instruction_hex

    def assemble(self, buffer: List[str]):
        self.raw = buffer
        self.current_instruction = 0
        self.assembled = [self._translate(instruction)
                          for instruction in buffer]

    def execute(self):
        assert (len(self.raw) == len(self.assembled)
                ), "You must assemble before execution"
        while self.current_instruction < len(self.raw):
            instruction = self.raw[self.current_instruction]
            opcode, values = self._split_instruction(instruction)
            opcode = opcode.rstrip()
            func = self.instructions[opcode][2]
            previous_instruction = self.current_instruction
            func(*values)
            if self.current_instruction == previous_instruction:
                self.current_instruction += 1

    def _split_instruction(self, instruction: str) -> Tuple[str, List[str]]:
        split = instruction.split(" ")
        opcode = split[0]
        values = "".join(split[1:]).split(",")
        return opcode, values

    def _to_twos_complement(self, integer):
        return f'{integer % (1 << 16):016b}'

    def _binary_to_hex(self, binary, size):
        format = f'0{size}x'
        hex = f'0x{int(binary,2):{format}}'
        return hex

    def _from_twos_complement(self, hex):
        as_int = int(hex, 16)
        if as_int & (1 << 15) != 0:
            as_int -= (1 << 16)
        return as_int

    def _load(self, *args):
        integer = int(args[1])
        register = int(args[0][1]) + self.register_types[args[0][0]]
        hex_int = self._binary_to_hex(self._to_twos_complement(integer), 4)
        self.registers[register] = hex_int

    def _add(self, *args):
        result_register = int(args[0][1]) + self.register_types[args[0][0]]
        val1 = self._from_twos_complement(
            self.registers[int(args[1][1]) + self.register_types[args[1][0]]])
        val2 = self._from_twos_complement(self.registers[int(
            args[2][1]) + self.register_types[args[2][0]]]) if self._is_register(args[2]) else int(args[2][0])
        result = val1+val2
        hex_int = self._binary_to_hex(self._to_twos_complement(result), 4)
        self.registers[result_register] = hex_int

    def _sub(self, *args):
        result_register = int(args[0][1]) + self.register_types[args[0][0]]
        val1 = self._from_twos_complement(
            self.registers[int(args[1][1]) + self.register_types[args[1][0]]])
        val2 = self._from_twos_complement(self.registers[int(
            args[2][1]) + self.register_types[args[2][0]]]) if self._is_register(args[2]) else int(args[2][0])
        result = val1-val2
        hex_int = self._binary_to_hex(self._to_twos_complement(result), 4)
        self.registers[result_register] = hex_int

    def _mul(self, *args):
        result_register = int(args[0][1]) + self.register_types[args[0][0]]
        val1 = self._from_twos_complement(
            self.registers[int(args[1][1]) + self.register_types[args[1][0]]])
        val2 = self._from_twos_complement(self.registers[int(
            args[2][1]) + self.register_types[args[2][0]]]) if self._is_register(args[2]) else int(args[2][0])
        result = val1*val2
        hex_int = self._binary_to_hex(self._to_twos_complement(result), 4)
        self.registers[result_register] = hex_int

    def _goto(self, *args):  
        line = int(args[0])
        line -= 1
        self.current_instruction = line

    def _gotoeq(self, *args):
        value_int = self._from_twos_complement(
            self.registers[int(args[0][1]) + self.register_types[args[0][0]]])
        comp = self._from_twos_complement(
            self.registers[int(args[1][1]) + self.register_types[args[1][0]]])
        line = int(args[2])
        line -= 1
        if value_int == comp:
            self.current_instruction = line

    def _gotolt(self, *args):
        value_int = self._from_twos_complement(
            self.registers[int(args[0][1]) + self.register_types[args[0][0]]])
        comp = self._from_twos_complement(
            self.registers[int(args[1][1]) + self.register_types[args[1][0]]])
        line = int(args[2])
        line -= 1
        if value_int < comp:
            self.current_instruction = line

    def _gotogt(self, *args):
        value_int = self._from_twos_complement(
            self.registers[int(args[0][1]) + self.register_types[args[0][0]]])
        comp = self._from_twos_complement(
            self.registers[int(args[1][1]) + self.register_types[args[1][0]]])
        line = int(args[2])
        line -= 1
        if value_int > comp:
            self.current_instruction = line

    def _mv(self, *args):
        self.registers[int(args[0][1]) + self.register_types[args[0][0]]
                       ] = self.registers[int(args[1][1]) + self.register_types[args[1][0]]]

    def _system(self, *args):
        if bool(self.registers[0]) and bool(int(self.registers[0], 16)):
            print(self._from_twos_complement(self.registers[0]))

    def _is_register(self, value: str) -> bool:
        if not bool(value): return False
        return value[0] in Assembler.register_types.keys()

def read_file(filepath : str) -> List[str]:
    file = open(filepath)
    return file.readlines()

def print_assembled(assembler : Assembler):
    print(f'{"Opcode":>6}{"Values":>10}')
    for instruction in assembler.assembled:
        print(f'{instruction[0]:>3}{instruction[1]:>16}')

def print_registers(assembler : Assembler):
    print(f"\n{'Register':>8}{'Value':>8}")
    a_register = assembler.register_types['A']
    print(f'{"A"+str(a_register):2s}{assembler.registers[a_register]:>15}')
    for index,value in enumerate(assembler.registers[1:]):
        print(f'{"R"+str(index):>2}{value:>15}')
    print('\n')

def parse_args():
    parser = argparse.ArgumentParser(description="Steven Cassidy's simple assembler")
    parser.add_argument('-l', '--load_file', dest='load_file',
                        help='The file you would like to assemble', required=False)
    parser.add_argument('-a', '--assemble', dest='assemble',
                        help='Assemble the code', required=False)
    parser.add_argument('-x', '--execute', dest='execute',
                        help='Execute the code', required=False)
    args = parser.parse_args()
    return args

if __name__=='__main__':

    args = parse_args()
    filepath = None
    assembler = Assembler()
    
    try:
        if args.load_file:
            filepath = args.load_file
            buffer = read_file(filepath)

            if args.assemble:
                assembler.assemble(buffer)
                print_assembled(assembler)
                if args.execute:
                    print_registers(assembler)
                    assembler.execute()
                    print_registers(assembler)

    except:
        traceback.print_exc()

    keep_going = True
    
    while keep_going:
        try:
            print(f'1 Load new assembly file (current: {filepath})')
            print('2 Assemble the code')
            print('3 Execute the code')
            print('4 Exit')
            print('\n\n\n\n')

            choice = input(':')
            try:
                choice = int(choice)
            except ValueError:
                print('Input must be an integer')
                continue

            if choice == 1:
                filepath= input('filepath: ')
                buffer = read_file(filepath)
            elif choice == 2:
                if not bool(buffer):
                    print("No assembly file loaded. Please load a file")
                    continue
                assembler.assemble(buffer)
                print_assembled(assembler)
            elif choice ==3:
                print_registers(assembler)
                assembler.execute()
                print_registers(assembler)
            elif choice==4:
                keep_going =False
                print("Goodbye")
            else:
                print('Incorrect choice please choose Options 1-4')
                
        except:
            traceback.print_exc()
            continue
            


