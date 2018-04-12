import sys
import getopt

def open_files(args_wo_options):
    if len(args_wo_options) == 0:
        in_file = sys.stdin
        out_file = sys.stdout
    elif len(args_wo_options) == 1:
        in_file = open(args_wo_options[0], 'rb')
        out_file = sys.stdout
    elif len(args_wo_options) == 2:
        in_file = open(args_wo_options[0], 'rb')
        out_file = open(args_wo_options[1], 'w+')
    else:
        print('error: too many files')
        sys.exit(1)
    return in_file, out_file

def write_u1(file, format, data):
    if format == 10:
        file.write(',{0:d}'.format(data)),
    elif format == 2:
        file.write(',`{0:0>8b}'.format(data)),
    else:
        file.write(',#{0:0>2x}'.format(data)),

def write_u2(file, format, data):
    if format == 10:
        file.write(',{0:d}'.format(data)),
    elif format == 2:
        file.write(',`{0:0>16b}'.format(data)),
    else:
        file.write(',#{0:0>4x}'.format(data)),

def write_base16(file, data):
    b1 = 64+(data>>4)
    b2 = 64+(data & 0xf)
    file.write(chr(b1)),
    file.write(chr(b2)),

class Base128:
    __index = 0
    __byte_count = 0
    __reminder = 0
    
    #encoding (using 0x30~0x7A and 0xAB~0xDF)
    #update: for Hankaku_Kana, using 0xFF6B~0xFF9F
    def __encode(self, val):
        if val < 75:
            code = val + 0x30
        else:
            code = val + 0xFF20
        return unichr(code).encode('utf-8')
    
    #actual writing method
    def __write(self, file, val):
        str = self.__encode(val)
        #print('-> %s %d %s' % (format(val,'07b'), val, str))
        file.write(str),
        
    #public interface
    def write_base128(self, file, data):
        #print ('{} {} '.format(self.__byte_count, self.__index)),
        #divide & combine to align 7bit
        val = data >> (self.__index + 1) 
        #print ('%s %s %s ' % ( format(data,'02x'),format(data,'08b'), format(val,'07b'))),

        #write val 
        #if on the 7bit border write reminder
        #else combine devided val with reminder
        val_to_write = 0
        if self.__index == 0 and self.__byte_count > 0:
            self.__write(file, self.__reminder)
            val_to_write = val
        else:
            val_to_write = (val | self.__reminder)
        #print ('%s %s' % (format(self.__reminder,'07b'), format(val_to_write,'07b'))),
        self.__write(file, val_to_write)
        
        #calcurate reminder and update index
        reminder_shift = 6 - self.__index
        self.__reminder = (data & (0x7f >> reminder_shift)) << reminder_shift
        self.__index = (self.__index + 1) % 7
        self.__byte_count = self.__byte_count + 1
        
    #don't forget to write the last reminder at the end of the file
    def reminded_char(self):
        return self.__encode(self.__reminder)
    
    #total bytes processed
    def bytes(self):
        return self.__byte_count
    
    
def get_u3_u8(inst):
    u3 = (inst >> 8) & 0x0007
    u8 = inst & 0x00ff
    return u3, u8

def get_u3_u3(inst):
    u3_h = (inst >> 3) & 0x0007
    u3_l = inst & 0x0007
    return u3_h, u3_l

def get_u5_u3_u3(inst):
    u5 = (inst >> 6) & 0x001f
    u3_h = (inst >> 3) & 0x0007
    u3_l = inst & 0x0007
    return u5, u3_h, u3_l

def get_u3_u3_u3(inst):
    u5, n, d = get_u5_u3_u3(inst)
    u3 = u5 & 0x0007
    return u3, n, d

def get_s8(inst):
    u8 = inst & 0x00ff
    if u8 & 0x80:
        return -((u8 - 1) ^ 0xff)
    else:
        return u8

def get_s11(inst):
    u11 = inst & 0x07ff
    if u11 & 0x400:
        return -((u11 - 1) ^ 0x7ff)
    else:
        return u11

inst_str15_11_s11 = {
    0b1110000000000000: lambda n11: 'GOTO {0:}'.format(n11 + 2)
}

inst_str15_11_u3_u8 = {
    0b0010000000000000: lambda d,u8: 'R{0:}={1:}'.format(d, u8),
    0b0011000000000000: lambda d,u8: 'R{0:}=R{0:}+{1:}'.format(d, u8),
    0b0011100000000000: lambda d,u8: 'R{0:}=R{0:}-{1:}'.format(d, u8),
    0b0010100000000000: lambda n,u8: 'R{0:}-{1:}'.format(n, u8)
}

inst_str15_11_u5_u3_u3 = {
    0b0111100000000000: lambda u5,n,d: 'R{0:}=[R{1:}+{2:}]'.format(d, n, u5),
    0b0111000000000000: lambda u5,n,d: '[R{0:}+{1:}]=R{2:}'.format(n, u5, d),
    0b0000000000000000: lambda u5,m,d: 'R{0:}=R{1:}<<{2:}'.format(d, m, u5),
    0b0000100000000000: lambda u5,m,d: 'R{0:}=R{1:}>>{2:}'.format(d, m, u5)
}
    
inst_str15_9_u3_u3_u3 = {
    0b0101110000000000: lambda m,n,d: 'R{0:}=[R{1:}+R{2:}]'.format(d, n, m),
    0b0101010000000000: lambda m,n,d: '[R{0:}+R{1:}]=R{2:}'.format(n, m, d),
    0b0001100000000000: lambda m,n,d: 'R{0:}=R{1:}+R{2:}'.format(d, n, m),
    0b0001101000000000: lambda m,n,d: 'R{0:}=R{1:}-R{2:}'.format(d, n, m),
    0b0001110000000000: lambda u3,n,d: 'R{0:}=R{1:}+{2:}'.format(d, n, u3),
    0b0001111000000000: lambda u3,n,d: 'R{0:}=R{1:}-{2:}'.format(d, n, u3)
}

inst_str15_8_s8 = {
    0b1101000000000000: lambda n8: 'IF 0 GOTO {0:}'.format(n8 + 2),
    0b1101000100000000: lambda n8: 'IF !0 GOTO {0:}'.format(n8 + 2)
}

inst_str15_6_u3_u3 = {
    0b0100011000000000: lambda m,d: 'R{0:}=R{1:}'.format(d, m),
    0b0100000000000000: lambda m,d: 'R{0:}=R{0:}&R{1:}'.format(d, m),
    0b0100000001000000: lambda m,d: 'R{0:}=R{0:}^R{1:}'.format(d, m),
    0b0100000010000000: lambda s,d: 'R{0:}=R{0:}<<R{1:}'.format(d, s),
    0b0100000011000000: lambda s,d: 'R{0:}=R{0:}>>R{1:}'.format(d, s),
    0b0100001001000000: lambda m,d: 'R{0:}=-R{1:}'.format(d, m),
    0b0100001100000000: lambda m,d: 'R{0:}=R{0:}|R{1:}'.format(d, m),
    0b0100001101000000: lambda m,d: 'R{0:}=R{0:}*R{1:}'.format(d, m),
    0b0100001110000000: lambda m,d: 'R{0:}=R{0:}&~R{1:}'.format(d, m),
    0b0100001111000000: lambda m,d: 'R{0:}=~R{1:}'.format(d, m),
    0b0100001010000000: lambda m,n: 'R{0:}-R{1:}'.format(n, m),
    0b0100001000000000: lambda m,n: 'R{0:}&R{1:}'.format(n, m)
}

inst_str15_0 = {
    0b0100011101110000: 'RET'
}

def disasm(inst):
    inst_str = 'unknown'
    inst15_11 = inst & 0xf800
    inst15_9  = inst & 0xfe00
    inst15_8  = inst & 0xff00
    inst15_6  = inst & 0xffc0

    if inst in inst_str15_0:
        inst_str = inst_str15_0[inst]
    elif inst15_11 in inst_str15_11_s11:
        n11 = get_s11(inst)
        inst_str = inst_str15_11_s11[inst15_11](n11)
    elif inst15_11 in inst_str15_11_u3_u8:
        d, u8 = get_u3_u8(inst)
        inst_str = inst_str15_11_u3_u8[inst15_11](d, u8)
    elif inst15_11 in inst_str15_11_u5_u3_u3:
        u5, n, d = get_u5_u3_u3(inst)
        inst_str = inst_str15_11_u5_u3_u3[inst15_11](u5, n, d)
    elif inst15_9 in inst_str15_9_u3_u3_u3:
        m, n, d = get_u3_u3_u3(inst)
        inst_str = inst_str15_9_u3_u3_u3[inst15_9](m, n, d)
    elif inst15_8 in inst_str15_8_s8:
        n8 = get_s8(inst)
        inst_str = inst_str15_8_s8[inst15_8](n8)
    elif inst15_6 in inst_str15_6_u3_u3:
        m, d = get_u3_u3(inst)
        inst_str = inst_str15_6_u3_u3[inst15_6](m, d)
    
    return inst_str

def main():
    # default value
    line_no = 100
    line_step = 10
    data_count = 8
    poke_address = 0x700
    output_format = 16
    array_mode = False
    disasm_mode = False
    base16_mode = False
    base128_mode = False
    support_formats = {'hex':16, 'dec':10, 'bin':2}

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:s:d:o:c:bx')
    except getopt.GetoptError, err:
        print(str(err))
        sys.exit(2)
    for o, a in opts:
        if o == '-a':
            if a.find('0x') == 0:
                a = a[2:]
            poke_address = int('0x' + a, 16)
            if poke_address == 0:
                array_mode = True
        elif o == '-s':
            line_no = int(a)
        elif o == '-d':
            line_step = int(a)
        elif o == '-o':
            if a in support_formats:
                output_format = support_formats[a]
            else:
                print('error: unsupported format')
                sys.exit(1)
        elif o == '-c':
            data_count = int(a)
        elif o == '-b':
            base16_mode = True
        elif o == '-x':
            base128_mode = True
        else:
            print('error: unhandled option')
            sys.exit(1)
    if array_mode and output_format == 2 and data_count == 1:
        disasm_mode = True

    in_file, out_file = open_files(args)
    out_file.softspace = False

    poke_address_base = poke_address
    pos_in_line = 0
    line_count = 0
    total_bytes = 0
    #base128 support
    base128 = Base128()
    while True:
        byte = in_file.read(1)
        if byte == '':
            break
        else:
            total_bytes += 1
            if pos_in_line == 0:
                if array_mode:
                    out_file.write('%d let[%d]' % (line_no, poke_address)),
                elif base16_mode:
                    out_file.write('%d \'' % (line_no))
                elif base128_mode:
                    out_file.write('%d \'' % (line_no))
                else:
                    out_file.write('%d poke#%03x' % (line_no, poke_address)),
                poke_address += data_count
            if array_mode:
                word = ord(byte)
                byte_h = in_file.read(1)
                if byte_h != '':
                    word = word | ord(byte_h) << 8
                write_u2(out_file, output_format, word)
                if disasm_mode:
                    disasm_code = disasm(word)
                    out_file.write(':\'' + disasm_code),
                if byte_h == '':
                    break
            elif base16_mode:
                write_base16(out_file, ord(byte))
            elif base128_mode:
                base128.write_base128(out_file, ord(byte))
            else:
                write_u1(out_file, output_format, ord(byte))
            pos_in_line += 1
            #print ('pos_in_line:%d / %d' % (pos_in_line,data_count))
            if pos_in_line >= data_count:
                pos_in_line = 0
                line_no += line_step
                #print('line count incremented')
                out_file.write('\n')
    in_file.close()

    if base128_mode:
        out_file.write(base128.reminded_char())
        #print('last char:{}'.format(base128.reminded_char())) 

    if pos_in_line != 0:
        out_file.write('\n')
    
    if base16_mode:
        line_no += line_step
        if line_count == 1:
            out_file.write('%d O=#C04:FORI=0TO%d:POKE#%03x+I,(PEEK(O+I*2)-64)<<4+PEEK(O+1+I*2)-64:NEXT' % (line_no, total_bytes, poke_address_base)),
        else:
            out_file.write('%d O=#C04:D=0:FORJ=0TO%d:N=PEEK(O-2):FORI=0TON/2-2:POKE#%03x+D,(PEEK(O+i*2)-64)<<4+PEEK(O+1+i*2)-64:D=D+1:NEXT:O=O+N+4:NEXT' % (line_no, line_count, poke_address_base)),
        out_file.write('\n')
    
    #2 O=#C04:I=0:K=0:M=9
    #3 S=I%8:A=PEEK(O+I):A=A-(1+(A>#AA))*#30:IFSV=A>>(7-S)|C:POKE#800+K*2,V>>4,V&#FF:K=K+1
    #4 C=(A&(#7F>>S))<<(S+1):I=I+1:IFK<MGOTO3
    if base128_mode:
        line_no += line_step
        total_bytes = base128.bytes()
        if line_count == 0:
            out_file.write('{0} O=#C04:I=0:K=0:M={1}\n'.format(line_no, total_bytes))
            out_file.write('{0} S=I%8:A=PEEK(O+I):A=A-(1+(A>#AA))*#30:IFSV=A>>(7-S)|C:POKE#{1:x}+K,V:K=K+1\n'.format(line_no + 1, poke_address_base))
            out_file.write('{0} C=(A&(#7F>>S))<<(S+1):I=I+1:IFK<MGOTO{1}\n'.format(line_no + 2, line_no + 1))
        else:
            out_file.write('%d O=#C04:D=0:FORJ=0TO%d:N=PEEK(O-2):FORI=0TON/2-2:POKE#%03x+D,(PEEK(O+i*2)-64)<<4+PEEK(O+1+i*2)-64:D=D+1:NEXT:O=O+N+4:NEXT' % (line_no, line_count, poke_address_base)),
        out_file.write('\n')
    
    out_file.close()
                    

if __name__ == '__main__':
    main()

