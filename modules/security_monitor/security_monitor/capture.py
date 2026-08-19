from __future__ import annotations

import threading


class PacketCapture:
    """An explicitly started, metadata-only packet capture session."""
    def __init__(self, observe) -> None:
        self.observe = observe
        self.sniffer = None
        self.timer: threading.Timer | None = None
        self.last_error: str | None = None

    @property
    def active(self) -> bool:
        return bool(self.sniffer and self.sniffer.running)

    def start(self, seconds: int, interface: str | None = None) -> None:
        if self.active:
            raise RuntimeError("Network monitoring is already running.")
        try:
            from scapy.all import AsyncSniffer, IP, TCP, UDP  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError(
                "Scapy is unavailable. Install the root requirements file; on Windows, "
                "network capture also requires Npcap and an authorised capture environment."
            ) from error

        def inspect(packet) -> None:
            if not packet.haslayer(IP):
                return
            ip = packet[IP]
            if packet.haslayer(TCP):
                tcp = packet[TCP]
                flags = int(tcp.flags)
                self.observe(ip.src, ip.dst, "tcp", int(tcp.dport), bool(flags & 0x02), bool(flags & 0x10))
            elif packet.haslayer(UDP):
                udp = packet[UDP]
                self.observe(ip.src, ip.dst, "udp", int(udp.dport), False, False)

        try:
            self.sniffer = AsyncSniffer(iface=interface, prn=inspect, store=False)
            self.sniffer.start()
        except Exception as error:
            self.sniffer = None
            self.last_error = str(error)
            raise RuntimeError(
                "Network capture could not start. Check Npcap, the selected interface, "
                "and capture permission."
            ) from error
        self.timer = threading.Timer(seconds, self.stop)
        self.timer.daemon = True
        self.timer.start()

    def stop(self) -> None:
        if self.timer:
            self.timer.cancel()
            self.timer = None
        if self.sniffer and self.sniffer.running:
            self.sniffer.stop()
