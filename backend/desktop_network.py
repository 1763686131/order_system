"""Discover private IPv4 interfaces and serve a Windows desktop instance."""

import ctypes as ct
import logging
import socket
from contextlib import ExitStack, contextmanager
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, NetmaskValueError
from struct import Struct
from threading import Event, Thread

from flask import abort, jsonify, request
from waitress import create_server, wasyncore


HOST = "127.0.0.1"
PORT = 17899
_PRIVATE_NETWORKS = tuple(IPv4Network(network) for network in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16"
))
_IP_ADDRESS_ROW = Struct("<4sI4sIIHH")
_PUBLIC_ENDPOINTS = {
    "health_check", "auth.bootstrap_status", "auth.bootstrap", "auth.login",
    "hr_qualifications.get_shared_qualification",
    "hr_reports.download_shared_file",
}


def private_interfaces():
    table = ct.WinDLL("iphlpapi").GetIpAddrTable
    table.argtypes = [ct.c_void_p, ct.POINTER(ct.c_ulong), ct.c_int]
    table.restype = ct.c_ulong
    size = ct.c_ulong()
    buffer = None
    status = table(None, ct.byref(size), False)
    while status == 122:  # ERROR_INSUFFICIENT_BUFFER
        buffer = ct.create_string_buffer(size.value)
        status = table(buffer, ct.byref(size), False)
    if status:
        raise ct.WinError(status)
    if buffer is None:
        return ()

    count = int.from_bytes(buffer[:4], byteorder="little")
    interfaces = {}
    for index in range(count):
        address, _, mask, _, _, _, flags = _IP_ADDRESS_ROW.unpack_from(buffer, 4 + index * _IP_ADDRESS_ROW.size)
        ip = IPv4Address(address)
        if not any(ip in network for network in _PRIVATE_NETWORKS) or flags & 0x0048:  # Disconnected or being deleted.
            continue
        if int.from_bytes(mask, "big"):
            try:
                interface = IPv4Interface(f"{ip}/{IPv4Address(mask)}")
            except NetmaskValueError:
                continue
            interfaces[str(ip)] = interface

    # Prefer the default-route adapter if Windows has one. A UDP socket connect
    # selects an interface without sending packets to the documentation address.
    preferred = None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("192.0.2.1", 9))
            preferred = probe.getsockname()[0]
        except OSError:
            pass
    return tuple(sorted(interfaces.values(), key=lambda item: str(item.ip) != preferred))


@contextmanager
def _listeners(interfaces):
    hosts = (HOST, *(str(interface.ip) for interface in interfaces))
    # All addresses use the same port, and no wildcard/public interface is bound.
    for requested_port in (PORT, 0):
        with ExitStack() as stack:
            listeners = []
            port = requested_port
            try:
                for host in hosts:
                    listener = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
                    listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    listener.bind((host, port))
                    port = listener.getsockname()[1]
                    listeners.append(listener)
            except OSError as error:
                if requested_port and error.winerror in (10048, 10013):
                    continue
                raise
            yield listeners, port, hosts
            return


def _access_policy(app, hosts, interfaces, port):
    from utils.auth import get_current_user

    allowed_hosts = {f"{host}:{port}" for host in hosts}

    @app.before_request
    def protect_desktop_requests():
        if request.host not in allowed_hosts:
            abort(400)
        peer = request.remote_addr
        if peer != HOST:
            client = IPv4Address(peer)
            if not any(client in network for network in _PRIVATE_NETWORKS):
                abort(403)
            if not any(client in interface.network for interface in interfaces):
                abort(403)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            request_origin = request.headers.get("Origin")
            if request_origin is not None and request_origin != f"http://{request.host}":
                abort(403)

        is_api_or_upload = request.path.startswith(("/api/", "/uploads/"))
        if is_api_or_upload and request.endpoint not in _PUBLIC_ENDPOINTS and not get_current_user():
            return jsonify(success=False, message="请先登录"), 401


@contextmanager
def local_server(app, interfaces=()):
    with _listeners(interfaces) as (listeners, port, hosts):
        _access_policy(app, hosts, interfaces, port)
        stopping = Event()
        sockets = {}
        server = create_server(app, map=sockets, sockets=listeners, threads=24, ident="OrderSystem")

        def serve():
            try:
                while not stopping.is_set():
                    wasyncore.loop(timeout=0.25, count=1, map=sockets)
            except Exception:
                logging.exception("The server stopped unexpectedly")
            finally:
                wasyncore.close_all(sockets, ignore_all=True)
                server.task_dispatcher.shutdown(timeout=2)

        worker = Thread(target=serve, name="desktop-server", daemon=True)
        worker.start()
        urls = [f"http://{host}:{port}" for host in hosts]
        for url in urls:
            logging.info("Listening on %s", url)
        try:
            yield urls, worker
        finally:
            stopping.set()
            worker.join(timeout=3)
