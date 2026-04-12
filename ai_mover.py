import copy
from collections import deque
import config

class AIChainedMover:
    def __init__(self, logic_instance):
        self.logic = logic_instance
        self.max_steps = 200

    def try_ai_move(self, start_grade, start_cls, start_day, start_period, target_day, target_period):
        self.logic.save_snapshot()
        
        backup_schedule = copy.deepcopy(self.logic.schedule)
        backup_teachers = copy.deepcopy(self.logic.teachers_schedule)
        backup_logs = copy.deepcopy(self.logic.change_logs)
        backup_all_teachers = copy.deepcopy(self.logic.all_teachers)
        
        start_data = self.logic.schedule[str(start_grade)][str(start_cls)][start_day].get(int(start_period))
        if not start_data:
            self.logic.history_stack.pop() 
            return False, "이동할 수업이 없습니다.", []

        queue = deque()
        queue.append({
            'grade': str(start_grade), 'cls': str(start_cls),
            'subject': start_data['subject'], 'teacher': start_data['teacher'],
            'target_day': target_day, 'target_period': int(target_period),
            'source_day': start_day, 'source_period': int(start_period)
        })

        logs = []
        steps = 0
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
                    
                    # [신규] 행사 제외 학년인지 확인하여 차단
                    if self.logic.is_excluded(g, t_day):
                        raise Exception(f"{g}학년은 {t_day}요일에 제외 처리(행사 등)되어 있어 이동할 수 없습니다.")
                    
                    if self.logic.is_locked(g, c, t_day, t_period):
                        raise Exception(f"{g}-{c} {t_day}{t_period} 교시는 잠겨있어 이동할 수 없습니다.")

                    if task.get('source_day'):
                        self.logic.remove_class(g, c, task['source_day'], task['source_period'])

                    busy_locations = self.logic.get_busy_info(teacher, t_day, t_period)
                    valid_busy_locations = []
                    
                    for other_g, other_c in busy_locations:
                        # [수정] 충돌 교사의 다른 반이 제외 학년이면 충돌(밀어내기) 대상에서 제외함 (중복 허용)
                        if self.logic.is_excluded(other_g, t_day):
                            continue
                            
                        if self.logic.is_locked(other_g, other_c, t_day, t_period):
                             raise Exception(f"{teacher} 교사는 {other_g}-{other_c} {t_day}{t_period} 수업이 고정(잠금)되어 있어 중복 배정할 수 없습니다.")
                        valid_busy_locations.append((other_g, other_c))

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
                    protected_slots.add((g, c, t_day, t_period))
                    
                    if len(valid_busy_locations) >= 1: 
                        for other_g, other_c in valid_busy_locations:
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
                "type": "AI이동", "class": f"{start_grade}-{start_cls}",
                "desc": f"AI 자동 연쇄 이동 ({steps}단계 완료)",
                "log_key": ("AI_MOVE", start_grade, start_cls)
            })
            return True, f"AI 자동 이동 완료 ({steps}회 연쇄)", logs

        except Exception as e:
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
        
        # [신규] 해당 학년이 이 요일에 제외되었다면 빈자리 검색 즉시 실패
        if self.logic.is_excluded(grade, target_day):
            return None, None
        
        for p in range(1, limit + 1):
            if not self.logic.schedule[grade][cls][target_day].get(p):
                if not self.logic.is_teacher_busy(teacher, target_day, p):
                    if not self.logic.check_consecutive_classes(teacher, target_day, p):
                        return target_day, p

        for p in range(1, limit + 1):
            if (grade, cls, target_day, p) in protected_slots: continue
            if self.logic.schedule[grade][cls][target_day].get(p):
                if not self.logic.is_locked(grade, cls, target_day, p):
                    if not self.logic.is_teacher_busy(teacher, target_day, p):
                        if not self.logic.check_consecutive_classes(teacher, target_day, p):
                            return target_day, p

        for p in range(1, limit + 1):
             if not self.logic.schedule[grade][cls][target_day].get(p):
                if not self.logic.is_teacher_busy(teacher, target_day, p):
                    return target_day, p
        
        for p in range(1, limit + 1):
             if (grade, cls, target_day, p) in protected_slots: continue
             if not self.logic.is_locked(grade, cls, target_day, p):
                 if not self.logic.is_teacher_busy(teacher, target_day, p):
                     return target_day, p

        return None, None