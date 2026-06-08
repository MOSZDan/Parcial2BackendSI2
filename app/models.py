from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, ForeignKey, DateTime, func, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base

# Tabla intermedia Taller - Especialidad
taller_especialidad = Table(
    'taller_especialidad',
    Base.metadata,
    Column('taller_id', UUID(as_uuid=True), ForeignKey('taller.id'), primary_key=True),
    Column('especialidad_id', UUID(as_uuid=True), ForeignKey('especialidad.id'), primary_key=True),
    Column('tenant_id', UUID(as_uuid=True), nullable=False)
)

class Rol(Base):
    __tablename__ = 'rol'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255))
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class PlanSuscripcion(Base):
    __tablename__ = 'plan_suscripcion'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_plan = Column(String(50), nullable=False)
    precio_mensual = Column(Numeric(12, 2), nullable=False)
    limite_usuarios = Column(Integer, nullable=False)
    porcentaje_retencion_base = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Organizacion(Base):
    __tablename__ = 'organizacion'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_comercial = Column(String(150), nullable=False)
    nit = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(255))
    telefono = Column(String(20))
    email = Column(String(100), unique=True, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    plan_suscripcion_id = Column(UUID(as_uuid=True), ForeignKey('plan_suscripcion.id'))
    fecha_vencimiento_plan = Column(DateTime)
    estado_pago_suscripcion = Column(String(30))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    usuarios = relationship("Usuario", back_populates="organizacion")
    talleres = relationship("Taller", back_populates="organizacion")

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correo = Column(String(100), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    estado = Column(String(20), nullable=False, default="Activo")
    fecha_registro = Column(DateTime, server_default=func.now(), nullable=False)
    rol_id = Column(UUID(as_uuid=True), ForeignKey('rol.id'), nullable=False)
    organizacion_id = Column(UUID(as_uuid=True), ForeignKey('organizacion.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    rol = relationship("Rol")
    organizacion = relationship("Organizacion", back_populates="usuarios")

class Sesion(Base):
    __tablename__ = 'sesion'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(500), unique=True, nullable=False)
    fecha_inicio = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_fin = Column(DateTime)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Conductor(Base):
    __tablename__ = 'conductor'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_completo = Column(String(150), nullable=False)
    telefono = Column(String(20), nullable=False)
    licencia = Column(String(50), unique=True)
    activo = Column(Boolean, nullable=False, default=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Taller(Base):
    __tablename__ = 'taller'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_comercial = Column(String(150), nullable=False)
    nit = Column(String(20), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100))
    latitud = Column(Numeric(10, 8))
    longitud = Column(Numeric(11, 8))
    activo = Column(Boolean, nullable=False, default=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'), unique=True, nullable=False)
    organizacion_id = Column(UUID(as_uuid=True), ForeignKey('organizacion.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    organizacion = relationship("Organizacion", back_populates="talleres")
    tecnicos = relationship("Tecnico", back_populates="taller")
    especialidades = relationship("Especialidad", secondary=taller_especialidad, back_populates="talleres")

class Tecnico(Base):
    __tablename__ = 'tecnico'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_completo = Column(String(150), nullable=False)
    telefono = Column(String(20), nullable=False)
    estado_disponible = Column(Boolean, nullable=False, default=True)
    activo = Column(Boolean, nullable=False, default=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'), unique=True, nullable=False)
    taller_id = Column(UUID(as_uuid=True), ForeignKey('taller.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    taller = relationship("Taller", back_populates="tecnicos")

class Vehiculo(Base):
    __tablename__ = 'vehiculo'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placa = Column(String(15), unique=True, nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    ano = Column(Integer, nullable=False)
    color = Column(String(30))
    conductor_id = Column(UUID(as_uuid=True), ForeignKey('conductor.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Especialidad(Base):
    __tablename__ = 'especialidad'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_servicio = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255))
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    talleres = relationship("Taller", secondary=taller_especialidad, back_populates="especialidades")

class Incidente(Base):
    __tablename__ = 'incidente'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(40), unique=True, nullable=False)
    estado_actual = Column(String(30), nullable=False)
    tipo_problema = Column(String(100), nullable=False)
    descripcion = Column(Text)
    prioridad = Column(String(20), nullable=False)
    latitud = Column(Numeric(10, 8), nullable=False)
    longitud = Column(Numeric(11, 8), nullable=False)
    direccion_referencia = Column(String(255))
    solicitado_en = Column(DateTime, server_default=func.now(), nullable=False)
    asignado_en = Column(DateTime)
    finalizado_en = Column(DateTime)
    conductor_id = Column(UUID(as_uuid=True), ForeignKey('conductor.id'), nullable=False)
    vehiculo_id = Column(UUID(as_uuid=True), ForeignKey('vehiculo.id'), nullable=False)
    taller_id = Column(UUID(as_uuid=True), ForeignKey('taller.id'))
    tecnico_id = Column(UUID(as_uuid=True), ForeignKey('tecnico.id'))
    especialidad_id = Column(UUID(as_uuid=True), ForeignKey('especialidad.id'))
    organizacion_id = Column(UUID(as_uuid=True), ForeignKey('organizacion.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    creado_offline = Column(Boolean, nullable=False, default=False)
    fecha_sincronizacion = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class HistorialIncidente(Base):
    __tablename__ = 'historial_incidente'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estado_anterior = Column(String(30))
    estado_nuevo = Column(String(30), nullable=False)
    observaciones = Column(Text)
    cambiado_en = Column(DateTime, server_default=func.now(), nullable=False)
    incidente_id = Column(UUID(as_uuid=True), ForeignKey('incidente.id'), nullable=False)
    cambiado_por_usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'))
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class OportunidadIncidente(Base):
    __tablename__ = 'oportunidad_incidente'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estado = Column(String(20), nullable=False)
    precio_estimado = Column(Numeric(12, 2))
    eta_minutos = Column(Integer)
    ofrecida_en = Column(DateTime, server_default=func.now(), nullable=False)
    respondida_en = Column(DateTime)
    expira_en = Column(DateTime, nullable=False)
    incidente_id = Column(UUID(as_uuid=True), ForeignKey('incidente.id'), nullable=False)
    taller_id = Column(UUID(as_uuid=True), ForeignKey('taller.id'), nullable=False)
    tecnico_id = Column(UUID(as_uuid=True), ForeignKey('tecnico.id'), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class EvidenciaMultimedia(Base):
    __tablename__ = 'evidencia_multimedia'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(String(20), nullable=False)
    url_archivo = Column(String(500), nullable=False)
    descripcion = Column(String(255))
    cargado_en = Column(DateTime, server_default=func.now(), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    incidente_id = Column(UUID(as_uuid=True), ForeignKey('incidente.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class DiagnosticoIA(Base):
    __tablename__ = 'diagnostico_ia'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proveedor = Column(String(50))
    resultado = Column(Text)
    probabilidad_falla = Column(Numeric(5, 2))
    confianza = Column(Numeric(5, 2))
    analizado_en = Column(DateTime, server_default=func.now(), nullable=False)
    incidente_id = Column(UUID(as_uuid=True), ForeignKey('incidente.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Transaccion(Base):
    __tablename__ = 'transaccion'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referencia = Column(String(100), unique=True, nullable=False)
    metodo_pago = Column(String(30), nullable=False)
    estado = Column(String(30), nullable=False)
    moneda = Column(String(10), nullable=False)
    monto_total = Column(Numeric(12, 2), nullable=False)
    pagado_en = Column(DateTime)
    incidente_id = Column(UUID(as_uuid=True), ForeignKey('incidente.id'), nullable=False)
    proveedor_pasarela = Column(String(50))
    token_pago_externo = Column(String(255))
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Comprobante(Base):
    __tablename__ = 'comprobante'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero = Column(String(50), unique=True, nullable=False)
    url_pdf = Column(String(500))
    emitido_en = Column(DateTime, server_default=func.now(), nullable=False)
    transaccion_id = Column(UUID(as_uuid=True), ForeignKey('transaccion.id'), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Comision(Base):
    __tablename__ = 'comision'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    porcentaje = Column(Numeric(5, 2), nullable=False)
    monto_comision = Column(Numeric(12, 2), nullable=False)
    monto_neto_taller = Column(Numeric(12, 2), nullable=False)
    liquidada = Column(Boolean, nullable=False, default=False)
    calculada_en = Column(DateTime, server_default=func.now(), nullable=False)
    transaccion_id = Column(UUID(as_uuid=True), ForeignKey('transaccion.id'), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class HistorialRutaTecnico(Base):
    __tablename__ = 'historial_ruta_tecnico'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitud = Column(Numeric(10, 8), nullable=False)
    longitud = Column(Numeric(11, 8), nullable=False)
    registrado_en = Column(DateTime, server_default=func.now(), nullable=False)
    incidente_id = Column(UUID(as_uuid=True), ForeignKey('incidente.id'), nullable=False)
    tecnico_id = Column(UUID(as_uuid=True), ForeignKey('tecnico.id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class ConfiguracionKPI(Base):
    __tablename__ = 'configuracion_kpi'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tiempo_respuesta_maximo_minutos = Column(Integer, nullable=False)
    meta_ingresos_mensual = Column(Numeric(12, 2), nullable=False)
    meta_servicios_completados = Column(Integer, nullable=False)
    actualizado_en = Column(DateTime, server_default=func.now(), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('organizacion.id'), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Bitacora(Base):
    __tablename__ = 'bitacora'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuario.id'), nullable=False)
    accion = Column(String(255), nullable=False)
    tabla_afectada = Column(String(100))
    fecha = Column(DateTime, server_default=func.now(), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
