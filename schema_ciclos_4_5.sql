-- ==============================================================================
-- SCRIPT DE ACTUALIZACIÓN: CICLOS 4 Y 5
-- ==============================================================================

-- 1. CREACIÓN DE NUEVAS TABLAS (SaaS, Rastreo y KPIs)

CREATE TABLE "plan_suscripcion" (
    "id" uuid PRIMARY KEY,
    "nombre_plan" varchar(50) NOT NULL,
    "precio_mensual" numeric(12, 2) NOT NULL,
    "limite_usuarios" integer NOT NULL,
    "porcentaje_retencion_base" numeric(5, 2) NOT NULL,
    "created_at" timestamp NOT NULL DEFAULT NOW(),
    "updated_at" timestamp NOT NULL DEFAULT NOW()
);

CREATE TABLE "historial_ruta_tecnico" (
    "id" uuid PRIMARY KEY,
    "latitud" numeric(10, 8) NOT NULL,
    "longitud" numeric(11, 8) NOT NULL,
    "registrado_en" timestamp NOT NULL DEFAULT NOW(),
    "incidente_id" uuid NOT NULL,
    "tecnico_id" uuid NOT NULL,
    "tenant_id" uuid NOT NULL,
    "created_at" timestamp NOT NULL DEFAULT NOW(),
    "updated_at" timestamp NOT NULL DEFAULT NOW(),
    CONSTRAINT "historial_ruta_tecnico_incidente_id_fkey" FOREIGN KEY ("incidente_id") REFERENCES "incidente"("id"),
    CONSTRAINT "historial_ruta_tecnico_tecnico_id_fkey" FOREIGN KEY ("tecnico_id") REFERENCES "tecnico"("id")
);

CREATE TABLE "configuracion_kpi" (
    "id" uuid PRIMARY KEY,
    "tiempo_respuesta_maximo_minutos" integer NOT NULL,
    "meta_ingresos_mensual" numeric(12, 2) NOT NULL,
    "meta_servicios_completados" integer NOT NULL,
    "actualizado_en" timestamp NOT NULL DEFAULT NOW(),
    "tenant_id" uuid NOT NULL UNIQUE,
    "created_at" timestamp NOT NULL DEFAULT NOW(),
    "updated_at" timestamp NOT NULL DEFAULT NOW(),
    CONSTRAINT "configuracion_kpi_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "organizacion"("id")
);


-- 2. MODIFICACIÓN DE TABLAS EXISTENTES (Soporte Offline y Pagos)

-- Para soporte Offline (Ciclo 4)
ALTER TABLE "incidente"
ADD COLUMN "creado_offline" boolean NOT NULL DEFAULT false,
ADD COLUMN "fecha_sincronizacion" timestamp;

-- Para modelo SaaS Multi-tenant (Ciclo 4)
ALTER TABLE "organizacion"
ADD COLUMN "plan_suscripcion_id" uuid,
ADD COLUMN "fecha_vencimiento_plan" timestamp,
ADD COLUMN "estado_pago_suscripcion" varchar(30),
ADD CONSTRAINT "organizacion_plan_suscripcion_id_fkey" FOREIGN KEY ("plan_suscripcion_id") REFERENCES "plan_suscripcion"("id");

-- Para Pagos y Comisiones (Ciclo 5)
ALTER TABLE "transaccion"
ADD COLUMN "proveedor_pasarela" varchar(50),
ADD COLUMN "token_pago_externo" varchar(255);


-- 3. CREACIÓN DE ÍNDICES PARA OPTIMIZACIÓN (Rastreo y KPIs)

CREATE INDEX "idx_historial_ruta_incidente" ON "historial_ruta_tecnico" ("incidente_id");
CREATE INDEX "ix_historial_ruta_tenant_id" ON "historial_ruta_tecnico" ("tenant_id");
CREATE INDEX "ix_configuracion_kpi_tenant_id" ON "configuracion_kpi" ("tenant_id");
