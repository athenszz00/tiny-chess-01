import json, os, urllib.request

# 0x88 board. piece = type | colour<<3; types 1..6 = P N B R Q K; colour 0 white, 1 black.
# move = from | to<<7 | promo<<14 | 1<<17 capture | 1<<18 ep | 1<<19 castle | 1<<20 double push
V = (0, 100, 320, 330, 500, 900, 0)
NV = V[:1] + (0,) + V[2:]
MATE = 100000
PHASE = 6200
BUDGET = 100000
KN = (33, 31, 18, 14, -14, -18, -31, -33)
KI = (1, -1, 16, -16, 15, 17, -15, -17)
BI = (15, 17, -15, -17)
RI = (1, -1, 16, -16)
CK = [15] * 128
CK[0] = 13; CK[7] = 14; CK[4] = 12; CK[112] = 7; CK[119] = 11; CK[116] = 3

ZB = [0] * 2073
_x = 0x243F6A8885A308D3
for _i in range(2073):
    _x = (_x * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    ZB[_i] = _x


def _pst(t, r, f):
    c = min(f, 7 - f) + min(r, 7 - r)
    return ((0, 0, 4, 8, 14, 24, 40, 0)[r] + (f in (3, 4)) * (0, 0, 0, 10, 15, 10, 5, 0)[r],
            6 * c - 20, 4 * c - 8, (15 if r == 6 else 0) + (5 if r == 0 and f in (3, 4) else 0),
            2 * c - 6)[t - 1]


PV = [0] * 2048
KM = [0] * 256
KE = [0] * 256
for _sq in range(128):
    if _sq & 0x88: continue
    _f = _sq & 7; _r = _sq >> 4
    for _t in range(1, 6):
        PV[_t * 128 + _sq] = V[_t] + _pst(_t, _r, _f)
        PV[(_t | 8) * 128 + _sq] = -(V[_t] + _pst(_t, 7 - _r, _f))
    _c = min(_f, 7 - _f) + min(_r, 7 - _r)
    _b = (20, 25, 10, 0, 0, 10, 25, 20)[_f]
    KM[_sq] = _b if _r == 0 else max(-50, -15 * _r)
    KE[_sq] = 8 * _c - 24
    KM[128 + _sq] = -(_b if _r == 7 else max(-50, -15 * (7 - _r)))
    KE[128 + _sq] = -(8 * _c - 24)

B = [0] * 128
S = 0
C = 15
E = -1
H = 0
K = [4, 116]
Z = 0
PS = 0
NP = 0
BW = 0
BB = 0
U = []
HIST = []
GH = set()
RX = 0
TT = {}
KL = [0] * 256
N = 0
LIM = 0
AB = 0
CG = 0


def add(pc, sq):
    global PS, NP, BW, BB
    PS += PV[pc * 128 + sq]
    NP += NV[pc & 7]
    if pc == 3: BW += 1
    elif pc == 11: BB += 1


def rem(pc, sq):
    global PS, NP, BW, BB
    PS -= PV[pc * 128 + sq]
    NP -= NV[pc & 7]
    if pc == 3: BW -= 1
    elif pc == 11: BB -= 1


def reset():
    global B, S, C, E, H, Z, PS, NP, BW, BB, K, U
    B = [0] * 128
    back = (4, 2, 3, 5, 6, 3, 2, 4)
    for i, t in enumerate(back):
        B[i] = t; B[112 + i] = t | 8
        B[16 + i] = 1; B[96 + i] = 9
    S = 0; C = 15; E = -1; H = 0
    K = [4, 116]
    U = []
    PS = 0; NP = 0; BW = 0; BB = 0
    Z = ZB[2049 + 15]
    for sq in range(128):
        if sq & 0x88: continue
        pc = B[sq]
        if pc:
            Z ^= ZB[pc * 128 + sq]
            add(pc, sq)


def atk(sq, by):
    e = by << 3
    if by == 0:
        if not (sq - 15) & 0x88 and B[sq - 15] == 1: return 1
        if not (sq - 17) & 0x88 and B[sq - 17] == 1: return 1
    else:
        if not (sq + 15) & 0x88 and B[sq + 15] == 9: return 1
        if not (sq + 17) & 0x88 and B[sq + 17] == 9: return 1
    for d in KN:
        t = sq + d
        if not t & 0x88 and B[t] == 2 | e: return 1
    for d in KI:
        t = sq + d
        if not t & 0x88 and B[t] == 6 | e: return 1
    for d in BI:
        t = sq + d
        while not t & 0x88:
            p = B[t]
            if p:
                if p == 3 | e or p == 5 | e: return 1
                break
            t += d
    for d in RI:
        t = sq + d
        while not t & 0x88:
            p = B[t]
            if p:
                if p == 4 | e or p == 5 | e: return 1
                break
            t += d
    return 0


def csl(ms):
    us = S; them = us ^ 1
    base = 0 if us == 0 else 112
    k = base + 4
    if K[us] != k: return
    sh = 1 if us == 0 else 4
    lo = 2 if us == 0 else 8
    if not (C & (sh | lo)) or atk(k, them): return
    if C & sh and B[base + 5] == 0 and B[base + 6] == 0 and not atk(base + 5, them) and not atk(base + 6, them):
        ms.append(k | (base + 6) << 7 | 1 << 19)
    if C & lo and B[base + 3] == 0 and B[base + 2] == 0 and B[base + 1] == 0 and not atk(base + 3, them) and not atk(base + 2, them):
        ms.append(k | (base + 2) << 7 | 1 << 19)


def gen(caps):
    ms = []
    us = S; them = us ^ 1
    for f in range(128):
        if f & 0x88: continue
        pc = B[f]
        if not pc or pc >> 3 != us: continue
        t = pc & 7
        if t == 1:
            d = 16 - 32 * us
            r = f >> 4
            last = r == 6 - 5 * us
            o = f + d
            if B[o] == 0:
                if last:
                    for p in (5, 4, 3, 2): ms.append(f | o << 7 | p << 14)
                elif not caps:
                    ms.append(f | o << 7)
                    if r == 1 + 5 * us:
                        w = o + d
                        if B[w] == 0: ms.append(f | w << 7 | 1 << 20)
            for s in (d - 1, d + 1):
                to = f + s
                if to & 0x88: continue
                tg = B[to]
                if tg and tg >> 3 == them:
                    if last:
                        for p in (5, 4, 3, 2): ms.append(f | to << 7 | p << 14 | 1 << 17)
                    else: ms.append(f | to << 7 | 1 << 17)
                elif to == E:
                    ms.append(f | to << 7 | 1 << 17 | 1 << 18)
        elif t == 2 or t == 6:
            for s in KN if t == 2 else KI:
                to = f + s
                if to & 0x88: continue
                tg = B[to]
                if tg == 0:
                    if not caps: ms.append(f | to << 7)
                elif tg >> 3 == them: ms.append(f | to << 7 | 1 << 17)
            if t == 6 and not caps: csl(ms)
        else:
            for s in BI if t == 3 else RI if t == 4 else KI:
                to = f + s
                while not to & 0x88:
                    tg = B[to]
                    if tg == 0:
                        if not caps: ms.append(f | to << 7)
                    else:
                        if tg >> 3 == them: ms.append(f | to << 7 | 1 << 17)
                        break
                    to += s
    return ms


def make(m):
    global S, C, E, H, Z
    f = m & 127; t = (m >> 7) & 127
    pc = B[f]; us = S
    cs = t
    if m & 1 << 18: cs = t - 16 if us == 0 else t + 16
    cap = B[cs]
    U.append((m, cap, C, E, H, Z, PS, NP, BW, BB))
    if cap:
        Z ^= ZB[cap * 128 + cs]; B[cs] = 0; rem(cap, cs)
    Z ^= ZB[pc * 128 + f]; B[f] = 0; rem(pc, f)
    pr = (m >> 14) & 7
    pl = pc if pr == 0 else pr | us << 3
    B[t] = pl; add(pl, t); Z ^= ZB[pl * 128 + t]
    if (pc & 7) == 6: K[us] = t
    if m & 1 << 19:
        rf = f + 3 if t > f else f - 4
        rt = f + 1 if t > f else f - 1
        rk = B[rf]
        Z ^= ZB[rk * 128 + rf]; B[rf] = 0; rem(rk, rf)
        B[rt] = rk; add(rk, rt); Z ^= ZB[rk * 128 + rt]
    Z ^= ZB[2049 + C]
    C &= CK[f] & CK[t]
    Z ^= ZB[2049 + C]
    if E != -1: Z ^= ZB[2065 + (E & 7)]
    E = -1
    if m & 1 << 20:
        ep = 1 | (us ^ 1) << 3
        if (not (t + 1) & 0x88 and B[t + 1] == ep) or (not (t - 1) & 0x88 and B[t - 1] == ep):
            E = (f + t) >> 1
            Z ^= ZB[2065 + (E & 7)]
    H = 0 if (pc & 7) == 1 or cap else H + 1
    S ^= 1
    Z ^= ZB[2048]
    if atk(K[us], us ^ 1):
        unmake()
        return 0
    return 1


def unmake():
    global S, C, E, H, Z, PS, NP, BW, BB
    m, cap, C, E, H, Z, PS, NP, BW, BB = U.pop()
    S ^= 1
    us = S
    f = m & 127; t = (m >> 7) & 127
    pl = B[t]
    pc = 1 | us << 3 if (m >> 14) & 7 else pl
    B[f] = pc; B[t] = 0
    if (pc & 7) == 6: K[us] = f
    if cap:
        cs = t - 16 if (m & 1 << 18) and us == 0 else t + 16 if m & 1 << 18 else t
        B[cs] = cap
    if m & 1 << 19:
        rf = f + 3 if t > f else f - 4
        rt = f + 1 if t > f else f - 1
        B[rf] = B[rt]; B[rt] = 0


def ev():
    ph = NP if NP < PHASE else PHASE
    w = K[0]; b = 128 + K[1]
    s = PS + (KM[w] * ph + KE[w] * (PHASE - ph)) // PHASE + (KM[b] * ph + KE[b] * (PHASE - ph)) // PHASE
    if BW > 1: s += 30
    if BB > 1: s -= 30
    return s if S == 0 else -s


def rep():
    if Z in GH: return 1
    n = len(HIST)
    i = n - 3
    while i > RX:
        if HIST[i] == Z: return 1
        i -= 2
    return 0


def order(ms, ply, tm):
    def key(m):
        if m == tm: return 1 << 30
        s = 0
        if m & 1 << 17:
            v = B[(m >> 7) & 127]
            s = 100000 + 10 * (V[v & 7] if v else 100) - (B[m & 127] & 7)
        if (m >> 14) & 7: s += 200000 + V[(m >> 14) & 7]
        if s == 0:
            if m == KL[ply * 2]: s = 50000
            elif m == KL[ply * 2 + 1]: s = 40000
        return s
    ms.sort(key=key, reverse=True)


def qs(a, b, ply):
    global N, AB
    N += 1
    if LIM and N >= LIM: AB = 1; return 0
    ck = atk(K[S], S ^ 1)
    if ply >= 128: return ev()
    best = -MATE - 1
    if not ck:
        st = ev()
        if st >= b: return st
        best = st
        if st > a: a = st
    ms = gen(0 if ck else 1)
    order(ms, ply, 0)
    legal = 0
    for m in ms:
        if not ck:
            v = B[(m >> 7) & 127]
            g = (V[v & 7] if v else 100) + (V[(m >> 14) & 7] - 100 if (m >> 14) & 7 else 0)
            if st + g + 200 < a: continue
        if make(m):
            legal += 1
            s = -qs(-b, -a, ply + 1)
            unmake()
            if AB: return 0
            if s > best: best = s
            if s >= b: return s
            if s > a: a = s
    if ck and legal == 0: return -MATE + ply
    return best


def ab(d, a, b, ply):
    global N, AB
    if ply > 0 and (H >= 100 or rep()): return 0
    if d <= 0 or ply >= 128: return qs(a, b, ply)
    N += 1
    if LIM and N >= LIM: AB = 1; return 0
    e = TT.get(Z)
    tm = 0
    if e:
        tm = e[3]
        if e[1] >= d:
            s = e[0]
            if s > MATE - 128: s -= ply
            elif s < -MATE + 128: s += ply
            if e[2] == 0 or (e[2] == 1 and s >= b) or (e[2] == 2 and s <= a): return s
    a0 = a
    ms = gen(0)
    order(ms, ply, tm)
    legal = 0; best = -MATE - 1; bm = 0
    for m in ms:
        if make(m):
            legal += 1
            HIST.append(Z)
            s = -ab(d - 1, -b, -a, ply + 1)
            HIST.pop()
            unmake()
            if AB: return 0
            if s > best: best = s; bm = m
            if s > a: a = s
            if a >= b:
                if not (m & 1 << 17) and not ((m >> 14) & 7) and KL[ply * 2] != m:
                    KL[ply * 2 + 1] = KL[ply * 2]; KL[ply * 2] = m
                break
    if legal == 0: return -MATE + ply if atk(K[S], S ^ 1) else 0
    s = best
    if s > MATE - 128: s += ply
    elif s < -MATE + 128: s -= ply
    TT[Z] = (s, d, 0 if best > a0 and best < b else 1 if best >= b else 2, bm)
    return best


def sr():
    global LIM, AB, N, RX
    ms = gen(0)
    lg = []
    for m in ms:
        if make(m):
            lg.append(m)
            unmake()
    if len(lg) == 1: return lg[0], 0
    N = 0
    RX = len(HIST) - 1
    order = [[m, 0] for m in lg]
    best = lg[0]; bs = 0
    for d in range(1, 65):
        LIM = 0 if d == 1 else BUDGET
        AB = 0
        a = -MATE - 1
        for r in order:
            make(r[0]); HIST.append(Z)
            r[1] = -ab(d - 1, -MATE - 1, -a, 1)
            HIST.pop(); unmake()
            if AB: break
            if r[1] > a: a = r[1]
        if AB: break
        order.sort(key=lambda r: -r[1])
        best, bs = order[0]
        if bs >= MATE - 128: break
    return best, bs


def uci(m):
    f = m & 127; t = (m >> 7) & 127
    s = "abcdefgh"[f & 7] + str((f >> 4) + 1) + "abcdefgh"[t & 7] + str((t >> 4) + 1)
    p = (m >> 14) & 7
    if p: s += " nbrq"[p]
    return s


def pu(u):
    f = (ord(u[1]) - 49) * 16 + ord(u[0]) - 97
    t = (ord(u[3]) - 49) * 16 + ord(u[2]) - 97
    p = " nbrq".index(u[4]) if len(u) == 5 else 0
    for m in gen(0):
        if (m & 127) == f and ((m >> 7) & 127) == t and ((m >> 14) & 7) == p and make(m):
            return
    raise ValueError("bad move " + u)


def ch(g):
    global GH, CG
    reset()
    h = [Z]
    for u in g["moves"]:
        pu(u)
        h.append(Z)
    HIST[:] = h
    GH = set(h[-1::-2][:H // 2 + 1])
    if g["game"] != CG:
        CG = g["game"]
        TT.clear()
    mv, sc = sr()
    return uci(mv), sc


def post(p, b):
    with urllib.request.urlopen(URL + p, json.dumps(b).encode()) as x:
        return json.load(x)


# === DRIVER ===
URL = os.environ["MAKEFUN_ENV_URL"]
while True:
    g = post("/game", {})
    if g["status"] == "done": break
    while g["status"] == "your_move":
        try:
            mv, sc = ch(g)
        except Exception:
            mv, sc = g["legal_moves"][0], 0
        try:
            g = post("/move", {"game": g["game"], "move": mv})
        except Exception:
            g = post("/move", {"game": g["game"], "move": g["legal_moves"][0]})
    print("game", g["game"], g["outcome"], g["reason"])
print("done", g.get("wins"), g.get("draws"), g.get("losses"))
