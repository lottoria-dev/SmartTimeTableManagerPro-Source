from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PySide6.QtCore import Qt
import config
from gui_styles import COLORS
from gui_components import ClickableFrame

class GridRenderer:
    """화면 레이아웃 그리기 및 셀 시각화 업데이트를 분리한 클래스"""
    def __init__(self, main_window):
        self.mw = main_window

    def refresh_grid(self, _=None):
        old_widget = self.mw.scroll_area.widget()
        if old_widget: old_widget.deleteLater()
            
        self.mw.grid_container = QWidget()
        
        main_vbox = QVBoxLayout(self.mw.grid_container)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)
        
        h_box = QHBoxLayout()
        h_box.setContentsMargins(0, 0, 0, 0)
        h_box.setSpacing(0)
        
        self.mw.grid_layout = QGridLayout()
        self.mw.grid_layout.setSpacing(1)
        self.mw.grid_layout.setContentsMargins(1, 1, 1, 1)
        
        h_box.addLayout(self.mw.grid_layout)
        h_box.addStretch(1) 
        
        main_vbox.addLayout(h_box)
        main_vbox.addStretch(1) 
        
        self.mw.scroll_area.setWidget(self.mw.grid_container)
        
        self.mw.cell_widget_map.clear()
        
        if self.mw.view_mode == "ALL_WEEK": self.render_all_week()
        elif self.mw.view_mode == "ALL_DAY": self.render_all_day()
        elif self.mw.view_mode == "SINGLE": self.render_single()
        elif self.mw.view_mode == "TEACHER": self.render_teacher()
        elif self.mw.view_mode == "ALL_TEACHER": self.render_all_teacher()
        elif self.mw.view_mode == "SUBJECT": self.render_subject()

    def get_changed_classes(self):
        changed = set()
        if not self.mw.logic.original_schedule: return changed
        classes = self.mw.logic.get_all_sorted_classes()
        for g, c in classes:
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    if self.mw.logic.is_changed(g, c, day, p):
                        changed.add((str(g), str(c)))
        return changed

    def get_changed_teachers(self):
        changed = set()
        if not self.mw.logic.original_schedule: return changed
        classes = self.mw.logic.get_all_sorted_classes()
        for g, c in classes:
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    if self.mw.logic.is_changed(g, c, day, p):
                        curr = self.mw.logic.schedule[str(g)][str(c)][day].get(p)
                        if curr and curr.get('teacher'):
                            changed.add(curr['teacher'])
                        
                        orig_g = self.mw.logic.original_schedule.get(str(g), {})
                        orig_c = orig_g.get(str(c), {})
                        orig_d = orig_c.get(day, {})
                        orig_p = orig_d.get(p)
                        if orig_p and orig_p.get('teacher'):
                            changed.add(orig_p['teacher'])
        return changed    

    def update_cell_visuals(self):
        for key, cell_widget in self.mw.cell_widget_map.items():
            self._update_single_cell(cell_widget, key)

    def _update_single_cell(self, cell, key):
        if isinstance(key, tuple) and key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            
            bg_color = COLORS["cell_default"]
            border_color = "#e5e7eb"
            border_width = 1
            text_color = "#1f2937"
            main_text, sub_text = "", ""
            real_key = None

            if locations:
                g, c = locations[0]
                data = self.mw.logic.schedule[str(g)][str(c)][day].get(period)
                if data:
                    main_text, sub_text = data['subject'], f"{g}-{c}"
                    real_key = (str(g), str(c), day, period)
                    
                    if self.mw.logic.is_locked(g, c, day, period):
                        bg_color = COLORS["cell_locked"]
                        main_text = "🔒 " + main_text
                    if self.mw.logic.is_changed(g, c, day, period):
                        bg_color = COLORS["cell_changed"]
                    if len(locations) > 1:
                        border_color = "#ef4444"
                        border_width = 2

            if real_key and self.mw.swap_source == real_key:
                bg_color = COLORS["cell_selected"]
                border_color, border_width = COLORS["accent"], 2
            elif self.mw.work_mode == "SWAP" and self.mw.swap_source:
                src_g, src_c, _, _ = self.mw.swap_source
                if real_key and (str(g), str(c)) == (src_g, src_c) and (day, period) in self.mw.swap_candidates:
                    bg_color = COLORS["cell_target"]
                    border_color = "#10b981"
            elif self.mw.work_mode == "CHAIN" and self.mw.chain_floating_data:
                orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
                orig_d, orig_p = self.mw.chain_floating_data['origin_time']
                floater = self.mw.chain_floating_data['teacher']
                
                if day == orig_d and period == orig_p and teacher_name == floater:
                    bg_color = COLORS["cell_chain_tgt"] 
                elif teacher_name == floater:
                    if not self.mw.logic.is_locked(orig_g, orig_c, day, period):
                        bg_color = COLORS["cell_target"] 
                        border_color = "#10b981"

            if teacher_name and teacher_name in self.mw.highlighted_teachers:
                if bg_color in [COLORS["cell_default"], COLORS["cell_locked"], COLORS["cell_changed"], COLORS["cell_conflict"]]:
                    bg_color = self.mw.highlighted_teachers[teacher_name]
                    if bg_color == COLORS["cell_selected"]: border_color = COLORS["accent"]

            if teacher_name and self.mw.logic.check_consecutive_classes(teacher_name, day, period):
                text_color = "#9333ea" 

            cell.set_content(main_text, sub_text, bg_color, border_color, border_width, text_color)
            return
            
        grade, cls, day, period = key
        grade, cls = str(grade), str(cls)
        period = int(period)
        data = self.mw.logic.schedule[grade][cls][day].get(period)
        
        main_text, sub_text = "", ""
        teacher_name = data['teacher'] if data else None

        if data:
            if self.mw.view_mode in ["TEACHER", "ALL_TEACHER"]:
                main_text, sub_text = data['subject'], f"{grade}-{cls}"
            else:
                main_text, sub_text = data['subject'], teacher_name

        bg_color = COLORS["cell_default"]
        border_color = "#e5e7eb"
        border_width = 1
        text_color = "#1f2937" 

        if self.mw.logic.is_locked(grade, cls, day, period):
            bg_color = COLORS["cell_locked"]
            main_text = "🔒 " + main_text
        if self.mw.logic.is_changed(grade, cls, day, period):
            bg_color = COLORS["cell_changed"]

        if teacher_name:
            t_sched = self.mw.logic.teachers_schedule.get(teacher_name, {})
            if day in t_sched and period in t_sched[day]:
                if len(t_sched[day][period]) > 1:
                    border_color = "#ef4444"
                    border_width = 2

        if self.mw.swap_source == key:
            bg_color = COLORS["cell_selected"]
            border_color, border_width = COLORS["accent"], 2
        elif self.mw.work_mode == "SWAP" and self.mw.swap_source:
             src_g, src_c, _, _ = self.mw.swap_source
             if (grade, cls) == (src_g, src_c) and (day, period) in self.mw.swap_candidates:
                 bg_color = COLORS["cell_target"]
                 border_color = "#10b981"
        elif self.mw.work_mode == "COVER" and self.mw.selected_cell_info == key:
            bg_color = COLORS["cell_conflict"]
            border_color, border_width = "#ef4444", 2
        elif self.mw.work_mode == "CHAIN" and self.mw.chain_floating_data:
            orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
            orig_d, orig_p = self.mw.chain_floating_data['origin_time']
            floater = self.mw.chain_floating_data['teacher']
            if key == (str(orig_g), str(orig_c), orig_d, orig_p):
                bg_color = COLORS["cell_chain_tgt"]
            elif (grade, cls) == (str(orig_g), str(orig_c)):
                 if not self.mw.logic.is_locked(grade, cls, day, period):
                     if self.mw.logic.is_teacher_busy(floater, day, period):
                         bg_color = COLORS["cell_conflict"]
                     else:
                         bg_color = COLORS["cell_target"]
            if teacher_name == floater:
                bg_color = COLORS["cell_chain_src"]

        if teacher_name and teacher_name in self.mw.highlighted_teachers:
             if bg_color in [COLORS["cell_default"], COLORS["cell_locked"], COLORS["cell_changed"], COLORS["cell_conflict"]]:
                 bg_color = self.mw.highlighted_teachers[teacher_name]
                 if bg_color == COLORS["cell_selected"]: border_color = COLORS["accent"]

        if teacher_name and self.mw.logic.check_consecutive_classes(teacher_name, day, period):
             text_color = "#9333ea" 

        cell.set_content(main_text, sub_text, bg_color, border_color, border_width, text_color)

    # [수정] font_size 파라미터를 추가하여 특정 헤더의 텍스트 크기를 조절할 수 있도록 개선
    def add_header(self, text, r, c, rowspan=1, colspan=1, font_size=None):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_style = f"font-size: {font_size};" if font_size else ""
        lbl.setStyleSheet(f"background-color: #e5e7eb; font-weight: bold; border: 1px solid #d1d5db; color: #1f2937; {font_style}")
        lbl.setMinimumHeight(26)
        if len(text) > 4: lbl.setMinimumWidth(80) 
        else: lbl.setMinimumWidth(40)
        self.mw.grid_layout.addWidget(lbl, r, c, rowspan, colspan)

    def add_cell(self, grade, cls, day, period, r, c, rowspan=1, colspan=1):
        key = (str(grade), str(cls), day, int(period))
        cell = ClickableFrame(key)
        self._update_single_cell(cell, key)
        cell.clicked.connect(self.mw.interaction_handler.handle_cell_click)
        cell.right_clicked.connect(self.mw.interaction_handler.handle_right_click)
        # [업데이트] 드롭 시그널 연결
        cell.cell_dropped.connect(self.mw.interaction_handler.handle_cell_drop)
        self.mw.grid_layout.addWidget(cell, r, c, rowspan, colspan)
        self.mw.cell_widget_map[key] = cell

    def render_all_week(self):
        self.add_header("학반", 0, 0)
        self.mw.grid_layout.setColumnMinimumWidth(0, 50)
        
        classes = self.mw.logic.get_all_sorted_classes()
        
        if hasattr(self.mw, 'chk_only_changed') and self.mw.chk_only_changed.isChecked():
            changed_set = self.get_changed_classes()
            classes = [cls for cls in classes if (str(cls[0]), str(cls[1])) in changed_set]
            
            if not classes:
                lbl = QLabel("현재 변경된 학급 수업이 없습니다.")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #6b7280; padding: 20px;")
                self.mw.grid_layout.addWidget(lbl, 1, 0, 1, 10)
                return
        
        total_rows = len(classes) + 1  

        col = 1
        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY[day]
            for p in range(1, limit + 1):
                self.add_header(f"{day}{p}", 0, col)
                col += 1
            if day != config.DAYS[-1]:
                lbl = QLabel()
                lbl.setFixedWidth(5)
                lbl.setStyleSheet("background-color: #d1d5db;")
                self.mw.grid_layout.addWidget(lbl, 0, col, total_rows, 1)
                col += 1
        
        for r, (g, c) in enumerate(classes):
            row = r + 1
            self.add_header(f"{g}-{c}", row, 0)
            col = 1
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    self.add_cell(g, c, day, p, row, col)
                    col += 1
                if day != config.DAYS[-1]: col += 1

    def render_all_teacher(self):
        # [수정] 폰트 사이즈를 9pt로 줄이고, 제목 텍스트 간소화
        self.add_header("교사(과목,시수)", 0, 0, font_size="9pt")
        # [수정] 한 줄로 표시하기 위해 가로 폭을 충분히 넓힘 (105 -> 120)
        self.mw.grid_layout.setColumnMinimumWidth(0, 120) 
        
        # [수정] 사용자가 선택한 정렬 방식 적용
        sort_mode = getattr(self.mw, 'teacher_sort_mode', "과목순")
        teachers = self.mw.logic.get_sorted_teachers(sort_mode)
        
        if hasattr(self.mw, 'chk_only_changed') and self.mw.chk_only_changed.isChecked():
            changed_set = self.get_changed_teachers()
            teachers = [t for t in teachers if t in changed_set]
            
            if not teachers:
                lbl = QLabel("현재 변경된 교사 수업이 없습니다.")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #6b7280; padding: 20px;")
                self.mw.grid_layout.addWidget(lbl, 1, 0, 1, 10)
                return
        
        total_rows = len(teachers) + 1
        
        col = 1
        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY[day]
            for p in range(1, limit + 1):
                self.add_header(f"{day}{p}", 0, col)
                col += 1
            
            if day != config.DAYS[-1]:
                lbl = QLabel()
                lbl.setFixedWidth(5)
                lbl.setStyleSheet("background-color: #d1d5db;")
                self.mw.grid_layout.addWidget(lbl, 0, col, total_rows, 1) 
                col += 1

        for r, teacher in enumerate(teachers):
            row = r + 1
            subj = self.mw.logic.get_teacher_primary_subject(teacher)
            count = self.mw.logic.get_teacher_class_count(teacher)
            
            # [수정] 개행문자(\n)를 제거하여 한 줄로 표시 (셀 높이 축소를 통해 표시 가능 행 수 증가)
            if subj:
                display_text = f"{teacher} ({subj},{count}h)"
            else:
                display_text = f"{teacher} ({count}h)"
                
            # [수정] 폰트 크기를 1포인트(10pt -> 9pt) 줄임
            self.add_header(display_text, row, 0, font_size="9pt")
            
            col = 1
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    key = ("TEACHER_VIEW", teacher, day, p)
                    cell = ClickableFrame(key)
                    self._update_single_cell(cell, key)
                    cell.clicked.connect(self.mw.interaction_handler.handle_cell_click)
                    cell.right_clicked.connect(self.mw.interaction_handler.handle_right_click)
                    # [업데이트] 교사 뷰에서도 드롭 시그널 연결
                    cell.cell_dropped.connect(self.mw.interaction_handler.handle_cell_drop)
                    self.mw.grid_layout.addWidget(cell, row, col)
                    self.mw.cell_widget_map[key] = cell
                    col += 1
                
                if day != config.DAYS[-1]:
                    col += 1

    def render_all_day(self):
        if not hasattr(self.mw, 'combo_sel'): return
        target_day = self.mw.combo_sel.currentText()
        if not target_day: return
        self.add_header("학반", 0, 0)
        self.mw.grid_layout.setColumnMinimumWidth(0, 50)
        limit = config.PERIODS_PER_DAY[target_day]
        for p in range(1, limit + 1):
            self.add_header(f"{p}교시", 0, p)
        classes = self.mw.logic.get_all_sorted_classes()
        for r, (g, c) in enumerate(classes):
            row = r + 1
            self.add_header(f"{g}-{c}", row, 0)
            for p in range(1, limit + 1):
                self.add_cell(g, c, target_day, p, row, p)

    def render_single(self):
        if not hasattr(self.mw, 'combo_sel'): return
        cls_str = self.mw.combo_sel.currentText()
        if not cls_str: return
        try: g, c = cls_str.split('-')
        except: return
        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.mw.grid_layout.setColumnMinimumWidth(i+1, 120)
        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                if p <= config.PERIODS_PER_DAY[day]:
                    self.add_cell(g, c, day, p, p, i+1)

    def render_teacher(self):
        if not hasattr(self.mw, 'combo_sel'): return
        t_name = self.mw.combo_sel.currentText()
        if not t_name: return
        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.mw.grid_layout.setColumnMinimumWidth(i+1, 120)
        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                found = False
                if t_name in self.mw.logic.teachers_schedule:
                    if day in self.mw.logic.teachers_schedule[t_name]:
                        if p in self.mw.logic.teachers_schedule[t_name][day]:
                            class_set = self.mw.logic.teachers_schedule[t_name][day][p]
                            if class_set:
                                info = list(class_set)[0]
                                g, c = str(info[0]), str(info[1])
                                self.add_cell(g, c, day, p, p, i+1)
                                found = True
                if not found and p <= config.PERIODS_PER_DAY[day]:
                    empty = QLabel()
                    empty.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb;")
                    self.mw.grid_layout.addWidget(empty, p, i+1)

    def render_subject(self):
        if not hasattr(self.mw, 'combo_sel'): return
        subj_name = self.mw.combo_sel.currentText()
        if not subj_name: return

        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.mw.grid_layout.setColumnMinimumWidth(i+1, 120)

        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                if p <= config.PERIODS_PER_DAY[day]:
                    matches = []
                    classes = self.mw.logic.get_all_sorted_classes()
                    for g, c in classes:
                        day_sched = self.mw.logic.schedule[str(g)][str(c)].get(day, {})
                        info = day_sched.get(p)
                        if info:
                            target_subject = info.get('subject')
                            if self.mw.is_subject_similar(target_subject, subj_name):
                                matches.append(f"{g}-{c}({info['teacher']})")
                    
                    if matches:
                        lbl = QLabel("\n".join(matches))
                        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        lbl.setWordWrap(True)
                        lbl.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb; font-size: 11px; padding: 2px;")
                        self.mw.grid_layout.addWidget(lbl, p, i+1)
                    else:
                        empty = QLabel()
                        empty.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb;")
                        self.mw.grid_layout.addWidget(empty, p, i+1)