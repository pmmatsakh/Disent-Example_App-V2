# Build the c_cpp example. Run `make` to produce ./server, then `./server`.
# On the container this must be compiled ON the box (a Mac binary won't run on
# Linux) — needs a C compiler (gcc/clang / build-essential). See CLAUDE.md §6.

CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra

server: server.c
	$(CC) $(CFLAGS) -o server server.c

run: server
	./server

clean:
	rm -f server

.PHONY: run clean
