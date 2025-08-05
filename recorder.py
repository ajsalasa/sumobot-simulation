"""
Grabador circular para replay y exportación CSV.
"""
import csv
class Recorder:
    def __init__(self, seconds=20, fps=60):
        self.max_frames = int(seconds*fps)
        self.frames = []

    def add(self, t_ms, p1, p2):
        self.frames.append({
            "t": t_ms,
            "p1x": p1.pos.x, "p1y": p1.pos.y, "p1h": p1.heading_deg,
            "p2x": p2.pos.x, "p2y": p2.pos.y, "p2h": p2.heading_deg,
            "p1ax": p1.accel[0], "p1ay": p1.accel[1],
            "p2ax": p2.accel[0], "p2ay": p2.accel[1],
        })
        if len(self.frames) > self.max_frames:
            self.frames.pop(0)

    def export_csv(self, filename="sumo_log.csv"):
        if not self.frames: return False
        with open(filename,"w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.frames[0].keys())
            w.writeheader(); w.writerows(self.frames)
        return True