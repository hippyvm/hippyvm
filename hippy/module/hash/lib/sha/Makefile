HEADERS=sha.h
C_FILES=sha.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libsha.so libsha1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libsha.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libsha.so $(O_FILES)

libsha1.a: $(O_FILES)
	ar rcs libsha1.a $(O_FILES)

clean:
	rm -f libsha.so libsha1.a $(O_FILES)
