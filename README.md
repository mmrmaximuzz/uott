# uott

Simple and stupid transparent proxy for UDP applications.

## Introduction

`uott` (UDP Over TCP Transport) is a simple and stupid proxy allowing to send UDP
datagrams over TCP streams.

There are some cases when somebody *really* needs to send UDP datagrams but it
is impossible to send them directly. This is not so uncommon, especially when
debugging UDP applications, for example:

1. You want to interact with some remote UDP application, but the UDP datagrams
   cannot be passed through the network for some reason (port is filtered / UDP
   is filtered / UDP datagrams are dropped due to fragmentation / ...). If you
   still can create TCP connections in that network, you can succeed with
   `uott`.

1. You want to interact with some remote UDP application from your local
   machine, but the remote application listens loopback device only, making it
   unreachable from the external networks. If you can run TCP applications
   listening on some public interface of that remote machine, you can succeed
   with `uott`.

1. You want to interact with some remote UDP application, but the application
   protocol is not protected, and there is a public network segment on the path.
   If you can forward TCP ports in a secure way (using SSH port forwarding or
   similar) to protect the channel on the public path, you can succeed with
   `uott`.

### Algorithm

### Pros/Cons

**Pros**

**Cons**

### Alternatives

## Usage

### Disclaimer

### Case 1: UDP application on a remote's loopback

### Case 2: secure UDP tunnel

### Case 3: UDP port forwarding for ADB
