HEADERS=ripemd.h
C_FILES=ripemd.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libripemd.so libripemd1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libripemd.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libripemd.so $(O_FILES)

libripemd1.a: $(O_FILES)
	ar rcs libripemd1.a $(O_FILES)

clean:
	rm -f libripemd.so libripemd1.a $(O_FILES)
