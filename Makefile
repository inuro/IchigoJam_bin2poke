TARGET_ARCH=arm-none-eabi-
CC=$(TARGET_ARCH)gcc
OBJCOPY=$(TARGET_ARCH)objcopy
RM=rm
PYTHON=python
BIN2POKE=bin2poke.py
CFLAGS=-c -mthumb -mlittle-endian -mno-unaligned-access -Os
# #700���Ϥ���poke���������Ϲ��ֹ�100�����ֹ���ʬ10
BIN2POKE_OPT=-a 0x700 -s 100 -d 10 

# poke�Υǡ�������10�ʿ��ǽ���(���������ɥ������︺��)
#BIN2POKE_OPT=-o dec

# poke�Υǡ�������1�Ԥ�16�ǡ�������(�����¿���Ķ��Ǹ��䤹��)
#BIN2POKE_OPT=-c 16

# poke�Υǡ�������2�ʿ��ǽ��ϡ�1�Ԥ�2�ǡ������ϡ�
#BIN2POKE_OPT=-o bin -c 2

# poke���������������ǽ���2�ʿ���1�Ԥ�1�ǡ���(�������1�ǡ�����16�ӥå�)��
# �ʲ����Ȥ߹�碌�Ǥν��Ϥ���ꤷ�����˸¤ꡢ���������˵ե�����֥륳���ɤ����
#BIN2POKE_OPT+=-a 0 -o bin -c 1

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

%.bin: %.o
	$(OBJCOPY) -O binary $< $@

%.bas: %.bin
	$(PYTHON) $(BIN2POKE) $(BIN2POKE_OPT) $< $@

clean:
	$(RM) *.o *.bin
