HEADERS=fnv.h
C_FILES=fnv.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libfnv.so libfnv1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libfnv.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libfnv.so $(O_FILES)

libfnv1.a: $(O_FILES)
	ar rcs libfnv1.a $(O_FILES)

clean:
	rm -f libfnv.so libfnv1.a $(O_FILES)
