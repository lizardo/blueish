CFLAGS = -Wall -O2 $(shell pkg-config --cflags valgrind)

all: bt-kernel.so

bt-kernel.so: bt-kernel.c
	$(CC) -shared -fPIC $(CFLAGS) -o $@ $<

clean:
	rm -f bt-kernel.so
