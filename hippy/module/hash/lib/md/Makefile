HEADERS=md.h
C_FILES=md.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libmd.so libmd1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libmd.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libmd.so $(O_FILES)

libmd1.a: $(O_FILES)
	ar rcs libmd1.a $(O_FILES)

clean:
	rm -f libmd.so libmd1.a $(O_FILES)
