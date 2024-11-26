#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>

#include <sys/un.h>
#include <sys/socket.h>

#include <alsa/asoundlib.h>

#define CAPABILITIES SND_SEQ_PORT_CAP_WRITE | SND_SEQ_PORT_CAP_READ | SND_SEQ_PORT_CAP_SUBS_WRITE | SND_SEQ_PORT_CAP_SUBS_READ
#define TEST(fail_expr, msg) if (fail_expr) { fputs(msg, stderr); return 1; }

const char* SOCKET_FILE = "/tmp/launchpad.socket";
int thread_running = 1;

typedef struct _args_t {
    snd_seq_t* seq;
    int sock;
} args_t;

typedef struct _col_update_t {
    int type;
    unsigned char button;
    unsigned char r;
    unsigned char g;
    unsigned char b;
} col_update_t;


col_update_t recv_decode(char* recv, size_t len) {
    col_update_t update = { .type = -1 };
    char tmp[2] = { '\0', '\0' };

    if (len != 8) {
        return update;
    }

    char *p = recv;
    strncpy(tmp, p, 2);
    update.button = strtol(tmp, NULL, 10);

    p += 2;
    strncpy(tmp, p, 2);
    update.r = strtol(tmp, NULL, 10);

    p += 2;
    strncpy(tmp, p, 2);
    update.g = strtol(tmp, NULL, 10);

    p += 2;
    strncpy(tmp, p, 2);
    update.b = strtol(tmp, NULL, 10);

    if (update.button == 99) {
        update.type = 1;
    }

    else {
        update.type = 0;
    }

    return update;
}

int update_colour(snd_seq_t* seq, col_update_t upd, int port) {
    unsigned char button = upd.button;
    unsigned char r = upd.r;
    unsigned char g = upd.g;
    unsigned char b = upd.b;

    if (upd.button > 90) { button = upd.button + 13; }
    if (upd.r > 63) { r = 63; }
    if (upd.g > 63) { g = 63; }
    if (upd.b > 63) { b = 63; }

    char data[] = { 0xF0, 0x00, 0x20, 0x29, 0x02, 0x18, 0x0B, button, r, g, b, 0xF7 };
    snd_seq_event_t ev;

    snd_seq_ev_clear(&ev);
    snd_seq_ev_set_source(&ev, port);
    snd_seq_ev_set_subs(&ev);
    snd_seq_ev_set_direct(&ev);

    snd_seq_ev_set_sysex(&ev, sizeof(data), data);

    if (snd_seq_event_output(seq, &ev) < 0) { return 1; }
    if (snd_seq_drain_output(seq) < 0) { return 1; }

    return 0;
}

int get_client(snd_seq_t* seq, snd_seq_client_info_t* info, const char* name) {
    snd_seq_client_info_set_client(info, -1);

    while (snd_seq_query_next_client(seq, info) >= 0) {
        if (strcmp(snd_seq_client_info_get_name(info), name) == 0) {
            return 0;
        }
    }

    return -1;
}

int get_port(snd_seq_t* seq, int client, unsigned int capability) {
    snd_seq_port_info_t* info;
    snd_seq_port_info_alloca(&info);

    snd_seq_port_info_set_client(info, client);
    snd_seq_port_info_set_port(info, -1);

    while (snd_seq_query_next_port(seq, info) >= 0) {
        if ((snd_seq_port_info_get_capability(info) & capability) == capability) {
            return snd_seq_port_info_get_port(info);
        }
    }

    return -1;
}

void hardware_update(snd_seq_t* seq, int sock) {
    snd_seq_event_t* ev;
    struct pollfd *pfd;
    int npfd;

    npfd = snd_seq_poll_descriptors_count(seq, POLLIN);
    pfd = (struct pollfd *)alloca(npfd * sizeof(struct pollfd));
    snd_seq_poll_descriptors(seq, pfd, npfd, POLLIN);


    while (thread_running) {
        /* Poll timeout here allows thread to exit */
        if (poll(pfd, npfd, 1000) > 0) {

            do {
                snd_seq_event_input(seq, &ev);
                int button = 0;
                int pressed = 0;

                switch (ev->type) {

                    case SND_SEQ_EVENT_CONTROLLER:
                        button = ev->data.control.param - 13;
                        pressed = ev->data.control.value > 0;
                        break;

                    case SND_SEQ_EVENT_NOTEON:
                        button = ev->data.note.note;
                        pressed = ev->data.note.velocity > 0;
                        break;

                    default:
                        continue;
                }

                char msg[3];
                if (pressed) { sprintf(msg, "%iP", button); }
                else { sprintf(msg, "%iR", button); }

                if (write(sock, msg, sizeof(msg)) != sizeof(msg)) {
                    continue;
                }

            } while (snd_seq_event_input_pending(seq, 0) > 0);
        }
    }
}

void *thread_update(void *_args) {
    args_t args = *((args_t*)_args);
    hardware_update(args.seq, args.sock);
    return NULL;
}

int main(int argc, char** argv) {
    int running = 1;

    snd_seq_client_info_t* lp_info;
    snd_seq_t* seq;

    snd_seq_client_info_alloca(&lp_info);

    TEST ((snd_seq_open(&seq, "default", SND_SEQ_OPEN_DUPLEX, 0) != 0), "Could not create seq object")
    TEST ((get_client(seq, lp_info, "Launchpad MK2") != 0), "Could not get launchpad mk2 client")

    int client = snd_seq_client_info_get_client(lp_info);
    int port = get_port(seq, client, CAPABILITIES);
    int user_port = snd_seq_create_simple_port(seq, "PORT", CAPABILITIES, SND_SEQ_PORT_TYPE_APPLICATION);

    TEST ((port < 0), "Could not find r/w port")
    TEST ((user_port < 0), "Could not create r/w port")

    TEST ((snd_seq_connect_from(seq, user_port, client, port) != 0), "Could not connect from port")
    TEST ((snd_seq_connect_to(seq, user_port, client, port) != 0), "Could not connect to port")

    struct sockaddr_un sock_addr;
    int sock = socket(AF_UNIX, SOCK_STREAM, 0);

    TEST ((sock < 0), "Could not create socket")
    TEST ((strlen(SOCKET_FILE) > sizeof(sock_addr.sun_path) - 1), "Socket filename is too large")

    memset(&sock_addr, 0, sizeof(struct sockaddr_un));
    sock_addr.sun_family = AF_UNIX;
    strncpy(sock_addr.sun_path, SOCKET_FILE, sizeof(sock_addr.sun_path) - 1);

    int retry_count = 0;

    while (connect(sock, (struct sockaddr *)&sock_addr, sizeof(struct sockaddr_un)) == -1) {
        if (errno == ECONNREFUSED) {
            fprintf(stderr, "Connection refused, retrying [%i/10]\n", ++retry_count);
        }

        else if (errno == ENOENT) {
            fprintf(stderr, "Socket file does not exist, retrying [%i/10]\n", ++retry_count);
        }

        else {
            fprintf(stderr, "Could not open socket\n");
            return 1;
        }

        if (retry_count >= 10) {
            fprintf(stderr, "Could not open socket\n");
            return 1;
        }

        sleep(1);
    }

    pthread_t t_id;
    args_t args = { .seq = seq, .sock = sock };

    TEST ((pthread_create(&t_id, NULL, thread_update, &args) != 0), "Could not create hardware poll thread")

    struct pollfd pfd[1];
    memset(pfd, 0, sizeof(pfd));

    pfd[0].fd = sock;
    pfd[0].events = POLLIN;

    char buf[8];
    memset(buf, 0, sizeof(buf));

    while (running) {
        if (poll(pfd, 1, -1) > 0) {
            int rc = recv(pfd[0].fd, buf, sizeof(buf), 0);

            if (rc == 0 || (rc < 0 && errno != EWOULDBLOCK)) {
                /* Socket exit / Receive failure */
                /* Assumption is system will restart upon exit */
                running = 0;
                thread_running = 0;
                continue;
            }

            if (rc != 8) {
                memset(buf, 0, sizeof(buf));
                continue;
            }

            col_update_t upd = recv_decode(buf, sizeof(buf));
            memset(buf, 0, sizeof(buf));

            if (upd.type < 0) {
                continue;
            }

            else if (upd.type > 0) {
                running = 0;
                thread_running = 0;
                continue;
            }

            if (update_colour(seq, upd, port) != 0) {
                continue;
            }
        }
    }

    pthread_exit(&t_id);
    return 0;
}
