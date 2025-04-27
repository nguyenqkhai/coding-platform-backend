from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.contests import Contest, ContestProblem, ContestParticipant
from app.models.problems import Problem
from app.models.users import User
from app.schemas.contests import (
    ContestCreate, ContestResponse, ContestUpdate, ContestDetailResponse,
    ContestProblemCreate, ContestProblemResponse, ContestProblemDetailResponse,
    ContestParticipantCreate, ContestParticipantResponse, ContestParticipantDetailResponse
)
from app.auth.oauth2 import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/contests", tags=["Contests"])

@router.post("/", response_model=ContestResponse, status_code=status.HTTP_201_CREATED)
def create_contest(
    contest: ContestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Tạo cuộc thi mới
    """
    # Chỉ admin mới có thể tạo cuộc thi
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create contests"
        )
    
    # Tạo cuộc thi
    db_contest = Contest(
        title=contest.title,
        description=contest.description,
        start_time=contest.start_time,
        end_time=contest.end_time,
        is_public=contest.is_public,
        created_by=current_user.id
    )
    
    db.add(db_contest)
    db.commit()
    db.refresh(db_contest)
    
    # Thêm các bài toán vào cuộc thi
    for problem in contest.problems:
        # Kiểm tra bài toán tồn tại
        db_problem = db.query(Problem).filter(Problem.id == problem.problem_id).first()
        if not db_problem:
            db.delete(db_contest)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Problem with ID {problem.problem_id} not found"
            )
        
        db_contest_problem = ContestProblem(
            contest_id=db_contest.id,
            problem_id=problem.problem_id,
            order=problem.order,
            points=problem.points
        )
        db.add(db_contest_problem)
    
    db.commit()
    db.refresh(db_contest)
    return db_contest

@router.get("/", response_model=List[ContestResponse])
def get_contests(
    skip: int = 0,
    limit: int = 100,
    upcoming: Optional[bool] = None,
    ongoing: Optional[bool] = None,
    past: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách cuộc thi với bộ lọc
    """
    query = db.query(Contest)
    
    # Tìm kiếm theo tiêu đề
    if search:
        query = query.filter(Contest.title.contains(search))
    
    # Lọc theo trạng thái cuộc thi
    now = datetime.utcnow()
    if upcoming is True:
        query = query.filter(Contest.start_time > now)
    elif ongoing is True:
        query = query.filter(Contest.start_time <= now, Contest.end_time >= now)
    elif past is True:
        query = query.filter(Contest.end_time < now)
    
    # Nếu không phải admin thì chỉ xem được cuộc thi public
    if not current_user.is_admin:
        query = query.filter(Contest.is_public == True)
    
    # Phân trang và lấy kết quả
    contests = query.offset(skip).limit(limit).all()
    return contests

@router.get("/{contest_id}", response_model=ContestDetailResponse)
def get_contest(
    contest_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy thông tin chi tiết cuộc thi theo ID
    """
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    
    # Kiểm tra cuộc thi tồn tại
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Kiểm tra quyền xem
    if not contest.is_public and not current_user.is_admin and contest.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this contest"
        )
    
    return contest

@router.put("/{contest_id}", response_model=ContestResponse)
def update_contest(
    contest_id: str,
    contest_update: ContestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cập nhật thông tin cuộc thi
    """
    # Lấy thông tin cuộc thi
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Kiểm tra quyền cập nhật (phải là admin hoặc người tạo)
    if not current_user.is_admin and db_contest.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this contest"
        )
    
    # Cập nhật thông tin
    update_data = contest_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_contest, key, value)
    
    db.commit()
    db.refresh(db_contest)
    return db_contest

@router.delete("/{contest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contest(
    contest_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Xóa cuộc thi (yêu cầu quyền admin)
    """
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    db.delete(db_contest)
    db.commit()
    return None

# API cho Contest Problems
@router.post("/{contest_id}/problems", response_model=ContestProblemResponse)
def add_problem_to_contest(
    contest_id: str,
    problem: ContestProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Thêm bài toán vào cuộc thi
    """
    # Kiểm tra cuộc thi tồn tại
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Kiểm tra bài toán tồn tại
    db_problem = db.query(Problem).filter(Problem.id == problem.problem_id).first()
    if not db_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Kiểm tra bài toán đã tồn tại trong cuộc thi
    existing = db.query(ContestProblem).filter(
        ContestProblem.contest_id == contest_id,
        ContestProblem.problem_id == problem.problem_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Problem already exists in the contest"
        )
    
    # Thêm bài toán vào cuộc thi
    db_contest_problem = ContestProblem(
        contest_id=contest_id,
        problem_id=problem.problem_id,
        order=problem.order,
        points=problem.points
    )
    
    db.add(db_contest_problem)
    db.commit()
    db.refresh(db_contest_problem)
    return db_contest_problem

@router.delete("/{contest_id}/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_problem_from_contest(
    contest_id: str,
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Xóa bài toán khỏi cuộc thi
    """
    # Kiểm tra bài toán tồn tại trong cuộc thi
    db_contest_problem = db.query(ContestProblem).filter(
        ContestProblem.contest_id == contest_id,
        ContestProblem.problem_id == problem_id
    ).first()
    
    if not db_contest_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found in the contest"
        )
    
    db.delete(db_contest_problem)
    db.commit()
    return None

# API cho Contest Participants
@router.post("/{contest_id}/participants", response_model=ContestParticipantResponse)
def register_for_contest(
    contest_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Đăng ký tham gia cuộc thi
    """
    # Kiểm tra cuộc thi tồn tại
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Kiểm tra quyền tham gia (cuộc thi public hoặc là admin)
    if not db_contest.is_public and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to join this contest"
        )
    
    # Kiểm tra đã đăng ký chưa
    existing = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id,
        ContestParticipant.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this contest"
        )
    
    # Đăng ký tham gia
    db_participant = ContestParticipant(
        contest_id=contest_id,
        user_id=current_user.id,
        score=0
    )
    
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

@router.get("/{contest_id}/participants", response_model=List[ContestParticipantDetailResponse])
def get_contest_participants(
    contest_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách người tham gia cuộc thi
    """
    # Kiểm tra cuộc thi tồn tại
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Lấy danh sách người tham gia
    participants = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id
    ).all()
    
    return participants

@router.delete("/{contest_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_participant_from_contest(
    contest_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Xóa người tham gia khỏi cuộc thi (yêu cầu quyền admin)
    """
    # Kiểm tra người tham gia tồn tại trong cuộc thi
    db_participant = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id,
        ContestParticipant.user_id == user_id
    ).first()
    
    if not db_participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found in the contest"
        )
    
    db.delete(db_participant)
    db.commit()
    return None

# API cho Contest Standings (bảng xếp hạng)
@router.get("/{contest_id}/standings", response_model=List[ContestParticipantDetailResponse])
def get_contest_standings(
    contest_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy bảng xếp hạng của cuộc thi
    """
    # Kiểm tra cuộc thi tồn tại
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Lấy danh sách người tham gia và sắp xếp theo điểm (giảm dần)
    standings = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id
    ).order_by(ContestParticipant.score.desc()).all()
    
    return standings

# API cho xác nhận trạng thái cuộc thi
@router.get("/{contest_id}/status", response_model=dict)
def get_contest_status(
    contest_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Kiểm tra trạng thái cuộc thi (sắp diễn ra, đang diễn ra, đã kết thúc)
    """
    # Kiểm tra cuộc thi tồn tại
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    now = datetime.utcnow()
    
    if now < db_contest.start_time:
        status = "upcoming"
        message = "Contest has not started yet"
    elif now >= db_contest.start_time and now <= db_contest.end_time:
        status = "ongoing"
        message = "Contest is currently active"
    else:
        status = "ended"
        message = "Contest has ended"
    
    # Kiểm tra người dùng đã đăng ký cuộc thi chưa
    is_registered = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id,
        ContestParticipant.user_id == current_user.id
    ).first() is not None
    
    return {
        "contest_id": contest_id,
        "status": status,
        "message": message,
        "is_registered": is_registered,
        "start_time": db_contest.start_time,
        "end_time": db_contest.end_time,
        "time_remaining": str(db_contest.end_time - now) if status == "ongoing" else None
    }

# API cho cập nhật điểm số người tham gia
@router.put("/{contest_id}/participants/{user_id}/score", response_model=ContestParticipantResponse)
def update_participant_score(
    contest_id: str,
    user_id: str,
    score: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Cập nhật điểm số cho người tham gia cuộc thi (yêu cầu quyền admin)
    """
    # Kiểm tra người tham gia tồn tại trong cuộc thi
    db_participant = db.query(ContestParticipant).filter(
        ContestParticipant.contest_id == contest_id,
        ContestParticipant.user_id == user_id
    ).first()
    
    if not db_participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found in the contest"
        )
    
    # Cập nhật điểm số
    db_participant.score = score
    db.commit()
    db.refresh(db_participant)
    return db_participant