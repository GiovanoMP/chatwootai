"""
Rotas para gerenciamento de agendamentos na API de simulação do Odoo.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentWithDetails, TimeSlot

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
    responses={404: {"description": "Agendamento não encontrado"}},
)

@router.get("/", response_model=List[AppointmentWithDetails])
def read_appointments(
    skip: int = 0, 
    limit: int = 100, 
    customer_id: Optional[int] = None,
    professional_id: Optional[int] = None,
    service_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de agendamentos com filtros opcionais.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **customer_id**: Filtrar por cliente
    - **professional_id**: Filtrar por profissional
    - **service_id**: Filtrar por serviço
    - **status**: Filtrar por status
    - **start_date**: Data de início para filtrar
    - **end_date**: Data de fim para filtrar
    """
    query = """
    SELECT a.*,
           c.first_name || ' ' || c.last_name as customer_name,
           s.name as service_name,
           s.duration as service_duration,
           p.first_name || ' ' || p.last_name as professional_name
    FROM appointments a
    JOIN customers c ON a.customer_id = c.id
    JOIN services s ON a.service_id = s.id
    JOIN professionals p ON a.professional_id = p.id
    WHERE 1=1
    """
    params = {}
    
    if customer_id is not None:
        query += " AND a.customer_id = :customer_id"
        params["customer_id"] = customer_id
    
    if professional_id is not None:
        query += " AND a.professional_id = :professional_id"
        params["professional_id"] = professional_id
    
    if service_id is not None:
        query += " AND a.service_id = :service_id"
        params["service_id"] = service_id
    
    if status is not None:
        query += " AND a.status = :status"
        params["status"] = status
    
    if start_date is not None:
        query += " AND a.start_time >= :start_date"
        params["start_date"] = start_date
    
    if end_date is not None:
        query += " AND a.start_time <= :end_date"
        params["end_date"] = end_date
    
    query += " ORDER BY a.start_time LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    appointments = [dict(row) for row in result]
    
    return appointments

@router.get("/{appointment_id}", response_model=AppointmentWithDetails)
def read_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um agendamento específico.
    
    - **appointment_id**: ID do agendamento
    """
    query = """
    SELECT a.*,
           c.first_name || ' ' || c.last_name as customer_name,
           s.name as service_name,
           s.duration as service_duration,
           p.first_name || ' ' || p.last_name as professional_name
    FROM appointments a
    JOIN customers c ON a.customer_id = c.id
    JOIN services s ON a.service_id = s.id
    JOIN professionals p ON a.professional_id = p.id
    WHERE a.id = :appointment_id
    """
    
    result = db.execute(text(query), {"appointment_id": appointment_id}).fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    return dict(result)

@router.post("/", response_model=Appointment, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    """
    Cria um novo agendamento.
    
    - **appointment**: Dados do agendamento a ser criado
    """
    # Verificar se o cliente existe
    check_customer = "SELECT id FROM customers WHERE id = :customer_id"
    customer_exists = db.execute(text(check_customer), {"customer_id": appointment.customer_id}).fetchone()
    
    if not customer_exists:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Verificar se o serviço existe
    check_service = "SELECT id, duration FROM services WHERE id = :service_id AND active = true"
    service = db.execute(text(check_service), {"service_id": appointment.service_id}).fetchone()
    
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado ou inativo")
    
    # Verificar se o profissional existe e está associado ao serviço
    check_professional = """
    SELECT p.id 
    FROM professionals p
    JOIN professional_services ps ON p.id = ps.professional_id
    WHERE p.id = :professional_id AND ps.service_id = :service_id AND p.active = true
    """
    professional_exists = db.execute(
        text(check_professional), 
        {"professional_id": appointment.professional_id, "service_id": appointment.service_id}
    ).fetchone()
    
    if not professional_exists:
        raise HTTPException(
            status_code=404, 
            detail="Profissional não encontrado, inativo ou não oferece este serviço"
        )
    
    # Verificar se o horário está disponível
    check_availability = """
    SELECT id FROM appointments 
    WHERE professional_id = :professional_id
    AND status NOT IN ('cancelled', 'no_show')
    AND (
        (start_time <= :start_time AND end_time > :start_time) OR
        (start_time < :end_time AND end_time >= :end_time) OR
        (start_time >= :start_time AND end_time <= :end_time)
    )
    """
    
    conflict = db.execute(
        text(check_availability), 
        {
            "professional_id": appointment.professional_id,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time
        }
    ).fetchone()
    
    if conflict:
        raise HTTPException(
            status_code=400, 
            detail="Horário não disponível para este profissional"
        )
    
    # Criar o agendamento
    query = """
    INSERT INTO appointments (
        customer_id, service_id, professional_id, 
        start_time, end_time, status, notes
    ) VALUES (
        :customer_id, :service_id, :professional_id, 
        :start_time, :end_time, :status, :notes
    ) RETURNING *
    """
    
    try:
        result = db.execute(
            text(query), 
            {
                "customer_id": appointment.customer_id,
                "service_id": appointment.service_id,
                "professional_id": appointment.professional_id,
                "start_time": appointment.start_time,
                "end_time": appointment.end_time,
                "status": appointment.status,
                "notes": appointment.notes
            }
        ).fetchone()
        
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar agendamento: {str(e)}")

@router.put("/{appointment_id}", response_model=Appointment)
def update_appointment(appointment_id: int, appointment: AppointmentUpdate, db: Session = Depends(get_db)):
    """
    Atualiza os dados de um agendamento existente.
    
    - **appointment_id**: ID do agendamento a ser atualizado
    - **appointment**: Dados do agendamento a serem atualizados
    """
    # Verificar se o agendamento existe
    check_query = "SELECT id, status FROM appointments WHERE id = :appointment_id"
    existing = db.execute(text(check_query), {"appointment_id": appointment_id}).fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    # Não permitir atualização de agendamentos concluídos ou cancelados
    if existing["status"] in ["completed", "cancelled", "no_show"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Não é possível atualizar um agendamento com status '{existing['status']}'"
        )
    
    # Se estiver atualizando o serviço ou profissional, verificar associação
    if appointment.service_id is not None and appointment.professional_id is not None:
        check_professional = """
        SELECT p.id 
        FROM professionals p
        JOIN professional_services ps ON p.id = ps.professional_id
        WHERE p.id = :professional_id AND ps.service_id = :service_id AND p.active = true
        """
        professional_exists = db.execute(
            text(check_professional), 
            {"professional_id": appointment.professional_id, "service_id": appointment.service_id}
        ).fetchone()
        
        if not professional_exists:
            raise HTTPException(
                status_code=404, 
                detail="Profissional não encontrado, inativo ou não oferece este serviço"
            )
    
    # Se estiver atualizando o horário, verificar disponibilidade
    if appointment.start_time is not None and appointment.end_time is not None:
        check_availability = """
        SELECT id FROM appointments 
        WHERE professional_id = COALESCE(:professional_id, professional_id)
        AND id != :appointment_id
        AND status NOT IN ('cancelled', 'no_show')
        AND (
            (start_time <= :start_time AND end_time > :start_time) OR
            (start_time < :end_time AND end_time >= :end_time) OR
            (start_time >= :start_time AND end_time <= :end_time)
        )
        """
        
        conflict = db.execute(
            text(check_availability), 
            {
                "appointment_id": appointment_id,
                "professional_id": appointment.professional_id,
                "start_time": appointment.start_time,
                "end_time": appointment.end_time
            }
        ).fetchone()
        
        if conflict:
            raise HTTPException(
                status_code=400, 
                detail="Horário não disponível para este profissional"
            )
    
    # Construir a query de atualização dinamicamente com base nos campos fornecidos
    update_fields = []
    params = {"appointment_id": appointment_id}
    
    # Dicionário com os campos e valores do modelo
    appointment_data = appointment.dict(exclude_unset=True)
    
    for field, value in appointment_data.items():
        if value is not None:  # Apenas incluir campos que não são None
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if not update_fields:
        # Se não houver campos para atualizar, retornar o agendamento atual
        return read_appointment(appointment_id, db)
    
    # Adicionar updated_at ao update
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    # Construir e executar a query
    query = f"""
    UPDATE appointments 
    SET {", ".join(update_fields)}
    WHERE id = :appointment_id
    RETURNING *
    """
    
    try:
        result = db.execute(text(query), params).fetchone()
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar agendamento: {str(e)}")

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Cancela um agendamento.
    
    - **appointment_id**: ID do agendamento a ser cancelado
    """
    # Verificar se o agendamento existe
    check_query = "SELECT id, status FROM appointments WHERE id = :appointment_id"
    existing = db.execute(text(check_query), {"appointment_id": appointment_id}).fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    # Não permitir cancelamento de agendamentos já concluídos
    if existing["status"] == "completed":
        raise HTTPException(
            status_code=400, 
            detail="Não é possível cancelar um agendamento já concluído"
        )
    
    # Atualizar o status para cancelado
    query = """
    UPDATE appointments 
    SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
    WHERE id = :appointment_id
    """
    
    try:
        db.execute(text(query), {"appointment_id": appointment_id})
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar agendamento: {str(e)}")

@router.get("/available-slots/", response_model=List[TimeSlot])
def get_available_slots(
    service_id: int,
    professional_id: Optional[int] = None,
    date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna os horários disponíveis para agendamento.
    
    - **service_id**: ID do serviço
    - **professional_id**: ID do profissional (opcional)
    - **date**: Data para verificar disponibilidade (opcional, padrão é a data atual)
    """
    # Se a data não for fornecida, usar a data atual
    if date is None:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Buscar informações do serviço
    service_query = "SELECT duration FROM services WHERE id = :service_id AND active = true"
    service = db.execute(text(service_query), {"service_id": service_id}).fetchone()
    
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado ou inativo")
    
    service_duration = service["duration"]
    
    # Buscar profissionais que oferecem o serviço
    professionals_query = """
    SELECT p.id, p.first_name || ' ' || p.last_name as name
    FROM professionals p
    JOIN professional_services ps ON p.id = ps.professional_id
    WHERE ps.service_id = :service_id AND p.active = true
    """
    params = {"service_id": service_id}
    
    if professional_id is not None:
        professionals_query += " AND p.id = :professional_id"
        params["professional_id"] = professional_id
    
    professionals = db.execute(text(professionals_query), params).fetchall()
    
    if not professionals:
        raise HTTPException(
            status_code=404, 
            detail="Nenhum profissional disponível para este serviço"
        )
    
    # Horário de funcionamento (9h às 18h)
    start_hour = 9
    end_hour = 18
    
    # Intervalo entre slots (30 minutos)
    slot_interval = 30
    
    # Data final (considerar 7 dias a partir da data fornecida)
    end_date = date + timedelta(days=7)
    
    # Buscar agendamentos existentes
    appointments_query = """
    SELECT professional_id, start_time, end_time
    FROM appointments
    WHERE professional_id IN :professional_ids
    AND start_time >= :start_date
    AND start_time < :end_date
    AND status NOT IN ('cancelled', 'no_show')
    """
    
    professional_ids = tuple([p["id"] for p in professionals])
    if len(professional_ids) == 1:
        # SQLAlchemy não lida bem com tuplas de um único elemento
        appointments_query = appointments_query.replace("IN :professional_ids", "= :professional_id")
        params = {
            "professional_id": professional_ids[0],
            "start_date": date,
            "end_date": end_date
        }
    else:
        params = {
            "professional_ids": professional_ids,
            "start_date": date,
            "end_date": end_date
        }
    
    existing_appointments = db.execute(text(appointments_query), params).fetchall()
    
    # Converter para um formato mais fácil de usar
    busy_slots = {}
    for appt in existing_appointments:
        if appt["professional_id"] not in busy_slots:
            busy_slots[appt["professional_id"]] = []
        
        busy_slots[appt["professional_id"]].append({
            "start": appt["start_time"],
            "end": appt["end_time"]
        })
    
    # Gerar slots disponíveis
    available_slots = []
    
    current_date = date
    while current_date < end_date:
        # Pular finais de semana (6 = sábado, 0 = domingo)
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        
        for professional in professionals:
            prof_id = professional["id"]
            prof_name = professional["name"]
            
            # Horários ocupados para este profissional neste dia
            prof_busy_slots = busy_slots.get(prof_id, [])
            
            # Gerar slots para cada intervalo de 30 minutos
            for hour in range(start_hour, end_hour):
                for minute in range(0, 60, slot_interval):
                    slot_start = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # Não mostrar slots no passado
                    if slot_start < datetime.now():
                        continue
                    
                    # Calcular o fim do slot com base na duração do serviço
                    slot_end = slot_start + timedelta(minutes=service_duration)
                    
                    # Verificar se o slot termina dentro do horário de funcionamento
                    if slot_end.hour > end_hour or (slot_end.hour == end_hour and slot_end.minute > 0):
                        continue
                    
                    # Verificar se o slot está disponível
                    is_available = True
                    for busy in prof_busy_slots:
                        busy_start = busy["start"]
                        busy_end = busy["end"]
                        
                        # Verificar sobreposição
                        if (slot_start < busy_end and slot_end > busy_start):
                            is_available = False
                            break
                    
                    # Adicionar slot à lista
                    available_slots.append({
                        "professional_id": prof_id,
                        "professional_name": prof_name,
                        "start_time": slot_start,
                        "end_time": slot_end,
                        "is_available": is_available
                    })
        
        # Avançar para o próximo dia
        current_date += timedelta(days=1)
    
    return available_slots
