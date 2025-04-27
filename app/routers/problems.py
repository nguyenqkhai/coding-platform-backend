from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database import get_db, generate_uuid
from app.models.problems import Problem, TestCase
from app.models.users import User
from app.schemas.problems import (
    DifficultyEnum,
    ProblemCreate, ProblemResponse, ProblemUpdate, ProblemDetailResponse,
    TestCaseCreate, TestCaseResponse
)
from app.auth.oauth2 import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/problems", tags=["Problems"])

@router.post("/", response_model=ProblemDetailResponse, status_code=status.HTTP_201_CREATED)
def create_problem(
    problem: ProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Tạo bài toán mới
    """
    # Chỉ admin và giáo viên mới có thể tạo bài toán
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create problems"
        )
    
    # Tạo bài toán
    db_problem = Problem(
        title=problem.title,
        description=problem.description,
        difficulty=problem.difficulty,
        tags=json.dumps(problem.tags),
        example_input=problem.example_input,
        example_output=problem.example_output,
        constraints=problem.constraints,
        is_public=problem.is_public,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_kb=problem.memory_limit_kb,
        created_by=current_user.id
    )
    
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    
    # Tạo các test cases
    for test_case in problem.test_cases:
        db_test_case = TestCase(
            problem_id=db_problem.id,
            input=test_case.input,
            expected_output=test_case.expected_output,
            is_sample=test_case.is_sample,
            order=test_case.order
        )
        db.add(db_test_case)
    
    db.commit()
    db.refresh(db_problem)
    return db_problem

@router.get("/", response_model=List[ProblemResponse])
def get_problems(
    skip: int = 0,
    limit: int = 100,
    difficulty: Optional[DifficultyEnum] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách bài toán với bộ lọc
    """
    query = db.query(Problem)
    
    # Lọc theo độ khó
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)
    
    # Tìm kiếm theo tiêu đề
    if search:
        query = query.filter(Problem.title.contains(search))
    
    # Nếu không phải admin thì chỉ xem được bài public
    if not current_user.is_admin:
        query = query.filter(Problem.is_public == True)
    
    # Phân trang và lấy kết quả
    problems = query.offset(skip).limit(limit).all()
    return problems

@router.get("/{problem_id}", response_model=ProblemDetailResponse)
def get_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy thông tin chi tiết bài toán theo ID
    """
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    
    # Kiểm tra bài toán tồn tại
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Kiểm tra quyền xem
    if not problem.is_public and not current_user.is_admin and problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this problem"
        )
    
    return problem

@router.put("/{problem_id}", response_model=ProblemDetailResponse)
def update_problem(
    problem_id: str,
    problem_update: ProblemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cập nhật thông tin bài toán
    """
    # Lấy thông tin bài toán
    db_problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not db_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Kiểm tra quyền cập nhật (phải là admin hoặc người tạo)
    if not current_user.is_admin and db_problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this problem"
        )
    
    # Cập nhật thông tin
    update_data = problem_update.dict(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"])
    
    for key, value in update_data.items():
        setattr(db_problem, key, value)
    
    db.commit()
    db.refresh(db_problem)
    return db_problem

@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Xóa bài toán (yêu cầu quyền admin)
    """
    db_problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not db_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    db.delete(db_problem)
    db.commit()
    return None

# API cho TestCase
@router.post("/{problem_id}/test-cases", response_model=TestCaseResponse)
def create_test_case(
    problem_id: str,
    test_case: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Thêm test case cho bài toán
    """
    # Lấy thông tin bài toán
    db_problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not db_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Kiểm tra quyền (phải là admin hoặc người tạo bài toán)
    if not current_user.is_admin and db_problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add test cases to this problem"
        )
    
    # Tạo test case mới
    db_test_case = TestCase(
        problem_id=problem_id,
        input=test_case.input,
        expected_output=test_case.expected_output,
        is_sample=test_case.is_sample,
        order=test_case.order
    )
    
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.get("/{problem_id}/test-cases", response_model=List[TestCaseResponse])
def get_test_cases(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách test cases của bài toán
    """
    # Lấy thông tin bài toán
    db_problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not db_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Kiểm tra quyền xem test case (phải là admin hoặc người tạo bài toán)
    if not current_user.is_admin and db_problem.created_by != current_user.id:
        # Nếu không phải admin hoặc người tạo, chỉ xem được test case sample
        test_cases = db.query(TestCase).filter(
            TestCase.problem_id == problem_id,
            TestCase.is_sample == True
        ).all()
    else:
        # Admin hoặc người tạo xem được tất cả test cases
        test_cases = db.query(TestCase).filter(TestCase.problem_id == problem_id).all()
    
    return test_cases

@router.delete("/{problem_id}/test-cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(
    problem_id: str,
    test_case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Xóa test case
    """
    # Lấy thông tin bài toán
    db_problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not db_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Kiểm tra quyền (phải là admin hoặc người tạo bài toán)
    if not current_user.is_admin and db_problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete test cases of this problem"
        )
    
    # Lấy thông tin test case
    db_test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.problem_id == problem_id
    ).first()
    
    if not db_test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    db.delete(db_test_case)
    db.commit()
    return None