# Plataforma investigativa segura (alternativa autohospedada)

Este módulo agrega una **base de datos de gestión de casos e inteligencia investigativa** pensada para uso **legal, auditado y multiusuario**. Está diseñada como una alternativa **más segura y moderna**, pero **no incluye vigilancia masiva, reconocimiento facial, scoring social ni automatización de decisiones coercitivas**.

## Objetivo

- Centralizar expedientes, leads, evidencia y notas analíticas.
- Permitir acceso desde varias computadoras mediante PostgreSQL.
- Integrar IA **local y sin licencias por consulta** usando motores autohospedados como **Ollama**, **vLLM** o **llama.cpp**.
- Mantener trazabilidad con control de acceso, auditoría y retención.

## Arquitectura sugerida

### 1. Base de datos
- **PostgreSQL 15+** como base principal compartida.
- Cifrado de disco del servidor.
- Backups cifrados y replicación opcional.

### 2. API interna
- Servicio backend separado que aplique:
  - autenticación MFA,
  - autorización por roles,
  - control granular por expediente,
  - registro obligatorio en `audit_log`.

### 3. IA local sin pago por uso
Modelos recomendados para despliegue local:
- **Llama 3.x Instruct** para redacción y resumen.
- **Qwen 2.5 Instruct** para extracción estructurada.
- **Mistral / Mixtral** para análisis comparativo.

Usos permitidos y recomendados:
- resumen de expedientes,
- borradores de informes,
- construcción de línea temporal,
- sugerencias de vínculos **siempre revisadas por una persona**,
- traducción de documentos.

Usos que deben evitarse:
- vigilancia indiscriminada,
- perfilado de población,
- clasificación automática de riesgo de personas,
- decisiones operativas totalmente automatizadas.

## Tablas principales

- `tenant`: separa instituciones o entornos.
- `app_user`, `role`, `permission`, `user_role`: seguridad y RBAC.
- `case_file`, `case_access`: expedientes y acceso por necesidad de saber.
- `person_entity`, `organization_entity`, `asset`: entidades investigativas.
- `lead`, `evidence`, `case_note`, `task_item`: trabajo analítico y operativo.
- `entity_link`: grafo de relaciones con nivel de confianza.
- `ai_model`, `ai_job`: integración de IA local auditable.
- `retention_policy`, `audit_log`: cumplimiento, trazabilidad y gobernanza.

## Despliegue rápido

### PostgreSQL
```bash
psql -U postgres -d intel_platform -f intel_platform/schema.sql
```

### Demo local en SQLite
```bash
python3 intel_platform/init_demo_db.py --db intel_platform/demo.db --seed
```

## Recomendaciones de operación

1. Separar red de usuarios, base de datos y nodo de IA.
2. Habilitar TLS entre equipos y API.
3. Usar MFA para todos los operadores.
4. Revisar periódicamente `audit_log`.
5. Definir política de retención antes de cargar datos reales.
6. Limitar la IA a funciones de apoyo; la decisión final siempre debe ser humana.
