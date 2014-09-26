HEADERS=gost.h gost_tables.h
C_FILES=gost.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libgost.so libgost1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libgost.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libgost.so $(O_FILES)

libgost1.a: $(O_FILES)
	ar rcs libgost1.a $(O_FILES)

clean:
	rm -f libgost.so libgost1.a $(O_FILES)
