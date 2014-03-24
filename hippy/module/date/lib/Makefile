HEADERS=fallbackmap.h timelib_config.h timelib.h timelib_structs.h timezonemap.h timezonedb.h astro.h
C_FILES=parse_tz.c timelib.c interval.c tm2unixtime.c unixtime2tm.c dow.c parse_date.c parse_iso_intervals.c astro.c
O_FILES=$(addsuffix .o,$(basename $(C_FILES)))

all: libtimelib.so libtimelib1.a

%.o: %.c $(HEADERS)
	gcc -g -fPIC -O2 -c $< -o $@

libtimelib.so: $(O_FILES)
	gcc -g -shared -fPIC -O2 -lm -o libtimelib.so $(O_FILES)

libtimelib1.a: $(O_FILES)
	ar rcs libtimelib1.a $(O_FILES)

clean:
	rm -f libtimelib.so libtimelib1.a $(O_FILES)
