# Inventario de datasets

## Resumen ejecutivo

| Tipo | Dataset | Estado | Publicable en GitHub | Uso |
| --- | --- | --- | --- | --- |
| Real | `mimic_context_aware_subset` | Construido con MIMIC-III | Solo documentacion, configuraciones, metricas y figuras agregadas | Comparar P1 temporal, P2 late fusion y P3 FiLM |
| Sintetico | `simulated_sleep_hr` | Construido fuera de `Experimentos` y agregado a `Data_Repository` | Si | Pruebas controladas con series de tiempo simuladas de sueno, frecuencia cardiaca y contexto de usuario |

## Dataset real: `mimic_context_aware_subset`

### Origen

Dataset derivado de MIMIC-III, usando los archivos:

- `ADMISSIONS.csv`
- `PATIENTS.csv`
- `CHARTEVENTS.csv`
- `LABEVENTS.csv`
- `D_LABITEMS.csv`

La ruta local usada por el notebook es `/Volumes/Seagate/MIMIC-III`.

### Unidad de analisis

Cada muestra corresponde a una admision hospitalaria (`hadm_id`). La cohorte se restringe a admisiones con datos disponibles en `CHARTEVENTS`.

### Tamano y particiones

| Split | Admisiones | Pacientes unicos | Mortalidad | Edad media |
| --- | ---: | ---: | ---: | ---: |
| Train | 1,400 | 1,388 | 0.1107 | 55.43 |
| Val | 299 | 297 | 0.0903 | 53.25 |
| Test | 301 | 298 | 0.0930 | 55.79 |

Resumen global:

- admisiones muestreadas: 2,000;
- pacientes unicos: 1,983;
- semilla aleatoria: 2026;
- ventana temporal: 168 horas;
- mortalidad global: 0.105;
- edad media: 55.16;
- desviacion estandar de edad: 27.61.

### Variables contextuales

| Variable | Fuente | Tratamiento |
| --- | --- | --- |
| `age` | `PATIENTS.DOB` + `ADMISSIONS.ADMITTIME` | Edad al ingreso; edades anonimizadas mayores a 120 se agrupan como 90 |
| `gender` | `PATIENTS.GENDER` | Categoria codificada con vocabulario aprendido en train |
| `insurance` | `ADMISSIONS.INSURANCE` | Categoria codificada con vocabulario aprendido en train |
| `admission_type` | `ADMISSIONS.ADMISSION_TYPE` | Categoria codificada con vocabulario aprendido en train |
| `admission_location` | `ADMISSIONS.ADMISSION_LOCATION` | Categoria codificada con vocabulario aprendido en train |
| `ethnicity` | `ADMISSIONS.ETHNICITY` | Categoria codificada con vocabulario aprendido en train |

### Variables temporales

| Variable | Fuente | Item IDs | Interpretacion |
| --- | --- | --- | --- |
| `heart_rate` | `CHARTEVENTS` | 211, 220045 | Frecuencia cardiaca observada |
| `glucose` | `LABEVENTS` | 50809, 50931 | Glucosa observada |

Cada observacion temporal conserva:

- tiempo relativo en horas desde admision;
- valor observado;
- variable y fuente;
- mascara de observacion.

No se regulariza ni interpola la serie. El padding y la mascara se aplican solo durante batching.

### Cobertura temporal agregada

El archivo de cobertura local registra 1,983 admisiones con al menos un evento temporal. La suma de eventos reportada en las configuraciones es 174,177.

| Variable | Total de eventos | Admisiones con al menos una observacion | Media obs/admission | Mediana obs/admission | Max obs/admission |
| --- | ---: | ---: | ---: | ---: | ---: |
| `heart_rate` | 158,218 | 1,915 | 79.79 | 54 | 9,697 |
| `glucose` | 15,959 | 1,704 | 8.05 | 7 | 77 |

### Archivos locales derivados

| Archivo | Tipo | Recomendacion GitHub |
| --- | --- | --- |
| `sample_admissions_2000.csv` | Registros derivados con IDs, fechas y etiquetas | No publicar |
| `sample_admissions_2000_summary.json` | Resumen agregado | Publicable |
| `temporal_coverage_2000.csv` | Cobertura por `hadm_id` | No publicar |
| `temporal_events_2000.csv` | Eventos temporales derivados | No publicar; no se encontro materializado localmente |
| `phase_experiment_summary*.csv` | Metricas por modelo | Publicable |
| `phase_training_history*.csv` | Historias de entrenamiento agregadas | Publicable |
| `tables/*` | Metricas/configuraciones agregadas | Publicable |
| `figures/*` | Figuras comparativas | Publicable |
| `models/*.pt` | Pesos de modelos | No publicar |

## Dataset sintetico: `simulated_sleep_hr`

La generacion de datos sinteticos se encontro en `Investigacion/Datasets/Data Simulation`, fuera de `Experimentos`.

Archivos fuente materializados:

| Archivo agregado | Filas | Columnas | Descripcion |
| --- | ---: | ---: | --- |
| `data/public/synthetic/simulated_sleep_data.csv` | 15,869 | 10 | Noches sinteticas de sueno por usuario |
| `data/public/synthetic/simulated_user_data.csv` | 100 | 8 | Demografia sintetica de usuarios |

Paquete completo regenerado dentro de `Data_Repository`:

| Archivo agregado | Filas | Columnas | Descripcion |
| --- | ---: | ---: | --- |
| `data/public/synthetic/regenerated_full_package/simulated_sleep_data.csv` | 15,869 | 10 | Noches sinteticas de sueno |
| `data/public/synthetic/regenerated_full_package/simulated_heart_rate_data.csv` | 96,107 | 10 | Eventos sinteticos de frecuencia cardiaca asociados a noches de sueno |
| `data/public/synthetic/regenerated_full_package/simulated_user_data.csv` | 100 | 8 | Demografia sintetica de usuarios |

Variables principales:

- sueno: `user_id`, `sleep_id`, `timestamp`, `light`, `rem`, `deep`, `fall_asleep`, `awake`, `device`, `is_anomalous`;
- frecuencia cardiaca: `user_id`, `sleep_id`, `timestamp`, `duration_secs`, `activity`, `hr_min`, `hr_avg`, `hr_max`, `device`, `is_anomalous`;
- usuarios: `user_id`, `registered_at`, `age`, `gender`, `height_cm`, `weight_kg`, `bmi`, `activity_level`.

Decisiones metodologicas:

- 100 usuarios sinteticos;
- hasta 300 noches por usuario;
- ano simulado: 2024;
- duracion total de sueno entre 4 y 10 horas;
- etapas de sueno generadas por proporciones plausibles;
- eventos de frecuencia cardiaca entre 6 y 24 horas antes del sueno;
- perfiles `sedentary` y `active` con rangos de frecuencia cardiaca distintos;
- anomalias sinteticas en sueno y frecuencia cardiaca;
- duplicados deliberados para simular multiples dispositivos.

La documentacion completa esta en `docs/SYNTHETIC_DATA.md`. La receta reproducible esta en `scripts/generate_synthetic_sleep_hr.py`.
