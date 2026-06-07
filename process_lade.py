"""
Procesamiento del dataset LaDe para visualización.
Descarga los CSVs de 3 ciudades desde HuggingFace,
calcula variables derivadas y genera 7 CSVs agregados.

Requisitos: pip install pandas numpy
Uso: python process_lade.py
"""

import pandas as pd
import numpy as np
import os
import urllib.request

# ============================================================
# 1. DESCARGA DE DATOS
# ============================================================
BASE_URL = "https://huggingface.co/datasets/Cainiao-AI/LaDe/resolve/main/delivery"
CITIES = {
    "Shanghai": "delivery_sh.csv",
    "Hangzhou": "delivery_hz.csv",
    "Yantai": "delivery_yt.csv",
}

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

for city, filename in CITIES.items():
    filepath = f"data/raw/{filename}"
    if not os.path.exists(filepath):
        print(f"Descargando {city}...")
        urllib.request.urlretrieve(f"{BASE_URL}/{filename}", filepath)
        print(f"  ✓ {filepath}")
    else:
        print(f"Ya existe {filepath}, saltando descarga.")


# ============================================================
# 2. FUNCIONES AUXILIARES
# ============================================================
def haversine(lon1, lat1, lon2, lat2):
    """Distancia haversine en km (vectorizada)."""
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def parse_time(series):
    """Parsea 'MM-DD HH:MM:SS' a datetime usando 2022 como año base."""
    return pd.to_datetime("2022-" + series, format="%Y-%m-%d %H:%M:%S", errors="coerce")


# ============================================================
# 3. PROCESAMIENTO PRINCIPAL
# ============================================================
all_hourly = []
all_region = []
all_summary = []
all_duration_dist = []
all_heatmap = []
all_monthly = []
all_timeslot = []

for city_name, filename in CITIES.items():
    print(f"\n{'='*50}")
    print(f"Procesando {city_name}...")
    print(f"{'='*50}")

    df = pd.read_csv(f"data/raw/{filename}")
    print(f"  Filas originales: {len(df):,}")

    # --- Parsear timestamps ---
    df["accept_dt"] = parse_time(df["accept_time"])
    df["delivery_dt"] = parse_time(df["delivery_time"])
    df = df.dropna(subset=["accept_dt", "delivery_dt"])

    # --- Variables derivadas ---
    df["duration_min"] = (df["delivery_dt"] - df["accept_dt"]).dt.total_seconds() / 60

    # Filtrar duraciones no razonables (negativas o > 24h)
    df = df[(df["duration_min"] > 0) & (df["duration_min"] <= 1440)]
    print(f"  Filas tras limpieza: {len(df):,}")

    # Distancia directa (haversine)
    df["direct_distance_km"] = haversine(
        df["accept_gps_lng"], df["accept_gps_lat"],
        df["delivery_gps_lng"], df["delivery_gps_lat"],
    )

    # Componentes temporales
    df["hour"] = df["accept_dt"].dt.hour
    df["dow"] = df["accept_dt"].dt.dayofweek  # 0=Lunes
    df["month"] = df["accept_dt"].dt.month
    df["time_slot"] = pd.cut(
        df["hour"],
        bins=[0, 8, 13, 18, 24],
        labels=["Noche (0-8)", "Mañana (8-13)", "Tarde (13-18)", "Noche (18-24)"],
        right=False,
    )

    # --- RESUMEN POR CIUDAD ---
    summary = {
        "city": city_name,
        "total_deliveries": len(df),
        "unique_couriers": df["courier_id"].nunique(),
        "unique_regions": df["region_id"].nunique(),
        "unique_aoi": df["aoi_id"].nunique(),
        "avg_duration_min": round(df["duration_min"].mean(), 1),
        "median_duration_min": round(df["duration_min"].median(), 1),
        "p25_duration": round(df["duration_min"].quantile(0.25), 1),
        "p75_duration": round(df["duration_min"].quantile(0.75), 1),
        "avg_distance_km": round(df["direct_distance_km"].mean(), 2),
        "median_distance_km": round(df["direct_distance_km"].median(), 2),
        "date_min": str(df["accept_dt"].min().date()),
        "date_max": str(df["accept_dt"].max().date()),
    }
    all_summary.append(summary)
    print(f"  Couriers: {summary['unique_couriers']}")
    print(f"  Duración media: {summary['avg_duration_min']} min")
    print(f"  Distancia media: {summary['avg_distance_km']} km")

    # --- POR HORA ---
    hourly = df.groupby("hour").agg(
        deliveries=("order_id", "count"),
        avg_duration=("duration_min", "mean"),
        median_duration=("duration_min", "median"),
        avg_distance=("direct_distance_km", "mean"),
    ).reset_index()
    hourly["city"] = city_name
    all_hourly.append(hourly)

    # --- POR REGIÓN/AOI (para mapas) ---
    region = df.groupby(["region_id", "aoi_id", "aoi_type"]).agg(
        deliveries=("order_id", "count"),
        avg_duration=("duration_min", "mean"),
        avg_distance=("direct_distance_km", "mean"),
        center_lng=("lng", "mean"),
        center_lat=("lat", "mean"),
        unique_couriers=("courier_id", "nunique"),
    ).reset_index()
    region["city"] = city_name
    all_region.append(region)

    # --- DISTRIBUCIÓN DE DURACIONES ---
    bins = list(range(0, 481, 15)) + [1440]
    labels = [f"{b}-{b+15}" for b in range(0, 481, 15)]
    labels[-1] = "480+"
    df["duration_bin"] = pd.cut(df["duration_min"], bins=bins, labels=labels, right=False)
    dur_dist = df.groupby("duration_bin", observed=True).size().reset_index(name="count")
    dur_dist["city"] = city_name
    all_duration_dist.append(dur_dist)

    # --- HEATMAP HORA × DÍA ---
    hm = df.groupby(["dow", "hour"]).agg(
        deliveries=("order_id", "count"),
        avg_duration=("duration_min", "mean"),
    ).reset_index()
    hm["city"] = city_name
    all_heatmap.append(hm)

    # --- TENDENCIA MENSUAL ---
    monthly = df.groupby("month").agg(
        deliveries=("order_id", "count"),
        avg_duration=("duration_min", "mean"),
        unique_couriers=("courier_id", "nunique"),
    ).reset_index()
    monthly["city"] = city_name
    all_monthly.append(monthly)

    # --- FRANJAS HORARIAS ---
    ts = df.groupby("time_slot").agg(
        deliveries=("order_id", "count"),
        avg_duration=("duration_min", "mean"),
    ).reset_index()
    ts["pct"] = (ts["deliveries"] / len(df) * 100).round(1)
    ts["city"] = city_name
    all_timeslot.append(ts)

    del df  # Liberar memoria


# ============================================================
# 4. EXPORTAR CSVs
# ============================================================
print(f"\n{'='*50}")
print("Exportando CSVs...")
print(f"{'='*50}")

exports = {
    "summary.csv": pd.DataFrame(all_summary),
    "hourly.csv": pd.concat(all_hourly).round(1),
    "regions.csv": pd.concat(all_region).round(4),
    "duration_distribution.csv": pd.concat(all_duration_dist),
    "heatmap_hour_dow.csv": pd.concat(all_heatmap).round(1),
    "monthly.csv": pd.concat(all_monthly).round(1),
    "timeslot.csv": pd.concat(all_timeslot).round(1),
}

for filename, df in exports.items():
    path = f"data/processed/{filename}"
    df.to_csv(path, index=False)
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✓ {filename}: {len(df)} filas, {size_kb:.1f} KB")

print(f"\n¡Listo! 7 archivos en ./data/processed/")
