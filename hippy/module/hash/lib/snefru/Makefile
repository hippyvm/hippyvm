HEADERS=snefru.h snefru_tables.h
C_FILES=snefru.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libsnefru.so libsnefru1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libsnefru.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libsnefru.so $(O_FILES)

libsnefru1.a: $(O_FILES)
	ar rcs libsnefru1.a $(O_FILES)

clean:
	rm -f libsnefru.so libsnefru1.a $(O_FILES)
