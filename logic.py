import csv
import re
import copy
import json
import base64
import traceback
from collections import defaultdict
import config

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
        self.history_stack = [] # 실행 취소(Undo)를 위한 스택
        
        # locked_cells: set of (grade, class, day, period)
        self.locked_cells = set()
    
    def _update_config_from_headers(self, rows_subset):
        """[최종] 헤더를 분석하여 요일별 교시 수를 동적으로 config에 업데이트합니다."""
        temp_periods = {day: 0 for day in config.DAYS}
        
        # 1. 단일 행 패턴 (예: 월1, 화1)
        pattern_combined = re.compile(f"({'|'.join(config.DAYS)})(\\d+)")
        
        header_found = False
        
        for i, row in enumerate(rows_subset):
            # Case 1: 단일 행 분석
            match = pattern_combined.search(str(row))
            if match:
                for cell in row:
                    m = pattern_combined.search(str(cell))
                    if m:
                        d, p = m.group(1), int(m.group(2))
                        if p > temp_periods[d]: temp_periods[d] = p
                header_found = True
                break
            
            # Case 2: 2단 행 분석 (윗줄 요일, 아랫줄 숫자)
            days_indices = {}
            for col_idx, cell in enumerate(row):
                cell_clean = str(cell).strip()
                if cell_clean in config.DAYS:
                    days_indices[cell_clean] = col_idx
            
            if days_indices and (i + 1 < len(rows_subset)):
                next_row = rows_subset[i+1]
                sorted_days = sorted(days_indices.keys(), key=lambda k: days_indices[k])
                
                for d_idx, day in enumerate(sorted_days):
                    start_col = days_indices[day]
                    if d_idx + 1 < len(sorted_days):
                        end_col = days_indices[sorted_days[d_idx+1]]
                    else:
                        end_col = len(next_row)
                    
                    max_p = 0
                    for c in range(start_col, end_col):
                        if c < len(next_row):
                            val = str(next_row[c]).strip()
                            if val.isdigit():
                                p = int(val)
                                if p > max_p: max_p = p
                    if max_p > 0: temp_periods[day] = max_p
                
                header_found = True
                break

        if header_found:
            current_max = max(temp_periods.values()) if temp_periods else 0
            if current_max > 0:
                config.PERIODS_PER_DAY.update(temp_periods)
                config.MAX_PERIODS = current_max
    
    
    def reset_data(self):
        """데이터 완전 삭제 (파일 로드 전 상태)"""
        self.schedule.clear()
        self.teachers_schedule.clear()
        self.all_teachers.clear()
        self.original_schedule = None
        self.change_logs = []
        self.history_stack = []
        self.locked_cells.clear()

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
        self.history_stack = [] # 히스토리도 초기화
        self.locked_cells.clear() 
        
        for grade, g_data in self.schedule.items():
            for cls, c_data in g_data.items():
                for day, d_data in c_data.items():
                    for period, info in d_data.items():
                        teacher = info.get('teacher')
                        if teacher and self._is_valid_teacher_name(teacher):
                            self.all_teachers.add(teacher)
                            self.teachers_schedule[teacher][day][period].add((grade, cls))
        return True

    def _set_original_state(self):
        self.original_schedule = copy.deepcopy(self.schedule)

    def save_snapshot(self):
        """
        현재 상태를 히스토리 스택에 저장합니다. 
        데이터 변경 직전에 호출해야 합니다.
        """
        snapshot = {
            'schedule': copy.deepcopy(self.schedule),
            'teachers_schedule': copy.deepcopy(self.teachers_schedule),
            'all_teachers': copy.deepcopy(self.all_teachers),
            'change_logs': copy.deepcopy(self.change_logs),
            'locked_cells': copy.deepcopy(self.locked_cells)
        }
        self.history_stack.append(snapshot)
        # 메모리 관리를 위해 히스토리가 너무 쌓이면(예: 100단계) 앞부분 삭제 가능
        if len(self.history_stack) > 100:
            self.history_stack.pop(0)

    def undo(self):
        """
        가장 최근 상태로 되돌립니다.
        복구에 성공하면 True, 히스토리가 비어있으면 False 반환
        """
        if not self.history_stack:
            return False
        
        last_state = self.history_stack.pop()
        self.schedule = last_state['schedule']
        self.teachers_schedule = last_state['teachers_schedule']
        self.all_teachers = last_state['all_teachers']
        self.change_logs = last_state['change_logs']
        self.locked_cells = last_state['locked_cells']
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
        """현재 상태와 원본 상태를 비교하여 스마트한 변경 목록(Diff) 생성"""
        if self.original_schedule is None:
            return []

        logs = []
        # 모든 학년/반 순회
        all_grades = set(self.schedule.keys()) | set(self.original_schedule.keys())
        sorted_grades = sorted(list(all_grades), key=lambda x: int(x) if x.isdigit() else x)

        for grade in sorted_grades:
            cls_keys = set(self.schedule[grade].keys()) | set(self.original_schedule.get(grade, {}).keys())
            sorted_cls = sorted(list(cls_keys), key=lambda x: int(x) if x.isdigit() else x)
            
            for cls in sorted_cls:
                # 해당 학반의 원본/현재 수업 리스트 추출
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

                # 1. 변경 없는 항목 제거 (완전 일치)
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
                            continue # 변경 없음
                        else:
                            unmatched_orig.append(o)
                            unmatched_curr.append(c)
                    elif o:
                        unmatched_orig.append(o)
                    elif c:
                        unmatched_curr.append(c)
                
                # 2. 이동(Move) 감지: 같은 과목/교사가 다른 시간대에 있는 경우
                # 원본 리스트를 순회하며 현재 리스트에서 위치 찾기
                temp_logs = []
                
                # 리스트 수정을 위해 복사본 사용 대신 인덱스로 처리하거나 pop 사용
                u_orig = unmatched_orig[:]
                u_curr = unmatched_curr[:]
                
                i = 0
                while i < len(u_orig):
                    o = u_orig[i]
                    found_idx = -1
                    # 현재 리스트에서 동일한 선생님/과목 찾기
                    for j, c in enumerate(u_curr):
                        if c['subject'] == o['subject'] and c['teacher'] == o['teacher']:
                            found_idx = j
                            break
                    
                    if found_idx != -1:
                        # 이동 발견
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
                
                # 3. 보강/변경 감지 (같은 시간대, 다른 내용)
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
                            "raw": None
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

        # 5. [고급] 상호 교환(Swap) 병합 로직
        # "A -> B 이동" 과 "B -> A 이동" 이 같은 반에 있다면 "교체"로 표시
        final_logs = []
        skip_indices = set()
        
        for i in range(len(logs)):
            if i in skip_indices: continue
            log1 = logs[i]
            
            matched = False
            if log1['type'] == "이동" and log1.get('raw'):
                # 짝을 찾는다
                for j in range(i + 1, len(logs)):
                    if j in skip_indices: continue
                    log2 = logs[j]
                    if log2['class'] == log1['class'] and log2['type'] == "이동" and log2.get('raw'):
                        r1 = log1['raw']
                        r2 = log2['raw']
                        # 서로 위치가 크로스되는지 확인
                        if r1['from'] == r2['to'] and r1['to'] == r2['from']:
                            # 교체 발견!
                            d1, p1 = r1['from']
                            d2, p2 = r1['to']
                            t1 = r1['teacher']
                            t2 = r2['teacher']
                            
                            final_logs.append({
                                "type": "교체",
                                "class": log1['class'],
                                "desc": f"{d1}{p1}({t1}) ↔ {d2}{p2}({t2})"
                            })
                            skip_indices.add(j)
                            matched = True
                            break
            
            if not matched:
                final_logs.append(log1)

        return final_logs

    def toggle_lock(self, grade, cls, day, period):
        # 잠금 기능은 undo 대상 아님 (UI 상태)
        key = (str(grade), str(cls), day, int(period))
        if key in self.locked_cells:
            self.locked_cells.remove(key)
            return False # Unlocked
        else:
            self.locked_cells.add(key)
            return True # Locked

    def is_locked(self, grade, cls, day, period):
        return (str(grade), str(cls), day, int(period)) in self.locked_cells

    def _is_valid_teacher_name(self, name):
        """
        유효한 교사 이름인지 검사합니다.
        - 숫자만 있는 경우 False
        - 특수문자만 있는 경우(한글, 영어, 숫자가 하나도 없는 경우) False
        """
        if not name: return False
        name = str(name).strip()
        if not name: return False
        
        # 1. 숫자만 있는 경우 제외 (예: "1", "123")
        if re.match(r'^\d+$', name):
            return False
            
        # 2. 유효 문자(한글, 영문, 숫자)가 하나도 없는 경우 제외 (예: "-", "**")
        if not re.search(r'[0-9a-zA-Z가-힣]', name):
            return False
            
        return True

    def add_class(self, grade, cls, day, period, subject, teacher):
        # add_class는 저수준 함수이므로 여기서 snapshot을 찍지 않습니다.
        # 상위 레벨(gui/ai_mover)에서 트랜잭션 단위로 찍습니다.
        grade, cls = str(grade), str(cls)
        period = int(period)
        
        if self.schedule[grade][cls][day].get(period):
            self.remove_class(grade, cls, day, period)

        self.schedule[grade][cls][day][period] = {
            "subject": subject,
            "teacher": teacher
        }
        
        # [수정] 유효한 교사명일 때만 관리 목록(충돌 체크용)에 추가
        if teacher and self._is_valid_teacher_name(teacher):
            self.teachers_schedule[teacher][day][period].add((grade, cls))
            self.all_teachers.add(teacher)

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
        return info

    def import_school_csv(self, file_path):
        self.reset_data()
        try:
            # [기존 코드 유지] 파일 인코딩 확인 및 읽기
            encodings = ['utf-8-sig', 'cp949', 'euc-kr']
            rows = []
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        reader = csv.reader(f)
                        rows = list(reader) # 여기서 rows가 채워집니다.
                    break
                except UnicodeDecodeError:
                    continue
            
            if not rows: return False, "파일을 읽을 수 없습니다. (인코딩 오류)"

            # [▼▼▼ 수정된 호출 코드 ▼▼▼]
            # 상위 10줄 정도를 통째로 넘겨서 분석시킵니다.
            self._update_config_from_headers(rows[:10])
            # [▲▲▲ 수정 끝 ▲▲▲]

            # [2. 컬럼 매핑 생성 (기존과 동일하게 유지하되 config. 사용 필수)]
            col_map = []
            current_col = 1
            
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day] # config. 확인!
                for p in range(1, limit + 1):
                    col_map.append((day, p, current_col))
                    current_col += 1

            class_pattern = re.compile(r'(\d+)\s*-\s*(\d+)')
            count = 0
            
            imported_original_json_str = None
            
            i = 0
            while i < len(rows):
                row = rows[i]
                if not row:
                    i += 1
                    continue
                
                cell_val = str(row[0]).strip()
                
                # [메타데이터 감지 로직 추가]
                if cell_val == "#METADATA_ORIGINAL_v1" and len(row) > 1:
                    try:
                        encoded_str = row[1]
                        json_str = base64.b64decode(encoded_str).decode('utf-8')
                        imported_original_json_str = json_str
                    except Exception:
                        print("메타데이터 로드 실패")
                    i += 1
                    continue

                match = class_pattern.match(cell_val)
                if match:
                    grade, cls = match.groups()
                    subj_row = row
                    teach_row = []
                    if i + 1 < len(rows):
                        teach_row = rows[i+1]
                    for day, period, col_idx in col_map:
                        subject = ""
                        teacher = ""
                        if col_idx < len(subj_row): subject = str(subj_row[col_idx]).strip()
                        if col_idx < len(teach_row): teacher = str(teach_row[col_idx]).strip()
                        if subject:
                            self.add_class(grade, cls, day, period, subject, teacher)
                    count += 1
                    i += 2 
                else:
                    i += 1 

            if count == 0: return False, "학반 정보(예: 1-1)를 찾을 수 없습니다."
            
            # 메타데이터가 있으면 복원, 없으면 현재 상태를 원본으로 설정
            if imported_original_json_str:
                try:
                    self._deserialize_original_schedule(imported_original_json_str)
                except Exception:
                    self._set_original_state() # 실패 시 현재 상태를 원본으로
            else:
                self._set_original_state()
                
            return True, f"총 {count}개 학급의 시간표를 불러왔습니다."
        except Exception as e:
            traceback.print_exc()
            return False, f"오류 발생: {str(e)}"
    
    def export_csv(self, file_path):
        """현재 시간표 데이터를 CSV로 내보내기 (재import 가능한 포맷 + 메타데이터 포함)"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Header Generation
                header = ["학반"]
                for day in config.DAYS:
                    limit = config.PERIODS_PER_DAY[day]
                    for p in range(1, limit + 1):
                        header.append(f"{day}{p}")
                writer.writerow(header)
                
                # Data Rows (Sorted by Grade, Class)
                classes = self.get_all_sorted_classes()
                for g, c in classes:
                    row_subj = [f"{g}-{c}"]
                    row_teach = [""]
                    
                    for day in config.DAYS:
                        limit = config.PERIODS_PER_DAY[day]
                        for p in range(1, limit + 1):
                            data = self.schedule[str(g)][str(c)][day].get(p)
                            if data:
                                row_subj.append(data['subject'])
                                row_teach.append(data['teacher'])
                            else:
                                row_subj.append("")
                                row_teach.append("")
                    
                    writer.writerow(row_subj)
                    writer.writerow(row_teach)
                
                # [메타데이터 저장] 원본 스케줄(초기 상태)을 숨김 데이터로 저장
                # 이것이 있어야 나중에 불러왔을 때 '수정됨(노란색)' 상태를 유지할 수 있음
                if self.original_schedule:
                    try:
                        # 1. JSON 직렬화
                        json_str = json.dumps(self.original_schedule, ensure_ascii=False)
                        # 2. Base64 인코딩 (CSV 포맷 훼손 방지)
                        encoded_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                        
                        # 별도 행에 기록
                        writer.writerow([])
                        writer.writerow(["#METADATA_ORIGINAL_v1", encoded_str])
                    except Exception as e:
                        print(f"메타데이터 저장 실패: {e}")

            return True, "파일 저장이 완료되었습니다."
        except Exception as e:
            return False, f"저장 실패: {str(e)}"

    def _deserialize_original_schedule(self, json_str):
        """JSON 문자열을 원본 스케줄로 복원 (Key 타입 변환 포함)"""
        data = json.loads(json_str)
        # JSON은 키가 모두 문자열이 되므로, period(교시) 키를 int로 변환해야 함
        
        self.original_schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        
        for grade, g_data in data.items():
            for cls, c_data in g_data.items():
                for day, d_data in c_data.items():
                    for period_str, info in d_data.items():
                        self.original_schedule[grade][cls][day][int(period_str)] = info

    def is_teacher_busy(self, teacher, day, period, ignore_grade=None, ignore_class=None):
        if not teacher: return False
        locations = self.teachers_schedule[teacher][day][period] # Set of (g, c)
        if not locations: return False
        
        count = 0
        for g, c in locations:
            if str(g) == str(ignore_grade) and str(c) == str(ignore_class):
                continue
            count += 1
        return count > 0

    def is_conflicted(self, teacher, day, period):
        if not teacher: return False
        locations = self.teachers_schedule[teacher][day][period]
        return len(locations) > 1

    def get_busy_info(self, teacher, day, period):
        if teacher in self.teachers_schedule:
             return list(self.teachers_schedule[teacher][day][period])
        return []

    def check_consecutive_classes(self, teacher, day, target_period):
        """
        해당 교사가 target_period를 포함하여 3교시 이상 연속 수업을 하는지 확인합니다.
        (단순히 하루에 3연강이 있는지 확인하는 것이 아니라, target_period가 그 연강의 일부인지 확인)
        """
        if not teacher: return False
        
        limit = config.PERIODS_PER_DAY[day]
        # 1. 스케줄 비트맵 생성 (1교시 ~ 마지막 교시)
        is_busy_list = []
        for p in range(1, limit + 1):
            busy = False
            # 실제 스케줄 확인
            if self.teachers_schedule[teacher][day][p]: 
                busy = True
            # 시뮬레이션: target_period는 사용 중이라고 가정
            if p == target_period:
                busy = True
            is_busy_list.append(busy)

        # 2. target_period (index = target_period - 1) 를 포함하는 연속 구간 찾기
        target_idx = target_period - 1
        
        # 만약 target_period 자체가 수업이 아니면(그럴리 없지만 로직상) False
        if not is_busy_list[target_idx]:
            return False
            
        # 앞쪽으로 확장
        start = target_idx
        while start > 0 and is_busy_list[start - 1]:
            start -= 1
            
        # 뒤쪽으로 확장
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
        # 변경 전 상태 저장
        self.save_snapshot()
        
        grade, cls = str(grade), str(cls)
        p1, p2 = int(p1), int(p2)
        data1 = self.schedule[grade][cls][d1].get(p1)
        data2 = self.schedule[grade][cls][d2].get(p2)
        info1 = data1.copy() if data1 else None
        info2 = data2.copy() if data2 else None
        
        # 로그는 내부 Undo 스택이 아닌 diff 표시용으로 유지
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

    def update_teacher(self, grade, cls, day, period, new_teacher):
        # 변경 전 상태 저장
        self.save_snapshot()
        
        grade, cls = str(grade), str(cls)
        period = int(period)
        
        current_data = self.schedule[grade][cls][day].get(period)
        old_teacher = current_data['teacher'] if current_data else "공강"
        subject = current_data['subject'] if current_data else "보강"
        
        log_msg = f"{day}{period}: {old_teacher} → {new_teacher}"
        self.change_logs.append({
            "type": "보강",
            "class": f"{grade}-{cls}",
            "desc": log_msg,
            "log_key": ("COVER", grade, cls, day, period)
        })

        self.remove_class(grade, cls, day, period)
        self.add_class(grade, cls, day, period, subject, new_teacher)

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