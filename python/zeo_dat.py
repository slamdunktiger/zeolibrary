"""
zeo_dat.py — Parse Zeo ZEOSLEEP.DAT binary files (firmware 2.6.3O).

Faithful Python-3 port of com.myzeo.decoder.ZeoData / ZeoDataDecoder
(Zeo, Inc. BSD-3-Clause). Records are exactly V22_SIZE = 1680 bytes,
prefixed by a 6-byte 'SLEEP\\0' identifier + 2-byte little-endian version.

VERIFIED against raipat/zeolibrary sample-files/ZEOSLEEP.DAT.

License: BSD-3-Clause (see LICENSE-BSD in repo).
"""
import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone

IDENTIFIER = b"SLEEP\x00"
IDENTIFIER_SIZE = 6
VERSION_SIZE = 2
V22_SIZE = 1680
EVENTS_SAVED = 4
ASSERT_NAME_MAX = 20
ALARM_EVENTS_SAVED = 2
SNOOZE_EVENTS_SAVED = 9
HEADBAND_IMPEDANCE_SIZE = 144
HEADBAND_PACKETS_SIZE = 144
HEADBAND_RSSI_SIZE = 144
HEADBAND_STATUS_SIZE = 36
HYP_BASE_LENGTH = 1920  # 16h / 30s


@dataclass
class ZeoRecord:
    timestamp: int = 0
    crc: int = 0
    airplane_off: int = 0
    airplane_on: int = 0
    factory_reset: int = 0
    headband_id: int = 0
    sensor_life_reset: int = 0
    sleep_stat_reset: int = 0
    alarm_off: int = 0
    awakenings: int = 0
    end_of_night: int = 0
    start_of_night: int = 0
    time_in_deep: int = 0
    time_in_light: int = 0
    time_in_rem: int = 0
    time_in_wake: int = 0
    time_to_z: int = 0
    total_z: int = 0
    zq: int = 0
    sleep_rating: int = 0
    base_hypnogram_count: int = 0
    base_hypnogram: list = field(default_factory=list)
    display_hypnogram: list = field(default_factory=list)

    def start_str(self):
        return datetime.fromtimestamp(self.start_of_night, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def end_str(self):
        return datetime.fromtimestamp(self.end_of_night, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def length_h(self):
        return (self.end_of_night - self.start_of_night) / 3600.0


def _u8(b):
    return b if b >= 0 else b + 256


def read_record(buf, off):
    """Parse one 1680-byte V22 record starting at buf[off]. Returns ZeoRecord."""
    r = ZeoRecord()
    p = off
    # little-endian helpers operating on a bytes slice
    def rd(fmt, n=1):
        nonlocal p
        out = []
        for _ in range(n):
            sz = struct.calcsize("<" + fmt)
            val = struct.unpack_from("<" + fmt, buf, p)[0]
            p += sz
            out.append(val)
        return out[0] if n == 1 else out

    r.timestamp = rd("I")
    r.crc = rd("I")
    tmp = rd("I")
    # bitfield: airplane_mode, alarm_reason, backlight, clock_mode, sleep_valid,
    #           snooze_time, wake_tone, wake_window, write_reason, zeo_wake_on, wdt_reset
    airplane_mode = tmp & 1
    alarm_reason = (tmp >> 1) & 0x7
    backlight = (tmp >> 4) & 0xF
    clock_mode = (tmp >> 8) & 1
    sleep_valid = (tmp >> 9) & 1
    snooze_time = (tmp >> 10) & 0x1F
    wake_tone = (tmp >> 15) & 0x7
    wake_window = (tmp >> 18) & 0x3F
    write_reason = (tmp >> 24) & 0x7
    zeo_wake_on = (tmp >> 27) & 1
    wdt_reset = (tmp >> 28) & 1
    r.airplane_off = rd("I")
    r.airplane_on = rd("I")
    rd("I", EVENTS_SAVED)  # change_time
    rd("I", EVENTS_SAVED)  # change_value
    rd("B", ASSERT_NAME_MAX)  # assert_function_name
    rd("i")  # assert_line_number
    r.factory_reset = rd("I")
    r.headband_id = rd("I")
    rd("B", HEADBAND_IMPEDANCE_SIZE)
    rd("B", HEADBAND_PACKETS_SIZE)
    rd("b", HEADBAND_RSSI_SIZE)  # signed
    rd("B", HEADBAND_STATUS_SIZE)
    rd("H")  # id_hw
    rd("H")  # id_sw
    rd("I", EVENTS_SAVED)  # change_time (2)
    rd("I", EVENTS_SAVED)  # change_value (2)
    r.sensor_life_reset = rd("I")
    r.sleep_stat_reset = rd("I")
    rd("I", ALARM_EVENTS_SAVED)  # alarm_ring
    rd("I", SNOOZE_EVENTS_SAVED)  # snooze
    r.alarm_off = rd("I")
    r.awakenings = rd("H")
    rd("H")  # awakenings_average
    r.end_of_night = rd("I")
    r.start_of_night = rd("I")
    r.time_in_deep = rd("H")
    rd("H")  # deep_average
    rd("H")  # deep_best
    r.time_in_light = rd("H")
    rd("H")  # light_average
    r.time_in_rem = rd("H")
    rd("H")  # rem_average
    rd("H")  # rem_best
    r.time_in_wake = rd("H")
    rd("H")  # wake_average
    r.time_to_z = rd("H")
    rd("H")  # to_z_average
    r.total_z = rd("H")
    rd("H")  # total_z_average
    rd("H")  # total_z_best
    r.zq = rd("H")
    rd("H")  # zq_average
    rd("H")  # zq_best
    rd("H")  # display_hypnogram_forced_index
    rd("H")  # display_hypnogram_forced_stage
    rd("I")  # hypnogram_start_time
    r.sleep_rating = rd("B")
    rd("B")  # pad
    rd("B")  # pad
    rd("B")  # pad
    rd("I")  # pad
    r.base_hypnogram_count = rd("I")
    # nibble-packed: 2 epochs per byte, low nibble first
    for i in range(0, HYP_BASE_LENGTH, 2):
        b = rd("B")
        r.base_hypnogram.append(b & 0xF)
        r.base_hypnogram.append(b >> 4)
    # build 5-min display hypnogram: collapse 10x30s epochs -> 1 stage
    # base stage codes: 0 unknown, 1 deep, 2 light, 3 rem, 4 wake, 6 deep2
    # display codes:    0 unknown, 1 deep, 2 light, 3 rem, 4 wake
    stage_map = {1: 1, 6: 1, 2: 2, 3: 3, 4: 4, 0: 0}
    n_display = r.base_hypnogram_count // 10
    for i in range(n_display):
        block = r.base_hypnogram[i * 10:(i + 1) * 10]
        nonzero = [s for s in block if s != 0]
        dom = max(set(nonzero), key=nonzero.count) if nonzero else 0
        r.display_hypnogram.append(stage_map.get(dom, 0))
    return r


def parse_dat(path):
    with open(path, "rb") as fh:
        data = fh.read()
    records = {}
    pos = 0
    n = len(data)
    while pos < n - (IDENTIFIER_SIZE + VERSION_SIZE + V22_SIZE):
        idx = data.find(IDENTIFIER, pos)
        if idx == -1:
            break
        v_off = idx + IDENTIFIER_SIZE
        version = struct.unpack_from("<H", data, v_off)[0]
        rec_off = v_off + VERSION_SIZE
        if rec_off + V22_SIZE > n:
            break
        try:
            r = read_record(data, rec_off)
        except (struct.error, IndexError):
            break
        if r.start_of_night > 0 and r.end_of_night > 0 and r.base_hypnogram_count > 0:
            records[r.start_of_night] = r
        pos = idx + 1
    return list(records.values())


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "sample-files/ZEOSLEEP.DAT"
    recs = parse_dat(src)
    print(f"Parsed {len(recs)} valid night records from {src}")
    if recs:
        r = sorted(recs, key=lambda x: x.start_of_night)[0]
        print(f"\nFirst night: {r.start_str()}")
        print(f"  end        : {r.end_str()}")
        print(f"  length     : {r.length_h():.2f} h")
        print(f"  ZQ         : {r.zq}")
        print(f"  Total Z    : {r.total_z} min")
        print(f"  Deep/Light/REM/Wake : {r.time_in_deep}/{r.time_in_light}/{r.time_in_rem}/{r.time_in_wake} min")
        print(f"  Time to Z  : {r.time_to_z} min")
        print(f"  sleep_rating: {r.sleep_rating}")
        print(f"  base hypnogram epochs: {len(r.base_hypnogram)} (count field={r.base_hypnogram_count})")
        print(f"  display hypnogram (5min) stages: {len(r.display_hypnogram)}")
        if len(recs) > 1:
            avg_zq = sum(x.zq for x in recs) / len(recs)
            avg_len = sum(x.length_h() for x in recs) / len(recs)
            avg_deep = sum(x.time_in_deep for x in recs) / len(recs)
            print(f"\nAverage over {len(recs)} nights:")
            print(f"  ZQ        : {avg_zq:.1f}")
            print(f"  length    : {avg_len:.2f} h")
            print(f"  deep      : {avg_deep:.1f} min")
