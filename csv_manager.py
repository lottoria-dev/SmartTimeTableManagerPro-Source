import csv
import re
import base64
import json
import traceback
import config

class CSVManager:
    """
    CSV 파일의 입출력 및 파싱을 전담하는 클래스입니다.
    TimetableLogic 인스턴스를 받아 데이터를 주입하거나 추출합니다.
    """
    
    def __init__(self):
        pass

    def _parse_headers_and_map(self, rows_subset):
        """
        상위 행들을 분석하여 컬럼 매핑 정보를 생성하고 config를 업데이트합니다.
        
        Returns:
            col_map (dict): {column_index: (day, period)}
        """
        col_map = {}
        temp_periods = {day: 0 for day in config.DAYS}
        
        # 패턴: "월1", "화2" 등 요일+숫자 조합
        pattern_combined = re.compile(f"({'|'.join(config.DAYS)})(\\d+)")
        
        # 1. [우선순위 1] 단일 행 헤더 분석 (저장된 파일 형식: "월1", "화1"...)
        for i, row in enumerate(rows_subset):
            matches_count = 0
            temp_map = {}
            local_max_periods = {day: 0 for day in config.DAYS}
            
            for j, cell in enumerate(row):
                val = str(cell).strip()
                # "월1" 같은 패턴 매칭
                m = pattern_combined.match(val)
                if m:
                    d, p = m.group(1), int(m.group(2))
                    temp_map[j] = (d, p)
                    if p > local_max_periods[d]: local_max_periods[d] = p
                    matches_count += 1
            
            # 유효한 헤더로 판단되면 (예: 3개 이상의 매칭이 한 행에 존재)
            if matches_count >= 3:
                # Config 업데이트
                current_max = max(local_max_periods.values()) if local_max_periods else 0
                if current_max > 0:
                    config.PERIODS_PER_DAY.update(local_max_periods)
                    config.MAX_PERIODS = current_max
                return temp_map

        # 2. [우선순위 2] 분리형 헤더 분석 (1행: "월", 2행: "1") - 기존 원본 파일 형식
        day_row_idx = -1
        day_cols = {} # {day: (start_col, end_col)}
        
        # 요일 헤더 찾기
        for i, row in enumerate(rows_subset):
            found_days = []
            for j, cell in enumerate(row):
                val = str(cell).strip()
                if val in config.DAYS:
                    found_days.append((val, j))
            
            if found_days:
                day_row_idx = i
                # 요일별 컬럼 범위 추정
                sorted_days = sorted(found_days, key=lambda x: x[1])
                for k, (day, start_col) in enumerate(sorted_days):
                    if k + 1 < len(sorted_days):
                        end_col = sorted_days[k+1][1]
                    else:
                        end_col = len(row) # 마지막 요일은 끝까지
                    day_cols[day] = (start_col, end_col)
                break
        
        # 요일 헤더를 찾았다면, 그 아래에서 교시(숫자) 찾기
        if day_row_idx != -1:
            period_row_idx = day_row_idx + 1
            if period_row_idx < len(rows_subset):
                row = rows_subset[period_row_idx]
                for day, (start, end) in day_cols.items():
                    for c in range(start, end):
                        if c < len(row):
                            val = str(row[c]).strip()
                            if val.isdigit():
                                p = int(val)
                                col_map[c] = (day, p)
                                if p > temp_periods[day]: temp_periods[day] = p
        
            # Config 업데이트
            current_max = max(temp_periods.values()) if temp_periods else 0
            if current_max > 0:
                config.PERIODS_PER_DAY.update(temp_periods)
                config.MAX_PERIODS = current_max
            
            return col_map

        return {} # 매핑 실패

    def _deserialize_original_schedule(self, json_str):
        """JSON 문자열을 파싱하여 원본 스케줄 딕셔너리로 반환"""
        from collections import defaultdict
        data = json.loads(json_str)
        
        restored_schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        
        for grade, g_data in data.items():
            for cls, c_data in g_data.items():
                for day, d_data in c_data.items():
                    for period_str, info in d_data.items():
                        restored_schedule[grade][cls][day][int(period_str)] = info
        return restored_schedule

    def load_csv(self, file_path, logic_instance):
        """
        CSV 파일을 읽어 logic_instance에 데이터를 채웁니다.
        지원 형식:
        1. 분리형: 학반(1-1) | 과목 행 \n (빈칸) | 교사 행
        2. 병합형: 학년 | 반 | "과목\n교사" 셀 (학년이 병합되어 빈칸인 경우 처리)
        3. 저장본: 학반(1-1) | "월1", "월2"... 헤더
        """
        logic_instance.reset_data()
        try:
            # 파일 인코딩 확인 및 읽기
            encodings = ['utf-8-sig', 'cp949', 'euc-kr']
            rows = []
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                    break
                except UnicodeDecodeError:
                    continue
            
            if not rows: return False, "파일을 읽을 수 없습니다. (인코딩 오류)"

            # 헤더 분석 및 컬럼 매핑 생성
            col_map = self._parse_headers_and_map(rows[:10])
            if not col_map:
                 return False, "요일/교시 헤더를 찾을 수 없습니다. (올바른 시간표 양식이 아닙니다)"

            count = 0
            imported_original_json_str = None
            current_grade = None # [수정] 병합된 학년 셀 처리를 위한 상태 변수
            
            i = 0
            while i < len(rows):
                row = rows[i]
                if not row:
                    i += 1
                    continue
                
                cell_val = str(row[0]).strip()
                
                # 메타데이터 처리
                if cell_val == "#METADATA_ORIGINAL_v1" and len(row) > 1:
                    try:
                        encoded_str = row[1]
                        json_str = base64.b64decode(encoded_str).decode('utf-8')
                        imported_original_json_str = json_str
                    except Exception:
                        pass
                    i += 1
                    continue

                # 학반 정보 파싱 및 행 타입 결정
                grade, cls = None, None
                is_split_rows = False # True면 다음 행이 교사 행임
                
                # 열 데이터 추출
                val_col0 = str(row[0]).strip()
                val_col1 = str(row[1]).strip() if len(row) > 1 else ""
                
                # 패턴 1: "1-1" 형식 (분리형 또는 저장본일 확률 높음)
                match_combined = re.match(r'(\d+)\s*-\s*(\d+)', val_col0)
                
                if match_combined:
                    grade, cls = match_combined.groups()
                    current_grade = grade # 학년 컨텍스트 업데이트
                    
                    # 다음 행 확인 로직 (분리형 여부 판단)
                    if i + 1 < len(rows) and str(rows[i+1][0]).strip() == "":
                        is_split_rows = True
                
                # 패턴 2: 별도 컬럼 (병합형일 확률 높음) -> 0열:학년, 1열:반
                elif val_col1.isdigit():
                    # 반(Col 1) 정보가 숫자라면 데이터 행일 가능성 높음
                    
                    if val_col0.isdigit():
                        # 학년이 명시된 경우 (예: 1반)
                        current_grade = val_col0
                        grade = current_grade
                        cls = val_col1
                        is_split_rows = False # 별도 컬럼형은 보통 병합셀 방식
                        
                    elif val_col0 == "" and current_grade is not None:
                        # [핵심 수정] 학년이 비어있지만(병합됨) 이전 학년 정보가 있는 경우
                        grade = current_grade
                        cls = val_col1
                        is_split_rows = False
                
                if grade and cls:
                    subj_row = row
                    teach_row = None
                    
                    if is_split_rows:
                        if i + 1 < len(rows):
                            teach_row = rows[i+1]
                        i += 2
                    else:
                        i += 1
                    
                    # 데이터 추출
                    for col_idx, (day, period) in col_map.items():
                        subject = ""
                        teacher = ""
                        
                        cell_text = ""
                        if col_idx < len(subj_row):
                            cell_text = str(subj_row[col_idx]).strip()
                        
                        if is_split_rows:
                            # 분리형: 현재 행=과목, 다음 행=교사
                            subject = cell_text
                            if teach_row and col_idx < len(teach_row):
                                teacher = str(teach_row[col_idx]).strip()
                        else:
                            # 병합형: 셀 안에 "과목\n교사" 또는 그냥 "과목"
                            if '\n' in cell_text:
                                parts = cell_text.split('\n', 1)
                                subject = parts[0].strip()
                                teacher = parts[1].strip()
                            else:
                                subject = cell_text
                                # 교사가 없는 경우(자습 등)거나 과목만 있는 경우
                        
                        if subject or teacher:
                            logic_instance.add_class(grade, cls, day, period, subject, teacher)
                    count += 1
                else:
                    i += 1

            if count == 0: return False, "학반 정보(예: 1-1 또는 학년/반 열)를 찾을 수 없습니다."
            
            if imported_original_json_str:
                try:
                    restored_orig = self._deserialize_original_schedule(imported_original_json_str)
                    logic_instance.original_schedule = restored_orig
                except Exception:
                    logic_instance._set_original_state()
            else:
                logic_instance._set_original_state()
                
            return True, f"총 {count}개 학급의 시간표를 불러왔습니다."
        except Exception as e:
            traceback.print_exc()
            return False, f"오류 발생: {str(e)}"

    def save_csv(self, file_path, logic_instance):
        """
        현재 logic_instance의 상태를 CSV로 저장합니다.
        (저장은 항상 호환성이 좋은 '분리형' 포맷을 사용합니다)
        """
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
                classes = logic_instance.get_all_sorted_classes()
                for g, c in classes:
                    row_subj = [f"{g}-{c}"]
                    row_teach = [""]
                    
                    for day in config.DAYS:
                        limit = config.PERIODS_PER_DAY[day]
                        for p in range(1, limit + 1):
                            data = logic_instance.schedule[str(g)][str(c)][day].get(p)
                            if data:
                                row_subj.append(data['subject'])
                                row_teach.append(data['teacher'])
                            else:
                                row_subj.append("")
                                row_teach.append("")
                    
                    writer.writerow(row_subj)
                    writer.writerow(row_teach)
                
                # [메타데이터 저장]
                if logic_instance.original_schedule:
                    try:
                        # 1. JSON 직렬화
                        json_str = json.dumps(logic_instance.original_schedule, ensure_ascii=False)
                        # 2. Base64 인코딩
                        encoded_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                        
                        # 별도 행에 기록
                        writer.writerow([])
                        writer.writerow(["#METADATA_ORIGINAL_v1", encoded_str])
                    except Exception as e:
                        print(f"메타데이터 저장 실패: {e}")

            return True, "파일 저장이 완료되었습니다."
        except Exception as e:
            return False, f"저장 실패: {str(e)}"