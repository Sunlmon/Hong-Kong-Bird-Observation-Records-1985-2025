# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///

"""
Draw 2025 GBIF bird observation records in Hong Kong.

Run:
    uv run plot.py
"""

import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"

# 这一个名字必须和 fetch.py 的 FILE 完全一样。
FILE = "gbif-hong-kong-birds-2025.json"


def bird_point(record):
    """从一条 GBIF 记录中取出：鸟名、经度、纬度。没有坐标则跳过。"""
    name = record.get("scientificName", "Unknown bird")
    longitude = record.get("decimalLongitude")
    latitude = record.get("decimalLatitude")

    if longitude is None or latitude is None:
        return None

    return name, float(longitude), float(latitude)


def load_birds(path):
    """读取 JSON，并把可用的鸟类位置放进列表。"""
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    birds = []

    for record in raw_data["results"]:
        point = bird_point(record)
        if point is not None:
            birds.append(point)

    return birds


def main():
    path = DATA / FILE

    if not path.exists():
        raise SystemExit(
            f"找不到 data/{FILE}。\n"
            "请先在终端运行：uv run fetch.py"
        )

    birds = load_birds(path)

    if not birds:
        raise SystemExit("数据中没有可绘制的鸟类坐标。")

    # 统计哪几种鸟的记录最多，只把前 6 种特别上色。
    counts = Counter(name for name, longitude, latitude in birds)
    common_birds = [name for name, count in counts.most_common(6)]

    fig, ax = plt.subplots(figsize=(8, 10))
    colours = plt.cm.tab10.colors

    # 其他鸟：浅灰色。
    other_birds = [
        (longitude, latitude)
        for name, longitude, latitude in birds
        if name not in common_birds
    ]

    if other_birds:
        xs, ys = zip(*other_birds)
        ax.scatter(xs, ys, s=18, color="lightgrey", alpha=0.6, label="Other species")

    # 最常出现的六种鸟：每种一种颜色。
    for index, name in enumerate(common_birds):
        locations = [
            (longitude, latitude)
            for bird_name, longitude, latitude in birds
            if bird_name == name
        ]

        xs, ys = zip(*locations)
        ax.scatter(
            xs,
            ys,
            s=30,
            color=colours[index],
            alpha=0.8,
            label=f"{name} ({len(locations)})",
        )

    ax.set_title("Bird occurrence records in Hong Kong, 2025", fontsize=15)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2)
    ax.legend(title="Most recorded species", fontsize=8)

    OUT.mkdir(exist_ok=True)
    output = OUT / "hong-kong-bird-records-2025.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")

    print(f"Saved {output}")
    plt.show()


if __name__ == "__main__":
    main()