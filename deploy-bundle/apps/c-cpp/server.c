/* c_cpp environment example — a minimal HTTP server in plain C, no framework.
 *
 * Uses only POSIX sockets from the standard library: it opens a TCP listener,
 * accepts connections in a loop, reads the request line to find the path, and
 * writes back a hand-built HTTP response. Two routes: "/health" returns JSON,
 * everything else returns the hello-world HTML card.
 *
 * Binds TCP 3007 on 0.0.0.0 (§8). my-container-3007.example.com -> :3007.
 * NOTE: :3007 is a PROPOSED port — confirm with Anthony.
 *
 * Build & run:   cc -O2 -o server server.c && ./server
 * (On the container this must be COMPILED there — a Mac binary won't run on
 *  Linux. Requires a C compiler/build-essential on the box; see CLAUDE.md §6.)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define APP_NAME "c_cpp"

static const char *HTML =
    "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
    "<title>" APP_NAME " &mdash; hello world</title><style>"
    "body{font:16px/1.5 system-ui,sans-serif;margin:0;display:grid;"
    "place-items:center;min-height:100vh;background:#0f1117;color:#e6e8ee}"
    ".card{text-align:center;padding:2rem 2.5rem;border:1px solid #262b38;"
    "border-radius:12px;background:#161a23}h1{margin:0 0 .25rem;font-size:1.4rem}"
    "code{background:#0f1117;padding:.1rem .4rem;border-radius:4px;color:#7dd3fc}"
    ".meta{color:#8a93a6;font-size:.85rem;margin-top:1rem}</style></head><body>"
    "<div class=\"card\"><h1>&#128075; hello from <code>" APP_NAME "</code></h1>"
    "<div>plain C &middot; POSIX sockets &middot; no framework</div>"
    "<div class=\"meta\">compiled binary listening on 0.0.0.0:3007 &middot; "
    "<a href=\"/health\" style=\"color:#7dd3fc\">/health</a></div></div>"
    "</body></html>";

static const char *HEALTH = "{\"app\":\"" APP_NAME "\",\"status\":\"ok\",\"lang\":\"c\"}";

/* Write an HTTP response with the given status, content-type and body. */
static void respond(int fd, const char *status, const char *ctype, const char *body) {
    char header[256];
    int n = snprintf(header, sizeof header,
                     "HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %zu\r\n"
                     "Connection: close\r\n\r\n",
                     status, ctype, strlen(body));
    write(fd, header, (size_t)n);
    write(fd, body, strlen(body));
}

int main(void) {
    const int PORT = 3007;
    signal(SIGPIPE, SIG_IGN); /* don't die if the client hangs up mid-write */

    int srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv < 0) { perror("socket"); return 1; }

    int one = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY); /* 0.0.0.0 — required (§8) */
    addr.sin_port = htons(PORT);

    if (bind(srv, (struct sockaddr *)&addr, sizeof addr) < 0) { perror("bind"); return 1; }
    if (listen(srv, 16) < 0) { perror("listen"); return 1; }

    printf("[%s] listening on http://0.0.0.0:%d\n", APP_NAME, PORT);
    fflush(stdout);

    for (;;) {
        int cli = accept(srv, NULL, NULL);
        if (cli < 0) continue;

        char buf[2048];
        ssize_t got = read(cli, buf, sizeof buf - 1);
        if (got > 0) {
            buf[got] = '\0';
            /* Request line looks like: "GET /path HTTP/1.1". Find the path. */
            char *path = strchr(buf, ' ');
            int is_health = 0;
            if (path) {
                path++;
                is_health = (strncmp(path, "/health", 7) == 0);
            }
            if (is_health)
                respond(cli, "200 OK", "application/json", HEALTH);
            else
                respond(cli, "200 OK", "text/html; charset=utf-8", HTML);
        }
        close(cli);
    }
}
