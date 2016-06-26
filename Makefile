TARGET_ARCH=arm-none-eabi-
CC=$(TARGET_ARCH)gcc
OBJCOPY=$(TARGET_ARCH)objcopy
OBJDUMP=$(TARGET_ARCH)objdump
LD=$(TARGET_ARCH)ld
RM=rm
PYTHON=python
BIN2POKE=bin2poke.py
CFLAGS=-c -mthumb -mcpu=cortex-m0 -mlittle-endian -mno-unaligned-access -Os -g

#700���Ϥ���poke���������Ϲ��ֹ�100�����ֹ���ʬ10
#BIN2POKE_OPT=-a 0x700 -s 100 -d 10 

# poke�Υǡ�������10�ʿ��ǽ���(���������ɥ������︺��)
#BIN2POKE_OPT=-o dec

# poke�Υǡ�������1�Ԥ�16�ǡ�������(�����¿���Ķ��Ǹ��䤹��)
#BIN2POKE_OPT=-c 16

# poke�Υǡ�������2�ʿ��ǽ��ϡ�1�Ԥ�2�ǡ������ϡ�
#BIN2POKE_OPT=-o bin -c 2

# poke����������������16�ʿ��ǽ��ϡ�IchigoJam�λ��;塢�����800���Ϥ���˸��ꡣ
BIN2POKE_OPT+=-a 0

# poke���������������ǽ���2�ʿ���1�Ԥ�1�ǡ���(�������1�ǡ�����16�ӥå�)��
# �ʲ����Ȥ߹�碌�Ǥν��Ϥ���ꤷ�����˸¤ꡢ���������˵ե�����֥륳���ɤ����
#BIN2POKE_OPT+=-a 0 -o bin -c 1

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

%.elf: %.o
	$(LD) -T bin2poke.ld -o $@ $<

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@

%.bas: %.bin
	$(PYTHON) $(BIN2POKE) $(BIN2POKE_OPT) $< $@

%.s: %.elf
	$(OBJDUMP) -d -S -l $< > $@

clean:
	$(RM) *.o *.bin
