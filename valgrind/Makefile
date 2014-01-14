CFLAGS = -Wall -O2 $(shell pkg-config --cflags valgrind)
LDFLAGS = $(shell pkg-config --libs valgrind)

%.so: %.c
	$(CC) -shared -fPIC $(CFLAGS) -o $@ $< $(LDFLAGS)

all: bt-kernel.so

bt-kernel.so: bt-kernel.c

clean:
	rm -f bt-kernel.so
