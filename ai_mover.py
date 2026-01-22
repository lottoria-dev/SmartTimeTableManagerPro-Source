import copy
from collections import deque
# from config import DAYS, PERIODS_PER_DAY
import config
class AIChainedMover:
    def __init__(self, logic_instance):
        """
        :param logic_instance: TimetableLogic 클래스의 인스턴스 (데이터 접근 및 수정용)
        """
        self.logic = logic_instance
        self.max_steps = 80  # 연쇄 이동 제한 횟수

    def try_ai_move(self, start_grade, start_cls, start_day, start_period, target_day, target_period):
        """
        사용자가 요청한 초기 이동을 시작으로 AI가 연쇄 이동을 시도합니다.
        성공 시 True, 실패(횟수 초과/해법 없음) 시 롤백 후 False를 반환합니다.
        """
        # [중요] AI 동작 전 상태 저장 (Atomic Undo를 위해 전체를 하나의 트랜잭션으로 취급)
        self.logic.save_snapshot()
        
        # 1. 실패 시 복구를 위한 백업 (트랜잭션 시작 - 로직 내부 Undo가 아니라 예외 처리용)
        backup_schedule = copy.deepcopy(self.logic.schedule)
        backup_teachers = copy.deepcopy(self.logic.teachers_schedule)
        backup_logs = copy.deepcopy(self.logic.change_logs)
        backup_all_teachers = copy.deepcopy(self.logic.all_teachers)
        
        # 2. 초기 데이터 준비
        start_data = self.logic.schedule[str(start_grade)][str(start_cls)][start_day].get(int(start_period))
        if not start_data:
            self.logic.history_stack.pop() 
            return False, "이동할 수업이 없습니다.", []

        # 작업 큐
        queue = deque()
        
        # 첫 번째 이동 명령
        queue.append({
            'grade': str(start_grade), 'cls': str(start_cls),
            'subject': start_data['subject'], 'teacher': start_data['teacher'],
            'target_day': target_day, 'target_period': int(target_period),
            'source_day': start_day, 'source_period': int(start_period)
        })

        logs = []
        steps = 0
        
        # [수정] 이번 연쇄 이동에서 '새로 배정된' 위치들을 기록하여, 
        # 밀려난 수업이 방금 이동해온 수업을 다시 밀어내버리는(원위치 복귀) 현상을 방지함
        protected_slots = set()

        try:
            while queue:
                steps += 1
                if steps > self.max_steps:
                    raise Exception(f"자동 이동에 실패했습니다.(수동 모드 추천)")

                task = queue.popleft()
                g, c = task['grade'], task['cls']
                subj, teacher = task['subject'], task['teacher']
                
                if task.get('target_day') and task.get('target_period'):
                    t_day, t_period = task['target_day'], task['target_period']
                    
                    if task.get('source_day'):
                        self.logic.remove_class(g, c, task['source_day'], task['source_period'])

                    existing_data = self.logic.schedule[g][c][t_day].get(t_period)
                    if existing_data:
                        queue.append({
                            'grade': g, 'cls': c,
                            'subject': existing_data['subject'], 'teacher': existing_data['teacher'],
                            'target_day': None, 'target_period': None, 
                            'search_day': t_day
                        })
                        logs.append(f"[{steps}단계] {g}-{c} {t_day}{t_period} 기존 수업({existing_data['teacher']}) 밀려남")

                    self.logic.add_class(g, c, t_day, t_period, subj, teacher)
                    
                    # [수정] 이곳은 방금 배정되었으므로, 이번 체인 내에서 다시 밀어내기 금지
                    protected_slots.add((g, c, t_day, t_period))
                    
                    busy_locations = self.logic.get_busy_info(teacher, t_day, t_period)
                    if len(busy_locations) > 1:
                        for other_g, other_c in busy_locations:
                            if (str(other_g), str(other_c)) == (str(g), str(c)):
                                continue
                            
                            conflict_data = self.logic.remove_class(other_g, other_c, t_day, t_period)
                            if conflict_data:
                                queue.append({
                                    'grade': str(other_g), 'cls': str(other_c),
                                    'subject': conflict_data['subject'], 'teacher': conflict_data['teacher'],
                                    'target_day': None, 'target_period': None,
                                    'search_day': t_day
                                })
                                logs.append(f"[{steps}단계] {teacher} 교사 중복으로 {other_g}-{other_c} 수업 이동됨")

                else:
                    search_day = task['search_day']
                    # [수정] protected_slots 전달
                    found_day, found_period = self._find_best_slot(g, c, teacher, search_day, protected_slots)
                    
                    if found_day is None:
                         raise Exception(f"{g}-{c} {teacher} 교사의 적절한 빈 자리를 찾을 수 없습니다.")

                    queue.append({
                        'grade': g, 'cls': c,
                        'subject': subj, 'teacher': teacher,
                        'target_day': found_day, 'target_period': found_period,
                        'source_day': None 
                    })

            self.logic.change_logs.append({
                "type": "AI이동",
                "class": f"{start_grade}-{start_cls}",
                "desc": f"AI 자동 연쇄 이동 ({steps}단계 완료)",
                "log_key": ("AI_MOVE", start_grade, start_cls)
            })
            return True, f"AI 자동 이동 완료 ({steps}회 연쇄)", logs

        except Exception as e:
            # 실패 시 즉시 롤백
            self.logic.schedule = backup_schedule
            self.logic.teachers_schedule = backup_teachers
            self.logic.change_logs = backup_logs
            self.logic.all_teachers = backup_all_teachers
            
            if self.logic.history_stack:
                self.logic.history_stack.pop()
                
            return False, str(e), logs

    def _find_best_slot(self, grade, cls, teacher, target_day, protected_slots=None):
        if protected_slots is None: protected_slots = set()
        limit = config.PERIODS_PER_DAY[target_day]
        
        # 1순위: 완전 무결한 빈 자리
        for p in range(1, limit + 1):
            if not self.logic.schedule[grade][cls][target_day].get(p): # 빈 자리
                if not self.logic.is_teacher_busy(teacher, target_day, p): # 교사 공강
                    if not self.logic.check_consecutive_classes(teacher, target_day, p): # 3연강 아님
                        return target_day, p

        # 2순위: 3연강이지만 일단 빈 자리
        for p in range(1, limit + 1):
             if not self.logic.schedule[grade][cls][target_day].get(p):
                if not self.logic.is_teacher_busy(teacher, target_day, p):
                    return target_day, p
        
        # 3순위: 기존 수업이 있지만 교사는 가능한 시간 (밀어내기)
        for p in range(1, limit + 1):
             # [수정] 이번 AI 연산에서 방금 배정된 자리(protected)는 밀어내지 않음
             if (grade, cls, target_day, p) in protected_slots:
                 continue

             if not self.logic.is_locked(grade, cls, target_day, p):
                 if not self.logic.is_teacher_busy(teacher, target_day, p):
                     return target_day, p

        return None, None