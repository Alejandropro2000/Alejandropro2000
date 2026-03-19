# SentinelAV para notebook

Listo: rehice el proyecto para que sea una **herramienta utilizable** (no texto de demo), con:

- detección por **firmas SHA-256**
- análisis **heurístico configurable por perfiles**
- **exclusiones** de rutas
- **cuarentena** automática
- **reportes JSON**
- modo **monitoreo continuo** (`--watch`)

> Importante: sigue siendo un escáner local en Python. Para máxima protección en producción, úsalo junto a un antivirus comercial/Defender actualizado.

## Requisitos

- Python 3.9+

## Uso

Escaneo normal:

```bash
python3 antivirus.py /ruta/a/escanear
```

Perfil más agresivo:

```bash
python3 antivirus.py /ruta/a/escanear --profile paranoid
```

Umbral personalizado:

```bash
python3 antivirus.py /ruta/a/escanear --threshold 25
```

Excluir rutas:

```bash
python3 antivirus.py /ruta/a/escanear --exclude /ruta/a/escanear/node_modules --exclude /ruta/a/escanear/.git
```

Cuarentena automática:

```bash
python3 antivirus.py /ruta/a/escanear --quarantine --quarantine-dir ./quarantine
```

Guardar reporte JSON:

```bash
python3 antivirus.py /ruta/a/escanear --json-report --report-dir ./reports
```

Monitoreo continuo cada 5 minutos:

```bash
python3 antivirus.py /ruta/a/escanear --watch 300 --json-report
```

## Recomendación para tu notebook

1. Programa escaneos diarios de `Descargas`, escritorio y carpetas compartidas.
2. Activa cuarentena en esas rutas de alto riesgo.
3. Revisa reportes JSON para seguimiento de incidentes.
4. Mantén sistema operativo, navegador y Office actualizados.
5. Usa este escáner como capa adicional junto a tu AV principal.


## Módulo adicional: plataforma investigativa segura

Se agregó un blueprint autohospedado en `intel_platform/` para una **base de gestión de casos e inteligencia investigativa** con soporte multiusuario, auditoría e integración de IA local sin pago por consulta.

Archivos incluidos:

- `intel_platform/schema.sql`: esquema PostgreSQL para despliegue compartido entre varias computadoras.
- `intel_platform/init_demo_db.py`: inicializador de demo SQLite con datos de ejemplo.
- `intel_platform/demo_viewer.py`: visor web local de solo lectura para inspeccionar la demo en navegador.
- `intel_platform/README.md`: arquitectura recomendada, cómo abrir la demo y límites de uso seguro.
