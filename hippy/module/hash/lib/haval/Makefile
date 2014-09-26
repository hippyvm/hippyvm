HEADERS=haval.h
C_FILES=haval.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libhaval.so libhaval1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libhaval.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libhaval.so $(O_FILES)

libhaval1.a: $(O_FILES)
	ar rcs libhaval1.a $(O_FILES)

clean:
	rm -f libhaval.so libhaval1.a $(O_FILES)
