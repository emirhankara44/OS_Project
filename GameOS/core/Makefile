CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -fPIC
LDFLAGS = -shared

# Shared library (Python ctypes ile kullanilacak)
all: libgameos.so scheduler_test memory_test

libgameos.so: scheduler.o memory.o
	$(CC) $(LDFLAGS) -o $@ $^

scheduler.o: scheduler.c scheduler.h
	$(CC) $(CFLAGS) -c scheduler.c

memory.o: memory.c memory.h
	$(CC) $(CFLAGS) -c memory.c

# Test programlari
scheduler_test: scheduler.c scheduler.h
	$(CC) $(CFLAGS) -DSCHEDULER_TEST -o $@ scheduler.c

memory_test: memory.c memory.h
	$(CC) $(CFLAGS) -DMEMORY_TEST -o $@ memory.c

clean:
	rm -f *.o *.so scheduler_test memory_test

.PHONY: all clean
