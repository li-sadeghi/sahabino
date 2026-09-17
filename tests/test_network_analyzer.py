import socket
from pathlib import Path

import dpkt

from network_service.analyzer import analyze_pcap


def packet(
    src,
    dst,
    sport,
    dport,
    flags,
    seq=0,
    window=8192,
    payload=b"",
):
    tcp = dpkt.tcp.TCP(
        sport=sport,
        dport=dport,
        flags=flags,
        seq=seq,
        win=window,
        data=payload,
    )

    ip = dpkt.ip.IP(
        src=socket.inet_aton(src),
        dst=socket.inet_aton(dst),
        p=dpkt.ip.IP_PROTO_TCP,
        data=tcp,
    )
    ip.len = len(ip)

    return bytes(
        dpkt.ethernet.Ethernet(
            src=b"\x00\x01\x02\x03\x04\x05",
            dst=b"\x06\x07\x08\x09\x0a\x0b",
            type=dpkt.ethernet.ETH_TYPE_IP,
            data=ip,
        )
    )


def udp_packet(payload=b"data"):
    udp = dpkt.udp.UDP(
        sport=1234,
        dport=443,
        data=payload,
    )
    udp.ulen = len(udp)

    ip = dpkt.ip.IP(
        src=socket.inet_aton("10.0.0.1"),
        dst=socket.inet_aton("10.0.0.2"),
        p=dpkt.ip.IP_PROTO_UDP,
        data=udp,
    )
    ip.len = len(ip)

    return bytes(
        dpkt.ethernet.Ethernet(
            src=b"\x00\x01\x02\x03\x04\x05",
            dst=b"\x06\x07\x08\x09\x0a\x0b",
            type=dpkt.ethernet.ETH_TYPE_IP,
            data=ip,
        )
    )


def test_analyze_pcap_calculates_required_metrics(
    tmp_path: Path,
):
    path = tmp_path / "sample.pcap"

    with path.open("wb") as stream:
        writer = dpkt.pcap.Writer(stream)

        writer.writepkt(
            packet(
                "10.0.0.1",
                "10.0.0.2",
                1234,
                443,
                dpkt.tcp.TH_SYN,
                seq=10,
            ),
            ts=1.0,
        )

        writer.writepkt(
            packet(
                "10.0.0.2",
                "10.0.0.1",
                443,
                1234,
                dpkt.tcp.TH_SYN | dpkt.tcp.TH_ACK,
                seq=20,
            ),
            ts=1.05,
        )

        data = packet(
            "10.0.0.1",
            "10.0.0.2",
            1234,
            443,
            dpkt.tcp.TH_PUSH | dpkt.tcp.TH_ACK,
            seq=11,
            payload=b"hello",
        )

        writer.writepkt(data, ts=1.1)
        writer.writepkt(data, ts=1.2)

        writer.writepkt(
            packet(
                "10.0.0.2",
                "10.0.0.1",
                443,
                1234,
                dpkt.tcp.TH_ACK,
                window=0,
            ),
            ts=1.3,
        )

        writer.writepkt(
            packet(
                "10.0.0.2",
                "10.0.0.1",
                443,
                1234,
                dpkt.tcp.TH_RST,
            ),
            ts=1.4,
        )

        writer.writepkt(
            udp_packet(b"udp"),
            ts=1.5,
        )

    result = analyze_pcap(path)

    assert result["handshake_rtt_ms"] == 50.0
    assert result["retransmission_count"] == 1
    assert result["zero_window_count"] == 1
    assert result["tcp_reset_count"] == 1
    assert result["payload_bytes"] == 13
    assert result["total_bytes"] > result["payload_bytes"]
    assert 0 < result["overhead_ratio"] < 1


def test_empty_pcap_has_zero_ratio(tmp_path: Path):
    path = tmp_path / "empty.pcap"

    with path.open("wb") as stream:
        dpkt.pcap.Writer(stream).close()

    result = analyze_pcap(path)

    assert result["total_bytes"] == 0
    assert result["overhead_ratio"] == 0.0

def test_handshake_rtt_uses_initial_syn_when_syn_is_retransmitted(
    tmp_path: Path,
):
    path = tmp_path / "syn-retransmission.pcap"

    with path.open("wb") as stream:
        writer = dpkt.pcap.Writer(stream)

        # Initial SYN.
        writer.writepkt(
            packet(
                "10.0.0.1",
                "10.0.0.2",
                1234,
                443,
                dpkt.tcp.TH_SYN,
                seq=10,
            ),
            ts=1.0,
        )

        # Retransmitted SYN.
        writer.writepkt(
            packet(
                "10.0.0.1",
                "10.0.0.2",
                1234,
                443,
                dpkt.tcp.TH_SYN,
                seq=10,
            ),
            ts=1.03,
        )

        # SYN-ACK is received 50 ms after the initial SYN.
        writer.writepkt(
            packet(
                "10.0.0.2",
                "10.0.0.1",
                443,
                1234,
                dpkt.tcp.TH_SYN | dpkt.tcp.TH_ACK,
                seq=20,
            ),
            ts=1.05,
        )

    result = analyze_pcap(path)

    assert result["handshake_rtt_ms"] == 50.0
    assert result["retransmission_count"] == 1
