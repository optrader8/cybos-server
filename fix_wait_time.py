"""
대기 시간 수정 스크립트
"""

def fix_wait_time():
    file_path = "src/services/price_update_service.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 기존 대기 시간 로직을 새로운 것으로 교체
    old_pattern = 'wait_time = random.uniform(schedule["safe_interval"], schedule["safe_interval"] * 1.5)'
    new_pattern = 'wait_time = random.uniform(3.0, 10.0)'
    
    content = content.replace(old_pattern, new_pattern)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 대기 시간이 3~10초로 수정되었습니다.")

if __name__ == "__main__":
    fix_wait_time()
