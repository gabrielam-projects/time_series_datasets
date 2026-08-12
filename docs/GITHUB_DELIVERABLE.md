# Entregable para repositorio GitHub

## Proposito

Este entregable sirve como evidencia metodologica del proyecto sin redistribuir datos restringidos de MIMIC-III.

## Incluir

Archivos recomendados:

- `README.md`
- `mTAN-MIMIC.ipynb`
- `requirements_mtan_mimic.txt`
- `.gitignore`
- `docs/DATASETS.md`
- `docs/METHODOLOGY.md`
- `docs/GITHUB_DELIVERABLE.md`
- `outputs/mimic_context_aware_subset/sample_admissions_2000_summary.json`
- `outputs/mimic_context_aware_subset/phase_experiment_summary.csv`
- `outputs/mimic_context_aware_subset/phase_experiment_summary_full_light.csv`
- `outputs/mimic_context_aware_subset/phase_training_history.csv`
- `outputs/mimic_context_aware_subset/phase_training_history_full_light.csv`
- `outputs/mimic_context_aware_subset/tables/`
- `outputs/mimic_context_aware_subset/figures/`

## No incluir

No subir a repositorios publicos:

- `data/`;
- `.venv/`;
- `outputs/**/sample_admissions_2000.csv`;
- `outputs/**/temporal_events_2000.csv`;
- `outputs/**/temporal_coverage_2000.csv`;
- `outputs/**/models/`;
- `outputs/**/matplotlib_cache/`;
- `*.pt`;
- `.DS_Store`.

Razon: esos archivos contienen o pueden contener datos derivados de MIMIC-III, identificadores clinicos, timestamps, pesos entrenados sobre datos restringidos, cache local o artefactos innecesarios.

## Estructura esperada

```text
Experimentos/
  README.md
  requirements_mtan_mimic.txt
  mTAN-MIMIC.ipynb
  docs/
    DATASETS.md
    METHODOLOGY.md
    GITHUB_DELIVERABLE.md
  outputs/
    mimic_context_aware_subset/
      sample_admissions_2000_summary.json
      phase_experiment_summary.csv
      phase_experiment_summary_full_light.csv
      phase_training_history.csv
      phase_training_history_full_light.csv
      tables/
      figures/
```

## Nota sobre reproducibilidad

El notebook contiene la receta para reconstruir los datasets desde MIMIC-III, pero la ejecucion completa requiere acceso autorizado a los archivos originales. En la copia revisada, `temporal_events_2000.csv` esta referenciado por las configuraciones y resumido por cobertura, pero no se encontro materializado localmente.

## Declaracion sugerida para el repositorio

Este repositorio documenta experimentos con una cohorte derivada de MIMIC-III. No redistribuye registros clinicos ni artefactos que permitan reconstruir datos protegidos. La reproduccion completa requiere acceso autorizado a MIMIC-III y aceptacion de sus terminos de uso.

