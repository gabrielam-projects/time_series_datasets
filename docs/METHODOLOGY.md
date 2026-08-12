# Metodologia de construccion de datasets

## Objetivo experimental

Construir datasets para comparar estrategias de integracion de contexto clinico en modelos de Deep Learning para series temporales irregulares:

- `P1TemporalOnly`: solo representacion temporal;
- `P2LateFusion`: representacion temporal concatenada con encoder MLP de contexto;
- `P3FiLMConditioned`: contexto usado para modular capas temporales mediante FiLM.

Los tres modelos comparten la misma base temporal para que la comparacion controle la representacion de eventos y cambie solo la estrategia de integracion de contexto.

## Cohorte real MIMIC-III

### Seleccion de admisiones

1. Se cargan `ADMISSIONS.csv` y `PATIENTS.csv`.
2. Se filtran admisiones con `HAS_CHARTEVENTS_DATA = 1`.
3. Se crea una muestra aleatoria reproducible de 2,000 admisiones usando `RANDOM_SEED = 2026`.
4. Se eliminan duplicados por par `subject_id`, `hadm_id`.

### Etiqueta

La etiqueta binaria es mortalidad intrahospitalaria:

- fuente: `HOSPITAL_EXPIRE_FLAG`;
- valores esperados: 0 o 1.

### Edad

La edad se calcula al momento de admision usando fecha de nacimiento y fecha de ingreso. Para evitar overflow por fechas anonimizadas de MIMIC-III:

- no se restan timestamps directamente;
- se calcula edad por anio, mes y dia;
- edades mayores a 120 se agrupan como 90, siguiendo la convencion habitual en MIMIC-III;
- la edad final se limita inferiormente a 0.

### Ventana temporal

Cada admision usa una ventana fija:

- inicio: `ADMITTIME`;
- fin: `ADMITTIME + 168 horas`;
- intervalo incluido: `[0, 168]` horas desde admision.

La decision mantiene una ventana comparable entre pacientes y permite modelar observaciones tempranas de hospitalizacion.

### Particiones

Las particiones se asignan por `subject_id`, no por fila, para evitar fuga de informacion cuando un mismo paciente tiene mas de una admision.

Fracciones objetivo:

- train: 70%;
- validation: 15%;
- test: 15%.

La asignacion usa la misma semilla aleatoria 2026. Todas las admisiones de un paciente quedan en el mismo split.

## Extraccion de eventos temporales

### Frecuencia cardiaca

- fuente: `CHARTEVENTS`;
- item IDs: 211 y 220045;
- variable final: `heart_rate`.

### Glucosa

- fuente: `LABEVENTS`;
- item IDs: 50809 y 50931;
- variable final: `glucose`.

### Reglas de extraccion

1. Leer los CSV grandes por chunks.
2. Conservar solo eventos cuyo `HADM_ID` pertenezca a la muestra.
3. Conservar solo los item IDs definidos para cada variable.
4. Eliminar filas sin `HADM_ID`, `VALUENUM` o timestamp valido.
5. Unir cada evento con la ventana de su admision.
6. Conservar solo eventos dentro de `[window_start, window_end]`.
7. Calcular `hours_since_admit`.
8. Guardar fuente, item ID, timestamp, valor observado y mascara.

No se imputan valores, no se interpola y no se regulariza a una grilla temporal.

## Preprocesamiento para modelos

### Valores temporales

La normalizacion de valores se aprende solo con eventos del split de entrenamiento:

- media por variable temporal;
- desviacion estandar por variable temporal;
- si la desviacion es 0 o no disponible, se reemplaza por 1.0.

Luego cada valor se transforma como z-score. El tiempo se normaliza como:

```text
time_norm = hours_since_admit / 168
```

El resultado se recorta al rango `[0, 1]`.

### Contexto tabular

El vector contextual incluye:

- edad normalizada con media y desviacion de train;
- variables categoricas codificadas con one-hot.

Los vocabularios categoricos se aprenden solo con train. Valores no vistos en validacion o test se asignan a `__OTHER__`; valores faltantes se asignan a `UNKNOWN`.

### Secuencias irregulares y batching

Cada admision conserva su secuencia irregular como lista de observaciones. En el `collate_fn`:

- se aplica padding por lote;
- se crea una mascara booleana;
- los tokens agregados por padding no contribuyen a la atencion ni al pooling;
- si una secuencia excede `max_seq_len`, se trunca a las primeras observaciones ordenadas por tiempo.

## Arquitecturas evaluadas

Todas usan:

- proyeccion lineal de valores;
- embedding de variable;
- codificacion continua de tiempo;
- capas Transformer encoder con atencion multi-cabeza;
- pooling enmascarado;
- clasificador binario con `BCEWithLogitsLoss`.

Diferencias controladas:

- P1 solo usa eventos temporales.
- P2 concatena representacion temporal y representacion contextual tardia.
- P3 genera parametros FiLM desde el contexto para modular la representacion temporal.

## Entrenamiento y evaluacion

Configuracion principal (`full_config`):

- epochs: 20;
- batch size: 64;
- eval batch size: 128;
- learning rate: 0.002;
- weight decay: 0.0001;
- gradient clipping: 1.0;
- `d_model`: 64;
- heads: 4;
- layers: 2;
- dropout: 0.2;
- `max_seq_len`: 512;
- device registrado: CPU.

Configuracion ligera (`full_light`):

- epochs: 5;
- batch size: 32;
- eval batch size: 128;
- `d_model`: 32;
- heads: 2;
- layers: 1;
- `max_seq_len`: 128;
- el resto de hiperparametros coincide con `full_config`.

La seleccion del mejor modelo se hace por AUROC de validacion. Se reportan AUROC, AUPRC y loss en test.

## Resultados agregados disponibles

### Configuracion principal

| Modelo | Mejor epoch | Validation AUROC | Validation AUPRC | Test AUROC | Test AUPRC | Test loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 12 | 0.843 | 0.465 | 0.803 | 0.425 | 0.911 |
| P2 | 7 | 0.832 | 0.520 | 0.827 | 0.440 | 0.901 |
| P3 | 3 | 0.807 | 0.312 | 0.785 | 0.235 | 0.940 |

### Configuracion ligera

| Modelo | Mejor epoch | Validation AUROC | Validation AUPRC | Test AUROC | Test AUPRC | Test loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 5 | 0.791 | 0.335 | 0.716 | 0.276 | 0.993 |
| P2 | 2 | 0.759 | 0.285 | 0.749 | 0.219 | 0.988 |
| P3 | 3 | 0.845 | 0.496 | 0.808 | 0.360 | 0.912 |

## Control de calidad

El notebook incluye validaciones para:

- tamano exacto de muestra;
- ausencia de duplicados por `subject_id`, `hadm_id`;
- etiqueta binaria;
- longitud de ventana de 168 horas;
- ausencia de fuga entre splits por `subject_id`;
- eventos dentro de la ventana temporal;
- compatibilidad de shapes para P1, P2 y P3.

