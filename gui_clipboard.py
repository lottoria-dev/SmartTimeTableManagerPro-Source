import config
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QMimeData

class ClipboardManager:
    """엑셀 및 클립보드 복사 관련 로직을 분리한 클래스"""
    def __init__(self, main_window):
        self.mw = main_window

    def copy_to_clipboard(self):
        if not self.mw.logic.schedule:
            self.mw.status_bar.setText("⚠️ 복사할 데이터가 없습니다.")
            return

        headers = []
        data_rows = []

        if self.mw.view_mode == "ALL_WEEK":
            headers = ["학반"]
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    headers.append(f"{day}{p}")
            
            classes = self.mw.logic.get_all_sorted_classes()
            
            # [수정] "변경된 항목만 보기" 활성화 시 필터링 적용
            if hasattr(self.mw, 'chk_only_changed') and self.mw.chk_only_changed.isChecked():
                changed_set = self.mw.grid_renderer.get_changed_classes()
                classes = [cls for cls in classes if (str(cls[0]), str(cls[1])) in changed_set]
                if not classes:
                    QMessageBox.warning(self.mw, "알림", "복사할 변경된 학급 데이터가 없습니다.")
                    return

            for g, c in classes:
                row_items = [f"{g}-{c}"]
                for day in config.DAYS:
                    limit = config.PERIODS_PER_DAY[day]
                    for p in range(1, limit + 1):
                        data = self.mw.logic.schedule[str(g)][str(c)][day].get(p)
                        if data:
                            row_items.append(f"{data['subject']} ({data['teacher']})")
                        else:
                            row_items.append("")
                data_rows.append(row_items)

        elif self.mw.view_mode == "ALL_DAY":
            target_day = self.mw.combo_sel.currentText() if hasattr(self.mw, 'combo_sel') else config.DAYS[0]
            if not target_day: return
            
            headers = ["학반"]
            limit = config.PERIODS_PER_DAY[target_day]
            for p in range(1, limit + 1):
                headers.append(f"{p}교시")
            
            classes = self.mw.logic.get_all_sorted_classes()
            for g, c in classes:
                row_items = [f"{g}-{c}"]
                for p in range(1, limit + 1):
                    data = self.mw.logic.schedule[str(g)][str(c)][target_day].get(p)
                    if data:
                        row_items.append(f"{data['subject']} ({data['teacher']})")
                    else:
                        row_items.append("")
                data_rows.append(row_items)
        
        elif self.mw.view_mode == "ALL_TEACHER":
            headers = ["교사(주교과, 시수)"]
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    headers.append(f"{day}{p}")
            
            # [수정] 콤보박스에서 선택된 정렬 방식 적용
            sort_mode = getattr(self.mw, 'teacher_sort_mode', "과목순")
            teachers = self.mw.logic.get_sorted_teachers(sort_mode)
            
            # [수정] "변경된 항목만 보기" 활성화 시 필터링 적용
            if hasattr(self.mw, 'chk_only_changed') and self.mw.chk_only_changed.isChecked():
                changed_set = self.mw.grid_renderer.get_changed_teachers()
                teachers = [t for t in teachers if t in changed_set]
                if not teachers:
                    QMessageBox.warning(self.mw, "알림", "복사할 변경된 교사 데이터가 없습니다.")
                    return

            for teacher in teachers:
                subj = self.mw.logic.get_teacher_primary_subject(teacher)
                count = self.mw.logic.get_teacher_class_count(teacher)
                
                if subj:
                    base_name = f"{teacher} ({subj}, {count}h)"
                else:
                    base_name = f"{teacher} ({count}h)"
                    
                row_items = [base_name]
                for day in config.DAYS:
                    limit = config.PERIODS_PER_DAY[day]
                    for p in range(1, limit + 1):
                        locations = list(self.mw.logic.teachers_schedule.get(teacher, {}).get(day, {}).get(p, set()))
                        if locations:
                            g, c = locations[0]
                            data = self.mw.logic.schedule[str(g)][str(c)][day].get(p)
                            subj_name = data['subject'] if data else ""
                            row_items.append(f"{g}-{c} ({subj_name})")
                        else:
                            row_items.append("")
                data_rows.append(row_items)
        
        elif self.mw.view_mode in ["SINGLE", "TEACHER", "SUBJECT"]:
            headers = ["교시"] + config.DAYS
            target_val = self.mw.combo_sel.currentText()
            
            for p in range(1, config.MAX_PERIODS + 1):
                row_items = [f"{p}교시"]
                for day in config.DAYS:
                    if p > config.PERIODS_PER_DAY[day]:
                        row_items.append("")
                        continue

                    content = ""
                    if self.mw.view_mode == "SINGLE":
                        try:
                            g, c = target_val.split('-')
                            data = self.mw.logic.schedule[g][c][day].get(p)
                            if data: content = f"{data['subject']} ({data['teacher']})"
                        except: pass
                    elif self.mw.view_mode == "TEACHER":
                         if target_val in self.mw.logic.teachers_schedule:
                            if day in self.mw.logic.teachers_schedule[target_val]:
                                if p in self.mw.logic.teachers_schedule[target_val][day]:
                                    class_set = self.mw.logic.teachers_schedule[target_val][day][p]
                                    if class_set:
                                        info = list(class_set)[0]
                                        content = f"{info[0]}-{info[1]} ({self.mw.logic.schedule[str(info[0])][str(info[1])][day][p]['subject']})"
                    elif self.mw.view_mode == "SUBJECT":
                        matches = []
                        classes = self.mw.logic.get_all_sorted_classes()
                        for g, c in classes:
                            info = self.mw.logic.schedule[str(g)][str(c)][day].get(p)
                            if info and self.mw.is_subject_similar(info.get('subject'), target_val):
                                matches.append(f"{g}-{c}({info['teacher']})")
                        content = ", ".join(matches)
                    
                    row_items.append(content)
                data_rows.append(row_items)

        tsv_lines = ["\t".join(headers)]
        for row in data_rows:
            tsv_lines.append("\t".join(row))
        full_tsv = "\n".join(tsv_lines)

        html_parts = []
        html_parts.append('<meta charset="utf-8">') 
        html_parts.append('<table border="1" style="border-collapse: collapse;">')
        
        html_parts.append('<thead><tr>')
        for h in headers:
            html_parts.append(f'<th style="background-color: #f0f0f0; padding: 5px;">{h}</th>')
        html_parts.append('</tr></thead>')
        
        html_parts.append('<tbody>')
        for row in data_rows:
            html_parts.append('<tr>')
            for cell in row:
                safe_cell = str(cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_parts.append(f'<td style="mso-number-format:\'@\'; padding: 5px;">{safe_cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody></table>')
        
        full_html = "".join(html_parts)

        mime_data = QMimeData()
        mime_data.setText(full_tsv) 
        mime_data.setHtml(full_html) 

        QApplication.clipboard().setMimeData(mime_data)
        
        self.mw.status_bar.setText("📋 복사 완료 (엑셀 날짜 변환 방지 적용)")
        self.mw.status_bar.setStyleSheet("color: #6366f1; font-weight: bold; padding-left: 10px; font-size: 11px;")
        
        # [수정] 복사 완료 안내 팝업창 띄우기
        QMessageBox.information(
            self.mw, 
            "복사 완료", 
            "현재 화면의 데이터가 클립보드에 복사되었습니다.\n원하는 곳(엑셀, 한글 등)에 붙여넣기(Ctrl+V) 하세요."
        )

    def copy_stats_to_clipboard(self):
        logs = self.mw.logic.get_diff_list()
        if not logs:
            QMessageBox.information(self.mw, "알림", "변경된 시간표 내역이 없습니다.")
            return

        detail_headers = ["요일", "교시", "학반", "결강 교사(원수업)", "보강 교사(대체)", "변경 타입", "사유 및 비고"]
        detail_rows = []
        cover_stats = {}

        for log in logs:
            log_type = log.get('type', '')
            cls_info = log.get('class', '')
            raw = log.get('raw')

            if log_type == "보강/변경" and raw:
                day = raw.get('day', '')
                period = f"{raw.get('period', '')}교시"
                orig_t = raw.get('orig_teacher', '')
                new_t = raw.get('new_teacher', '')
                
                detail_rows.append([day, period, cls_info, orig_t, new_t, "보강", ""])
                cover_stats[new_t] = cover_stats.get(new_t, 0) + 1
                
            elif log_type == "교체" and raw:
                f = raw.get('from', {})
                t = raw.get('to', {})
                day1, p1, t1 = f.get('day', ''), f"{f.get('period', '')}교시", f.get('teacher', '')
                day2, p2, t2 = t.get('day', ''), f"{t.get('period', '')}교시", t.get('teacher', '')
                
                # 교체의 경우: 1번 위치에는 2번 교사가, 2번 위치에는 1번 교사가 들어감
                detail_rows.append([day1, p1, cls_info, t1, t2, "교환", ""])
                detail_rows.append([day2, p2, cls_info, t2, t1, "교환", ""])

            elif log_type == "이동" and raw:
                f_slot = raw.get('from', ('', ''))
                t_slot = raw.get('to', ('', ''))
                t_name = raw.get('teacher', '')
                
                day1, p1 = f_slot[0], f"{f_slot[1]}교시"
                day2, p2 = t_slot[0], f"{t_slot[1]}교시"
                
                detail_rows.append([day1, p1, cls_info, t_name, t_name, "시간 변경", f"→ {day2} {p2} (으)로 이동"])
                detail_rows.append([day2, p2, cls_info, t_name, t_name, "시간 변경", f"← {day1} {p1} 에서 이동"])

        # 요일 및 교시 기준 정렬
        day_order = {d: i for i, d in enumerate(config.DAYS)}
        def sort_key(row):
            d_idx = day_order.get(row[0], 99)
            p_idx = int(row[1].replace("교시", "")) if row[1].replace("교시", "").isdigit() else 99
            return (d_idx, p_idx, row[2])
            
        detail_rows.sort(key=sort_key)

        html_parts = ['<meta charset="utf-8">']
        tsv_lines = []

        # --- Table 1: 상세 일지 ---
        html_parts.append('<h3>1. 결보강 상세 일지 (결재용)</h3>')
        html_parts.append('<table border="1" style="border-collapse: collapse; text-align: center;">')
        html_parts.append('<thead><tr>')
        for h in detail_headers:
            html_parts.append(f'<th style="background-color: #f0f0f0; padding: 8px;">{h}</th>')
        html_parts.append('</tr></thead><tbody>')

        tsv_lines.append("1. 결보강 상세 일지 (결재용)")
        tsv_lines.append("\t".join(detail_headers))

        if not detail_rows:
            detail_rows = [["-", "-", "-", "-", "-", "-", "변경 내역 없음"]]

        for row in detail_rows:
            html_parts.append('<tr>')
            for cell in row:
                safe_cell = str(cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_parts.append(f'<td style="mso-number-format:\'@\'; padding: 5px;">{safe_cell}</td>')
            html_parts.append('</tr>')
            tsv_lines.append("\t".join(row))

        html_parts.append('</tbody></table><br><br>')
        tsv_lines.append("")
        tsv_lines.append("")

        # --- Table 2: 통계 ---
        stat_headers = ["교사명", "이번주 보강 시수 (단위: 시간)", "비고"]
        html_parts.append('<h3>2. 교사별 보강 시수 통계 (수당 지급용)</h3>')
        html_parts.append('<table border="1" style="border-collapse: collapse; text-align: center;">')
        html_parts.append('<thead><tr>')
        for h in stat_headers:
            html_parts.append(f'<th style="background-color: #f0f0f0; padding: 8px;">{h}</th>')
        html_parts.append('</tr></thead><tbody>')

        tsv_lines.append("2. 교사별 보강 시수 통계 (수당 지급용)")
        tsv_lines.append("\t".join(stat_headers))

        stat_rows = []
        for t, count in sorted(cover_stats.items(), key=lambda x: (-x[1], x[0])):
            stat_rows.append([t, str(count), ""])
            
        if not stat_rows:
            stat_rows = [["-", "0", "보강 내역 없음"]]

        for row in stat_rows:
            html_parts.append('<tr>')
            for cell in row:
                safe_cell = str(cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_parts.append(f'<td style="mso-number-format:\'@\'; padding: 5px;">{safe_cell}</td>')
            html_parts.append('</tr>')
            tsv_lines.append("\t".join(row))

        html_parts.append('</tbody></table>')

        mime_data = QMimeData()
        mime_data.setText("\n".join(tsv_lines))
        mime_data.setHtml("".join(html_parts))

        QApplication.clipboard().setMimeData(mime_data)
        
        QMessageBox.information(
            self.mw, 
            "통계 복사 완료", 
            "결보강 상세 일지 및 통계 데이터가 클립보드에 복사되었습니다.\n엑셀이나 한글 문서에 붙여넣기(Ctrl+V) 하세요."
        )