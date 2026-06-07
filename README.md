# LaDe: Last-Mile Delivery — Eficiencia según escala urbana

Proyecto de visualización de datos para la asignatura **Visualización de datos** del Máster en Ciencia de Datos de la UOC.

## Descripción

Análisis comparativo de la eficiencia logística de última milla en tres ciudades chinas de distinto tamaño (Shanghai, Hangzhou y Yantai), a partir del dataset industrial [LaDe](https://huggingface.co/datasets/Cainiao-AI/LaDe) publicado por Cainiao Network (Alibaba Group).

**Preguntas que responde la visualización:**

- ¿Cómo varía el tiempo medio de entrega entre ciudades grandes y pequeñas?
- ¿En qué franjas horarias y días se concentran las entregas?
- ¿Cómo se distribuyen geográficamente las entregas dentro de cada ciudad?

## Visualización

La visualización interactiva está publicada en Tableau Public:

https://github.com/Gcaminal/lade-visualization

## Estructura del repositorio

```
lade-visualization/
├── README.md                  # Este archivo
├── LICENSE                    # Licencia Apache 2.0
├── requirements.txt           # Dependencias Python
├── .gitignore                 # Archivos excluidos de Git
├── process_lade.py            # Script de procesamiento de datos
└── data/
    └── processed/             # CSVs agregados (generados por el script)
        ├── summary.csv
        ├── hourly.csv
        ├── heatmap_hour_dow.csv
        ├── monthly.csv
        ├── timeslot.csv
        ├── duration_distribution.csv
        └── regions.csv
```

## Cómo ejecutar el script de procesamiento

### Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/TU_USUARIO/lade-visualization.git
cd lade-visualization
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

### Ejecución

```bash
python process_lade.py
```

El script realiza automáticamente los siguientes pasos:

1. **Descarga** los datos crudos de las 3 ciudades desde HuggingFace (~500 MB total) y los guarda en `data/raw/`.
2. **Calcula variables derivadas** sobre cada registro:
   - `duration_min`: tiempo entre aceptación y entrega (minutos).
   - `direct_distance_km`: distancia haversine entre punto de aceptación y punto de entrega.
   - `hour`, `dow`, `month`, `time_slot`: componentes temporales extraídos del timestamp.
3. **Limpia** registros con duraciones negativas o superiores a 24 horas.
4. **Agrega** los datos en 7 CSVs optimizados para visualización y los guarda en `data/processed/`.

La primera ejecución tarda unos minutos por la descarga. Las siguientes ejecuciones reutilizan los datos descargados.

### Archivos generados

| Archivo | Contenido | Uso en Tableau |
|---|---|---|
| `summary.csv` | KPIs por ciudad (media, mediana, P25, P75) | Barras comparativas, KPI cards |
| `hourly.csv` | Entregas y duración por hora × ciudad | Gráficos de líneas horarios |
| `heatmap_hour_dow.csv` | Hora × día de la semana × ciudad | Heatmap |
| `monthly.csv` | Tendencia mensual × ciudad | Barras agrupadas |
| `timeslot.csv` | Franjas horarias × ciudad | Barras de distribución |
| `duration_distribution.csv` | Histograma de duraciones × ciudad | Gráfico de área |
| `regions.csv` | Métricas por AOI con coordenadas GPS × ciudad | Mapa de burbujas |

## Dataset original

- **Nombre:** LaDe (Last-mile Delivery Dataset from Industry)
- **Fuente:** Cainiao Network / Alibaba Group
- **Paper:** Wu et al. (2024). *LaDe: The First Comprehensive Last-mile Express Dataset from Industry.* ACM SIGKDD 2024, pp. 5991-6002.
- **arXiv:** [2306.10675](https://arxiv.org/abs/2306.10675)
- **Datos:** [HuggingFace](https://huggingface.co/datasets/Cainiao-AI/LaDe)
- **Licencia del dataset:** Apache 2.0
- **Periodo:** Mayo–Octubre 2022
- **Escala:** 10.67M paquetes, 21K repartidores, 5 ciudades

## Licencia

Este proyecto está bajo la licencia Apache 2.0. Ver [LICENSE](LICENSE) para más detalles.
