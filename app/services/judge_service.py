import random
import time
from app.models.submissions import Submission, StatusEnum
from app.models.problems import Problem, TestCase

def judge_submission(submission: Submission, problem: Problem):
    """
    Chấm bài nộp (giả lập)
    
    Trong ứng dụng thực tế, bạn sẽ cần triển khai một hệ thống chấm bài thực sự,
    có thể chạy mã nguồn trong môi trường sandbox an toàn và kiểm tra kết quả.
    
    Hàm này chỉ là một mô phỏng đơn giản cho mục đích demo.
    """
    # Giả lập việc chấm bài
    # Trong thực tế, bạn sẽ cần:
    # 1. Biên dịch mã nguồn (nếu cần)
    # 2. Chạy mã nguồn với các test cases
    # 3. Kiểm tra kết quả và giới hạn tài nguyên
    
    # Giả lập thời gian xử lý
    time.sleep(0.5)
    
    # Giả lập kết quả chấm bài với tỉ lệ thành công ngẫu nhiên
    rand_val = random.random()
    
    if rand_val < 0.7:  # 70% tỉ lệ thành công
        status = StatusEnum.accepted
    elif rand_val < 0.8:
        status = StatusEnum.wrong_answer
    elif rand_val < 0.85:
        status = StatusEnum.time_limit_exceeded
    elif rand_val < 0.9:
        status = StatusEnum.memory_limit_exceeded
    elif rand_val < 0.95:
        status = StatusEnum.runtime_error
    else:
        status = StatusEnum.compilation_error
    
    # Giả lập thời gian thực thi và bộ nhớ sử dụng
    execution_time_ms = random.randint(10, problem.time_limit_ms - 10) if status != StatusEnum.time_limit_exceeded else problem.time_limit_ms + 100
    memory_used_kb = random.randint(1000, problem.memory_limit_kb - 1000) if status != StatusEnum.memory_limit_exceeded else problem.memory_limit_kb + 1000
    
    return {
        "status": status,
        "execution_time_ms": execution_time_ms,
        "memory_used_kb": memory_used_kb
    }

# Trong ứng dụng thực tế, bạn sẽ cần triển khai các hàm sau:
def compile_code(code: str, language: str):
    """Biên dịch mã nguồn"""
    pass

def run_test_case(compiled_code, test_case: TestCase, time_limit_ms: int, memory_limit_kb: int):
    """Chạy một test case và trả về kết quả"""
    pass

def check_output(actual_output: str, expected_output: str):
    """Kiểm tra output thực tế có khớp với output mong đợi không"""
    pass