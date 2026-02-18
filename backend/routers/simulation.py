# ---------------------------------------------------------
# Роутер для управления симуляцией
# ---------------------------------------------------------

from fastapi import APIRouter, Depends

from backend.database.postgr.models import User
from backend.schemas import SimulationControlRequest, SimulationStatus
from backend.services.deps import get_current_active_user

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Глобальная переменная для хранения экземпляра движка симуляции
# Будет установлена из main.py после создания
_sim_engine = None


def set_sim_engine(sim_engine):
    """Устанавливает экземпляр движка симуляции"""
    global _sim_engine
    _sim_engine = sim_engine


@router.post("/control", response_model=SimulationStatus)
async def control_simulation(
        payload: SimulationControlRequest,
        current_user: User = Depends(get_current_active_user)
) -> SimulationStatus:
    """
    Управление симуляцией (пауза или изменение скорости).
    """
    if _sim_engine is None:
        raise RuntimeError("Simulation engine not initialized")
    return await _sim_engine.control(action=payload.action, speed=payload.speed)
