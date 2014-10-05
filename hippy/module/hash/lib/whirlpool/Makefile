HEADERS=whirlpool.h whirlpool_tables.h
C_FILES=whirlpool.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libwhirlpool.so libwhirlpool1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libwhirlpool.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libwhirlpool.so $(O_FILES)

libwhirlpool1.a: $(O_FILES)
	ar rcs libwhirlpool1.a $(O_FILES)

clean:
	rm -f libwhirlpool.so libwhirlpool1.a $(O_FILES)
