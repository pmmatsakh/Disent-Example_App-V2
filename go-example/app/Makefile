# Build the go example. `make` produces ./server, then `./server` runs it.
# Must be compiled ON the container — a macOS binary will not run on Linux.
server: main.go go.mod
	go build -o server main.go

run: server
	./server

clean:
	rm -f server

.PHONY: run clean
