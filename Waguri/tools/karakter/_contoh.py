"""Contoh minimal pemakaian inti.py (tidak dimasukkan ke paket)."""
from inti import (Model, kuas_kain, kuas_kulit, kuas_lapis, kuas_per_sisi, kuas_poni, kuas_rambut,
                  kuas_ujung_rambut, kuas_wajah, pasang_mata, kuas_polos, kuas_lipit)

KULIT = "#f8dccb"
RAMBUT = ("#2f2338", "#1e1625", "#6a5684")


def buat():
    m = Model("contoh", "Contoh", "Contoh", 0.9, "uji kerangka")
    # kepala
    m.kubus("head", [-4.5, 23.5, -4.5], [9, 9, 9], kuas_per_sisi(
        depan=kuas_wajah(KULIT, RAMBUT[0], "senyum"), bawah=kuas_kulit(KULIT), lain=kuas_rambut(RAMBUT)))
    m.kubus("head", [-4.75, 28.5, -4.9], [9.5, 4, 1], kuas_per_sisi(depan=kuas_poni(RAMBUT), belakang=kuas_poni(RAMBUT), lain=kuas_rambut(RAMBUT)))
    pasang_mata(m, KULIT, "#3a4d8f", RAMBUT[0])
    m.kubus("rambut_belakang", [-5, 21, 3.5], [10, 11, 2], kuas_rambut(RAMBUT))
    m.kubus("rambut_belakang2", [-5, 13, 3.5], [10, 8, 2], kuas_ujung_rambut(RAMBUT, 0.6, "gelombang"))
    for i in range(5):
        m.cermin("head", [-5.3, 21 - i * 0.5, -3 + i * 1.4], [1, 10, 1.4], kuas_ujung_rambut(RAMBUT, 0.5), rot=[0, 0, 4 + i * 2])
    # badan
    m.kubus("body", [-1, 23, -1], [2, 1, 2], kuas_kulit(KULIT))
    m.kubus("body", [-3.5, 12, -2], [7, 11, 4], kuas_kain("#c98f9b"))
    m.cermin("rightArm", [-7, 17, -1.5], [3, 6, 3], kuas_kain("#c98f9b"))
    m.cermin("rightForearm", [-7, 13, -1.5], [3, 4, 3], kuas_kain("#c98f9b"))
    m.cermin("rightForearm", [-6.9, 11, -1.4], [2.8, 2, 2.8], kuas_kulit(KULIT))
    m.cermin("rightLeg", [-3.4, 6, -1.5], [3, 6, 3], kuas_kain("#24212b"))
    m.cermin("rightShin", [-3.4, 0, -1.5], [3, 6, 3], kuas_kain("#24212b"))
    for i in range(12):
        import math
        a = i / 12 * 360
        x, z = 4.2 * math.sin(math.radians(a)), -3.2 * math.cos(math.radians(a))
        m.kubus("rok", [x - 1.1, 5, z - 0.25], [2.2, 8, 0.5], kuas_lipit("#c98f9b", "#9f6874"), rot=[0, -a, 0])
    return [m]
