HEADERS=tiger.h tiger_tables.h
C_FILES=tiger.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libtiger.so libtiger1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libtiger.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libtiger.so $(O_FILES)

libtiger1.a: $(O_FILES)
	ar rcs libtiger1.a $(O_FILES)

clean:
	rm -f libtiger.so libtiger1.a $(O_FILES)
