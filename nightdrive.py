#!/usr/bin/env python3
"""NIGHT DRIVE v2 - an endless neon racer that runs in your terminal.

    <- -> / A D   steer            SPACE   nitro
    ^ / W         throttle         H       horn (traffic ahead moves over)
    v / S         brake            T       next scenery theme
    F / X         fire rocket      B       bomb (clears the road ahead)
    P pause    R restart    C change car    M mute    Q quit

Three cars with different specs, five stages (night, dawn, desert, storm, city),
guard rails, shields, nitro, rockets, bombs, power-ups, near-miss combos. Pure Python standard library (curses).
Run:  python3 nightdrive.py
"""
import curses
import math
import os
import random
import sys
import time

BEST_FILE = os.path.expanduser("~/.nightdrive_best")
D = 9.0            # perspective depth constant
FPS = 30
UNIT_M = 0.2778    # metres per world unit (speed 200 = 200 km/h)
STAGE_KM = 1.5
SCEN_GAP = 38.0
RAIL = 1.05         # guard rail position (road edge is 1.0)
COL = {}
HEADLESS = False

CARS = [
    dict(name="VIPER", col="p_viper", top=230, acc=55, grip=1.00, tank=100, shields=3, blurb="balanced all-rounder"),
    dict(name="BULL", col="p_bull", top=205, acc=75, grip=1.30, tank=70, shields=5, blurb="slow, sticky, built like a tank"),
    dict(name="GHOST", col="p_ghost", top=265, acc=42, grip=0.80, tank=140, shields=2, blurb="fastest, slippery, fragile"),
]

THEMES = [
    dict(name="NEON NIGHT", sky=(17, 54, 90), stars=True, sun=(226, 214, 199), moon=False, hill=53, city=False,
         rain=False, g=(233, 234), grid=199, rb=(199, 231), rd=(237, 238), mark=229, leaf=35, trunk=94,
         sign=199, scen=("palm", "lamp", "sign", "palm")),
    dict(name="DAWN", sky=(61, 175, 216), stars=False, sun=(231, 229, 222), moon=False, hill=60, city=False,
         rain=False, g=(28, 34), grid=None, rb=(196, 231), rd=(240, 241), mark=231, leaf=22, trunk=94,
         sign=33, scen=("pine", "palm", "pine", "lamp")),
    dict(name="DESERT", sky=(52, 166, 214), stars=False, sun=(226, 220, 208), moon=False, hill=130, city=False,
         rain=False, g=(179, 180), grid=None, rb=(124, 231), rd=(238, 239), mark=229, leaf=64, trunk=94,
         sign=124, scen=("cactus", "cactus", "sign", "cactus")),
    dict(name="STORM", sky=(234, 236, 238), stars=False, sun=None, moon=False, hill=232, city=False,
         rain=True, g=(22, 23), grid=None, rb=(244, 252), rd=(235, 236), mark=250, leaf=23, trunk=237,
         sign=240, scen=("pine", "lamp", "pine")),
    dict(name="CYBER CITY", sky=(16, 17, 18), stars=True, sun=(255, 253, 251), moon=True, hill=234, city=True,
         rain=False, g=(16, 232), grid=51, rb=(51, 201), rd=(235, 236), mark=201, leaf=30, trunk=240,
         sign=201, scen=("lamp", "sign", "lamp")),
]

# vehicle sprites: '#' body, 'o' tail light, 'w' wheel, ' ' transparent
CAR_SPR = {
    1: ["#"],
    3: ["▄#▄"],
    5: ["▗▄▄▄▖", "o###o"],
    7: ["▗▄▄▄▄▄▖", "▐#▀▀▀#▌", "o#####o", " w   w "],
    9: ["  ▄▄▄▄▄  ", " ▐#▀▀▀#▌ ", "▐o#####o▌", " ww   ww "],
}
TRUCK_SPR = {
    1: ["#"],
    3: ["###", "###"],
    5: ["#####", "#####", "o###o"],
    7: ["#######", "#######", "#######", "o#####o", " w   w "],
    9: [" ####### ", " ####### ", " ####### ", " ####### ", "▐o#####o▌", " ww   ww "],
}
PLAYER = ["   ▄▄▄▄▄   ",
          "  ▟#▀▀▀#▙  ",
          " ▐o#####o▌ ",
          " www   www "]
PICK_SPR = {1: ["?"], 3: ["[?]"], 5: [" ??? ", " ??? "], 7: ["       ", "   ?   ", "       "], 9: ["         ", "    ?    ", "         "]}
CAR_COLORS = ["c_cyan", "c_green", "c_yellow", "c_purple", "c_orange", "c_white"]
LANES = (-0.62, 0.0, 0.62)
SIGN_TEXT = ["NITRO", "FASTER", "NO BRAKES", "GO GO GO", "MOTEL", "EAT GAS", "HONK", "99 MILES"]

# roadside scenery: size -> rows of (text, colour); each row is centred, spaces are transparent
SCEN = {
    "palm": {1: [("▟▙", "leaf"), ("▌", "trunk")],
             2: [("▄▟██▙▄", "leaf"), ("▀ ▐▌ ▀", "leaf"), ("▐▌", "trunk"), ("▐▌", "trunk")],
             3: [(" ▄▄▟███▙▄▄ ", "leaf"), ("▟▀▀ ▟█▙ ▀▀▙", "leaf"), ("▀   ▐█▌   ▀", "leaf"),
                 ("▐█▌", "trunk"), ("▐█▌", "trunk"), ("▐█▌", "trunk"), ("▟█▙", "trunk")]},
    "pine": {1: [("▲", "leaf")],
             2: [("▟▙", "leaf"), ("▟██▙", "leaf"), ("▐▌", "trunk")],
             3: [("▟▙", "leaf"), ("▟██▙", "leaf"), ("▟████▙", "leaf"), ("▟██████▙", "leaf"),
                 ("▟████████▙", "leaf"), ("██", "trunk")]},
    "cactus": {1: [("╿", "leaf")],
               2: [("▄ █ ▄", "leaf"), ("▀▀█▀▀", "leaf"), ("█", "leaf")],
               3: [("██", "leaf"), ("█ ██ █", "leaf"), ("█ ██ █", "leaf"), ("▀▀██▀▀", "leaf"),
                   ("██", "leaf"), ("██", "leaf")]},
    "lamp": {1: [("•", "lamp"), ("│", "pole")],
             2: [("▄█▄", "lamp"), ("█", "pole"), ("█", "pole"), ("█", "pole")],
             3: [("▄███▄", "lamp"), ("▀▀█▀▀", "lamp"), ("█", "pole"), ("█", "pole"), ("█", "pole"),
                 ("█", "pole"), ("█", "pole")]},
    "sign": {1: [("▬", "lamp"), ("│", "pole")],
             2: [("%5s", "signt"), ("█", "pole"), ("█", "pole")],
             3: [("%11s", "signt"), ("%11t", "signt"), ("%11s", "signt"), ("█     █", "pole"),
                 ("█     █", "pole"), ("█     █", "pole")]},
}


def load_best():
    try:
        with open(BEST_FILE) as f:
            return float(f.read().strip())
    except Exception:
        return 0.0


def save_best(v):
    try:
        with open(BEST_FILE, "w") as f:
            f.write("%.3f" % v)
    except Exception:
        pass


def bar(frac, n, on="▰", off="▱"):
    k = max(0, min(n, int(round(frac * n))))
    return on * k + off * (n - k)


class Car:
    __slots__ = ("z", "l", "tl", "v", "c", "truck", "done", "hit")

    def __init__(self, z, l, v, c, truck):
        self.z, self.l, self.tl, self.v, self.c, self.truck = z, l, l, v, c, truck
        self.done = self.hit = False


class Game:
    def __init__(self, R, C, seed=None):
        self.rng = random.Random(seed)
        self.best = load_best()
        self.car_i = 0
        self.started = False
        self.mute = False
        self.fps = 0
        self.theme_shift = 0
        self.resize(R, C)
        self.reset()

    # ---------- setup ----------
    def resize(self, R, C):
        self.R, self.C = R, C
        self.hz = max(5, int(R * 0.38))
        r = random.Random(7)
        self.sky_w = W = C * 3
        a, b, c = r.random() * 6.3, r.random() * 6.3, r.random() * 6.3
        mh = self.hz * 0.45
        self.mtn = [int(mh * (0.45 + 0.28 * math.sin(2 * math.pi * x / W * 3 + a)
                              + 0.17 * math.sin(2 * math.pi * x / W * 8 + b)
                              + 0.10 * math.sin(2 * math.pi * x / W * 19 + c)))
                    for x in range(W)]
        self.city = [0] * W
        self.cid = [0] * W
        x = i = 0
        while x < W:
            w = r.randint(4, 9)
            h = r.randint(2, max(3, int(self.hz * 0.62)))
            for k in range(w):
                if x + k < W:
                    self.city[x + k] = h
                    self.cid[x + k] = i
            x += w + (1 if r.random() < 0.3 else 0)
            i += 1
        self.stars = [(r.randrange(W), r.randrange(2, max(3, self.hz - 2))) for _ in range(max(10, C // 3))]

    def reset(self):
        car = CARS[self.car_i]
        self.pos = 0.0
        self.speed = 0.0
        self.px = 0.0
        self.cars = []
        self.picks = []
        self.parts = []
        self.dead = False
        self.paused = False
        self.dist = 0.0
        self.t = 0.0
        self.next_car = 160.0
        self.next_pick = 420.0
        self.steer = 0
        self.steer_t = 0.0
        self.boost_t = 0.0
        self.brake_t = 0.0
        self.nitro_t = 0.0
        self.nit = False
        self.nitro = car["tank"] * 0.5
        self.shields = car["shields"]
        self.invuln = 0.0
        self.sky_off = 0.0
        self.shake = 0
        self.passed = 0
        self.score = 0.0
        self.combo = 0
        self.combo_t = 0.0
        self.best_combo = 0
        self.stage = 0
        self.flash = 0
        self.popup = None
        self.pop_t = 0.0
        self.new_best = False
        self.frame = 0
        self.rockets = 3
        self.bombs = 1
        self.shots = []
        self.star_t = 0.0
        self.x2_t = 0.0
        self.slow_t = 0.0
        self.on_rail = False
        self.smashed = 0

    # ---------- world ----------
    def theme_i(self):
        return (self.stage + self.theme_shift) % len(THEMES)

    def theme(self):
        return THEMES[self.theme_i()]

    def curve(self, z):
        return math.sin(z * 0.0045) * 0.8 + math.sin(z * 0.0017 + 1.3) * 0.7

    def vmax(self):
        car = CARS[self.car_i]
        return min(car["top"], car["top"] * 0.62 + self.t * 1.3)

    def road(self, p):
        """centre x and half width of the road on the row whose depth factor is p (0 far .. 1 near)"""
        C = self.C
        hw = C * 0.46 * p + 1
        c = self.curve(self.pos + 40)
        cx = C / 2 + c * (1 - p) ** 2 * C * 0.55 - self.px * hw
        return cx, hw

    def km(self):
        return self.dist * UNIT_M / 1000

    def say(self, text, t=1.6):
        self.popup, self.pop_t = text, t

    def beep(self):
        if not self.mute and not HEADLESS:
            try:
                curses.beep()
            except curses.error:
                pass

    def action(self, a):
        if a == "M":
            self.mute = not self.mute
            self.say("SOUND OFF" if self.mute else "SOUND ON", 1.0)
            return
        if not self.started:                       # car select menu
            if a == "L":
                self.car_i = (self.car_i - 1) % len(CARS)
            elif a == "R":
                self.car_i = (self.car_i + 1) % len(CARS)
            elif a in ("1", "2", "3"):
                self.car_i = int(a) - 1
            elif a in ("start", "N", "U"):
                self.reset()
                self.started = True
                self.say("STAGE 1 · " + self.theme()["name"], 2.0)
            return
        if a == "P" and not self.dead:
            self.paused = not self.paused
        elif a == "RST" and (self.dead or self.paused):
            self.reset()
        elif a == "C" and (self.dead or self.paused):
            self.reset()
            self.started = False
        elif a == "T":
            self.theme_shift += 1
            self.say(self.theme()["name"], 1.2)
        elif self.dead or self.paused:
            return
        elif a == "L":
            self.steer, self.steer_t = -1, 0.16
            self.px -= 0.04
        elif a == "R":
            self.steer, self.steer_t = 1, 0.16
            self.px += 0.04
        elif a == "U":
            self.boost_t = 0.3
        elif a == "D":
            self.brake_t = 0.3
        elif a == "N":
            if self.nitro > 1:
                self.nitro_t = 0.6
            else:
                self.say("NITRO EMPTY", 0.8)
        elif a == "F":
            if self.rockets > 0:
                self.rockets -= 1
                self.shots.append([self.pos + 2.0, self.px])
            else:
                self.say("NO ROCKETS", 0.8)
        elif a == "B":
            if self.bombs > 0:
                self.bombs -= 1
                hit = [o for o in self.cars if 0 < o.z - self.pos < 170]
                for o in hit:
                    self.smash(o, 100)
                self.cars = [o for o in self.cars if o not in hit]
                self.flash = 4
                self.shake = 10
                self.beep()
                self.say("BOMB!  %d destroyed" % len(hit), 1.3)
            else:
                self.say("NO BOMBS", 0.8)
        elif a == "H":
            self.beep()
            moved = 0
            for car in self.cars:
                dz = car.z - self.pos
                if 0 < dz < 120 and abs(car.l - self.px) < 0.4:
                    car.tl = max(LANES, key=lambda L: abs(L - self.px))
                    moved += 1
            self.say("HONK!" if moved else "honk", 0.7)

    def update(self, dt):
        self.frame += 1
        if self.shake:
            self.shake -= 1
        if self.flash:
            self.flash -= 1
        if self.pop_t > 0:
            self.pop_t -= dt
        self.move_parts(dt)
        if not self.started or self.paused or self.dead:
            return
        car = CARS[self.car_i]
        th = self.theme()
        rng = self.rng
        self.t += dt
        if self.invuln > 0:
            self.invuln -= dt

        # engine
        if self.nitro_t > 0:
            self.nitro_t -= dt
        self.nit = self.nitro_t > 0 and self.nitro > 0
        vm = self.vmax()
        if self.nit:
            vm += 55
            self.nitro = max(0.0, self.nitro - 38 * dt)
        else:
            self.nitro = min(car["tank"], self.nitro + 1.5 * dt)
        if self.brake_t > 0:
            self.speed -= 170 * dt
            self.brake_t -= dt
        elif self.nit:
            self.speed += (car["acc"] + 110) * dt
        elif self.boost_t > 0:
            self.speed += car["acc"] * 2 * dt
            self.boost_t -= dt
        else:
            self.speed += (car["acc"] if self.speed < vm * 0.7 else car["acc"] * 0.25) * dt
        if self.speed > vm:
            self.speed = max(vm, self.speed - 90 * dt)
        self.speed = max(0.0, self.speed)

        # steering
        grip = car["grip"] * (0.8 if th["rain"] else 1.0)
        if self.steer_t > 0:
            self.px += self.steer * dt * (1.5 + min(1.0, self.speed / vm) * 0.9) * grip
            self.steer_t -= dt
        c = self.curve(self.pos + 30)
        for name in ("star_t", "x2_t", "slow_t"):
            if getattr(self, name) > 0:
                setattr(self, name, getattr(self, name) - dt)
        sdt = dt * (0.45 if self.slow_t > 0 else 1.0)         # slow-mo slows the world, not your hands
        self.px -= c * (self.speed / 230) ** 1.5 * sdt * 1.7 / grip   # curves push you outward
        if abs(self.px) > RAIL:                                # guard rail: you cannot leave the road
            side = 1 if self.px > 0 else -1
            self.px = side * RAIL
            if not self.on_rail:                               # first contact: big scrub and bounce
                self.on_rail = True
                self.speed *= 0.7
                self.shake = max(self.shake, 5)
                self.px -= side * 0.05
                self.combo = 0
                self.say("RAIL!", 0.6)
            elif self.speed > 40:                              # grinding along it
                self.speed = max(40.0, self.speed - 130 * dt)
            self.burst(2, ("spark",), 0.5, self.C / 2 + side * 5, self.R - 3)
        elif abs(self.px) < RAIL - 0.08:
            self.on_rail = False
        self.sky_off += c * self.speed * sdt * 0.12
        self.pos += self.speed * sdt
        self.dist += self.speed * sdt
        self.add(self.speed * sdt * 0.1 * (1 + self.combo * 0.2))

        # stage
        st = int(self.km() / STAGE_KM)
        if st != self.stage:
            self.stage = st
            self.say("STAGE %d · %s" % (st + 1, self.theme()["name"]), 2.2)
        if th["rain"] and rng.random() < dt * 0.3:
            self.flash = 3
        if self.combo and self.combo_t > 0:
            self.combo_t -= dt
            if self.combo_t <= 0:
                self.combo = 0

        # spawn traffic and pickups
        if self.next_car < self.pos + 180:
            self.next_car = self.pos + 220
        while self.next_car < self.pos + 260:
            truck = rng.random() < 0.18
            l = rng.choice(LANES) + rng.uniform(-0.06, 0.06)
            v = rng.uniform(28, 50) if truck else rng.uniform(35, 80)
            col = rng.choice(("c_white", "c_orange")) if truck else rng.choice(CAR_COLORS)
            self.cars.append(Car(self.next_car, l, v, col, truck))
            gap = max(22.0, 85.0 - self.t * 0.7)
            self.next_car += rng.uniform(gap * 0.5, gap * 1.4)
        while self.next_pick < self.pos + 260:
            kind = "+" if self.shields < car["shields"] and rng.random() < 0.25 else rng.choice("NNRRB*2Z")
            self.picks.append([self.next_pick, rng.choice(LANES), kind])
            self.next_pick += rng.uniform(300, 600)

        thr = max(0.12, 9.0 / (self.C * 0.46 + 1))
        keep = []
        for o in self.cars:
            o.z += o.v * sdt
            if rng.random() < dt * 0.07 * (1 + self.stage * 0.4):       # lane change
                near = min(range(3), key=lambda i: abs(LANES[i] - o.l))
                o.tl = LANES[max(0, min(2, near + rng.choice((-1, 1))))]
            d = o.tl - o.l
            o.l += max(-0.7 * dt, min(0.7 * dt, d))
            dz = o.z - self.pos
            dl = abs(o.l - self.px)
            if -1.0 < dz < 1.3 and dl < thr * (1.35 if o.truck else 1.0) and (self.star_t > 0 or self.invuln <= 0):
                if self.star_t > 0:                            # invincible: plough straight through
                    self.smash(o, 200)
                    self.say("SMASH  +%d" % (200 * self.mult()), 0.8)
                    continue
                self.hit_car(o)
                if self.dead:
                    return
                continue
            if dz < 0 and not o.done:
                o.done = True
                self.passed += 1
                self.add(10)
                if dl < thr * 2.6 and self.speed > o.v + 25:
                    self.combo += 1
                    self.best_combo = max(self.best_combo, self.combo)
                    self.combo_t = 4.0
                    bonus = 50 * self.combo
                    self.add(bonus)
                    self.nitro = min(car["tank"], self.nitro + 12)
                    self.say("NEAR MISS  x%d  +%d" % (self.combo, bonus), 1.1)
            if dz > -6:
                keep.append(o)
        self.cars = keep

        if self.shots:                                         # rockets
            live = []
            for s_ in self.shots:
                z0 = s_[0]
                s_[0] += (self.speed + 260) * dt
                target = None
                for o in self.cars:
                    if abs(o.l - s_[1]) < 0.24 and z0 - 2 <= o.z <= s_[0] + 2 and (target is None or o.z < target.z):
                        target = o
                if target:
                    self.cars.remove(target)
                    self.smash(target, 150)
                    self.say("ROCKET HIT  +%d" % (150 * self.mult()), 0.9)
                elif s_[0] - self.pos < 240:
                    live.append(s_)
            self.shots = live

        keep = []
        for pk in self.picks:
            dz = pk[0] - self.pos
            if -1.0 < dz < 1.3 and abs(pk[1] - self.px) < thr * 1.5:
                k = pk[2]
                if k == "N":
                    self.nitro = min(car["tank"], self.nitro + 50)
                    self.say("NITRO +50", 1.0)
                elif k == "+":
                    self.shields = min(car["shields"], self.shields + 1)
                    self.say("SHIELD +1", 1.0)
                elif k == "R":
                    self.rockets = min(9, self.rockets + 3)
                    self.say("ROCKETS +3  (F to fire)", 1.2)
                elif k == "B":
                    self.bombs = min(3, self.bombs + 1)
                    self.say("BOMB +1  (B to drop)", 1.2)
                elif k == "*":
                    self.star_t = 6.0
                    self.say("INVINCIBLE!  ram everything", 1.4)
                elif k == "2":
                    self.x2_t = 10.0
                    self.say("DOUBLE SCORE", 1.2)
                else:
                    self.slow_t = 5.0
                    self.say("SLOW MOTION", 1.2)
                self.add(100)
                self.burst(10, ("spark",))
                continue
            if dz > -6:
                keep.append(pk)
        self.picks = keep

    def mult(self):
        return 2 if self.x2_t > 0 else 1

    def add(self, pts):
        self.score += pts * self.mult()

    def smash(self, o, pts):
        """blow up a traffic car at its place on screen (caller removes it from the list)"""
        dz = max(0.3, o.z - self.pos)
        p = D / (dz + D)
        cx, hw = self.road(p)
        self.burst(int(10 + 30 * p), ("spark", "tail", "flame"), 0.5 + p, cx + o.l * hw, self.hz - 1 + p * (self.R - self.hz) - 1)
        self.smashed += 1
        self.add(pts)

    def hit_car(self, o):
        self.shields -= 1
        self.combo = 0
        self.beep()
        if self.shields <= 0:
            self.crash()
            return
        self.speed *= 0.55
        self.invuln = 1.6
        self.shake = 8
        self.burst(18, ("spark", "tail"))
        self.say("HIT!  shields left: %d" % self.shields, 1.3)

    def crash(self):
        self.dead = True
        self.shake = 16
        self.speed = 0.0
        self.burst(70, ("spark", "tail", "flame"), 2.2)
        k = self.km()
        if k > self.best:
            self.best = k
            self.new_best = True
            save_best(k)

    # ---------- particles ----------
    def burst(self, n, cols, power=1.0, x=None, y=None):
        if x is None:
            x, y = self.C / 2, self.R - 3
        for _ in range(n):
            a = self.rng.uniform(0, math.pi)
            v = self.rng.uniform(8, 40) * power
            self.parts.append([x, y, math.cos(a) * v * 2, -math.sin(a) * v * 0.6,
                               self.rng.uniform(0.3, 1.1) * power, self.rng.choice("*✦•▪█"), self.rng.choice(cols)])

    def move_parts(self, dt):
        if not self.parts:
            return
        out = []
        for q in self.parts:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] += 22 * dt
            q[4] -= dt
            if q[4] > 0:
                out.append(q)
        self.parts = out

    # ---------- drawing ----------
    def put(self, scr, y, x, s, a):
        R, C = self.R, self.C
        if y < 0 or y >= R or not s:
            return
        x = int(x)
        if x < 0:
            s = s[-x:]
            x = 0
        lim = C - 1 if y == R - 1 else C
        if x >= lim:
            return
        s = s[:lim - x]
        if s:
            try:
                scr.addstr(y, x, s, a)
            except curses.error:
                pass

    def render(self, scr):
        R, C, hz = self.R, self.C, self.hz
        th = self.theme()
        sh = self.rng.randint(-1, 1) if self.shake else 0
        put = self.put

        # ----- sky -----
        for y in range(hz):
            put(scr, y, 0, " " * C, COL["sky%d" % min(2, y * 3 // hz)])
        if th["stars"]:
            so = int(self.sky_off * 0.3)
            for sx, sy in self.stars:
                x = (sx - so) % self.sky_w
                if x < C:
                    put(scr, sy, x, "·", COL["star"])
        if th["sun"]:
            r = max(3, min(hz - 2, C // 7))
            if th["moon"]:
                r = max(2, r // 2)
            scx = (C - int(self.sky_off * 0.05)) % (C + 4 * r) - 2 * r
            base = hz - (r if th["moon"] else 0)
            for y in range(base - r, base):
                dy = base - y
                if not th["moon"] and y > hz - r * 0.55 and y % 2 == 0:
                    continue                                  # retro stripes
                half = int(math.sqrt(max(0, r * r - dy * dy)) * 2)
                band = 0 if dy > r * 0.66 else (1 if dy > r * 0.33 else 2)
                put(scr, y, scx - half, "█" * (2 * half), COL["sun%d" % band])
        mo = int(self.sky_off)
        W = self.sky_w
        src = self.city if th["city"] else self.mtn
        heights = [src[(x + mo) % W] for x in range(C)]
        top = max(heights) if heights else 0
        for y in range(hz - top, hz):
            need = hz - y
            x = 0
            while x < C:
                if heights[x] >= need:
                    x0 = x
                    while x < C and heights[x] >= need:
                        x += 1
                    if th["city"]:
                        seg = "".join(
                            "▪" if (xx + mo) % 2 == 0 and (self.cid[(xx + mo) % W] * 31 + need * 17 + (xx + mo) * 7) % 5 < 2
                            else " " for xx in range(x0, x))
                        put(scr, y, x0, seg, COL["win"])
                    else:
                        put(scr, y, x0, "█" * (x - x0), COL["mtn"])
                else:
                    x += 1

        # ----- ground -----
        span = R - hz
        for y in range(hz, R):
            p = (y - hz + 1) / span
            z = self.pos + D * (1 / p - 1)
            pn = (y - hz + 2) / span
            zn = self.pos + D * (1 / pn - 1)
            stripe = int(z / 7) % 2
            grid = th["grid"] is not None and p > 0.06 and int(z / 7) != int(zn / 7)
            cx, hw = self.road(p)
            cx += sh
            rw = max(1.0, hw * 0.10)
            lo, li, ri, ro = int(cx - hw - rw), int(cx - hw), int(cx + hw), int(cx + hw + rw)
            g = COL["grid"] if grid else COL["g%d" % stripe]
            gch = "─" if grid else " "
            put(scr, y, 0, gch * max(0, lo), g)
            put(scr, y, lo, " " * max(0, li - lo), COL["rb%d" % stripe])
            put(scr, y, li, " " * max(0, ri - li), COL["rd%d" % stripe])
            put(scr, y, ri, " " * max(0, ro - ri), COL["rb%d" % stripe])
            put(scr, y, ro, gch * max(0, C - ro), g)
            put(scr, y, lo - 1, "▐", COL["rail" if stripe else "rail2"])
            put(scr, y, ro, "▌", COL["rail" if stripe else "rail2"])
            if stripe == 0:
                mw = max(1, int(hw * 0.025))
                for f in (-1 / 3, 1 / 3):
                    put(scr, y, int(cx + f * hw) - mw // 2, "█" * mw, COL["mark"])
        if self.nit:                                           # speed streaks
            for _ in range(10):
                y = self.rng.randrange(hz + 3, R - 1)
                p = (y - hz + 1) / span
                cx, hw = self.road(p)
                x = int(cx + self.rng.uniform(-0.95, 0.95) * hw)
                for k in range(max(1, int(p * 4))):
                    put(scr, y + k, x, "│", COL["mark"])

        # ----- roadside scenery (far to near) -----
        kinds = th["scen"]
        i_hi = int((self.pos + D * (1 / 0.05 - 1)) / SCEN_GAP)
        i_lo = int(self.pos / SCEN_GAP) + 1
        for i in range(i_hi, i_lo - 1, -1):
            dz = i * SCEN_GAP - self.pos
            if dz <= 0.3:
                continue
            p = D / (dz + D)
            size = 1 if p < 0.14 else 2 if p < 0.38 else 3
            y = int(hz - 1 + p * span)
            cx, hw = self.road(p)
            off = hw * 1.3 + 3
            for side in (-1, 1):
                h = ((i * 2 + (side > 0)) * 2654435761) & 0xffff
                if h % 5 == 0:
                    continue
                kind = kinds[(h >> 4) % len(kinds)]
                self.scenery(scr, SCEN[kind][size], y, int(cx + sh + side * off), SIGN_TEXT[(h >> 8) % len(SIGN_TEXT)])

        # ----- pickups and traffic (far to near) -----
        things = [(o.z - self.pos, o) for o in self.cars] + [(pk[0] - self.pos, pk) for pk in self.picks]
        things.sort(key=lambda t: -t[0])
        for dz, o in things:
            if dz <= 0.2:
                continue
            p = D / (dz + D)
            if p < 0.035:
                continue
            y = int(hz - 1 + p * span)
            cx, hw = self.road(p)
            wid = p * C * 0.08
            k = 1 if wid < 1.5 else 3 if wid < 3.5 else 5 if wid < 5.5 else 7 if wid < 8 else 9
            if isinstance(o, Car):
                self.sprite(scr, (TRUCK_SPR if o.truck else CAR_SPR)[k], y, int(cx + sh + o.l * hw), o.c)
            else:
                a = COL[{"N": "pk_n", "+": "pk_s", "R": "pk_r", "B": "pk_b"}.get(o[2], "pk_p")]
                rows = PICK_SPR[k]
                x0 = int(cx + sh + o[1] * hw) - len(rows[0]) // 2
                for j, line in enumerate(rows):
                    put(scr, y - (len(rows) - 1 - j), x0, line.replace("?", "★" if o[2] == "*" else o[2]), a)
        for s_ in self.shots:
            dz = s_[0] - self.pos
            if dz <= 0.2:
                continue
            p = D / (dz + D)
            y = int(hz - 1 + p * span)
            cx, hw = self.road(p)
            x = int(cx + sh + s_[1] * hw)
            if p > 0.3:
                put(scr, y - 2, x, "▲", COL["spark"])
                put(scr, y - 1, x, "█", COL["c_white"])
                put(scr, y, x, "▾", COL["flame"])
            else:
                put(scr, y, x, "╿", COL["spark"])

        # ----- player -----
        car = CARS[self.car_i]
        if not self.dead and not (self.invuln > 0 and self.frame % 4 < 2):
            pc = "spark" if self.star_t > 0 and self.frame % 2 else car["col"]
            self.sprite(scr, PLAYER, R - 2, C // 2 + sh, pc)
            if self.started and self.speed > 5:
                fl = COL["flame2"] if self.nit else COL["flame"]
                pat = ("▼▾▼", "▾▼▾")[self.frame % 2] if self.nit else ("˅", "ˇ")[self.frame // 2 % 2]
                for dx in (-3, 3):
                    put(scr, R - 1, C // 2 + sh + dx - len(pat) // 2, pat, fl)
        for q in self.parts:
            put(scr, int(q[1]), int(q[0]), q[5], COL[q[6]])

        # ----- rain -----
        if th["rain"]:
            for _ in range(C // 2):
                y = self.rng.randrange(2, R - 1)
                x = self.rng.randrange(0, C - 1)
                try:
                    a = scr.inch(y, x) & curses.A_COLOR
                except curses.error:
                    continue
                put(scr, y, x, "╱", a)

        self.hud(scr)

    def scenery(self, scr, rows, ybot, xc, text):
        n = len(rows)
        for i, (line, col) in enumerate(rows):
            y = ybot - (n - 1 - i)
            if col == "signt":
                w = int(line[1:-1])
                s = (text if line.endswith("t") or w < 6 else "")[:w].center(w)
                self.put(scr, y, xc - w // 2, s, COL[col])
                continue
            x0 = xc - len(line) // 2
            j = 0
            L = len(line)
            while j < L:                                       # draw runs, skip transparent gaps
                if line[j] == " ":
                    j += 1
                    continue
                k = j
                while k < L and line[k] != " ":
                    k += 1
                self.put(scr, y, x0 + j, line[j:k], COL[col])
                j = k

    def sprite(self, scr, rows, ybot, xc, color):
        n = len(rows)
        w = len(rows[0])
        x0 = xc - w // 2
        for i, line in enumerate(rows):
            y = ybot - (n - 1 - i)
            for j, ch in enumerate(line):
                if ch == " ":
                    continue
                if ch == "o":
                    self.put(scr, y, x0 + j, "█", COL["tail"])
                elif ch == "w":
                    self.put(scr, y, x0 + j, "▀", COL["wheel"])
                elif ch == "#":
                    self.put(scr, y, x0 + j, "▪" if w == 1 else "█", COL[color])
                else:
                    self.put(scr, y, x0 + j, ch, COL[color])

    def box(self, scr, lines):
        w = max(len(t) for t, _ in lines) + 8
        y0 = max(2, self.R // 2 - len(lines) // 2 - 1)
        x0 = (self.C - w) // 2
        self.put(scr, y0 - 1, x0, " " * w, COL["box"])
        for i, (t, col) in enumerate(lines):
            self.put(scr, y0 + i, x0, t.center(w), COL[col])
        self.put(scr, y0 + len(lines), x0, " " * w, COL["box"])
        return y0, x0, w

    def hud(self, scr):
        C = self.C
        car = CARS[self.car_i]
        top = car["top"] + 55
        gear = min(6, 1 + int(self.speed / (top / 6)))
        rpm = (self.speed % (top / 6)) / (top / 6) if self.speed > 1 else 0
        l0 = " NIGHT DRIVE │ %s │ STAGE %d %s │ SCORE %07d │ %s │ %.2f km │ BEST %.2f km" % (
            car["name"], self.stage + 1, self.theme()["name"], int(self.score),
            ("COMBO x%d" % self.combo) if self.combo else "combo --", self.km(), self.best)
        fps = "%d fps " % self.fps
        self.put(scr, 0, 0, l0.ljust(C), COL["hud"])
        self.put(scr, 0, C - len(fps), fps, COL["hud"])
        l1 = " %3d km/h  GEAR %d  RPM %s  " % (self.speed, gear, bar(rpm, 10, "▮", "▯"))
        self.put(scr, 1, 0, " " * C, COL["hud"])
        self.put(scr, 1, 0, l1, COL["hud"])
        x = len(l1)
        nt = "NITRO %s %3d%%  " % (bar(self.nitro / car["tank"], 10), self.nitro / car["tank"] * 100)
        self.put(scr, 1, x, nt, COL["hud2"])
        x += len(nt)
        sd = "SHIELD " + "♥" * self.shields + "♡" * (car["shields"] - self.shields)
        self.put(scr, 1, x, sd, COL["hudr"])
        x += len(sd)
        am = "   ROCKETS %d  BOMBS %d  " % (self.rockets, self.bombs)
        self.put(scr, 1, x, am, COL["hud"])
        x += len(am)
        pw = "".join(t % v for t, v in (("★ %.0fs  ", self.star_t), ("x2 %.0fs  ", self.x2_t), ("SLOW %.0fs  ", self.slow_t)) if v > 0)
        self.put(scr, 1, x, pw, COL["boxt"])
        if self.mute:
            self.put(scr, 1, x + len(pw), "[muted]", COL["hud"])

        if self.pop_t > 0 and self.popup and self.started and not self.dead:
            t = "  " + self.popup + "  "
            self.put(scr, 3, (C - len(t)) // 2, t, COL["boxt"])

        if not self.started:
            lines = [("N I G H T   D R I V E", "boxt"), ("", "box"),
                     ("◄   %d  %s   ►" % (self.car_i + 1, car["name"]), "boxt"),
                     (car["blurb"], "boxd"), ("", "box"), ("", "box"), ("", "box"), ("", "box"), ("", "box"), ("", "box"),
                     ("TOP SPEED  %s  %3d km/h" % (bar(car["top"] / 265, 10), car["top"]), "box"),
                     ("ACCEL      %s  %3d     " % (bar(car["acc"] / 75, 10), car["acc"]), "box"),
                     ("GRIP       %s  %.2f    " % (bar(car["grip"] / 1.3, 10), car["grip"]), "box"),
                     ("NITRO TANK %s  %3d     " % (bar(car["tank"] / 140, 10), car["tank"]), "box"),
                     ("SHIELDS    %s  %3d     " % (bar(car["shields"] / 5, 10), car["shields"]), "box"),
                     ("", "box"),
                     ("←→ steer   ↑ throttle   ↓ brake   SPACE nitro   H horn", "boxd"),
                     ("F rocket   B bomb   T theme   P pause   M mute   Q quit", "boxd"),
                     ("pick up:  N nitro  + shield  R rockets  B bomb", "boxd"),
                     ("★ invincible   2 double score   Z slow motion", "boxd"),
                     ("←→ pick a car, ENTER to drive", "boxt")]
            y0, x0, w = self.box(scr, lines)
            for k in range(6):
                self.put(scr, y0 + 4 + k, self.C // 2 - 9, " " * 19, COL["rd0"])
            self.sprite(scr, PLAYER, y0 + 8, self.C // 2, car["col"])
        elif self.paused:
            self.box(scr, [("PAUSED", "boxt"), ("", "box"), ("P continue    R restart    C change car    Q quit", "box")])
        elif self.dead:
            self.box(scr, [("W R E C K E D", "boxt"), ("", "box"),
                           ("SCORE %d" % int(self.score), "boxt"),
                           ("%.2f km    stage %d    %d passed    %d destroyed    best combo x%d" % (
                               self.km(), self.stage + 1, self.passed, self.smashed, self.best_combo), "box"),
                           ("NEW BEST DISTANCE!" if self.new_best else "best %.2f km" % self.best,
                            "boxt" if self.new_best else "boxd"), ("", "box"),
                           ("R restart    C change car    Q quit", "box")])


# ---------- colours ----------
def to8(n):
    """nearest of the 8 basic colours, for terminals without 256"""
    if n < 8:
        return n
    if n < 16:
        return n - 8
    if n >= 232:
        return 7 if n >= 244 else 0
    n -= 16
    r, g, b = n // 36, (n // 6) % 6, n % 6
    return (1 if r >= 3 else 0) | (2 if g >= 3 else 0) | (4 if b >= 3 else 0)


def theme_pairs(th, flash=False):
    s0, s1, s2 = (252, 253, 254) if flash else th["sky"]
    rd0, rd1 = th["rd"]
    g0, g1 = th["g"]
    sun = th["sun"] or (s0, s1, s2)
    rain = th["rain"]
    return {
        "sky0": (250 if rain else s0, s0), "sky1": (250 if rain else s1, s1), "sky2": (250 if rain else s2, s2),
        "star": (231, s0),
        "sun0": (sun[0], s1), "sun1": (sun[1], s1), "sun2": (sun[2], s2),
        "mtn": (th["hill"], s2), "win": (227, th["hill"]),
        "g0": (250 if rain else g0, g0), "g1": (250 if rain else g1, g1), "grid": (th["grid"] or g0, g0),
        "rb0": (th["rb"][0], th["rb"][0]), "rb1": (th["rb"][1], th["rb"][1]),
        "rd0": (250, rd0), "rd1": (250, rd1), "mark": (th["mark"], rd0),
        "tail": (196, rd0), "wheel": (232, rd0), "spark": (226, rd0), "flame": (208, rd0), "flame2": (51, rd0),
        "p_viper": (197, rd0), "p_bull": (208, rd0), "p_ghost": (159, rd0),
        "c_cyan": (51, rd0), "c_green": (46, rd0), "c_yellow": (226, rd0), "c_purple": (135, rd0),
        "c_orange": (214, rd0), "c_white": (255, rd0),
        "leaf": (th["leaf"], g0), "trunk": (th["trunk"], g0), "pole": (245, g0), "lamp": (229, g0),
        "signt": (231, th["sign"]),
        "pk_n": (16, 51), "pk_s": (231, 196), "pk_r": (231, 202), "pk_b": (231, 129), "pk_p": (16, 226),
        "rail": (252, g0), "rail2": (196, g0),
        "hud": (231, 16), "hud2": (51, 16), "hudr": (197, 16),
        "box": (231, 53), "boxt": (226, 53), "boxd": (250, 53),
    }


BOLD = {"hud", "hud2", "hudr", "boxt", "p_viper", "p_bull", "p_ghost", "pk_n", "pk_s", "pk_r", "pk_b", "pk_p", "rail", "rail2", "signt", "spark", "flame", "flame2"}


def apply_theme(th, flash=False):
    big = curses.COLORS >= 256
    for i, (name, (fg, bg)) in enumerate(theme_pairs(th, flash).items(), 1):
        curses.init_pair(i, fg if big else to8(fg), bg if big else to8(bg))
        COL[name] = curses.color_pair(i) | (curses.A_BOLD if name in BOLD else 0)


KEYMAP = {
    curses.KEY_LEFT: "L", ord("a"): "L", ord("A"): "L",
    curses.KEY_RIGHT: "R", ord("d"): "R", ord("D"): "R",
    curses.KEY_UP: "U", ord("w"): "U", ord("W"): "U",
    curses.KEY_DOWN: "D", ord("s"): "D", ord("S"): "D",
    ord(" "): "N", ord("n"): "N", ord("N"): "N",
    ord("f"): "F", ord("F"): "F", ord("x"): "F", ord("X"): "F", ord("b"): "B", ord("B"): "B",
    ord("h"): "H", ord("H"): "H", ord("t"): "T", ord("T"): "T",
    ord("p"): "P", ord("P"): "P", ord("r"): "RST", ord("R"): "RST",
    ord("c"): "C", ord("C"): "C", ord("m"): "M", ord("M"): "M",
    ord("1"): "1", ord("2"): "2", ord("3"): "3",
    10: "start", 13: "start", curses.KEY_ENTER: "start",
}


def main(stdscr):
    curses.curs_set(0)
    try:
        curses.set_escdelay(25)
    except Exception:
        pass
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.start_color()
    R, C = stdscr.getmaxyx()
    g = Game(R, C)
    applied = None
    last = time.time()
    fps_t, fps_n = last, 0
    while True:
        frame_start = time.time()
        while True:
            k = stdscr.getch()
            if k == -1:
                break
            if k in (ord("q"), ord("Q"), 27):
                return
            if k == curses.KEY_RESIZE:
                R, C = stdscr.getmaxyx()
                g.resize(R, C)
                stdscr.erase()
                continue
            a = KEYMAP.get(k)
            if a:
                g.action(a)
        now = time.time()
        g.update(min(0.05, now - last))
        last = now
        want = (g.theme_i(), g.flash > 0)
        if want != applied:
            apply_theme(THEMES[want[0]], want[1])
            applied = want
        if R < 24 or C < 80:
            stdscr.erase()
            g.put(stdscr, 0, 0, "Make the terminal bigger (80x24 or more)", 0)
        else:
            g.render(stdscr)
        stdscr.refresh()
        fps_n += 1
        if now - fps_t >= 1.0:
            g.fps, fps_n, fps_t = fps_n, 0, now
        time.sleep(max(0.0, 1 / FPS - (time.time() - frame_start)))


def selftest(frames=2500):
    """headless run: random driver, checks every draw stays on screen"""
    global HEADLESS, COL
    HEADLESS = True

    class Fake:
        def __init__(s, R, C):
            s.R, s.C, s.buf = R, C, [[" "] * C for _ in range(R)]

        def addstr(s, y, x, txt, a=0):
            assert 0 <= y < s.R and 0 <= x and x + len(txt) <= s.C, (y, x, len(txt))
            assert not (y == s.R - 1 and x + len(txt) >= s.C), "bottom-right cell"
            s.buf[y][x:x + len(txt)] = list(txt)

        def inch(s, y, x):
            assert 0 <= y < s.R and 0 <= x < s.C
            return 0

    class Z(dict):
        def __missing__(s, k):
            return 0
    COL = Z()
    names = set(theme_pairs(THEMES[0]))
    for th in THEMES:
        assert set(theme_pairs(th)) == names and set(theme_pairs(th, True)) == names
    shots = []
    for n, (R, C) in enumerate(((24, 80), (45, 160), (60, 230))):
        g = Game(R, C, seed=n + 1)
        g.best = 0.0
        scr = Fake(R, C)
        for ci in range(len(CARS)):                           # menu for every car
            g.car_i = ci
            g.render(scr)
        if n == 1:
            shots.append(scr)
            scr = Fake(R, C)
        g.car_i = n
        g.action("start")
        wrecks = hits = 0
        stages = set()
        for f in range(frames):
            if f % 5 == 0:
                g.action(random.choice(["L", "R", "L", "R", "U", "D", "N", "N", "H", "F", "F", "B", "x"]))
            if f % 400 == 399:
                g.action("T")
            if f == 100:
                g.action("P"); g.render(scr); g.action("P")
            if g.dead:
                wrecks += 1
                g.render(scr)
                g.action("RST")
            sh0 = g.shields
            g.update(1 / FPS)
            hits += g.shields < sh0
            stages.add(g.theme_i())
            g.render(scr)
        assert abs(g.px) <= RAIL + 1e-6
        print("%dx%d %s ok  wrecks=%d hits=%d themes=%s score=%d km=%.2f destroyed=%d" % (
            C, R, CARS[n]["name"], wrecks, hits, sorted(stages), g.score, g.km(), g.smashed))
        if n == 1:
            shots.append(scr)
    return shots


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        BEST_FILE = os.devnull
        for s in selftest():
            print("\n".join("".join(r) for r in s.buf))
    else:
        curses.wrapper(main)
