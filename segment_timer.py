#!/usr/bin/env python3
"""
Ruhiger Segment-Timer

Zeigt einen Timer als Reihe von "Lampen"-Segmenten, die sich nacheinander
langsam von dunkel zu grün einfärben. Es werden bewusst KEINE Minuten/
Sekunden angezeigt, damit der Timer nicht stresst oder ablenkt.

Bedienung:
    Leertaste          -> Start / Pause
    +  / Pfeil-Hoch     -> Zeit verlängern (fügt ein weiteres, gleich
                            langes Segment hinzu)
    -  / Pfeil-Runter   -> Zeit verkürzen (entfernt das letzte Segment)
    R                   -> Zurücksetzen
    F / F11             -> Vollbild an/aus
    Escape              -> Beenden (im Vollbild zuerst nur Vollbild verlassen)

Alle Segmente sind stets gleich lang (gleiche Zeitdauer). Mit +/- wird
nicht die Länge eines Segments verändert, sondern die Anzahl der
Segmente - jedes neue Segment hat exakt dieselbe Dauer wie die übrigen.

Wird keine Segmentanzahl angegeben, ergibt sie sich automatisch: Ist die
Timerlänge glatt durch 60 Sekunden teilbar, entspricht die Segmentanzahl
der Anzahl an Minuten (z.B. 10 Minuten -> 10 Segmente). Andernfalls wird
DEFAULT_SEGMENTS_FALLBACK verwendet.

Aufruf-Beispiele:
    python timer.py                     # DEFAULT_MINUTES Minuten -> DEFAULT_MINUTES Segmente
    python timer.py --minutes 10        # 10 Minuten -> 10 Segmente
    python timer.py --seconds 90        # nicht durch 60 teilbar -> DEFAULT_SEGMENTS_FALLBACK Segmente
    python timer.py --minutes 10 --segments 6 --fullscreen
"""

import argparse
import time
import tkinter as tk


# ---------------------------------------------------------------------------
# Standardwerte
# ---------------------------------------------------------------------------
DEFAULT_MINUTES = 5             # Timerlänge, wenn weder --minutes noch --seconds angegeben ist
DEFAULT_SEGMENTS_FALLBACK = 4    # Segmentanzahl, wenn die Timerlänge NICHT glatt durch 60s teilbar ist


# ---------------------------------------------------------------------------
# Farben: ruhig, gedämpft, kein grelles Neongrün, kein Rot/Orange (Stress)
# ---------------------------------------------------------------------------
BG_COLOR = "#111814"           # sehr dunkler Hintergrund (während des Timers)
BG_DONE_COLOR = "#2d6649"      # ruhiges Grün als Hintergrund, wenn Zeit vorbei ist
SEGMENT_OFF = "#22262f"        # "aus" - dunkles Blaugrau, ruhig
SEGMENT_ON = "#57c78f"         # sanftes, warmes Grün ("Lampe leuchtet") - bleibt auch nach Ablauf so
FRAME_COLOR = "#43996e"        # heller Rahmen um die gesamte Progressbar
FRAME_WIDTH = 5                # Strichbreite des hellen Rahmens in Pixel
GAP = 10                       # Abstand zwischen Segmenten in Pixel
MARGIN = 60                    # Außenabstand
FRAME_PADDING = 14             # Abstand zwischen Segmenten und Außenrahmen

MIN_SEGMENTS = 1               # es muss mindestens ein Segment übrig bleiben


def lerp(a, b, t):
    """Lineare Interpolation zwischen a und b (t in [0,1])."""
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    """Interpoliert zwischen zwei Hexfarben."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(lerp(r1, r2, t))
    g = int(lerp(g1, g2, t))
    b = int(lerp(b1, b2, t))
    return f"#{r:02x}{g:02x}{b:02x}"


class TimerApp:
    def __init__(self, root, total_seconds: float, segments: int, start_fullscreen: bool):
        self.root = root
        self.is_fullscreen = start_fullscreen

        # Die Dauer EINES Segments bleibt für die gesamte Laufzeit fix.
        # Verlängern/Verkürzen ändert nur die Anzahl der Segmente, nie
        # deren einzelne Länge - alle Segmente sind also immer gleich groß.
        segments = max(MIN_SEGMENTS, segments)
        self.segment_duration = total_seconds / segments
        self.segment_count = segments

        self.running = False
        self.finished = False
        self.elapsed = 0.0          # bereits verstrichene Zeit (für Pause)
        self.last_tick = None       # Zeitpunkt des letzten Frames

        self.root.title("Timer")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1000x300")

        self.canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._bind_keys()
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<Button-1>", lambda e: self.toggle_running())

        if self.is_fullscreen:
            self.root.attributes("-fullscreen", True)

        self.draw()
        self._loop()

    @property
    def total_seconds(self):
        return self.segment_duration * self.segment_count

    # ------------------------------------------------------------------
    # Eingaben
    # ------------------------------------------------------------------
    def _bind_keys(self):
        self.root.bind("<space>", lambda e: self.toggle_running())
        self.root.bind("<r>", lambda e: self.reset())
        self.root.bind("<R>", lambda e: self.reset())
        self.root.bind("<f>", lambda e: self.toggle_fullscreen())
        self.root.bind("<F>", lambda e: self.toggle_fullscreen())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", self._on_escape)

        # Zeit verlängern / verkürzen - jeweils um ein ganzes, gleich
        # langes Segment.
        self.root.bind("<plus>", lambda e: self.add_segment())
        self.root.bind("<KP_Add>", lambda e: self.add_segment())
        self.root.bind("<Up>", lambda e: self.add_segment())
        self.root.bind("<minus>", lambda e: self.remove_segment())
        self.root.bind("<KP_Subtract>", lambda e: self.remove_segment())
        self.root.bind("<Down>", lambda e: self.remove_segment())

    def _on_escape(self, event):
        if self.is_fullscreen:
            self.set_fullscreen(False)
        else:
            self.root.destroy()

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.is_fullscreen)

    def set_fullscreen(self, value: bool):
        self.is_fullscreen = value
        self.root.attributes("-fullscreen", value)
        self.draw()

    def toggle_running(self):
        if self.finished:
            return
        if self.running:
            self.running = False
        else:
            self.running = True
            self.last_tick = time.monotonic()

    def reset(self):
        self.running = False
        self.finished = False
        self.elapsed = 0.0
        self.last_tick = None
        self.draw()

    def add_segment(self):
        """Verlängert die Zeit um ein weiteres Segment gleicher Länge."""
        self.segment_count += 1
        # Falls die Zeit vorher abgelaufen war, ist jetzt wieder Zeit übrig
        if self.elapsed < self.total_seconds:
            self.finished = False
        self.draw()

    def remove_segment(self):
        """Verkürzt die Zeit um ein Segment (das letzte wird entfernt)."""
        if self.segment_count <= MIN_SEGMENTS:
            return
        self.segment_count -= 1
        if self.elapsed > self.total_seconds:
            self.elapsed = self.total_seconds
        if self.elapsed >= self.total_seconds:
            self.finished = True
            self.running = False
        self.draw()

    # ------------------------------------------------------------------
    # Zeit-Update
    # ------------------------------------------------------------------
    def _loop(self):
        if self.running and not self.finished:
            now = time.monotonic()
            dt = now - self.last_tick
            self.last_tick = now
            self.elapsed = min(self.total_seconds, self.elapsed + dt)
            if self.elapsed >= self.total_seconds:
                self.finished = True
                self.running = False
            self.draw()
        # ~30 Bilder pro Sekunde reicht für ein ruhiges, weiches Einfärben
        self.root.after(33, self._loop)

    # ------------------------------------------------------------------
    # Zeichnen
    # ------------------------------------------------------------------
    def draw(self):
        # Hintergrund wechselt auf ein ruhiges Grün, sobald die Zeit um ist
        bg = BG_DONE_COLOR if self.finished else BG_COLOR
        self.canvas.configure(bg=bg)
        self.root.configure(bg=bg)

        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        n = self.segment_count
        progress = 0.0 if self.total_seconds <= 0 else self.elapsed / self.total_seconds
        progress = max(0.0, min(1.0, progress))
        lit_units = progress * n  # z.B. 3.4 -> 3 volle Segmente + Segment 4 zu 40%

        avail_width = width - 2 * MARGIN - GAP * (n - 1)
        seg_width = max(4, avail_width / n)
        seg_height = min(height - 2 * MARGIN, 140)
        y0 = (height - seg_height) / 2

        # Heller Außenrahmen um die gesamte Progressbar, damit ihr Umfang
        # klar erkennbar ist, unabhängig vom aktuellen Fortschritt.
        frame_x1 = MARGIN - FRAME_PADDING
        frame_y1 = y0 - FRAME_PADDING
        frame_x2 = MARGIN + avail_width + GAP * (n - 1) + FRAME_PADDING
        frame_y2 = y0 + seg_height + FRAME_PADDING
        self._round_rect(
            frame_x1, frame_y1, frame_x2, frame_y2,
            min(20, FRAME_PADDING + 6),
            fill="", outline=FRAME_COLOR, width=FRAME_WIDTH,
        )

        x = MARGIN
        for i in range(n):
            # Ist die Zeit abgelaufen, bleiben alle Segmente einfach an
            # (volles Grün) - es gibt keine gesonderte "fertig"-Farbe mehr.
            fill_amount = 1.0 if self.finished else max(0.0, min(1.0, lit_units - i))

            if fill_amount <= 0:
                color = SEGMENT_OFF
            elif fill_amount >= 1:
                color = SEGMENT_ON
            else:
                color = lerp_color(SEGMENT_OFF, SEGMENT_ON, fill_amount)

            x1, y1, x2, y2 = x, y0, x + seg_width, y0 + seg_height
            radius = min(14, seg_height / 2, seg_width / 2)
            self._round_rect(x1, y1, x2, y2, radius, fill=color, outline="")

            x += seg_width + GAP

        # sehr dezenter Hinweis, nur solange noch nicht gestartet wurde
        if not self.running and not self.finished and self.elapsed == 0:
            self.canvas.create_text(
                width / 2, y0 + seg_height + 40,
                text="Leertaste zum Starten   ·   +/- zum Anpassen der Zeit",
                fill="#4a4f5a",
                font=("Helvetica", 12),
            )
        elif self.finished:
            self.canvas.create_text(
                width / 2, y0 + seg_height + 40,
                text="",
                fill="#4a4f5a",
                font=("Helvetica", 12),
            )

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)


def parse_args():
    parser = argparse.ArgumentParser(description="Ruhiger Segment-Timer ohne Zeitanzeige")
    parser.add_argument("--minutes", type=float, default=None, help="Dauer in Minuten")
    parser.add_argument("--seconds", type=float, default=None, help="Dauer in Sekunden (überschreibt --minutes)")
    parser.add_argument(
        "--segments", type=int, default=None,
        help=(
            "Anzahl der Segmente/Lampen. Ohne Angabe: entspricht der Anzahl "
            "Minuten, falls die Timerlänge glatt durch 60s teilbar ist, "
            f"sonst {DEFAULT_SEGMENTS_FALLBACK}."
        ),
    )
    parser.add_argument("--fullscreen", action="store_true", help="Direkt im Vollbild starten")
    args = parser.parse_args()

    if args.seconds is not None:
        total_seconds = args.seconds
    elif args.minutes is not None:
        total_seconds = args.minutes * 60
    else:
        total_seconds = DEFAULT_MINUTES * 60

    if args.segments is not None:
        segments = args.segments
    elif total_seconds > 0 and total_seconds % 60 == 0:
        segments = int(total_seconds // 60)
    else:
        segments = DEFAULT_SEGMENTS_FALLBACK

    return total_seconds, segments, args.fullscreen


def main():
    total_seconds, segments, start_fullscreen = parse_args()
    root = tk.Tk()
    TimerApp(root, total_seconds, segments, start_fullscreen)
    root.mainloop()


if __name__ == "__main__":
    main()