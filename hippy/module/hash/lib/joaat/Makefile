HEADERS=joaat.h
C_FILES=joaat.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libjoaat.so libjoaat1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libjoaat.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libjoaat.so $(O_FILES)

libjoaat1.a: $(O_FILES)
	ar rcs libjoaat1.a $(O_FILES)

clean:
	rm -f libjoaat.so libjoaat1.a $(O_FILES)
