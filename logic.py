import re
import copy
import config
from collections import defaultdict
from csv_manager import CSVManager

class TimetableLogic:
    def __init__(self):
        # schedule[grade][class][day][period] = {subject, teacher}
        self.schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        
        # teachers_schedule[teacher][day][period] = {(grade, class), (grade, class)...}
        self.teachers_schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        
        self.all_teachers = set()
        self.original_schedule = None
        
        # 로그 및 실행 취소 관리
        self.change_logs = []
        self.history_stack = [] 
        
        # locked_cells: set of (grade, class, day, period)
        self.locked_cells = set()

        # CSV 관리자 인스턴스 생성
        self.csv_manager = CSVManager()

        # [v1.2.0] 변경 사항 추적 플래그
        self.is_modified = False
    
    def reset_data(self):
        """데이터 완전 삭제 (파일 로드 전 상태)"""
        self.schedule.clear()
        self.teachers_schedule.clear()
        self.all_teachers.clear()
        self.original_schedule = None
        self.change_logs = []
        self.history_stack = []
        self.locked_cells.clear()
        self.is_modified = False

    def import_school_csv(self, file_path):
        """CSV 파일을 불러옵니다. (CSVManager 위임)"""
        result, msg = self.csv_manager.load_csv(file_path, self)
        if result:
            self.is_modified = False # 불러온 직후는 변경 없음 상태
        return result, msg
    
    def export_csv(self, file_path):
        """현재 상태를 CSV로 저장합니다. (CSVManager 위임)"""
        result, msg = self.csv_manager.save_csv(file_path, self)
        if result:
            self.is_modified = False # 저장 완료 시 변경 없음 상태로 초기화
        return result, msg

    def restore_original_state(self):
        """CSV 로드 직후 상태로 복구"""
        if self.original_schedule is None:
            return False
        
        # 1. 스케줄 원복
        self.schedule = copy.deepcopy(self.original_schedule)
        
        # 2. 파생 데이터(교사 스케줄 등) 재구축
        self.teachers_schedule.clear()
        self.all_teachers.clear()
        self.change_logs = []
        self.history_stack = [] 
        self.locked_cells.clear() 
        
        for grade, g_data in self.schedule.items():
            for cls, c_data in g_data.items():
                for day, d_data in c_data.items():
                    for period, info in d_data.items():
                        teacher = info.get('teacher')
                        if teacher and self._is_valid_teacher_name(teacher):
                            self.all_teachers.add(teacher)
                            self.teachers_schedule[teacher][day][period].add((grade, cls))
        
        self.is_modified = False
        return True

    def _set_original_state(self):
        """현재 상태를 원본 상태로 설정 (CSV 로드 직후 호출됨)"""
        self.original_schedule = copy.deepcopy(self.schedule)

    def save_snapshot(self):
        """현재 상태를 히스토리 스택에 저장합니다."""
        snapshot = {
            'schedule': copy.deepcopy(self.schedule),
            'teachers_schedule': copy.deepcopy(self.teachers_schedule),
            'all_teachers': copy.deepcopy(self.all_teachers),
            'change_logs': copy.deepcopy(self.change_logs),
            'locked_cells': copy.deepcopy(self.locked_cells),
            'is_modified': self.is_modified,
            'original_schedule': copy.deepcopy(self.original_schedule),
            'periods_per_day': copy.deepcopy(config.PERIODS_PER_DAY)
        }
        self.history_stack.append(snapshot)
        if len(self.history_stack) > 100:
            self.history_stack.pop(0)

    def undo(self):
        """가장 최근 상태로 되돌립니다."""
        if not self.history_stack:
            return False
        
        last_state = self.history_stack.pop()
        self.schedule = last_state['schedule']
        self.teachers_schedule = last_state['teachers_schedule']
        self.all_teachers = last_state['all_teachers']
        self.change_logs = last_state['change_logs']
        self.locked_cells = last_state['locked_cells']
        self.is_modified = last_state['is_modified']
        
        if 'original_schedule' in last_state:
            self.original_schedule = last_state['original_schedule']
        if 'periods_per_day' in last_state:
            config.PERIODS_PER_DAY.update(last_state['periods_per_day'])
            
        return True

    def is_changed(self, grade, cls, day, period):
        if self.original_schedule is None: return False
        grade, cls = str(grade), str(cls)
        period = int(period)
        
        curr = self.schedule[grade][cls][day].get(period)
        orig_grade = self.original_schedule.get(grade, {})
        orig_cls = orig_grade.get(cls, {})
        orig_day = orig_cls.get(day, {})
        orig = orig_day.get(period)
        
        if curr == orig: return False
        if not curr and not orig: return False
        return True

    def get_diff_list(self):
        """현재 상태와 원본 상태를 비교하여 변경 목록(Diff) 생성"""
        if self.original_schedule is None:
            return []

        logs = []
        all_grades = set(self.schedule.keys()) | set(self.original_schedule.keys())
        sorted_grades = sorted(list(all_grades), key=lambda x: int(x) if x.isdigit() else x)

        for grade in sorted_grades:
            cls_keys = set(self.schedule[grade].keys()) | set(self.original_schedule.get(grade, {}).keys())
            sorted_cls = sorted(list(cls_keys), key=lambda x: int(x) if x.isdigit() else x)
            
            for cls in sorted_cls:
                def get_items(sched_dict):
                    items = []
                    if not sched_dict: return items
                    for d in config.DAYS:
                        for p in range(1, config.MAX_PERIODS + 1):
                            info = sched_dict[d].get(p)
                            if info and info.get('teacher'):
                                items.append({
                                    'day': d, 'period': p, 
                                    'subject': info['subject'], 
                                    'teacher': info['teacher']
                                })
                    return items

                orig_items = get_items(self.original_schedule.get(grade, {}).get(cls, {}))
                curr_items = get_items(self.schedule[grade][cls])

                # 1. 변경 없는 항목 제거
                orig_map = {(x['day'], x['period']): x for x in orig_items}
                curr_map = {(x['day'], x['period']): x for x in curr_items}
                all_slots = set(orig_map.keys()) | set(curr_map.keys())
                
                unmatched_orig = []
                unmatched_curr = []
                
                for slot in all_slots:
                    o = orig_map.get(slot)
                    c = curr_map.get(slot)
                    if o and c:
                        if o['subject'] == c['subject'] and o['teacher'] == c['teacher']:
                            continue 
                        else:
                            unmatched_orig.append(o)
                            unmatched_curr.append(c)
                    elif o:
                        unmatched_orig.append(o)
                    elif c:
                        unmatched_curr.append(c)
                
                # 2. 이동(Move) 감지
                temp_logs = []
                u_orig = unmatched_orig[:]
                u_curr = unmatched_curr[:]
                
                i = 0
                while i < len(u_orig):
                    o = u_orig[i]
                    found_idx = -1
                    for j, c in enumerate(u_curr):
                        if c['subject'] == o['subject'] and c['teacher'] == o['teacher']:
                            found_idx = j
                            break
                    
                    if found_idx != -1:
                        c = u_curr.pop(found_idx)
                        temp_logs.append({
                            "type": "이동",
                            "class": f"{grade}-{cls}",
                            "desc": f"{o['teacher']}({o['subject']}): {o['day']}{o['period']} → {c['day']}{c['period']}",
                            "raw": {'from': (o['day'], o['period']), 'to': (c['day'], c['period']), 'teacher': o['teacher']}
                        })
                        u_orig.pop(i)
                    else:
                        i += 1
                
                # 3. 보강/변경 감지
                u_curr_slot_map = {(x['day'], x['period']): x for x in u_curr}
                i = 0
                while i < len(u_orig):
                    o = u_orig[i]
                    slot = (o['day'], o['period'])
                    if slot in u_curr_slot_map:
                        c = u_curr_slot_map[slot]
                        u_curr.remove(c)
                        del u_curr_slot_map[slot]
                        
                        temp_logs.append({
                            "type": "보강/변경",
                            "class": f"{grade}-{cls}",
                            "desc": f"{o['day']}{o['period']}: {o['teacher']} → {c['teacher']} ({c['subject']})",
                            "raw": {
                                'day': o['day'], 
                                'period': o['period'], 
                                'orig_teacher': o['teacher'], 
                                'new_teacher': c['teacher']
                            }
                        })
                        u_orig.pop(i)
                    else:
                        i += 1
                        
                # 4. 삭제 및 추가
                for o in u_orig:
                    temp_logs.append({
                        "type": "삭제",
                        "class": f"{grade}-{cls}",
                        "desc": f"{o['day']}{o['period']}: {o['teacher']} 삭제됨",
                        "raw": None
                    })
                for c in u_curr:
                    temp_logs.append({
                        "type": "추가",
                        "class": f"{grade}-{cls}",
                        "desc": f"{c['day']}{c['period']}: {c['teacher']} 추가됨",
                        "raw": None
                    })
                    
                logs.extend(temp_logs)

        # 5. 상호 교환(Swap) 병합
        final_logs = []
        skip_indices = set()
        
        for i in range(len(logs)):
            if i in skip_indices: continue
            log1 = logs[i]
            
            matched = False
            if log1['type'] == "이동" and log1.get('raw'):
                for j in range(i + 1, len(logs)):
                    if j in skip_indices: continue
                    log2 = logs[j]
                    if log2['class'] == log1['class'] and log2['type'] == "이동" and log2.get('raw'):
                        r1 = log1['raw']
                        r2 = log2['raw']
                        if r1['from'] == r2['to'] and r1['to'] == r2['from']:
                            d1, p1 = r1['from']
                            d2, p2 = r1['to']
                            t1 = r1['teacher']
                            t2 = r2['teacher']
                            final_logs.append({
                                "type": "교체",
                                "class": log1['class'],
                                "desc": f"{d1}{p1}({t1}) ↔ {d2}{p2}({t2})",
                                "raw": {
                                    'from': {'day': d1, 'period': p1, 'teacher': t1},
                                    'to': {'day': d2, 'period': p2, 'teacher': t2}
                                }
                            })
                            skip_indices.add(j)
                            matched = True
                            break
            
            if not matched:
                final_logs.append(log1)

        return final_logs

    def toggle_lock(self, grade, cls, day, period):
        key = (str(grade), str(cls), day, int(period))
        if key in self.locked_cells:
            self.locked_cells.remove(key)
            return False 
        else:
            self.locked_cells.add(key)
            return True 

    def is_locked(self, grade, cls, day, period):
        return (str(grade), str(cls), day, int(period)) in self.locked_cells

    def _is_valid_teacher_name(self, name):
        """유효한 교사 이름인지 검사합니다."""
        if not name: return False
        name = str(name).strip()
        if not name: return False
        
        # 1. 숫자만 있는 경우 제외
        if re.match(r'^\d+$', name):
            return False
            
        # 2. 유효 문자(한글, 영문, 숫자)가 하나도 없는 경우 제외
        if not re.search(r'[0-9a-zA-Z가-힣]', name):
            return False
            
        return True

    def add_class(self, grade, cls, day, period, subject, teacher):
        grade, cls = str(grade), str(cls)
        period = int(period)
        
        if self.schedule[grade][cls][day].get(period):
            self.remove_class(grade, cls, day, period)

        self.schedule[grade][cls][day][period] = {
            "subject": subject,
            "teacher": teacher
        }
        
        if teacher and self._is_valid_teacher_name(teacher):
            self.teachers_schedule[teacher][day][period].add((grade, cls))
            self.all_teachers.add(teacher)
        
        self.is_modified = True

    def remove_class(self, grade, cls, day, period):
        grade, cls = str(grade), str(cls)
        period = int(period)
        info = self.schedule[grade][cls][day].get(period)
        if info:
            teacher = info['teacher']
            if teacher and teacher in self.teachers_schedule:
                if day in self.teachers_schedule[teacher] and period in self.teachers_schedule[teacher][day]:
                    self.teachers_schedule[teacher][day][period].discard((grade, cls))
                    if not self.teachers_schedule[teacher][day][period]:
                        del self.teachers_schedule[teacher][day][period]
            
            del self.schedule[grade][cls][day][period]
            self.is_modified = True
        return info

    def is_teacher_busy(self, teacher, day, period, ignore_grade=None, ignore_class=None):
        if not teacher: return False
        locations = self.teachers_schedule.get(teacher, {}).get(day, {}).get(period, set())
        if not locations: return False
        
        count = 0
        for g, c in locations:
            if str(g) == str(ignore_grade) and str(c) == str(ignore_class):
                continue
            count += 1
        return count > 0

    def is_conflicted(self, teacher, day, period):
        if not teacher: return False
        locations = self.teachers_schedule.get(teacher, {}).get(day, {}).get(period, set())
        return len(locations) > 1

    def get_busy_info(self, teacher, day, period):
        return list(self.teachers_schedule.get(teacher, {}).get(day, {}).get(period, set()))

    def check_consecutive_classes(self, teacher, day, target_period):
        if not teacher: return False
        
        limit = config.PERIODS_PER_DAY[day]
        is_busy_list = []
        for p in range(1, limit + 1):
            busy = False
            if self.teachers_schedule.get(teacher, {}).get(day, {}).get(p, set()): 
                busy = True
            if p == target_period:
                busy = True
            is_busy_list.append(busy)

        target_idx = target_period - 1
        
        if not is_busy_list[target_idx]:
            return False
            
        start = target_idx
        while start > 0 and is_busy_list[start - 1]:
            start -= 1
            
        end = target_idx
        while end < len(is_busy_list) - 1 and is_busy_list[end + 1]:
            end += 1
            
        streak_len = end - start + 1
        return streak_len >= 3

    def get_cover_candidates(self, day, period):
        candidates = []
        for teacher in sorted(list(self.all_teachers)):
            if self.is_teacher_busy(teacher, day, period): continue
            if self.check_consecutive_classes(teacher, day, period): continue
            candidates.append(teacher)
        
        candidates.append("특별보강(교장)")
        candidates.append("특별보강(교감)")
        return candidates

    def get_swap_candidates(self, grade, cls, src_day, src_period):
        grade, cls = str(grade), str(cls)
        src_period = int(src_period)
        src_data = self.schedule[grade][cls][src_day].get(src_period)
        if not src_data: return [] 

        src_teacher = src_data['teacher']
        candidates = []

        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY[day]
            for p in range(1, limit + 1):
                if day == src_day and p == src_period: continue
                
                target_data = self.schedule[grade][cls][day].get(p)
                target_teacher = target_data['teacher'] if target_data else None
                
                if src_teacher == target_teacher: continue
                
                if self.is_teacher_busy(src_teacher, day, p, ignore_grade=grade, ignore_class=cls): continue
                if target_teacher:
                    if self.is_teacher_busy(target_teacher, src_day, src_period, ignore_grade=grade, ignore_class=cls): continue
                
                candidates.append((day, p))
        return candidates

    def execute_swap(self, grade, cls, d1, p1, d2, p2):
        self.save_snapshot()
        
        grade, cls = str(grade), str(cls)
        p1, p2 = int(p1), int(p2)
        data1 = self.schedule[grade][cls][d1].get(p1)
        data2 = self.schedule[grade][cls][d2].get(p2)
        info1 = data1.copy() if data1 else None
        info2 = data2.copy() if data2 else None
        
        t1 = info1['teacher'] if info1 else "공강"
        t2 = info2['teacher'] if info2 else "공강"
        log_msg = f"{d1}{p1}({t1}) ↔ {d2}{p2}({t2})"
        
        self.change_logs.append({
            "type": "교체",
            "class": f"{grade}-{cls}",
            "desc": log_msg,
            "log_key": ("SWAP", grade, cls, d1, p1, d2, p2)
        })

        self.remove_class(grade, cls, d1, p1)
        self.remove_class(grade, cls, d2, p2)
        
        if info1: self.add_class(grade, cls, d2, p2, info1['subject'], info1['teacher'])
        if info2: self.add_class(grade, cls, d1, p1, info2['subject'], info2['teacher'])
        
        self.is_modified = True

    # --- [수정] update_teacher 메서드 복구 (보강 기능) ---
    def update_teacher(self, grade, cls, day, period, new_teacher):
        self.save_snapshot()
        
        grade, cls = str(grade), str(cls)
        period = int(period)
        
        old_data = self.schedule[grade][cls][day].get(period)
        if not old_data: return False
        
        old_teacher = old_data['teacher']
        subject = old_data['subject']
        
        # 1. 기존 교사의 스케줄에서 해당 수업 제거
        if old_teacher and old_teacher in self.teachers_schedule:
            if day in self.teachers_schedule[old_teacher] and period in self.teachers_schedule[old_teacher][day]:
                self.teachers_schedule[old_teacher][day][period].discard((grade, cls))
                if not self.teachers_schedule[old_teacher][day][period]:
                    del self.teachers_schedule[old_teacher][day][period]
                    
        # 2. 새로운 교사로 데이터 업데이트
        self.schedule[grade][cls][day][period]['teacher'] = new_teacher
        
        # 3. 새로운 교사의 스케줄에 추가
        if new_teacher and self._is_valid_teacher_name(new_teacher):
            self.teachers_schedule[new_teacher][day][period].add((grade, cls))
            self.all_teachers.add(new_teacher)
            
        # 4. 수동 로그 추가 (get_diff_list()에서 자동 감지하지만 안전장치)
        self.change_logs.append({
            "type": "보강/변경",
            "class": f"{grade}-{cls}",
            "desc": f"{day}{period}: {old_teacher} → {new_teacher} ({subject})",
            "log_key": ("COVER", grade, cls, day, period)
        })
        
        self.is_modified = True
        return True
    # --------------------------------------------------------

    # [개선] 특정 요일의 일과를 덮어쓸 때, 현재 변동 내역이 아닌 '기초 시간표'를 덮어쓰도록 구조 최적화
    def apply_day_routine(self, source_day, target_day):
        """특정 요일의 전체 일과를 다른 요일에 덮어씁니다. (학사일정 변경용)"""
        self.save_snapshot()
        
        classes = self.get_all_sorted_classes()
        
        # 1. 대상 요일의 기존 수업을 모두 제거
        for g, c in classes:
            for p in range(1, config.MAX_PERIODS + 1):
                if self.schedule[g][c][target_day].get(p):
                    self.remove_class(g, c, target_day, p)
                    
        # 2. 원본 요일의 '기초 시간표(original_schedule)'를 대상 요일로 복사
        for g, c in classes:
            for p in range(1, config.MAX_PERIODS + 1):
                # 기초 시간표가 존재하면 우선적으로 가져오기 (결보강 등 변동 내역 무시)
                if self.original_schedule:
                    data = self.original_schedule.get(g, {}).get(c, {}).get(source_day, {}).get(p)
                else:
                    data = self.schedule[g][c][source_day].get(p)
                    
                if data:
                    self.add_class(g, c, target_day, p, data['subject'], data['teacher'])
                    
        # 3. 결보강 통계에서 제외하기 위해 original_schedule도 함께 업데이트
        #    (학사일정 자체가 바뀐 것이므로 개별 결강/보강으로 처리하지 않음)
        if self.original_schedule is not None:
            for g, c in classes:
                if target_day in self.original_schedule.get(g, {}).get(c, {}):
                    self.original_schedule[g][c][target_day] = {}
                
                for p in range(1, config.MAX_PERIODS + 1):
                    orig_data = self.original_schedule.get(g, {}).get(c, {}).get(source_day, {}).get(p)
                    if orig_data:
                        if g not in self.original_schedule: self.original_schedule[g] = {}
                        if c not in self.original_schedule[g]: self.original_schedule[g][c] = {}
                        if target_day not in self.original_schedule[g][c]: self.original_schedule[g][c][target_day] = {}
                        self.original_schedule[g][c][target_day][p] = copy.deepcopy(orig_data)

        # 4. 요일별 최대 교시 수 동기화 (예: 7교시인 화요일에 6교시인 월요일 덮어쓰면 화면에서도 6교시로 단축)
        config.PERIODS_PER_DAY[target_day] = config.PERIODS_PER_DAY[source_day]

        self.change_logs.append({
            "type": "일과변경",
            "class": "전체",
            "desc": f"{source_day}요일 일과를 {target_day}요일로 변경 (통계 제외)",
            "log_key": ("DAY_ROUTINE", source_day, target_day)
        })
        self.is_modified = True
        return True

    def get_all_sorted_classes(self):
        classes = []
        for g in self.schedule.keys():
            for c in self.schedule[g].keys():
                classes.append((g, c))
        classes.sort(key=lambda x: (
            int(x[0]) if x[0].isdigit() else x[0], 
            int(x[1]) if x[1].isdigit() else x[1]
        ))
        return classes

    def get_all_teachers_sorted(self):
        return sorted(list(self.all_teachers))
        
    def get_teacher_primary_subject(self, teacher):
        """교사의 주 담당 교과를 추출합니다."""
        subjects = []
        for day in self.teachers_schedule.get(teacher, {}):
            for p in self.teachers_schedule.get(teacher, {}).get(day, {}):
                for g, c in self.teachers_schedule[teacher][day][p]:
                    data = self.schedule[str(g)][str(c)][day].get(p)
                    if data and data.get('subject'):
                        subjects.append(data['subject'])
        if not subjects:
            return ""
        
        # 배정된 횟수가 가장 많은 교과를 반환
        from collections import Counter
        return Counter(subjects).most_common(1)[0][0]

    def get_teacher_class_count(self, teacher):
        """해당 교사의 주당 수업 시수를 계산합니다. (교시 수 기준)"""
        count = 0
        teacher_days = self.teachers_schedule.get(teacher, {})
        for day, periods in teacher_days.items():
            for p, classes in periods.items():
                if classes:  # 실제 배정된 반(set)이 있는 경우만 카운트
                    count += 1
        return count

    def get_sorted_teachers(self, sort_type="과목순"):
        """사용자가 선택한 기준에 따라 교사 목록을 정렬하여 반환합니다."""
        teachers = self.get_all_teachers_sorted() # 기본 이름 가나다순 정렬됨
        
        if sort_type == "이름순":
            return teachers
        elif sort_type == "과목순":
            teachers.sort(key=lambda t: (self.get_teacher_primary_subject(t), t))
        elif sort_type == "시수 많은순":
            teachers.sort(key=lambda t: (-self.get_teacher_class_count(t), t))
        elif sort_type == "시수 적은순":
            teachers.sort(key=lambda t: (self.get_teacher_class_count(t), t))
            
        return teachers