from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.submissions import Submission, StatusEnum
from app.models.problems import Problem
from app.models.contests import Contest, ContestParticipant, ContestProblem
from app.models.users import User
from app.schemas.submissions import (
    SubmissionCreate, SubmissionResponse, SubmissionDetailResponse,
    LanguageEnum, StatusEnum as SchemaStatusEnum
)
from app.auth.oauth2 import get_current_active_user, get_current_admin_user
from app.services.judge_service import judge_submission

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])

@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    submission: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Tạo bài nộp mới
    """
    # Kiểm tra bài toán tồn tại
    db_problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
    if not db_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Nếu có contest_id, kiểm tra người dùng có đăng ký cuộc thi không
    if submission.contest_id:
        # Kiểm tra cuộc thi tồn tại
        db_contest = db.query(Contest).filter(Contest.id == submission.contest_id).first()
        if not db_contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        # Kiểm tra cuộc thi đang diễn ra
        now = datetime.utcnow()
        if now < db_contest.start_time or now > db_contest.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest is not active"
            )
        
        # Kiểm tra người dùng đã đăng ký cuộc thi
        participant = db.query(ContestParticipant).filter(
            ContestParticipant.contest_id == submission.contest_id,
            ContestParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not registered for this contest"
            )
    
    # Tạo bài nộp
    db_submission = Submission(
        user_id=current_user.id,
        problem_id=submission.problem_id,
        code=submission.code,
        language=submission.language,
        status=StatusEnum.pending,
        contest_id=submission.contest_id
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Chấm bài nộp (trong thực tế sẽ được xử lý bất đồng bộ)
    try:
        judge_result = judge_submission(db_submission, db_problem)
        db_submission.status = judge_result["status"]
        db_submission.execution_time_ms = judge_result["execution_time_ms"]
        db_submission.memory_used_kb = judge_result["memory_used_kb"]
        
        # Nếu là bài nộp trong cuộc thi và được chấp nhận, cập nhật điểm
        if submission.contest_id and db_submission.status == StatusEnum.accepted:
            contest_problem = db.query(ContestProblem).filter(
                ContestProblem.contest_id == submission.contest_id,
                ContestProblem.problem_id == submission.problem_id
            ).first()
            
            if contest_problem:
                participant.score += contest_problem.points
                db.commit()
        
        db.commit()
        db.refresh(db_submission)
    except Exception as e:
        # Xử lý lỗi khi chấm bài
        db_submission.status = StatusEnum.runtime_error
        db.commit()
    
    return db_submission

@router.get("/", response_model=List[SubmissionResponse])
def get_submissions(
    skip: int = 0,
    limit: int = 100,
    problem_id: Optional[str] = None,
    user_id: Optional[str] = None,
    contest_id: Optional[str] = None,
    status: Optional[SchemaStatusEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách bài nộp với bộ lọc
    """
    query = db.query(Submission)
    
    # Nếu không phải admin, chỉ xem được bài nộp của mình
    if not current_user.is_admin:
        query = query.filter(Submission.user_id == current_user.id)
    
    # Áp dụng các bộ lọc
    if problem_id:
        query = query.filter(Submission.problem_id == problem_id)
    
    if user_id and current_user.is_admin:
        query = query.filter(Submission.user_id == user_id)
    
    if contest_id:
        query = query.filter(Submission.contest_id == contest_id)
    
    if status:
        query = query.filter(Submission.status == status)
    
    # Sắp xếp theo thời gian nộp (mới nhất trước)
    query = query.order_by(Submission.submitted_at.desc())
    
    # Phân trang và lấy kết quả
    submissions = query.offset(skip).limit(limit).all()
    return submissions

@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy thông tin chi tiết bài nộp theo ID
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    
    # Kiểm tra bài nộp tồn tại
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Kiểm tra quyền xem (phải là admin hoặc chủ của bài nộp)
    if not current_user.is_admin and submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission"
        )
    
    return submission

@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Xóa bài nộp (yêu cầu quyền admin)
    """
    db_submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not db_submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    db.delete(db_submission)
    db.commit()
    return None

@router.get("/user/me", response_model=List[SubmissionResponse])
def get_my_submissions(
    skip: int = 0,
    limit: int = 100,
    problem_id: Optional[str] = None,
    contest_id: Optional[str] = None,
    status: Optional[SchemaStatusEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách bài nộp của người dùng hiện tại
    """
    query = db.query(Submission).filter(Submission.user_id == current_user.id)
    
    # Áp dụng các bộ lọc
    if problem_id:
        query = query.filter(Submission.problem_id == problem_id)
    
    if contest_id:
        query = query.filter(Submission.contest_id == contest_id)
    
    if status:
        query = query.filter(Submission.status == status)
    
    # Sắp xếp theo thời gian nộp (mới nhất trước)
    query = query.order_by(Submission.submitted_at.desc())
    
    # Phân trang và lấy kết quả
    submissions = query.offset(skip).limit(limit).all()
    return submissions

@router.get("/problem/{problem_id}/best", response_model=SubmissionResponse)
def get_best_submission_for_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy bài nộp tốt nhất của người dùng cho một bài toán
    """
    # Lấy bài nộp đã được accepted với thời gian thực thi thấp nhất
    best_submission = db.query(Submission).filter(
        Submission.user_id == current_user.id,
        Submission.problem_id == problem_id,
        Submission.status == StatusEnum.accepted
    ).order_by(
        Submission.execution_time_ms.asc()
    ).first()
    
    if not best_submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No accepted submission found for this problem"
        )
    
    return best_submission

@router.get("/contest/{contest_id}/stats", response_model=dict)
def get_contest_submission_stats(
    contest_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy thống kê bài nộp trong cuộc thi
    """
    # Kiểm tra cuộc thi tồn tại
    db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not db_contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Đếm số lượng bài nộp theo trạng thái
    stats = {}
    
    # Tổng số bài nộp
    total_submissions = db.query(Submission).filter(Submission.contest_id == contest_id).count()
    stats["total"] = total_submissions
    
    # Số lượng theo trạng thái
    for status_value in StatusEnum:
        count = db.query(Submission).filter(
            Submission.contest_id == contest_id,
            Submission.status == status_value
        ).count()
        stats[status_value.name] = count
    
    # Số người tham gia đã nộp bài
    participants_with_submissions = db.query(Submission.user_id).filter(
        Submission.contest_id == contest_id
    ).distinct().count()
    stats["participants_with_submissions"] = participants_with_submissions
    
    # Số bài toán đã có người giải
    problems_with_accepted = db.query(Submission.problem_id).filter(
        Submission.contest_id == contest_id,
        Submission.status == StatusEnum.accepted
    ).distinct().count()
    stats["problems_with_accepted"] = problems_with_accepted
    
    return stats