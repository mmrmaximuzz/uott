# uott

Simple and stupid transparent proxy for UDP applications. There are probably
lots of better ways to do it.

## Introduction

`uott` (UDP Over TCP Transport) is a simple and stupid proxy allowing to send UDP
datagrams over TCP streams.

There are some cases when somebody *really* needs to send UDP datagrams but it
is impossible to send them directly. This is not so uncommon, especially when
debugging UDP applications, for example:

1. You want to interact with some remote UDP application from your local
   machine, but the remote application listens loopback device only, making it
   unreachable from the external networks. If you can run TCP applications
   listening on some public interface of that remote machine, you can succeed
   with `uott`.

1. You want to interact with some remote UDP application, but the UDP datagrams
   cannot be passed through the network for some reason (port is filtered / UDP
   is filtered / UDP datagrams are dropped due to fragmentation / ...). If you
   still can create TCP connections in that network, you can succeed with
   `uott`.

1. You want to interact with some remote UDP application, but the application
   protocol is not protected, and there is a public network segment on the path.
   If you can forward TCP ports in a secure way (using SSH port forwarding or
   similar) to protect the channel on the public path, you can succeed with
   `uott`.

### Algorithm

The algorithm of `uott` is very simple. First of all, the `uott-proxy` service
is started on the remote side. After that, the `uott-client` service is launched
on the local side. The client service establishes TCP connection with the proxy
and opens a UDP socket for the clients.

#### Client loop

For each UDP message got from the UDP socket, the client checks the sources
*address:port* of the received datagram. The client accounts the *address:port*
pairs and assign a unique number (*tag*) for each pair. This *tag* is used then
to deliver the UDP response to the original address. Then the UDP message's
content is packed in UOTT message, which contains some magic number, *tag*,
datagram length and the actual UDP payload. This UOTT message is serialized to
the TCP stream and processed by the proxy service.

#### Proxy loop

The proxy service listens the TCP stream from the client and deserializes the
UDP messages using *tag* and length encoded in the stream. For each new *tag*
the proxy creates a new UDP socket. The socket is then used to send UDP
datagrams, corresponding to this *tag*, to the remote UDP service. The answers
from the remote UDP service are serialized again and sent over the TCP stream
back to the client.

#### Diagram

There will be a nice picture soon.

### Pros/Cons

Let's describe the advantages and the drawbacks of `uott`.

**Pros**

* `uott` has no dependencies except the Python itself. Python is very common
  now, so `uott` can be used in many cases with ease.
* `uott` is very simple. Like many UNIX tools, it solves one single task. The
  whole package is < 10 files, < 500 lines of code, easy to audit.
* `uott` does not require any root privileges (until you want it to listen
  privileged ports), so you can run it on remote machines as a regular user.

**Cons**

* `uott` does not protect its own TCP streams. If you need a protection, try to
  use `uott` in combination with SSH port forwarding. This is the cost of being
  simple and stupid, because network security is really complicated.
* `uott` keeps all the UDP sockets on the proxy side for the whole session even
  when they are not used. You can reach the OS limit of opened sockets very
  quickly. In this case you may need a more complex solution like a VPN tunnel.
  This is the cost of being simple and stupid, because a trivial proxy cannot
  investigate general UDP content to understand a UDP connection status.

### Alternatives

Let' compare `uott` with some alternatives:

* *netcat/socat*. These programs are really good in debugging networks. However,
  the task of transferring UDP datagrams over TCP channel cannot be solved using
  these tools. *netcat/socat* just redirect streams, and the boundaries of UDP
  messages are not preserved. You still can use it for proxying simple UDP
  programs, but be ready for merged/truncated UDP datagrams.
* *VPN tunnel*. VPN tunnels make the remote UDP endpoint reachable for the local
  applications. There is no need to proxying UDP sockets on the remote side, and
  the OS limitation on the number of opened files does not matter anymore. Some
  adequate network protection is also provided, so most of the `uott` drawbacks
  are resolved. However, an establishing of a full-blown VPN may be a complex
  task, and usually it requires root privileges. Moreover, VPNs lack *proxy*
  functionality, thus some `uott` cases cannot be covered (such as access to
  remote loopback application).
* *Advanced proxies*. If `uott` solves your task but lacks some extra
  functionality, try to use advanced proxies, such as:
  - SOCKS
  - Shadowsocks
  - [pproxy](https://github.com/qwj/python-proxy)
  - [sshuttle](https://github.com/sshuttle/sshuttle)
  - or search the internet for comprehensive tools review like
    [anderspitman/awesome-tunneling](https://github.com/anderspitman/awesome-tunneling)
  These projects are larger and can more complex than `uott` to use and setup,
  but they provide more features.

## Usage

Before using `uott`, make sure that you understand its drawbacks. The short
disclaimer is provided here to emphasize the possible problems with `uott`.

### Disclaimer

The TCP connections created by `uott` are not protected - make sure that you
don't use it over the public networks. UDP sockets are keeped on the remote
proxying side for the end of the session - make sure that the remote OS will not
become unreachable due to opening so many sockets.

### Use cases

#### Case 1: UDP application on a remote's loopback

Let's simulate the UDP application on the loopback using `netcat` tool. Run the
following command on the remote side:

```shell
netcat -ul 127.0.0.1 50000
```

It will open the UDP server on remote's loopback with port `50000`. In another
terminal session launch `uott` proxy:

```shell
python3 -m uott proxy 0.0.0.0:40000 127.0.0.1:50000
```

This will launch the proxy on `40000` TCP port. Then connect the client:

```shell
python3 -m uott client 127.0.0.1:30000 ${REMOTE_IP}:40000
```

This will launch the client listening local UDP port `30000` connected to the
proxy on `REMOTE_IP:40000`. Try the established proxy connection by running UDP
client on the client side in another terminal.

```shell
netcat -u 127.0.0.1 30000
```

Now you can see UDP clients talk transparently.

#### Case 2: secure UDP tunnel over SSH

Let's imagine that remote UDP service is on the `X.Y.Z.K:PORT_X` endpoint and
the SSH gateway has the `A.B.C.D` address. First launch the proxy on SSH gateway
(open TCP port on loopback, not on 0.0.0.0 to avoid connections from the
external network):

```shell
python3 -m uott proxy 127.0.0.1:PORT_A X.Y.Z.K:PORT_X
```

Then on the client side forward some local `PORT_B` port to `PORT_A` of the
SSH gateway:

```shell
ssh -L PORT_B:127.0.0.1:PORT_A LOGIN@A.B.C.D
```

Then launch the client on the client side listening UDP port `PORT_UDP` and
connected to forwarded TCP port `PORT_B` (choose the best variant for you):

```shell
# listen on 127.0.0.1 if you want to use just local programs
python3 -m uott client 127.0.0.1:PORT_UDP 127.0.0.1:PORT_B

# listen on 0.0.0.0 if you want to allow external nodes to use the UDP tunnel
python3 -m uott client 0.0.0.0:PORT_UDP 127.0.0.1:PORT_B
```

Then you can use your `PORT_UDP` port on your client to transfer UDP datagrams
to `X.Y.Z.K:PORT_X` using SSH gateway `A.B.C.D`.

#### Case 3: UDP port forwarding for Android Debug Bridge (ADB)

The same as in case #2, but forward TCP ports using ADB instead of SSH.

```shell
adb forward tcp:PORT_B tcp:PORT_A
```
