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
            headers = ["교사(주교과)"]
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    headers.append(f"{day}{p}")
            
            teachers = self.mw.logic.get_all_teachers_sorted_by_subject()
            
            # [수정] "변경된 항목만 보기" 활성화 시 필터링 적용
            if hasattr(self.mw, 'chk_only_changed') and self.mw.chk_only_changed.isChecked():
                changed_set = self.mw.grid_renderer.get_changed_teachers()
                teachers = [t for t in teachers if t in changed_set]
                if not teachers:
                    QMessageBox.warning(self.mw, "알림", "복사할 변경된 교사 데이터가 없습니다.")
                    return

            for teacher in teachers:
                subj = self.mw.logic.get_teacher_primary_subject(teacher)
                row_items = [f"{teacher} ({subj})" if subj else teacher]
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