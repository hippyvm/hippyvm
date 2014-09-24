HEADERS=adler32.h
C_FILES=adler32.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libadler32.so libadler321.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libadler32.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libadler32.so $(O_FILES)

libadler321.a: $(O_FILES)
	ar rcs libadler321.a $(O_FILES)

clean:
	rm -f libadler32.so libadler321.a $(O_FILES)
