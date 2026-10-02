"""真太陽時校正 (兩岸共用). 不讓 LLM 心算時間."""
import json, math
from datetime import datetime, timedelta
from pathlib import Path

CITIES = json.load(open(Path(__file__).resolve().parent.parent / "data" / "cities.json"))
FLAT = {c["name"]: c["lon"] for k in CITIES for c in CITIES[k]}
# 別名: 已有"市/縣/區"後綴的不動; 其餘自動加"市"別名 (使用者自然輸入).
# 縣市中心同經度近似 (差<1分, 遠小於時柱2小時, 跨界案例以--lon精確為準).
for _name, _lon in list(FLAT.items()):
    if not _name.endswith(("市", "縣", "县", "區", "区")):
        FLAT.setdefault(_name + "市", _lon)

def equation_of_time(dt: datetime) -> float:
    """均時差 EoT (分). Wikipedia 近似式, 誤差<1分."""
    y = dt.year
    d = dt.timetuple().tm_yday
    D = 6.24004077 + 0.01720197 * (365.25 * (y - 2000) + d)
    return -7.659 * math.sin(D) + 9.863 * math.sin(2 * D + 3.5932)

def true_solar(dt: datetime, city: str = "", lon: float = None):
    """鐘錶時間(UTC+8) -> 真太陽時. 回傳 (校正後dt, 明細dict)."""
    if lon is None:
        if city not in FLAT:
            raise ValueError(f"未知城市:{city}, 可用 --lon 手輸經度")
        lon = FLAT[city]
    eot = equation_of_time(dt)
    delta = (lon - 120.0) * 4.0 + eot  # 分
    out = dt + timedelta(minutes=delta)
    return out, {"city": city or f"lon{lon}", "lon": lon, "eot_min": round(eot, 2),
                 "lon_corr_min": round((lon - 120.0) * 4.0, 2),
                 "total_corr_min": round(delta, 2),
                 "input": dt.strftime("%Y-%m-%d %H:%M"),
                 "true_solar": out.strftime("%Y-%m-%d %H:%M")}
