import csv
import re
import base64
import json
import traceback
import copy
from collections import defaultdict
import config

class CSVManager:
    """
    CSV 파일의 입출력 및 파싱을 전담하는 클래스입니다.
    TimetableLogic 인스턴스를 받아 데이터를 주입하거나 추출합니다.
    """
    
    def __init__(self):
        pass

    def _extract_grade_class(self, val):
        """다양한 형식의 학반 문자열에서 학년과 반을 추출합니다."""
        val = str(val).strip()
        m = re.match(r'(\d+)월\s*(\d+)일', val)
        if m:
            return m.group(1).lstrip('0'), m.group(2).lstrip('0')
        m = re.match(r'(\d+)[-\.학년\s]+(\d+)반?', val)
        if m:
            return m.group(1), m.group(2)
        return None, None

    def _parse_headers_and_map(self, rows_subset):
        col_map = {}
        temp_periods = {day: 0 for day in config.DAYS}
        
        day_pattern_list = getattr(config, 'BASE_DAYS', []) + config.DAYS
        pattern_combined = re.compile(rf"({'|'.join(day_pattern_list)})(\s*)(\d+)")
        
        for i, row in enumerate(rows_subset):
            matches_count = 0
            temp_map = {}
            local_max_periods = {day: 0 for day in config.DAYS}
            
            for j, cell in enumerate(row):
                val = str(cell).strip()
                m = pattern_combined.search(val)
                if m:
                    day = m.group(1)
                    period = int(m.group(3))
                    
                    if day in getattr(config, 'BASE_DAYS', []):
                        day = f"1주 {day}"
                        
                    if day in temp_periods:
                        temp_map[j] = (day, period)
                        if period > local_max_periods[day]:
                            local_max_periods[day] = period
                        matches_count += 1
                    
            if matches_count > len(config.DAYS) / 2: 
                col_map = temp_map
                for d, p in local_max_periods.items():
                    if p > temp_periods[d]:
                        temp_periods[d] = p
                break
                
        if not col_map:
            day_map = {}
            for j, cell in enumerate(rows_subset[0]):
                val = str(cell).strip()
                day_str = val.replace("요일", "").strip()
                
                if day_str in getattr(config, 'BASE_DAYS', []):
                    day_str = f"1주 {day_str}"
                    
                if day_str in config.DAYS:
                    day_map[j] = day_str
                    
            if day_map and len(rows_subset) > 1:
                for j, cell in enumerate(rows_subset[1]):
                    val = str(cell).strip()
                    if val.isdigit():
                        period = int(val)
                        day_str = None
                        for k in range(j, -1, -1):
                            if k in day_map:
                                day_str = day_map[k]
                                break
                        if day_str:
                            col_map[j] = (day_str, period)
                            if period > temp_periods.get(day_str, 0):
                                temp_periods[day_str] = period

        return col_map, temp_periods

    def load_csv(self, file_path, logic_instance):
        try:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='cp949') as f:
                    content = f.read()
                    
            reader = list(csv.reader(content.splitlines()))

            if not reader:
                return False, "파일이 비어있습니다."

            header_rows = reader[:3]
            col_map, parsed_periods = self._parse_headers_and_map(header_rows)

            if not col_map:
                return False, "시간표 형식을 인식할 수 없습니다. 열 제목(요일/교시)을 확인해주세요."

            logic_instance.reset_data()
            config.PERIODS_PER_DAY.update(parsed_periods)

            data_rows = []
            metadata_original = None
            metadata_locked = None
            metadata_excluded = None

            for row in reader:
                if not row: continue
                first_cell = str(row[0]).strip()
                if first_cell == "#METADATA_ORIGINAL_v1":
                    try:
                        decoded = base64.b64decode(row[1]).decode('utf-8')
                        metadata_original = json.loads(decoded)
                    except: pass
                elif first_cell == "#METADATA_LOCKED_v1":
                    try:
                        decoded = base64.b64decode(row[1]).decode('utf-8')
                        metadata_locked = json.loads(decoded)
                    except: pass
                elif first_cell == "#METADATA_EXCLUDED_v1":
                    try:
                        decoded = base64.b64decode(row[1]).decode('utf-8')
                        metadata_excluded = json.loads(decoded)
                    except: pass
                else:
                    data_rows.append(row)

            i = 0
            while i < len(data_rows):
                row = data_rows[i]
                if len(row) < 2:
                    i += 1
                    continue

                grade, cls = None, None
                gc_match = self._extract_grade_class(row[0])
                if gc_match[0]:
                    grade, cls = gc_match
                else:
                    if str(row[0]).strip().isdigit() and str(row[1]).strip().isdigit():
                        grade, cls = str(row[0]).strip(), str(row[1]).strip()

                if not grade or not cls:
                    i += 1
                    continue

                is_split = False
                if i + 1 < len(data_rows):
                    next_row = data_rows[i+1]
                    if not str(next_row[0]).strip() or not self._extract_grade_class(next_row[0])[0]:
                        teacher_count = sum(1 for j, _ in col_map.items() if j < len(next_row) and str(next_row[j]).strip())
                        if teacher_count > 0:
                            newline_count = sum(1 for j, _ in col_map.items() if j < len(row) and '\n' in str(row[j]))
                            if newline_count < teacher_count:
                                is_split = True

                if is_split:
                    subj_row = row
                    teach_row = data_rows[i+1]
                    for j, (day, period) in col_map.items():
                        if j < len(subj_row) and j < len(teach_row):
                            subj = str(subj_row[j]).strip()
                            teach = str(teach_row[j]).strip()
                            if subj and teach:
                                logic_instance.add_class(grade, cls, day, period, subj, teach)
                    i += 2
                else:
                    for j, (day, period) in col_map.items():
                        if j < len(row):
                            cell_val = str(row[j]).strip()
                            if not cell_val: continue
                            
                            if '\n' in cell_val:
                                parts = cell_val.split('\n')
                                subj = parts[0].strip()
                                teach = parts[1].strip() if len(parts) > 1 else ""
                            else:
                                parts = cell_val.rsplit(' ', 1)
                                subj = parts[0].strip()
                                teach = parts[1].strip() if len(parts) > 1 else ""
                                
                            if subj and teach:
                                logic_instance.add_class(grade, cls, day, period, subj, teach)
                    i += 1

            has_w2 = any("2주" in d for d_dict in logic_instance.schedule.values() for c_dict in d_dict.values() for d in c_dict.keys())
            if not has_w2:
                if metadata_original:
                    for g in list(metadata_original.keys()):
                        for c in list(metadata_original[g].keys()):
                            old_days = list(metadata_original[g][c].keys())
                            for day in old_days:
                                if day in getattr(config, 'BASE_DAYS', []):
                                    metadata_original[g][c][f"1주 {day}"] = metadata_original[g][c].pop(day)

                source_for_w2 = metadata_original if metadata_original else logic_instance.schedule
                for g in list(logic_instance.schedule.keys()):
                    for c in list(logic_instance.schedule[g].keys()):
                        w1_days = [d for d in logic_instance.schedule[g][c].keys() if "1주" in d]
                        for day in w1_days:
                            w2_day = day.replace("1주", "2주")
                            base_day_data = source_for_w2.get(str(g), {}).get(str(c), {}).get(day)
                            if base_day_data is not None:
                                # [핵심 수정] JSON에서 복사된 데이터일 경우 교시(period) 키가 문자열이므로 정수(int)로 변환
                                converted_data = {int(k): copy.deepcopy(v) for k, v in base_day_data.items()}
                                logic_instance.schedule[g][c][w2_day] = converted_data
                            else:
                                logic_instance.schedule[g][c][w2_day] = {}
                
                if metadata_original:
                    for g in list(metadata_original.keys()):
                        for c in list(metadata_original[g].keys()):
                            for day in list(metadata_original[g][c].keys()):
                                if "1주" in day:
                                    w2_day = day.replace("1주", "2주")
                                    metadata_original[g][c][w2_day] = copy.deepcopy(metadata_original[g][c][day])
                
                if metadata_locked:
                    for item in metadata_locked:
                        if len(item) >= 3 and item[2] in getattr(config, 'BASE_DAYS', []):
                            item[2] = f"1주 {item[2]}"
                    new_locks = []
                    for item in metadata_locked:
                        if len(item) == 4 and "1주" in item[2]:
                            new_locks.append([item[0], item[1], item[2].replace("1주", "2주"), item[3]])
                    metadata_locked.extend(new_locks)
                
                if metadata_excluded:
                    old_keys = list(metadata_excluded.keys())
                    for k in old_keys:
                        if k in getattr(config, 'BASE_DAYS', []):
                            metadata_excluded[f"1주 {k}"] = metadata_excluded.pop(k)
                    new_excl = {}
                    for k, v in metadata_excluded.items():
                        new_excl[k] = v
                        if "1주" in k:
                            new_excl[k.replace("1주", "2주")] = v
                    metadata_excluded = new_excl
                    
                for day in getattr(config, 'BASE_DAYS', []):
                    config.PERIODS_PER_DAY[f"2주 {day}"] = config.PERIODS_PER_DAY.get(f"1주 {day}", 7)

            if metadata_original:
                restored_original = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
                for g, g_dict in metadata_original.items():
                    for c, c_dict in g_dict.items():
                        for day, d_dict in c_dict.items():
                            for p, p_info in d_dict.items():
                                restored_original[str(g)][str(c)][day][int(p)] = p_info
                                
                logic_instance.original_schedule = restored_original
                logic_instance.initial_schedule = copy.deepcopy(restored_original)
                logic_instance.initial_periods_per_day = copy.deepcopy(config.PERIODS_PER_DAY)
            else:
                logic_instance._set_original_state()

            if metadata_locked:
                logic_instance.locked_cells = set(tuple(x) for x in metadata_locked)
                
            if metadata_excluded:
                logic_instance.excluded_groups = {k: set(v) for k, v in metadata_excluded.items()}

            for g, g_data in logic_instance.schedule.items():
                for c, c_data in g_data.items():
                    for d, d_data in c_data.items():
                        for p, info in d_data.items():
                            teacher = info.get('teacher')
                            if teacher and logic_instance._is_valid_teacher_name(teacher):
                                logic_instance.all_teachers.add(teacher)
                                logic_instance.teachers_schedule[teacher][d][p].add((g, c))

            return True, "파일 불러오기가 완료되었습니다."
        except Exception as e:
            traceback.print_exc()
            return False, f"파일 파싱 중 오류가 발생했습니다: {str(e)}"

    def save_csv(self, file_path, logic_instance):
        try:
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                
                row1 = ["학반"]
                row2 = [""]
                
                for day in config.DAYS:
                    limit = config.PERIODS_PER_DAY.get(day, config.MAX_PERIODS)
                    row1.append(day)
                    for _ in range(limit - 1): row1.append("")
                    for p in range(1, limit + 1):
                        row2.append(str(p))
                        
                writer.writerow(row1)
                writer.writerow(row2)
                
                classes = logic_instance.get_all_sorted_classes()
                for g, c in classes:
                    row_subj = [f"{g}-{c}"]
                    row_teach = [""]
                    
                    for day in config.DAYS:
                        limit = config.PERIODS_PER_DAY.get(day, config.MAX_PERIODS)
                        for p in range(1, limit + 1):
                            data = logic_instance.schedule.get(str(g), {}).get(str(c), {}).get(day, {}).get(p)
                            if data:
                                row_subj.append(data.get('subject', ''))
                                row_teach.append(data.get('teacher', ''))
                            else:
                                row_subj.append("")
                                row_teach.append("")
                                
                    writer.writerow(row_subj)
                    writer.writerow(row_teach)
                    
                if logic_instance.original_schedule:
                    try:
                        json_str = json.dumps(logic_instance.original_schedule, ensure_ascii=False)
                        encoded_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                        writer.writerow([])
                        writer.writerow(["#METADATA_ORIGINAL_v1", encoded_str])
                    except Exception as e:
                        print(f"메타데이터 저장 실패: {e}")

                if logic_instance.locked_cells:
                    try:
                        locked_list = list(logic_instance.locked_cells)
                        json_str = json.dumps(locked_list, ensure_ascii=False)
                        encoded_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                        writer.writerow(["#METADATA_LOCKED_v1", encoded_str])
                    except Exception as e:
                        print(f"잠금 데이터 저장 실패: {e}")
                        
                if hasattr(logic_instance, 'excluded_groups') and any(logic_instance.excluded_groups.values()):
                    try:
                        excluded_dict = {k: list(v) for k, v in logic_instance.excluded_groups.items()}
                        json_str = json.dumps(excluded_dict, ensure_ascii=False)
                        encoded_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                        writer.writerow(["#METADATA_EXCLUDED_v1", encoded_str])
                    except Exception as e:
                        print(f"제외 그룹 데이터 저장 실패: {e}")

            return True, "파일 저장이 완료되었습니다."
        except Exception as e:
            traceback.print_exc()
            return False, f"파일 저장 중 오류가 발생했습니다: {str(e)}"