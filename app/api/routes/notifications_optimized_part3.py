"""
Parte final del archivo notifications_optimized.py
Webhooks, configuración y utilidades de administración
"""

# =====================================================================
# WEBHOOK DE WHATSAPP OPTIMIZADO
# =====================================================================

@router.get(
    "/webhook",
    summary="Verificación de webhook",
    description="Endpoint para verificación del webhook de WhatsApp Business API",
    tags=["Webhook"],
    include_in_schema=False  # No mostrar en documentación pública
)
async def verify_webhook(
    request: Request,
    response: Response,
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge")
):
    """Verificación de webhook de WhatsApp (GET) optimizada"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        logger.info(
            "Webhook verification attempt",
            extra={
                "request_id": request_id,
                "mode": hub_mode,
                "token_hash": hash(hub_verify_token),
                "ip": request.client.host if request.client else "unknown"
            }
        )
        
        # Verificar token y modo
        verification_result = await whatsapp_service.verify_webhook(
            mode=hub_mode,
            token=hub_verify_token,
            challenge=hub_challenge
        )
        
        if verification_result:
            # Agregar headers de seguridad básicos (webhook debe ser rápido)
            response.headers.update({
                "X-Content-Type-Options": "nosniff",
                "X-Request-ID": request_id,
                "Cache-Control": "no-cache"
            })
            
            log_api_call(request_id, "GET", "/notifications/webhook", start_time, 200)
            
            return JSONResponse(
                content=verification_result,
                status_code=200,
                media_type="text/plain"
            )
        else:
            log_api_call(request_id, "GET", "/notifications/webhook", start_time, 403, "Invalid token")
            raise HTTPException(status_code=403, detail="Webhook verification failed")
        
    except HTTPException:
        raise
    except Exception as e:
        log_api_call(request_id, "GET", "/notifications/webhook", start_time, 500, str(e))
        logger.error(f"Webhook verification error: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error en verificación de webhook")

@router.post(
    "/webhook",
    summary="Webhook de WhatsApp",
    description="Endpoint para recibir callbacks de estado de mensajes de WhatsApp",
    tags=["Webhook"],
    include_in_schema=False  # No mostrar en documentación pública
)
async def handle_webhook(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manejo optimizado de webhook de WhatsApp (POST)"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Leer payload de webhook
        payload = await request.json()
        
        logger.info(
            "Webhook received",
            extra={
                "request_id": request_id,
                "payload_size": len(json.dumps(payload)),
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("User-Agent", "")
            }
        )
        
        # Validar estructura básica del payload
        if not isinstance(payload, dict) or "entry" not in payload:
            logger.warning(f"Invalid webhook payload structure", extra={"request_id": request_id})
            return JSONResponse(
                content={"status": "invalid_payload"},
                status_code=200  # Siempre 200 para evitar reintentos
            )
        
        # Procesar webhook en background para respuesta rápida
        background_tasks.add_task(
            process_webhook_updates_background,
            payload=payload,
            request_id=request_id
        )
        
        # Respuesta inmediata (WhatsApp requiere respuesta rápida)
        response.headers.update({
            "X-Request-ID": request_id,
            "Cache-Control": "no-cache"
        })
        
        log_api_call(request_id, "POST", "/notifications/webhook", start_time, 200)
        
        return JSONResponse(
            content={
                "status": "received",
                "request_id": request_id,
                "processing": "async"
            },
            status_code=200
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {str(e)}", extra={"request_id": request_id})
        return JSONResponse(
            content={"status": "invalid_json"},
            status_code=200  # Siempre 200 para webhooks
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", extra={"request_id": request_id})
        # WhatsApp requiere respuesta 200 para evitar reintentos
        return JSONResponse(
            content={"status": "error", "message": "Internal processing error"},
            status_code=200
        )

async def process_webhook_updates_background(payload: Dict[str, Any], request_id: str):
    """Procesar actualizaciones de webhook en background"""
    try:
        # Obtener nueva sesión de base de datos para background task
        from app.core.database import SessionLocal
        
        with SessionLocal() as db:
            # Procesar eventos del webhook
            result = await notification_service.process_webhook_updates(
                db=db,
                payload=payload,
                context={"request_id": request_id}
            )
            
            logger.info(
                "Webhook processed",
                extra={
                    "request_id": request_id,
                    "events_processed": result.get("processed_events", 0),
                    "updates_made": result.get("updates_made", 0),
                    "errors": result.get("errors", 0)
                }
            )
            
            # Invalidar cache relacionado si hubo actualizaciones
            if result.get("updates_made", 0) > 0:
                await invalidate_notification_cache([
                    "notifications:list",
                    "notifications:metrics"
                ])
        
    except Exception as e:
        logger.error(
            f"Background webhook processing failed: {str(e)}",
            extra={"request_id": request_id}
        )

# =====================================================================
# ENDPOINTS DE CONFIGURACIÓN OPTIMIZADOS
# =====================================================================

@router.get(
    "/contacts",
    response_model=APIResponse,
    summary="Listar contactos",
    description="Obtener lista de contactos de WhatsApp con filtros optimizados"
)
@rate_limit(requests_per_minute=80)
async def list_contacts(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user_context: Dict = Depends(get_user_context),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    tipo: Optional[str] = Query(None, description="Tipo de contacto"),
    empresa_id: Optional[int] = Query(None, gt=0, description="ID de empresa"),
    limit: int = Query(50, ge=1, le=200, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    search: Optional[str] = Query(None, min_length=2, description="Búsqueda por nombre o teléfono")
):
    """Listar contactos con query optimizada"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Query optimizada con joins
        query = db.query(WhatsAppContactosDB).options(
            joinedload(WhatsAppContactosDB.empresa),
            joinedload(WhatsAppContactosDB.horario_configuracion)
        )
        
        # Aplicar filtros
        filters = []
        
        if activo is not None:
            filters.append(WhatsAppContactosDB.activo == activo)
        
        if tipo:
            filters.append(WhatsAppContactosDB.tipo_contacto == tipo)
        
        if empresa_id:
            filters.append(WhatsAppContactosDB.empresa_id == empresa_id)
        
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    WhatsAppContactosDB.nombre.ilike(search_term),
                    WhatsAppContactosDB.telefono.ilike(search_term),
                    WhatsAppContactosDB.email.ilike(search_term)
                )
            )
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Obtener total para paginación
        total = query.count()
        
        # Aplicar paginación y ordenamiento
        contactos = query.order_by(
            WhatsAppContactosDB.nombre
        ).offset(offset).limit(limit).all()
        
        # Formatear respuesta
        contacts_data = []
        for contacto in contactos:
            contact_data = {
                "id": contacto.id,
                "nombre": contacto.nombre,
                "telefono": contacto.telefono,
                "email": contacto.email,
                "tipo_contacto": contacto.tipo_contacto,
                "activo": contacto.activo,
                "created_at": contacto.created_at,
                "updated_at": contacto.updated_at,
                
                # Información relacionada
                "empresa": {
                    "id": contacto.empresa.id,
                    "razon_social": contacto.empresa.razon_social,
                    "ruc": contacto.empresa.ruc
                } if contacto.empresa else None,
                
                "configuracion_horarios": {
                    "id": contacto.horario_configuracion.id,
                    "nombre": contacto.horario_configuracion.nombre,
                    "activo": contacto.horario_configuracion.activo
                } if contacto.horario_configuracion else None
            }
            contacts_data.append(contact_data)
        
        # Agregar headers
        add_security_headers(response)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Total-Count"] = str(total)
        
        log_api_call(request_id, "GET", "/notifications/contacts", start_time, 200)
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(contacts_data)} contactos",
            data={
                "items": contacts_data,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            },
            request_id=request_id
        )
        
    except Exception as e:
        log_api_call(request_id, "GET", "/notifications/contacts", start_time, 500, str(e))
        logger.error(f"Error listing contacts: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get(
    "/templates",
    response_model=APIResponse,
    summary="Listar plantillas",
    description="Obtener lista de plantillas de mensajes con filtros"
)
@rate_limit(requests_per_minute=80)
async def list_templates(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user_context: Dict = Depends(get_user_context),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    evento: Optional[EventoTrigger] = Query(None, description="Filtrar por evento"),
    include_content: bool = Query(False, description="Incluir contenido de plantillas"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados")
):
    """Listar plantillas optimizado"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Query base
        query = db.query(WhatsAppPlantillasMensajesDB)
        
        # Aplicar filtros
        filters = []
        
        if activo is not None:
            filters.append(WhatsAppPlantillasMensajesDB.activo == activo)
        
        if evento:
            filters.append(WhatsAppPlantillasMensajesDB.evento_trigger == evento.value)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Ejecutar query
        plantillas = query.order_by(
            WhatsAppPlantillasMensajesDB.nombre
        ).limit(limit).all()
        
        # Formatear respuesta
        templates_data = []
        for plantilla in plantillas:
            template_data = {
                "id": plantilla.id,
                "codigo": plantilla.codigo,
                "nombre": plantilla.nombre,
                "descripcion": plantilla.descripcion,
                "evento_trigger": plantilla.evento_trigger,
                "estado_valorizacion": plantilla.estado_valorizacion,
                "tipo_destinatario": plantilla.tipo_destinatario,
                "activo": plantilla.activo,
                "created_at": plantilla.created_at,
                "updated_at": plantilla.updated_at
            }
            
            # Incluir contenido solo si se solicita
            if include_content:
                template_data.update({
                    "plantilla_mensaje": plantilla.plantilla_mensaje,
                    "variables_disponibles": plantilla.variables_disponibles
                })
            
            templates_data.append(template_data)
        
        # Agregar headers
        add_security_headers(response)
        response.headers["X-Request-ID"] = request_id
        
        log_api_call(request_id, "GET", "/notifications/templates", start_time, 200)
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(templates_data)} plantillas",
            data={
                "items": templates_data,
                "total": len(templates_data),
                "include_content": include_content,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            },
            request_id=request_id
        )
        
    except Exception as e:
        log_api_call(request_id, "GET", "/notifications/templates", start_time, 500, str(e))
        logger.error(f"Error listing templates: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# =====================================================================
# ENDPOINTS DE ADMINISTRACIÓN AVANZADA
# =====================================================================

@router.post(
    "/admin/process-pending",
    response_model=APIResponse,
    summary="Procesar notificaciones pendientes",
    description="Forzar procesamiento de notificaciones pendientes (endpoint administrativo)"
)
@rate_limit(requests_per_minute=5)
async def process_pending_notifications(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_context: Dict = Depends(get_user_context),
    limit: int = Query(50, ge=1, le=200, description="Máximo de notificaciones a procesar"),
    force: bool = Query(False, description="Forzar procesamiento incluso si hay errores recientes"),
    dry_run: bool = Query(False, description="Simular procesamiento sin enviar mensajes")
):
    """Procesamiento administrativo de notificaciones pendientes"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Validar permisos administrativos
        if user_context["client_type"] != "authenticated":
            raise HTTPException(status_code=403, detail="Requiere autenticación")
        
        logger.info(
            "Admin processing pending notifications",
            extra={
                "request_id": request_id,
                "limit": limit,
                "force": force,
                "dry_run": dry_run,
                "user_id": user_context["user_id"]
            }
        )
        
        # Obtener notificaciones pendientes
        pending_query = db.query(WhatsAppNotificacionesDB).filter(
            WhatsAppNotificacionesDB.estado == EstadoNotificacion.PENDIENTE
        ).order_by(WhatsAppNotificacionesDB.created_at)
        
        if not force:
            # Excluir las que han fallado recientemente
            recent_errors = datetime.now() - timedelta(minutes=30)
            pending_query = pending_query.filter(
                or_(
                    WhatsAppNotificacionesDB.fecha_ultimo_error.is_(None),
                    WhatsAppNotificacionesDB.fecha_ultimo_error < recent_errors
                )
            )
        
        pending_notifications = pending_query.limit(limit).all()
        
        if dry_run:
            # Solo simular
            result_data = {
                "mode": "dry_run",
                "would_process": len(pending_notifications),
                "pending_notifications": [
                    {
                        "id": n.id,
                        "valorizacion_id": n.valorizacion_id,
                        "evento": n.evento_trigger,
                        "created_at": n.created_at
                    } for n in pending_notifications
                ]
            }
        else:
            # Procesar en background
            background_tasks.add_task(
                process_notifications_batch,
                notification_ids=[n.id for n in pending_notifications],
                user_id=user_context["user_id"],
                request_id=request_id
            )
            
            result_data = {
                "mode": "processing",
                "queued_for_processing": len(pending_notifications),
                "estimated_completion_minutes": max(1, len(pending_notifications) // 10)
            }
        
        # Agregar headers
        add_security_headers(response)
        response.headers["X-Request-ID"] = request_id
        
        log_api_call(request_id, "POST", "/notifications/admin/process-pending", start_time, 200)
        
        return APIResponse(
            success=True,
            message=f"{'Simulación de' if dry_run else ''} Procesamiento iniciado para {len(pending_notifications)} notificaciones",
            data=result_data,
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_api_call(request_id, "POST", "/notifications/admin/process-pending", start_time, 500, str(e))
        logger.error(f"Error in admin processing: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error en procesamiento administrativo")

async def process_notifications_batch(
    notification_ids: List[int],
    user_id: str,
    request_id: str
):
    """Procesar lote de notificaciones en background"""
    try:
        from app.core.database import SessionLocal
        
        with SessionLocal() as db:
            stats = await notification_service.send_pending_notifications_batch(
                db=db,
                notification_ids=notification_ids,
                context={
                    "initiated_by": user_id,
                    "request_id": request_id,
                    "type": "admin_batch"
                }
            )
            
            logger.info(
                "Batch processing completed",
                extra={
                    "request_id": request_id,
                    "processed": stats.get("processed", 0),
                    "success": stats.get("success", 0),
                    "errors": stats.get("errors", 0),
                    "user_id": user_id
                }
            )
        
    except Exception as e:
        logger.error(
            f"Batch processing failed: {str(e)}",
            extra={"request_id": request_id, "user_id": user_id}
        )

# =====================================================================
# UTILIDADES Y FUNCIONES DE APOYO
# =====================================================================

@router.get(
    "/stats/summary",
    response_model=APIResponse,
    summary="Resumen estadístico",
    description="Resumen rápido de estadísticas del sistema para dashboards"
)
@rate_limit(requests_per_minute=60)
async def get_stats_summary(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user_context: Dict = Depends(get_user_context)
):
    """Resumen estadístico optimizado para dashboards"""
    request_id = get_request_id()
    start_time = time.time()
    
    try:
        # Query optimizada con múltiples agregaciones
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        week_start = today_start - timedelta(days=7)
        
        # Stats de hoy
        today_stats = db.query(
            func.count(WhatsAppNotificacionesDB.id).label('total'),
            func.sum(func.case([(WhatsAppNotificacionesDB.estado == 'ENVIADA', 1)], else_=0)).label('sent'),
            func.sum(func.case([(WhatsAppNotificacionesDB.estado == 'ERROR', 1)], else_=0)).label('errors'),
            func.sum(func.case([(WhatsAppNotificacionesDB.estado == 'PENDIENTE', 1)], else_=0)).label('pending')
        ).filter(
            WhatsAppNotificacionesDB.created_at >= today_start
        ).first()
        
        # Stats de ayer para comparación
        yesterday_total = db.query(func.count(WhatsAppNotificacionesDB.id)).filter(
            and_(
                WhatsAppNotificacionesDB.created_at >= yesterday_start,
                WhatsAppNotificacionesDB.created_at < today_start
            )
        ).scalar()
        
        # Stats de la semana
        week_total = db.query(func.count(WhatsAppNotificacionesDB.id)).filter(
            WhatsAppNotificacionesDB.created_at >= week_start
        ).scalar()
        
        # Calcular tendencias
        today_total = today_stats.total or 0
        growth_vs_yesterday = 0
        if yesterday_total and yesterday_total > 0:
            growth_vs_yesterday = ((today_total - yesterday_total) / yesterday_total) * 100
        
        summary_data = {
            "today": {
                "total": today_total,
                "sent": today_stats.sent or 0,
                "errors": today_stats.errors or 0,
                "pending": today_stats.pending or 0,
                "success_rate": round(((today_stats.sent or 0) / max(today_total, 1)) * 100, 1)
            },
            "comparisons": {
                "yesterday_total": yesterday_total or 0,
                "growth_percentage": round(growth_vs_yesterday, 1),
                "week_total": week_total or 0,
                "daily_average_week": round((week_total or 0) / 7, 1)
            },
            "system_status": {
                "healthy": (today_stats.errors or 0) < (today_total * 0.05),  # Menos del 5% errores
                "last_updated": datetime.now(),
                "processing_time_ms": 0  # Se calcula al final
            }
        }
        
        # Agregar headers optimizados
        add_security_headers(response)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "public, max-age=60"  # Cache por 1 minuto
        
        summary_data["system_status"]["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        log_api_call(request_id, "GET", "/notifications/stats/summary", start_time, 200)
        
        return APIResponse(
            success=True,
            message="Resumen estadístico generado",
            data=summary_data,
            request_id=request_id
        )
        
    except Exception as e:
        log_api_call(request_id, "GET", "/notifications/stats/summary", start_time, 500, str(e))
        logger.error(f"Error getting stats summary: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail="Error obteniendo resumen estadístico")

# =====================================================================
# EXPORTAR ROUTER FINAL
# =====================================================================

# El router se exporta desde el archivo principal notifications_optimized.py