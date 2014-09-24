HEADERS=crc32.h crc32_tables.h
C_FILES=crc32.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libcrc32.so libcrc321.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libcrc32.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libcrc32.so $(O_FILES)

libcrc321.a: $(O_FILES)
	ar rcs libcrc321.a $(O_FILES)

clean:
	rm -f libcrc32.so libcrc321.a $(O_FILES)
