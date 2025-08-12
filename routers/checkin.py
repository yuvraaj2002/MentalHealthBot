import sys
import os
import logging
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

# Add project root to path for imports
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

from models.database_models import User, get_db
from models.pydantic_models import MorningCheckin, EveningCheckin, CheckinResponse
from services.auth_service import get_current_active_user
from models.database_models import Checkin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/checkin", tags=["Daily Check-ins"])

@router.post("/morning", response_model=CheckinResponse)
async def morning_checkin(
    checkin_data: MorningCheckin,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record morning mental health check-in"""
    
    try:
        
        db_checkin = Checkin(
            user_id=current_user.id,
            checkin_type="morning",
            sleep_quality=checkin_data.sleep_quality,
            body_sensation=checkin_data.body_sensation,
            energy_level=checkin_data.energy_level,
            mental_state=checkin_data.mental_state,
            executive_task=checkin_data.executive_task,
            emotion_category=None,  # Not applicable for morning
            overwhelm_amount=None,   # Not applicable for morning
            emotion_in_moment=None,  # Not applicable for morning
            surroundings_impact=None, # Not applicable for morning
            meaningful_moments_quantity=None, # Not applicable for morning
            checkin_time=datetime.now(UTC)
        )
        
        db.add(db_checkin)
        db.commit()
        db.refresh(db_checkin)
        
        logger.info(f"Morning checkin recorded for user {current_user.id}")
        
        return CheckinResponse(
            message="Morning check-in recorded successfully",
            checkin_id=f"{current_user.id}_{db_checkin.id}_0",
            checkin_type="morning",
            timestamp=db_checkin.checkin_time.isoformat(),
            user_id=current_user.id
        )
        
    except Exception as e:
        logger.error(f"Error recording morning checkin: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record morning check-in"
        )

@router.post("/evening", response_model=CheckinResponse)
async def evening_checkin(
    checkin_data: EveningCheckin,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record evening mental health check-in"""
    
    try:
        # Create checkin record in database
        
        db_checkin = Checkin(
            user_id=current_user.id,
            checkin_type="evening",
            sleep_quality=None,      # Not applicable for evening
            body_sensation=None,     # Not applicable for evening
            energy_level=None,       # Not applicable for evening
            mental_state=None,       # Not applicable for evening
            executive_task=None,     # Not applicable for evening
            emotion_category=checkin_data.emotion_category,
            overwhelm_amount=checkin_data.overwhelm_amount,
            emotion_in_moment=checkin_data.emotion_in_moment,
            surroundings_impact=checkin_data.surroundings_impact,
            meaningful_moments_quantity=checkin_data.meaningful_moments_quantity,
            checkin_time=datetime.now(UTC)
        )
        
        db.add(db_checkin)
        db.commit()
        db.refresh(db_checkin)
        
        logger.info(f"Evening checkin recorded for user {current_user.id}")
        
        return CheckinResponse(
            message="Evening check-in recorded successfully",
            checkin_id=f"{current_user.id}_{db_checkin.id}_1",
            checkin_type="evening",
            timestamp=db_checkin.checkin_time.isoformat(),
            user_id=current_user.id
        )
        
    except Exception as e:
        logger.error(f"Error recording evening checkin: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record evening check-in"
        )

@router.get("/history")
async def get_checkin_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 30
):
    """Get user's check-in history"""
    
    try:
        
        checkins = db.query(Checkin)\
            .filter(Checkin.user_id == current_user.id)\
            .order_by(Checkin.checkin_time.desc())\
            .limit(limit)\
            .all()
        
        return {
            "user_id": current_user.id,
            "checkins": [
                {
                    "id": checkin.id,
                    "checkin_type": checkin.checkin_type,
                    "checkin_time": checkin.checkin_time.isoformat(),
                    "morning_data": {
                        "sleep_quality": checkin.sleep_quality,
                        "body_sensation": checkin.body_sensation,
                        "energy_level": checkin.energy_level,
                        "mental_state": checkin.mental_state,
                        "executive_task": checkin.executive_task
                    } if checkin.checkin_type == "morning" else None,
                    "evening_data": {
                        "emotion_category": checkin.emotion_category,
                        "overwhelm_amount": checkin.overwhelm_amount,
                        "emotion_in_moment": checkin.emotion_in_moment,
                        "surroundings_impact": checkin.surroundings_impact,
                        "meaningful_moments_quantity": checkin.meaningful_moments_quantity
                    } if checkin.checkin_type == "evening" else None
                }
                for checkin in checkins
            ],
            "total_count": len(checkins)
        }
        
    except Exception as e:
        logger.error(f"Error fetching checkin history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch check-in history"
        )

@router.get("/today")
async def get_today_checkins(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get today's check-ins for the current user"""
    
    try:
        from models.database_models import Checkin
        from datetime import date
        
        today = date.today()
        
        today_checkins = db.query(Checkin)\
            .filter(Checkin.user_id == current_user.id)\
            .filter(Checkin.checkin_time >= today)\
            .order_by(Checkin.checkin_time.asc())\
            .all()
        
        return {
            "user_id": current_user.id,
            "date": today.isoformat(),
            "morning_checkin": next(
                (c for c in today_checkins if c.checkin_type == "morning"), 
                None
            ),
            "evening_checkin": next(
                (c for c in today_checkins if c.checkin_type == "evening"), 
                None
            ),
            "total_checkins": len(today_checkins)
        }
        
    except Exception as e:
        logger.error(f"Error fetching today's checkins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch today's check-ins"
        )
