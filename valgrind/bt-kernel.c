#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/un.h>
#include <string.h>
#include <fcntl.h>
#include <poll.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <unistd.h>

#include <valgrind.h>

#ifndef BTPROTO_L2CAP
#define BTPROTO_L2CAP 0
#endif
#ifndef SOL_L2CAP
#define SOL_L2CAP 6
#endif
#ifndef SOL_BLUETOOTH
#define SOL_BLUETOOTH 274
#endif
#ifndef BT_RCVMTU
#define BT_RCVMTU 13
#endif

#ifndef L2CAP_OPTIONS
#define L2CAP_OPTIONS 1
struct l2cap_options {
	uint16_t	omtu;
	uint16_t	imtu;
	uint16_t	flush_to;
	uint8_t		mode;
	uint8_t		fcs;
	uint8_t		max_tx;
	uint16_t	txwin_size;
};
#endif

/* Base file descriptor for intercepted sockets */
#define VIRTUAL_SK_BASE 1000
/* Maximum number of intercepted sockets */
#define VIRTUAL_SK_MAX 100

#define SOCK_ADDR_MAX_LEN 14

/* libc.so.6 */
#define WRAP_FN(fn) I_WRAP_SONAME_FNNAME_ZZ(libcZdsoZd6,fn)
/* libpthread.so.0 */
#define WRAP_FN2(fn) I_WRAP_SONAME_FNNAME_ZZ(libpthreadZdsoZd0,fn)

#define DEBUG
#ifdef DEBUG
#define DBG(fmt, arg...) do { \
	dbg("[EMULATOR] %s:%s() " fmt "\n",  __FILE__, __func__ , ## arg); \
} while (0)

static void dbg(const char *format, ...) __attribute__((format(printf, 1, 2)));
static void dbg(const char *format, ...)
{
	char msg[LINE_MAX];
	va_list ap;
	int ret;

	va_start(ap, format);
	vsnprintf(msg, sizeof(msg), format, ap);
	/* Do not use write() to avoid infinite loop as write() is wrapped */
	ret = syscall(SYS_write, 2, msg, strlen(msg));
	assert(ret == strlen(msg));
	va_end(ap);
}
#else
#define DBG(fmt, arg...)
#endif

static struct {
	int emu_sk;
	int protocol;
	int flags;

	unsigned char src_addr[SOCK_ADDR_MAX_LEN];
	int src_addrlen;
	unsigned char dst_addr[SOCK_ADDR_MAX_LEN];
	int dst_addrlen;
} socket_data[VIRTUAL_SK_MAX];

static int verify_send(int ret, int len)
{
	if (ret < 0) {
		DBG("Could not send data to UNIX socket");
		return -1;
	}

	if (ret < len) {
		DBG("Sent less data than expected (%d != %d)", ret, len);
		errno = EINVAL;
		return -1;
	}

	return 0;
}

static int init_sockaddr_un(struct sockaddr_un *addr, const char *path)
{
	addr->sun_family = AF_UNIX;
	addr->sun_path[0] = '\0';
	strcpy(&addr->sun_path[1], path);

	return offsetof(struct sockaddr_un, sun_path) + strlen(path) + 1;
}

int WRAP_FN(socket)(int domain, int type, int protocol)
{
	static int virtual_sk = VIRTUAL_SK_BASE;
	struct sockaddr_un addr;
	int ret, emu_sk, addrlen;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("socket(%d, %d, %d)", domain, type, protocol);

	if (domain != PF_BLUETOOTH) {
		CALL_FN_W_WWW(ret, fn, domain, type, protocol);
		return ret;
	}

	if (virtual_sk == VIRTUAL_SK_MAX) {
		DBG("Reached maximum number of intercepted sockets");
		errno = ENOMEM;
		return -1;
	}

	emu_sk = socket(AF_UNIX, SOCK_SEQPACKET, 0);
	if (emu_sk < 0) {
		DBG("Could not create UNIX socket: %s", strerror(errno));
		return -1;
	}

	addrlen = init_sockaddr_un(&addr, "/bt_emulator");
	if (connect(emu_sk, (struct sockaddr *) &addr, addrlen) < 0) {
		DBG("Could not connect to UNIX socket: %s", strerror(errno));
		return -1;
	}

	socket_data[virtual_sk - VIRTUAL_SK_BASE].emu_sk = emu_sk;
	socket_data[virtual_sk - VIRTUAL_SK_BASE].protocol = protocol;
	socket_data[virtual_sk - VIRTUAL_SK_BASE].flags = O_RDWR;
	if (type & SOCK_NONBLOCK)
		socket_data[virtual_sk - VIRTUAL_SK_BASE].flags |= SOCK_NONBLOCK;
	/* FIXME: fill socket_data.stat if necessary */

	return virtual_sk++;
}

int WRAP_FN(bind)(int fd, void *addr, unsigned int addrlen)
{
	int ret, emu_sk, protocol;
	OrigFn fn;
	struct msghdr msg;
	struct iovec iov[2];

	VALGRIND_GET_ORIG_FN(fn);
	DBG("bind(%d, %p, %d)", fd, addr, addrlen);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WWW(ret, fn, fd, addr, addrlen);
		return ret;
	}

	assert(addrlen <= SOCK_ADDR_MAX_LEN);
	memcpy(socket_data[fd - VIRTUAL_SK_BASE].src_addr, addr, addrlen);
	socket_data[fd - VIRTUAL_SK_BASE].src_addrlen = addrlen;

	emu_sk = socket_data[fd - VIRTUAL_SK_BASE].emu_sk;
	protocol = socket_data[fd - VIRTUAL_SK_BASE].protocol;

	iov[0].iov_base = &protocol;
	iov[0].iov_len = sizeof(protocol);
	iov[1].iov_base = addr;
	iov[1].iov_len = addrlen;

	memset(&msg, 0, sizeof(msg));
	msg.msg_iov = iov;
	msg.msg_iovlen = 2;

	ret = sendmsg(emu_sk, &msg, 0);
	if (verify_send(ret, sizeof(protocol) + addrlen))
		return -1;

	return 0;
}

int WRAP_FN(listen)(int fd, int backlog)
{
	int ret;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("listen(%d, %d)", fd, backlog);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WW(ret, fn, fd, backlog);
		return ret;
	}

	return 0;
}

int WRAP_FN(poll)(struct pollfd *fds, int nfds, int timeout)
{
	int ret, i, j;
	struct {
		int idx;
		int orig_fd;
	} virtual_fds[nfds];
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("poll(%p, %d, %d)", fds, nfds, timeout);

	for (i = 0, j = 0; i < nfds; i++) {
		if (fds[i].fd < VIRTUAL_SK_BASE)
			continue;

		virtual_fds[j].idx = i;
		virtual_fds[j++].orig_fd = fds[i].fd;
		fds[i].fd = socket_data[fds[i].fd - VIRTUAL_SK_BASE].emu_sk;
	}

	CALL_FN_W_WWW(ret, fn, fds, nfds, timeout);

	for (i = 0; i < j; i++)
		fds[virtual_fds[i].idx].fd = virtual_fds[i].orig_fd;

	return ret;
}

int WRAP_FN(write)(int fd, void *buf, int count)
{
	int ret, emu_sk;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("write(%d, %p, %d)", fd, buf, count);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WWW(ret, fn, fd, buf, count);
		return ret;
	}

	emu_sk = socket_data[fd - VIRTUAL_SK_BASE].emu_sk;

	return send(emu_sk, buf, count, 0);
}

int WRAP_FN(read)(int fd, void *buf, int count)
{
	int ret, emu_sk;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("read(%d, %p, %d)", fd, buf, count);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WWW(ret, fn, fd, buf, count);
		return ret;
	}

	emu_sk = socket_data[fd - VIRTUAL_SK_BASE].emu_sk;

	return recv(emu_sk, buf, count, 0);
}

int WRAP_FN(fcntl)(int fd, int cmd, int arg)
{
	int ret;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("fcntl(%d, %d)", fd, cmd);

	if (fd < VIRTUAL_SK_BASE) {
		if (cmd == F_GETFL)
			CALL_FN_W_WW(ret, fn, fd, cmd);
		else if (cmd == F_SETFL)
			CALL_FN_W_WWW(ret, fn, fd, cmd, arg);
		else {
			DBG("Unsupported command: %d", cmd);
			errno = ENOSYS;
			return -1;
		}
		return ret;
	}

	if (cmd == F_GETFL)
		return socket_data[fd - VIRTUAL_SK_BASE].flags;
	else if (cmd == F_SETFL) {
		socket_data[fd - VIRTUAL_SK_BASE].flags = arg;
		return 0;
	}

	DBG("Unsupported command: %d", cmd);
	errno = ENOSYS;

	return -1;
}

int WRAP_FN(setsockopt)(int fd, int level, int optname,
		const void *optval, int optlen)
{
	int ret;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("setsockopt(%d, %d, %d, %p, %d)", fd, level, optname, optval,
			optlen);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_5W(ret, fn, fd, level, optname, optval, optlen);
		return ret;
	}

	return 0;
}

int WRAP_FN(getsockopt)(int fd, int level, int optname,
		void *optval, int *optlen)
{
	int ret;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("getsockopt(%d, %d, %d, %p, %p)", fd, level, optname, optval,
			optlen);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_5W(ret, fn, fd, level, optname, optval, optlen);
		return ret;
	}

	if (level == SOL_SOCKET) {
		switch (optname) {
		case SO_ERROR:
			*((int *) optval) = 0;
			*optlen = sizeof(int);
			return 0;
		case SO_DOMAIN:
			*((int *) optval) = AF_BLUETOOTH;
			*optlen = sizeof(int);
			return 0;
		case SO_PROTOCOL:
			*((int *) optval) = BTPROTO_L2CAP;
			*optlen = sizeof(int);
			return 0;
		}
	} else if (level == SOL_BLUETOOTH) {
		switch (optname) {
		case BT_RCVMTU:
			/* TODO: implement support for this */
			errno = EPROTONOSUPPORT;
			return -1;
		}
	} else if (level == SOL_L2CAP) {
		switch (optname) {
		case L2CAP_OPTIONS:
			assert(optlen &&
				*optlen >= sizeof(struct l2cap_options));
			memset(optval, 0, *optlen);
			((struct l2cap_options *) optval)->imtu = 672;
			((struct l2cap_options *) optval)->omtu = 672;
			*optlen = sizeof(struct l2cap_options);
			return 0;
		}
	}

	errno = ENOSYS;
	return -1;
}

int WRAP_FN(connect)(int fd, void *addr, int addrlen)
{
	int ret, emu_sk;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("connect(%d, %p, %d)", fd, addr, addrlen);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WWW(ret, fn, fd, addr, addrlen);
		return ret;
	}

	assert(addrlen <= SOCK_ADDR_MAX_LEN);
	memcpy(socket_data[fd - VIRTUAL_SK_BASE].dst_addr, addr, addrlen);
	socket_data[fd - VIRTUAL_SK_BASE].dst_addrlen = addrlen;

	emu_sk = socket_data[fd - VIRTUAL_SK_BASE].emu_sk;

	ret = send(emu_sk, addr, addrlen, 0);
	if (verify_send(ret, addrlen))
		return -1;

	return 0;
}

int WRAP_FN(getsockname)(int fd, void *addr, int *addrlen)
{
	int ret;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("getsockname(%d, %p, %p)", fd, addr, addrlen);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WWW(ret, fn, fd, addr, addrlen);
		return ret;
	}

	assert(*addrlen >= socket_data[fd - VIRTUAL_SK_BASE].src_addrlen);
	*addrlen = socket_data[fd - VIRTUAL_SK_BASE].src_addrlen;
	memcpy(addr, socket_data[fd - VIRTUAL_SK_BASE].src_addr, *addrlen);

	return 0;
}

int WRAP_FN(getpeername)(int fd, void *addr, int *addrlen)
{
	int ret;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	DBG("getpeername(%d, %p, %p)", fd, addr, addrlen);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WWW(ret, fn, fd, addr, addrlen);
		return ret;
	}

	assert(*addrlen >= socket_data[fd - VIRTUAL_SK_BASE].dst_addrlen);
	*addrlen = socket_data[fd - VIRTUAL_SK_BASE].dst_addrlen;
	memcpy(addr, socket_data[fd - VIRTUAL_SK_BASE].dst_addr, *addrlen);

	return 0;
}

#if 0
int WRAP_FN(fstat)(int fd, void *buf)
{
	int ret;
	OrigFn fn;

	VALGRIND_GET_ORIG_FN(fn);
	fprintf(stderr, LOG_PREFIX "fstat(%d, %p)\n", fd, buf);

	if (fd < VIRTUAL_SK_BASE) {
		CALL_FN_W_WW(ret, fn, fd, buf);
		return ret;
	}

	memcpy(buf, &socket_data[fd - VIRTUAL_SK_BASE].stat,
			sizeof(socket_data[fd - VIRTUAL_SK_BASE].stat));

	return 0;
}
#endif

int WRAP_FN2(write)(int fd, void *buf, int count)
{
	return WRAP_FN(write)(fd, buf, count);
}

int WRAP_FN2(read)(int fd, void *buf, int count)
{
	return WRAP_FN(read)(fd, buf, count);
}

int WRAP_FN2(fcntl)(int fd, int cmd, int arg)
{
	return WRAP_FN(fcntl)(fd, cmd, arg);
}

int WRAP_FN2(connect)(int fd, void *addr, int addrlen)
{
	return WRAP_FN(connect)(fd, addr, addrlen);
}

