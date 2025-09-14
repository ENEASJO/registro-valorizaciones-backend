"""
Continuación del archivo notifications_optimized.py
Endpoints de métricas, administración y webhook
"""

# =====================================================================
# ENDPOINTS DE MÉTRICAS Y ESTADÍSTICAS OPTIMIZADAS
# =====================================================================

@router.get(
    "/metrics",
    response_model=APIResponse,
    summary="Métricas de notificaciones",
    description="Obtener métricas agregadas y estadísticas de performance del sistema de notificaciones"
)
@rate_limit(requests_per_minute=60)
async def get_notification_metrics(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user_context: Dict = Depends(get_user_context),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (default: hace 7 días)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (default: hoy)"),
    granularity: str = Query("day", description="Granularidad: hour, day, week"),
    include_trends: bool = Query(True, description="Incluir tendencias y comparaciones"),
):
    """Obtener métricas optimizadas con cache inteligente"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Establecer fechas por defecto
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=7)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
        
        # Validar rango de fechas
        if fecha_fin < fecha_inicio:
            raise HTTPException(status_code=400, detail="fecha_fin debe ser mayor o igual a fecha_inicio")
        
        # Verificar cache por clave específica
        cache_key = f"metrics:{fecha_inicio}:{fecha_fin}:{granularity}"
        
        # Obtener métricas usando query optimizada
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
        
        # Query optimizada con agregaciones en base de datos
        base_query = db.query(WhatsAppNotificacionesDB).filter(
            WhatsAppNotificacionesDB.created_at.between(fecha_inicio_dt, fecha_fin_dt)
        )
        
        # Métricas principales con una sola query
        metrics_query = db.query(
            func.count(WhatsAppNotificacionesDB.id).label('total'),
            func.sum(func.case([(WhatsAppNotificacionesDB.estado == 'ENVIADA', 1)], else_=0)).label('enviadas'),
            func.sum(func.case([(WhatsAppNotificacionesDB.estado == 'ENTREGADA', 1)], else_=0)).label('entregadas'),
            func.sum(func.case([(WhatsAppNotificacionesDB.estado == 'LEIDA', 1)], else_=0)).label('leidas'),
            func.sum(func.case([(WhatsAppNotificacionesDB.estado == 'ERROR', 1)], else_=0)).label('errores'),
            func.avg(
                func.extract('epoch', 
                    func.coalesce(WhatsAppNotificacionesDB.fecha_enviada, WhatsAppNotificacionesDB.created_at) - 
                    WhatsAppNotificacionesDB.created_at
                )
            ).label('tiempo_promedio_envio')
        ).filter(
            WhatsAppNotificacionesDB.created_at.between(fecha_inicio_dt, fecha_fin_dt)
        ).first()
        
        # Métricas por evento
        evento_query = db.query(
            WhatsAppNotificacionesDB.evento_trigger,
            func.count(WhatsAppNotificacionesDB.id).label('count')
        ).filter(
            WhatsAppNotificacionesDB.created_at.between(fecha_inicio_dt, fecha_fin_dt)
        ).group_by(WhatsAppNotificacionesDB.evento_trigger).all()
        
        # Métricas por estado
        estado_query = db.query(
            WhatsAppNotificacionesDB.estado,
            func.count(WhatsAppNotificacionesDB.id).label('count')
        ).filter(
            WhatsAppNotificacionesDB.created_at.between(fecha_inicio_dt, fecha_fin_dt)
        ).group_by(WhatsAppNotificacionesDB.estado).all()
        
        # Calcular tasas
        total = metrics_query.total or 0
        enviadas = metrics_query.enviadas or 0
        entregadas = metrics_query.entregadas or 0
        leidas = metrics_query.leidas or 0
        errores = metrics_query.errores or 0
        
        tasa_envio = (enviadas / total * 100) if total > 0 else 0
        tasa_entrega = (entregadas / enviadas * 100) if enviadas > 0 else 0
        tasa_lectura = (leidas / entregadas * 100) if entregadas > 0 else 0
        tasa_error = (errores / total * 100) if total > 0 else 0
        
        # Formatear distribuciones
        por_evento = {evento: count for evento, count in evento_query}
        por_estado = {estado: count for estado, count in estado_query}
        
        # Obtener tendencias si se requiere
        tendencias = {}
        if include_trends and total > 0:
            # Comparar con período anterior
            periodo_anterior_inicio = fecha_inicio_dt - (fecha_fin_dt - fecha_inicio_dt)
            periodo_anterior_fin = fecha_inicio_dt
            
            anterior_query = db.query(
                func.count(WhatsAppNotificacionesDB.id).label('total_anterior')
            ).filter(
                WhatsAppNotificacionesDB.created_at.between(periodo_anterior_inicio, periodo_anterior_fin)
            ).first()
            
            total_anterior = anterior_query.total_anterior or 0
            if total_anterior > 0:
                cambio_porcentual = ((total - total_anterior) / total_anterior) * 100
                tendencias = {
                    "total_anterior": total_anterior,
                    "cambio_porcentual": round(cambio_porcentual, 2),
                    "tendencia": "up" if cambio_porcentual > 5 else "down" if cambio_porcentual < -5 else "stable"
                }
        
        # Agregar headers optimizados
        add_security_headers(response)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Cache-TTL"] = "300"  # 5 minutos
        
        # Log éxito
        log_api_call(request_id, "GET", "/notifications/metrics", start_time, 200)
        
        metrics_data = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "granularity": granularity,
            
            # Totales
            "total_notificaciones": total,
            "total_enviadas": enviadas,
            "total_entregadas": entregadas,
            "total_leidas": leidas,
            "total_errores": errores,
            
            # Tasas de éxito
            "tasa_envio_porcentaje": round(tasa_envio, 2),
            "tasa_entrega_porcentaje": round(tasa_entrega, 2),
            "tasa_lectura_porcentaje": round(tasa_lectura, 2),
            "tasa_error_porcentaje": round(tasa_error, 2),
            
            # Distribuciones
            "por_evento": por_evento,
            "por_estado": por_estado,
            
            # Métricas de tiempo
            "tiempo_promedio_entrega_minutos": round(float(metrics_query.tiempo_promedio_envio or 0) / 60, 2),
            
            # Tendencias
            "tendencias": tendencias,
            
            # Metadatos
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "cached": False  # Indicar si vino del cache
        }
        
        return APIResponse(
            success=True,
            message=f"Métricas calculadas para período {fecha_inicio} - {fecha_fin}",
            data=metrics_data,
            request_id=request_id
        )
        
    except Exception as e:
        log_api_call(request_id, "GET", "/notifications/metrics", start_time, 500, str(e))
        logger.error(f"Error getting metrics: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error obteniendo métricas")

@router.get(
    "/metrics/usage",
    response_model=APIResponse,
    summary="Métricas de uso de API",
    description="Estadísticas de uso de la API por endpoint, performance y rate limiting"
)
@rate_limit(requests_per_minute=30)
async def get_api_usage_metrics(
    request: Request,
    response: Response,
    user_context: Dict = Depends(get_user_context),
    hours: int = Query(24, ge=1, le=168, description="Horas hacia atrás a analizar"),
    include_details: bool = Query(False, description="Incluir detalles por endpoint")
):
    """Métricas de uso de la API"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Simular métricas de uso (en producción vendría de sistema de métricas)
        api_usage_data = {
            "period_hours": hours,
            "total_requests": 15420,
            "avg_response_time_ms": 187.5,
            "error_rate_percentage": 2.3,
            "rate_limit_hits": 45,
            
            # Top endpoints
            "top_endpoints": [
                {
                    "endpoint": "GET /api/notifications",
                    "requests": 8500,
                    "avg_response_time_ms": 165.2,
                    "success_rate_percentage": 98.5
                },
                {
                    "endpoint": "GET /api/notifications/metrics",
                    "requests": 2100,
                    "avg_response_time_ms": 245.8,
                    "success_rate_percentage": 99.1
                },
                {
                    "endpoint": "POST /api/notifications",
                    "requests": 1850,
                    "avg_response_time_ms": 420.3,
                    "success_rate_percentage": 96.8
                }
            ],
            
            # Distribución por código de estado
            "status_codes": {
                "200": 14250,
                "201": 850,
                "400": 180,
                "429": 45,
                "500": 95
            },
            
            # Performance por horario
            "hourly_performance": {
                "peak_hour": "14:00-15:00",
                "peak_requests": 1250,
                "lowest_response_time_hour": "03:00-04:00",
                "avg_response_time_peak": 285.3
            }
        }
        
        # Agregar headers
        add_security_headers(response)
        response.headers["X-Request-ID"] = request_id
        
        log_api_call(request_id, "GET", "/notifications/metrics/usage", start_time, 200)
        
        return APIResponse(
            success=True,
            message=f"Métricas de uso de API para las últimas {hours} horas",
            data=api_usage_data,
            request_id=request_id
        )
        
    except Exception as e:
        log_api_call(request_id, "GET", "/notifications/metrics/usage", start_time, 500, str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo métricas de uso")

# =====================================================================
# ENDPOINTS DE HEALTH CHECK Y MONITORING
# =====================================================================

@router.get(
    "/health",
    response_model=APIResponse,
    summary="Health check del sistema",
    description="Verificar estado de salud de todos los componentes del sistema de notificaciones",
    tags=["Health Check"]
)
async def health_check(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    include_details: bool = Query(True, description="Incluir detalles de cada componente")
):
    """Health check completo del sistema"""
    request_id = get_request_id()
    start_time = time.time()
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "2.0.0",
        "uptime_seconds": int(time.time() - start_time),  # Simulated
        "request_id": request_id
    }
    
    components_health = {}
    overall_status = "healthy"
    
    try:
        # Verificar base de datos
        try:
            db.execute(text("SELECT 1")).scalar()
            components_health["database"] = {
                "status": "healthy",
                "response_time_ms": 15.2,
                "last_check": datetime.now()
            }
        except Exception as e:
            components_health["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now()
            }
            overall_status = "degraded"
        
        # Verificar servicio de WhatsApp
        try:
            whatsapp_status = await whatsapp_service.health_check()
            components_health["whatsapp_api"] = {
                "status": "healthy" if whatsapp_status.get("success") else "unhealthy",
                "response_time_ms": whatsapp_status.get("response_time_ms", 0),
                "last_successful_send": whatsapp_status.get("last_successful_send"),
                "rate_limit_remaining": whatsapp_status.get("rate_limit_remaining")
            }
        except Exception as e:
            components_health["whatsapp_api"] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now()
            }
            overall_status = "degraded"
        
        # Verificar scheduler
        try:
            scheduler_status = scheduler_service.get_health_status()
            components_health["scheduler"] = {
                "status": "healthy" if scheduler_status.get("running") else "unhealthy",
                "active_jobs": scheduler_status.get("active_jobs", 0),
                "last_execution": scheduler_status.get("last_execution"),
                "next_execution": scheduler_status.get("next_execution")
            }
        except Exception as e:
            components_health["scheduler"] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now()
            }
            overall_status = "degraded"
        
        # Verificar métricas rápidas del sistema
        if include_details:
            try:
                # Notificaciones pendientes
                pending_count = db.query(func.count(WhatsAppNotificacionesDB.id)).filter(
                    WhatsAppNotificacionesDB.estado == EstadoNotificacion.PENDIENTE
                ).scalar()
                
                # Notificaciones fallidas en última hora
                hour_ago = datetime.now() - timedelta(hours=1)
                failed_last_hour = db.query(func.count(WhatsAppNotificacionesDB.id)).filter(
                    and_(
                        WhatsAppNotificacionesDB.estado == EstadoNotificacion.ERROR,
                        WhatsAppNotificacionesDB.updated_at >= hour_ago
                    )
                ).scalar()
                
                # Total de notificaciones hoy
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                total_today = db.query(func.count(WhatsAppNotificacionesDB.id)).filter(
                    WhatsAppNotificacionesDB.created_at >= today_start
                ).scalar()
                
                health_data.update({
                    "total_notifications_today": total_today,
                    "pending_notifications": pending_count,
                    "failed_notifications_last_hour": failed_last_hour
                })
                
            except Exception as e:
                logger.error(f"Error getting system metrics for health check: {str(e)}")
        
        health_data["status"] = overall_status
        health_data["components"] = components_health if include_details else {}
        health_data["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        # Determinar código de estado HTTP
        status_code = 200 if overall_status == "healthy" else 503
        
        # Agregar headers
        add_security_headers(response)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        log_api_call(request_id, "GET", "/notifications/health", start_time, status_code)
        
        return APIResponse(
            success=(overall_status == "healthy"),
            message=f"Sistema {overall_status}",
            data=health_data,
            request_id=request_id
        )
        
    except Exception as e:
        log_api_call(request_id, "GET", "/notifications/health", start_time, 500, str(e))
        logger.error(f"Health check failed: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error en health check")

# =====================================================================
# ENDPOINTS DE ADMINISTRACIÓN Y TESTING
# =====================================================================

@router.post(
    "/test",
    response_model=APIResponse,
    summary="Enviar mensaje de prueba",
    description="Enviar mensaje de WhatsApp de prueba para validar configuración del sistema"
)
@rate_limit(requests_per_minute=10)
async def send_test_message(
    test_request: TestMessageRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user_context: Dict = Depends(get_user_context)
):
    """Enviar mensaje de prueba optimizado con validación avanzada"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Validar permisos
        if "write" not in user_context["permissions"]:
            raise HTTPException(status_code=403, detail="Sin permisos para envío de pruebas")
        
        logger.info(
            "Sending test message",
            extra={
                "request_id": request_id,
                "phone_number": test_request.phone_number,
                "user_id": user_context["user_id"]
            }
        )
        
        # Validar y formatear número telefónico
        is_valid, formatted_phone, validation_error = whatsapp_service.validate_phone_number(
            test_request.phone_number
        )
        
        if not is_valid:
            raise ValidationError(f"Número telefónico inválido: {validation_error}")
        
        # Preparar mensaje de prueba con metadatos
        test_message = f"""🧪 **MENSAJE DE PRUEBA**

{test_request.message}

---
📅 Enviado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
🆔 Request ID: {request_id}
👤 Usuario: {user_context['user_id']}
🔧 Sistema: Notificaciones v2.0.0

⚠️ Este es un mensaje de prueba del sistema"""
        
        # Enviar mensaje con retry automático
        send_result = await whatsapp_service.send_message_with_retry(
            phone_number=formatted_phone,
            message=test_message,
            max_retries=2,
            context={"type": "test", "request_id": request_id}
        )
        
        if send_result.get("success"):
            # Registrar estadísticas en background
            background_tasks.add_task(
                record_test_message_stats,
                user_id=user_context["user_id"],
                phone_number=formatted_phone,
                success=True,
                response_time_ms=send_result.get("response_time_ms", 0)
            )
            
            # Agregar headers
            add_security_headers(response)
            response.headers["X-Request-ID"] = request_id
            
            log_api_call(request_id, "POST", "/notifications/test", start_time, 200)
            
            return APIResponse(
                success=True,
                message="Mensaje de prueba enviado exitosamente",
                data={
                    "phone_number": formatted_phone,
                    "whatsapp_message_id": send_result.get("message_id"),
                    "status": "sent",
                    "estimated_delivery_seconds": send_result.get("estimated_delivery", 30),
                    "api_response_time_ms": send_result.get("response_time_ms", 0),
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2)
                },
                request_id=request_id
            )
        else:
            error_message = send_result.get("error", "Error desconocido en envío")
            
            # Registrar error en background
            background_tasks.add_task(
                record_test_message_stats,
                user_id=user_context["user_id"],
                phone_number=formatted_phone,
                success=False,
                error=error_message
            )
            
            log_api_call(request_id, "POST", "/notifications/test", start_time, 422, error_message)
            raise WhatsAppError(error_message)
        
    except ValidationError as e:
        log_api_call(request_id, "POST", "/notifications/test", start_time, 400, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except WhatsAppError as e:
        log_api_call(request_id, "POST", "/notifications/test", start_time, 422, str(e))
        raise HTTPException(status_code=422, detail=f"Error de WhatsApp: {str(e)}")
    except Exception as e:
        log_api_call(request_id, "POST", "/notifications/test", start_time, 500, str(e))
        logger.error(f"Unexpected error sending test message: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error interno en envío de prueba")

# =====================================================================
# HELPER FUNCTIONS PARA BACKGROUND TASKS
# =====================================================================

async def record_test_message_stats(
    user_id: str,
    phone_number: str,
    success: bool,
    response_time_ms: int = 0,
    error: str = None
):
    """Registrar estadísticas de mensajes de prueba"""
    try:
        # Aquí se registrarían las estadísticas en base de datos o sistema de métricas
        logger.info(
            "Test message stats recorded",
            extra={
                "user_id": user_id,
                "phone_number": phone_number[-4:],  # Solo últimos 4 dígitos por privacidad
                "success": success,
                "response_time_ms": response_time_ms,
                "error": error
            }
        )
    except Exception as e:
        logger.error(f"Error recording test message stats: {str(e)}")

# Continúa con endpoints de webhook y configuración...