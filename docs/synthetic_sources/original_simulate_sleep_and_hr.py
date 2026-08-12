import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Ruta del directorio donde está el script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Nombres de archivo en esa carpeta
sleep_file = os.path.join(SCRIPT_DIR, "simulated_sleep_data.csv")
fc_file = os.path.join(SCRIPT_DIR, "simulated_heart_rate_data.csv")


# Semilla para reproducibilidad
np.random.seed(42)
random.seed(42)

# Constantes
NUM_USERS = 100
MIN_DAYS = 1
MAX_DAYS = 300
MIN_SLEEP_SECS = 14400  # 4 horas
MAX_SLEEP_SECS = 36000  # 10 horas
DEVICES = ['Source_A', 'Source_B', 'Source_C', 'Source_D', 'Source_E', 'Source_F']
ACTIVITIES = ['Cycling', 'Walking', 'Running', 'Swimming', 'Yoga', 'Gym']
YEAR = 2024

# Generar datos de sueño simulados
def generate_sleep_stages(total_sleep_seconds):
    deep = int(total_sleep_seconds * np.random.uniform(0.13, 0.23))
    rem = int(total_sleep_seconds * np.random.uniform(0.20, 0.25))
    light = int(total_sleep_seconds * np.random.uniform(0.45, 0.55))
    awake = int(total_sleep_seconds * np.random.uniform(0.03, 0.07))
    fall_asleep = total_sleep_seconds - (deep + rem + light + awake)
    return max(0, light), max(0, rem), max(0, deep), max(0, fall_asleep), max(0, awake)

sleep_records = []
for user_id in range(1, NUM_USERS + 1):
    num_nights = np.random.randint(MIN_DAYS, MAX_DAYS + 1)
    base_date = datetime(YEAR, 1, 1)
    for i in range(num_nights):
        date = base_date + timedelta(days=i)
        sleep_start = datetime(date.year, date.month, date.day,
                               np.random.randint(21, 24), np.random.randint(0, 60))
        total_sleep = np.random.randint(MIN_SLEEP_SECS, MAX_SLEEP_SECS + 1)
        light, rem, deep, fall_asleep, awake = generate_sleep_stages(total_sleep)
        device = random.choice(DEVICES)
        is_anomalous = random.random() < 0.15  # 15% anomalías

        if is_anomalous:
            light = rem = deep = fall_asleep = awake = np.nan

        sleep_records.append({
            "user_id": user_id,
            "sleep_id": f"{user_id}_{date.strftime('%Y%m%d')}",
            "timestamp": sleep_start.isoformat(),
            "light": light,
            "rem": rem,
            "deep": deep,
            "fall_asleep": fall_asleep,
            "awake": awake,
            "device": device,
            "is_anomalous": is_anomalous
        })

# Duplicados (10%)
num_duplicates = int(len(sleep_records) * 0.1)
duplicate_sleep_records = random.sample(sleep_records, num_duplicates)
for record in duplicate_sleep_records:
    dup = record.copy()
    dup["device"] = random.choice(DEVICES)
    for stage in ["light", "rem", "deep", "fall_asleep", "awake"]:
        if pd.notnull(dup[stage]):
            dup[stage] += np.random.randint(-60, 60)
    sleep_records.append(dup)

df_sleep = pd.DataFrame(sleep_records)





# Frecuencia cardíaca
fc_records = []
for record in sleep_records:
    user_id = record["user_id"]
    sleep_timestamp = datetime.fromisoformat(record["timestamp"])
    num_events = np.random.randint(1, 11)
    for _ in range(num_events):
        event_time = sleep_timestamp - timedelta(hours=np.random.randint(6, 24),
                                                 minutes=np.random.randint(0, 60))
        duration = np.random.randint(300, 7200)
        activity = random.choice(ACTIVITIES)
        profile = np.random.choice(['sedentary', 'active'])

        if profile == 'sedentary':
            hr_min = np.random.randint(60, 71)
            hr_avg = np.random.randint(70, 91)
            hr_max = np.random.randint(90, 131)
        else:
            hr_min = np.random.randint(40, 56)
            hr_avg = np.random.randint(55, 76)
            hr_max = np.random.randint(75, 191)

        is_anomalous = False
        if random.random() < 0.15:
            is_anomalous = True
            hr_min = np.random.randint(20, 35)
            hr_avg = np.random.randint(35, 45)
            hr_max = np.random.randint(200, 220)

        fc_records.append({
            "user_id": user_id,
            "sleep_id": record["sleep_id"],
            "timestamp": event_time.isoformat(),
            "duration_secs": duration,
            "activity": activity,
            "hr_min": hr_min,
            "hr_avg": hr_avg,
            "hr_max": hr_max,
            "device": random.choice(DEVICES),
            "is_anomalous": is_anomalous
        })

# Duplicados FC
num_fc_duplicates = int(len(fc_records) * 0.1)
duplicate_fc_records = random.sample(fc_records, num_fc_duplicates)
for rec in duplicate_fc_records:
    dup = rec.copy()
    dup["device"] = random.choice(DEVICES)
    dup["hr_avg"] += np.random.randint(-3, 4)
    fc_records.append(dup)

df_fc = pd.DataFrame(fc_records)






# Verifica si los archivos ya existen
for filepath in [sleep_file, fc_file]:
    if os.path.exists(filepath):
        print(f"Sobrescribiendo archivo: {os.path.basename(filepath)}")

# Guardar como CSV
df_sleep.to_csv(sleep_file, index=False)
df_fc.to_csv(fc_file, index=False)

print("Dataset files generated successfully.")




# Data visualization

def plot_user_timeseries(user_id, df_sleep, df_fc):
    # Filtrar datos del usuario
    sleep_user = df_sleep[df_sleep['user_id'] == user_id].copy()
    fc_user = df_fc[df_fc['user_id'] == user_id].copy()

    # Asegurarse de que los timestamps sean datetime
    sleep_user['timestamp'] = pd.to_datetime(sleep_user['timestamp'])
    fc_user['timestamp'] = pd.to_datetime(fc_user['timestamp'])

    # Calcular duración total del sueño (suma de todas las etapas)
    sleep_user['sleep_total'] = sleep_user[['light', 'rem', 'deep', 'fall_asleep', 'awake']].sum(axis=1)

    # Crear figura
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # Plot sueño como línea (barra opcional)
    ax1.plot(sleep_user['timestamp'], sleep_user['sleep_total'] / 3600, label='Total Sleep (hrs)',
             color='blue', marker='o', linestyle='-', linewidth=2)
    ax1.set_ylabel('Sleep Duration (hrs)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Marcar anomalías en sueño
    anomalous_sleep = sleep_user[sleep_user['is_anomalous']]
    if not anomalous_sleep.empty:
        ax1.scatter(anomalous_sleep['timestamp'], [0.2]*len(anomalous_sleep),
                    color='red', label='Anomalous Sleep', zorder=5)

    # Segundo eje para FC
    ax2 = ax1.twinx()
    ax2.set_ylabel('Heart Rate (bpm)', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    # Graficar eventos de FC
    ax2.plot(fc_user['timestamp'], fc_user['hr_min'], label='HR Min', color='green', linestyle='dotted')
    ax2.plot(fc_user['timestamp'], fc_user['hr_avg'], label='HR Avg', color='orange', linestyle='-')
    ax2.plot(fc_user['timestamp'], fc_user['hr_max'], label='HR Max', color='red', linestyle='dashed')

    # Marcar anomalías en FC
    anomalous_fc = fc_user[fc_user['is_anomalous']]
    if not anomalous_fc.empty:
        ax2.scatter(anomalous_fc['timestamp'], anomalous_fc['hr_max'],
                    color='darkred', marker='x', label='Anomalous HR')

    # Mejoras visuales
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    fig.autofmt_xdate()
    plt.title(f"Sleep & Heart Rate Time Series - User {user_id}")
    fig.legend(loc="upper right", bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


plot_user_timeseries(user_id=7, df_sleep=df_sleep, df_fc=df_fc)