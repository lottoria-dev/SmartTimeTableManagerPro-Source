from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QCheckBox, QPushButton, QSizePolicy, QApplication, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QObject, QEvent, QTimer
import config
from gui_styles import COLORS
from gui_components import ClickableFrame
from gui_grid_views import render_view
import re

class WatermarkFilter(QObject):
    def __init__(self, watermark):
        super().__init__(watermark)
        self.watermark = watermark

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            self.watermark.resize(event.size())
        return False

class GridRenderer:
    """그리드 위젯의 메모리 풀링 및 공통 기능(Core)만 담당하는 메인 렌더러"""
    def __init__(self, main_window):
        self.mw = main_window
        self.cell_pool = []
        self.header_pool = []
        self.view_caches = {}
        self.current_cache_key = None
        self.last_structural_fingerprint = None

    def _pool_widgets_from(self, container):
        if not container or not container.layout():
            return
        layout = container.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                if isinstance(widget, ClickableFrame):
                    widget.hide()
                    widget.setParent(None)
                    
                    wm = widget.findChild(QLabel, "LockWatermark")
                    if wm: 
                        wm.hide()
                        wm._is_visible = False
                    self.cell_pool.append(widget)
                elif type(widget) == QLabel and widget.objectName() not in ["DayControl", "LockWatermark"]:
                    widget.hide()
                    widget.setParent(None)
                    self.header_pool.append(widget)
                else:
                    widget.setParent(None)
                    widget.deleteLater()

    def clear_cache(self):
        for cache in self.view_caches.values():
            for container in [cache['left'], cache['right'], cache['h_left'], cache['h_right']]:
                if container:
                    self._pool_widgets_from(container)
                    container.deleteLater()
        self.view_caches.clear()
        
        for scroll in [self.mw.left_scroll, self.mw.right_scroll, self.mw.header_left_scroll, self.mw.header_right_scroll]:
            old = scroll.takeWidget()
            if old:
                self._pool_widgets_from(old)
                old.deleteLater()
                
        self.mw.cell_widget_map.clear()
        self.current_cache_key = None

    def refresh_grid(self, _=None):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            current_classes = tuple(self.mw.logic.get_all_sorted_classes())
            periods_fingerprint = tuple(config.PERIODS_PER_DAY.items())
            current_fingerprint = hash((current_classes, periods_fingerprint, tuple(config.DAYS)))
            
            if self.last_structural_fingerprint is not None and self.last_structural_fingerprint != current_fingerprint:
                self.clear_cache()
                
            self.last_structural_fingerprint = current_fingerprint

            combo_text = self.mw.combo_sel.currentText() if hasattr(self.mw, 'combo_sel') and getattr(self.mw.combo_sel, 'isVisible', lambda: False)() else ""
            pinned_day = self.mw.combo_pinned_day.currentText() if hasattr(self.mw, 'combo_pinned_day') else "고정 안함"
            only_changed = self.mw.chk_only_changed.isChecked() if hasattr(self.mw, 'chk_only_changed') else False
            
            new_cache_key = (self.mw.view_mode, combo_text, pinned_day, only_changed)

            if self.current_cache_key == new_cache_key:
                self.update_cell_visuals()
            else:
                if self.current_cache_key:
                    old_left = self.mw.left_scroll.takeWidget()
                    old_right = self.mw.right_scroll.takeWidget()
                    old_h_left = self.mw.header_left_scroll.takeWidget()
                    old_h_right = self.mw.header_right_scroll.takeWidget()
                    
                    self.view_caches[self.current_cache_key] = {
                        'left': old_left, 'right': old_right, 'h_left': old_h_left, 'h_right': old_h_right,
                        'cell_map': self.mw.cell_widget_map.copy()
                    }
                    self.current_cache_key = None

                if new_cache_key in self.view_caches:
                    cached = self.view_caches[new_cache_key]
                    self.mw.left_container = cached['left']
                    self.mw.right_container = cached['right']
                    self.mw.header_left_container = cached['h_left']
                    self.mw.header_right_container = cached['h_right']

                    self.mw.left_layout = self.mw.left_container.layout()
                    self.mw.right_layout = self.mw.right_container.layout()
                    self.mw.header_left_layout = self.mw.header_left_container.layout()
                    self.mw.header_right_layout = self.mw.header_right_container.layout()

                    self.mw.left_scroll.setWidget(self.mw.left_container)
                    self.mw.right_scroll.setWidget(self.mw.right_container)
                    self.mw.header_left_scroll.setWidget(self.mw.header_left_container)
                    self.mw.header_right_scroll.setWidget(self.mw.header_right_container)
                    
                    self.mw.cell_widget_map = cached['cell_map']
                    self.current_cache_key = new_cache_key
                    self.update_cell_visuals()

                else:
                    self.mw.cell_widget_map.clear()
                    
                    self.mw.left_container = QWidget()
                    self.mw.left_layout = QGridLayout(self.mw.left_container)
                    self.mw.left_layout.setSpacing(2)
                    self.mw.left_layout.setContentsMargins(2, 2, 2, 2)
                    
                    self.mw.right_container = QWidget()
                    self.mw.right_layout = QGridLayout(self.mw.right_container)
                    self.mw.right_layout.setSpacing(2)
                    self.mw.right_layout.setContentsMargins(2, 2, 2, 2)
                    
                    self.mw.header_left_container = QWidget()
                    self.mw.header_left_layout = QGridLayout(self.mw.header_left_container)
                    self.mw.header_left_layout.setSpacing(2)
                    self.mw.header_left_layout.setContentsMargins(2, 2, 2, 2)
                    
                    self.mw.header_right_container = QWidget()
                    self.mw.header_right_layout = QGridLayout(self.mw.header_right_container)
                    self.mw.header_right_layout.setSpacing(2)
                    self.mw.header_right_layout.setContentsMargins(2, 2, 2, 2)
                    
                    header_rows = 2 if self.mw.view_mode in ["ALL_WEEK", "ALL_DAY", "ALL_TEACHER"] else 1
                    self.mw.header_splitter.setFixedHeight(36 * header_rows + 2 * header_rows + 2)
                    
                    # [핵심] 분리된 뷰 렌더링 모듈로 위임
                    render_view(self)
                    
                    self.mw.left_layout.setColumnStretch(1000, 1)
                    self.mw.right_layout.setColumnStretch(1000, 1)
                    self.mw.header_left_layout.setColumnStretch(1000, 1)
                    self.mw.header_right_layout.setColumnStretch(1000, 1)
                    
                    self.mw.left_scroll.setWidget(self.mw.left_container)
                    self.mw.right_scroll.setWidget(self.mw.right_container)
                    self.mw.header_left_scroll.setWidget(self.mw.header_left_container)
                    self.mw.header_right_scroll.setWidget(self.mw.header_right_container)
                    
                    self.current_cache_key = new_cache_key

            show_pinned = self.mw.view_mode in ["ALL_WEEK", "ALL_TEACHER"]
            if hasattr(self.mw, 'combo_pinned_day'):
                self.mw.combo_pinned_day.setVisible(show_pinned)
                parent_layout = self.mw.combo_pinned_day.parentWidget().layout()
                if parent_layout:
                    for i in range(parent_layout.count()):
                        item = parent_layout.itemAt(i)
                        if item and item.widget() == self.mw.combo_pinned_day:
                            prev_item = parent_layout.itemAt(i - 1)
                            if prev_item and prev_item.widget() and isinstance(prev_item.widget(), QLabel):
                                prev_item.widget().setVisible(show_pinned)
                            break
            
            is_split_mode = self.mw.view_mode in ["ALL_WEEK", "ALL_TEACHER"]
            if not is_split_mode:
                self.mw.left_scroll.hide()
                self.mw.header_left_scroll.hide()
                self.mw.main_splitter.setSizes([0, 1400]) 
                self.mw.header_splitter.setSizes([0, 1400]) 
            else:
                self.mw.left_scroll.show()
                self.mw.header_left_scroll.show()
                limit = config.PERIODS_PER_DAY.get(pinned_day, 7) if pinned_day != "고정 안함" else 0
                if limit < 1 and pinned_day != "고정 안함": limit = 7
                
                if self.mw.view_mode == "ALL_TEACHER":
                    base_width = 140; col_width = 40 
                else:
                    base_width = 60; col_width = 40 
                
                if pinned_day == "고정 안함": expected_width = base_width + 10
                else: expected_width = base_width + (limit * col_width) + (limit * 2) + 20 
                self.mw.main_splitter.setSizes([expected_width, 1400])
                self.mw.header_splitter.setSizes([expected_width, 1400])
                
        finally:
            QTimer.singleShot(0, QApplication.restoreOverrideCursor)

    def get_changed_classes(self):
        changed = set()
        if not self.mw.logic.original_schedule: return changed
        classes = self.mw.logic.get_all_sorted_classes()
        for g, c in classes:
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY.get(day, 7)
                if limit < 1: limit = 7
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
                limit = config.PERIODS_PER_DAY.get(day, 7)
                if limit < 1: limit = 7
                for p in range(1, limit + 1):
                    if self.mw.logic.is_changed(g, c, day, p):
                        curr = self.mw.logic.schedule[str(g)][str(c)][day].get(p)
                        if curr and curr.get('teacher'): changed.add(curr['teacher'])
                        orig_g = self.mw.logic.original_schedule.get(str(g), {})
                        orig_c = orig_g.get(str(c), {})
                        orig_d = orig_c.get(day, {})
                        orig_p = orig_d.get(p)
                        if orig_p and orig_p.get('teacher'): changed.add(orig_p['teacher'])
        return changed    

    def update_cell_visuals(self):
        for key, cell_widget in self.mw.cell_widget_map.items():
            self._update_single_cell(cell_widget, key)

    def _update_single_cell(self, cell, key):
        is_locked_cell = False
        
        if isinstance(key, tuple) and key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            
            # [수정] 정상반(우선)과 제외된 반을 분리
            normal_locs = [loc for loc in locations if not self.mw.logic.is_excluded(loc[0], day)]
            excluded_locs = [loc for loc in locations if self.mw.logic.is_excluded(loc[0], day)]
            
            target_locs = normal_locs if normal_locs else excluded_locs
            
            bg_color = COLORS["cell_default"]
            border_color = "rgba(226, 232, 240, 0.8)" 
            border_width = 1
            text_color = COLORS["text_primary"]
            main_text, sub_text = "", ""
            real_key = None

            if target_locs:
                g, c = target_locs[0]
                data = self.mw.logic.schedule[str(g)][str(c)][day].get(period)
                if data:
                    main_text, sub_text = data['subject'], f"{g}-{c}"
                    real_key = (str(g), str(c), day, period)
                    
                    # [수정] 정상 반도 있고 제외 반도 같이 있는 경우(허용된 겹침) '*' 기호 및 색상 강조
                    if normal_locs and excluded_locs:
                        main_text += "*"
                        sub_text += "*"
                        border_color = "#10b981"; border_width = 2 # 초록색으로 허용된 겹침 표시
                    elif len(normal_locs) > 1:
                        border_color = "#ef4444"; border_width = 2
                        
                    if self.mw.logic.is_excluded(g, day):
                        bg_color = COLORS["cell_excluded"]; text_color = "#94a3b8"
                    elif self.mw.logic.is_changed(g, c, day, period):
                        bg_color = COLORS["cell_changed"]
                    if self.mw.logic.is_locked(g, c, day, period):
                        is_locked_cell = True

            if real_key and self.mw.swap_source == real_key:
                bg_color = COLORS["cell_selected"]; border_color, border_width = COLORS["accent"], 2
            elif self.mw.work_mode == "SWAP" and self.mw.swap_source:
                src_g, src_c, _, _ = self.mw.swap_source
                if real_key and (str(g), str(c)) == (src_g, src_c) and (day, period) in self.mw.swap_candidates:
                    bg_color = COLORS["cell_target"]; border_color = "#10b981"
            elif self.mw.work_mode == "CHAIN" and self.mw.chain_floating_data:
                orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
                orig_d, orig_p = self.mw.chain_floating_data['origin_time']
                floater = self.mw.chain_floating_data['teacher']
                if day == orig_d and period == orig_p and teacher_name == floater:
                    bg_color = COLORS["cell_chain_tgt"] 
                elif teacher_name == floater:
                    if real_key and not self.mw.logic.is_locked(str(g), str(c), day, period) and not self.mw.logic.is_excluded(str(g), day):
                        bg_color = COLORS["cell_target"]; border_color = "#10b981"

            if teacher_name and teacher_name in self.mw.highlighted_teachers:
                if bg_color in [COLORS["cell_default"], COLORS["cell_changed"], COLORS["cell_conflict"]]:
                    bg_color = self.mw.highlighted_teachers[teacher_name]
                    if bg_color == COLORS["cell_selected"]: border_color = COLORS["accent"]

            if teacher_name and self.mw.logic.check_consecutive_classes(teacher_name, day, period):
                text_color = "#7c3aed" 
        else:
            grade, cls, day, period = key
            grade, cls, period = str(grade), str(cls), int(period)
            data = self.mw.logic.schedule[grade][cls][day].get(period)
            
            main_text, sub_text = "", ""
            teacher_name = data['teacher'] if data else None
            
            # [수정] 해당 교사가 이 시간에 제외 학년의 다른 수업도 맡고 있는지 확인
            has_excluded_class = False
            if teacher_name:
                t_sched = self.mw.logic.teachers_schedule.get(teacher_name, {})
                if day in t_sched and period in t_sched[day]:
                    for other_g, other_c in t_sched[day][period]:
                        if (str(other_g), str(other_c)) != (str(grade), str(cls)) and self.mw.logic.is_excluded(other_g, day):
                            has_excluded_class = True
                            break

            if data:
                display_teacher = f"{teacher_name}*" if has_excluded_class else teacher_name
                if self.mw.view_mode in ["TEACHER", "ALL_TEACHER"]:
                    main_text, sub_text = data['subject'], f"{grade}-{cls}"
                else:
                    main_text, sub_text = data['subject'], display_teacher

            bg_color = COLORS["cell_default"]
            border_color = "rgba(226, 232, 240, 0.8)"
            border_width = 1
            text_color = COLORS["text_primary"]

            if self.mw.logic.is_excluded(grade, day):
                bg_color = COLORS["cell_excluded"]; text_color = "#94a3b8"
            elif self.mw.logic.is_changed(grade, cls, day, period):
                bg_color = COLORS["cell_changed"]
            if self.mw.logic.is_locked(grade, cls, day, period):
                is_locked_cell = True

            if teacher_name:
                t_sched = self.mw.logic.teachers_schedule.get(teacher_name, {})
                if day in t_sched and period in t_sched[day]:
                    # [수정] 교사 충돌 표시 시, 제외반+정상반의 허용된 겹침은 초록 테두리로 표시
                    normal_locs = [loc for loc in t_sched[day][period] if not self.mw.logic.is_excluded(loc[0], day)]
                    excluded_locs = [loc for loc in t_sched[day][period] if self.mw.logic.is_excluded(loc[0], day)]
                    if len(normal_locs) > 1:
                        border_color = "#ef4444"; border_width = 2
                    elif len(normal_locs) == 1 and excluded_locs:
                        border_color = "#10b981"; border_width = 2

            if self.mw.swap_source == key:
                bg_color = COLORS["cell_selected"]; border_color, border_width = COLORS["accent"], 2
            elif self.mw.work_mode == "SWAP" and self.mw.swap_source:
                 src_g, src_c, _, _ = self.mw.swap_source
                 if (grade, cls) == (src_g, src_c) and (day, period) in self.mw.swap_candidates:
                     bg_color = COLORS["cell_target"]; border_color = "#10b981"
            elif self.mw.work_mode == "COVER" and self.mw.selected_cell_info == key:
                bg_color = COLORS["cell_conflict"]; border_color, border_width = "#ef4444", 2
            elif self.mw.work_mode == "CHAIN" and self.mw.chain_floating_data:
                orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
                orig_d, orig_p = self.mw.chain_floating_data['origin_time']
                floater = self.mw.chain_floating_data['teacher']
                if key == (str(orig_g), str(orig_c), orig_d, orig_p):
                    bg_color = COLORS["cell_chain_tgt"]
                elif (grade, cls) == (str(orig_g), str(orig_c)):
                     if not self.mw.logic.is_locked(grade, cls, day, period) and not self.mw.logic.is_excluded(grade, day):
                         if self.mw.logic.is_teacher_busy(floater, day, period):
                             bg_color = COLORS["cell_conflict"]
                         else:
                             bg_color = COLORS["cell_target"]
                if teacher_name == floater:
                    bg_color = COLORS["cell_chain_src"]

            if teacher_name and teacher_name in self.mw.highlighted_teachers:
                 if bg_color in [COLORS["cell_default"], COLORS["cell_changed"], COLORS["cell_conflict"], COLORS["cell_excluded"]]:
                     bg_color = self.mw.highlighted_teachers[teacher_name]
                     if bg_color == COLORS["cell_selected"]: border_color = COLORS["accent"]
            if teacher_name and self.mw.logic.check_consecutive_classes(teacher_name, day, period):
                 text_color = "#7c3aed" 

        cell.set_content(main_text, sub_text, bg_color, border_color, border_width, text_color)

        watermark = cell.findChild(QLabel, "LockWatermark")
        if is_locked_cell:
            if not watermark:
                watermark = QLabel("🔒", cell)
                watermark.setObjectName("LockWatermark")
                watermark.setStyleSheet("font-size: 18px; background: transparent;")
                watermark.setAlignment(Qt.AlignmentFlag.AlignCenter)
                watermark.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                
                effect = QGraphicsOpacityEffect(watermark)
                effect.setOpacity(0.3) 
                watermark.setGraphicsEffect(effect)
                
                filter_obj = WatermarkFilter(watermark)
                cell.installEventFilter(filter_obj)
                watermark.filter_obj = filter_obj 
                watermark._is_visible = False
                
            if getattr(watermark, '_last_size', None) != cell.size():
                watermark.resize(cell.size())
                watermark._last_size = cell.size()
                
            watermark.lower()
            if not getattr(watermark, '_is_visible', False):
                watermark.show()
                watermark._is_visible = True
        else:
            if watermark:
                if getattr(watermark, '_is_visible', True):
                    watermark.hide()
                    watermark._is_visible = False

    def add_header(self, text, r, c, rowspan=1, colspan=1, font_size=None, is_pinned=None):
        if self.header_pool:
            lbl = self.header_pool.pop()
            lbl.setText(text)
        else:
            lbl = QLabel(text)
            
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setObjectName("GridHeader") # [수정] 스타일시트 적용을 위한 ObjectName
        if font_size:
            lbl.setStyleSheet(f"font-size: {font_size};")
        else:
            lbl.setStyleSheet("") # 인라인 초기화
            
        lbl.setFixedHeight(36 * rowspan + (rowspan - 1))
        
        if c == 0:
            if self.mw.view_mode == "ALL_TEACHER": lbl.setFixedWidth(140)
            else: lbl.setFixedWidth(60)
        elif colspan == 1:
            cell_width = 40 if self.mw.view_mode in ["ALL_WEEK", "ALL_TEACHER"] else 90 
            lbl.setFixedWidth(cell_width)
        
        pinned_day = "고정 안함"
        if hasattr(self.mw, 'combo_pinned_day'):
            pinned_day = self.mw.combo_pinned_day.currentText()
        is_split_mode = self.mw.view_mode in ["ALL_WEEK", "ALL_TEACHER"]

        if is_pinned is None: is_pinned = (c == 0)
        if not is_split_mode: is_pinned = False
            
        header_rows = 2 if self.mw.view_mode in ["ALL_WEEK", "ALL_DAY", "ALL_TEACHER"] else 1
        
        if r < header_rows:
            target_layout = self.mw.header_left_layout if is_pinned else self.mw.header_right_layout
            r_idx = r
        else:
            target_layout = self.mw.left_layout if is_pinned else self.mw.right_layout
            r_idx = r - header_rows
            
        target_layout.addWidget(lbl, r_idx, c, rowspan, colspan)
        lbl.show()

    def add_cell(self, grade, cls, day, period, r, c, rowspan=1, colspan=1, is_pinned=None):
        key = (str(grade), str(cls), day, int(period))
        
        if self.cell_pool:
            cell = self.cell_pool.pop()
            cell.data_key = key
        else:
            cell = ClickableFrame(key)
            # 신규 생성 시에만 시그널을 연결하여 경고 메시지 방지
            cell.clicked.connect(self.mw.interaction_handler.handle_cell_click)
            cell.right_clicked.connect(self.mw.interaction_handler.handle_right_click)
            cell.cell_dropped.connect(self.mw.interaction_handler.handle_cell_drop)
            
        self._update_single_cell(cell, key)
        
        cell.setFixedHeight(36)
        cell_width = 40 if self.mw.view_mode in ["ALL_WEEK", "ALL_TEACHER"] else 90
        cell.setFixedWidth(cell_width) 
        
        pinned_day = "고정 안함"
        if hasattr(self.mw, 'combo_pinned_day'):
            pinned_day = self.mw.combo_pinned_day.currentText()
        is_split_mode = self.mw.view_mode in ["ALL_WEEK", "ALL_TEACHER"]

        if is_pinned is None: is_pinned = (c == 0)
        if not is_split_mode: is_pinned = False
            
        header_rows = 2 if self.mw.view_mode in ["ALL_WEEK", "ALL_DAY", "ALL_TEACHER"] else 1
        target_layout = self.mw.left_layout if is_pinned else self.mw.right_layout
        r_idx = r - header_rows
        
        target_layout.addWidget(cell, r_idx, c, rowspan, colspan)
        self.mw.cell_widget_map[key] = cell
        cell.show()

    def get_base_grades(self, classes):
        unique_grades = sorted(list(set([str(g) for g, c in classes])))
        base_grades = []
        for g in unique_grades:
            m = re.search(r'\d+', g)
            if m and m.group(0) not in base_grades: base_grades.append(m.group(0))
        return base_grades

    def create_day_control_widget(self, day, base_grades):
        control_widget = QWidget()
        control_widget.setObjectName("DayControl")
        control_widget.setFixedHeight(36)
        control_widget.setMinimumWidth(10)
        control_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(6, 0, 6, 0)
        control_layout.setSpacing(4)
        
        lbl_day = QLabel(f"<b>{day}</b>")
        lbl_day.setObjectName("DayLabel")
        control_layout.addWidget(lbl_day)

        if base_grades:
            lbl_excl = QLabel("제외:")
            lbl_excl.setObjectName("ExclLabel")
            control_layout.addWidget(lbl_excl)
            
            for bg in base_grades:
                chk = QCheckBox(f"{bg}")
                chk.setObjectName("ExclCheck")
                if bg in self.mw.logic.excluded_groups.get(day, set()):
                    chk.setChecked(True)
                chk.toggled.connect(lambda checked, d=day, g=bg: self.mw.toggle_excluded_grade(d, g, checked))
                control_layout.addWidget(chk)
            
        control_layout.addStretch()
        
        btn_replace = QPushButton("🔄변경")
        btn_replace.setObjectName("ReplaceBtn")
        btn_replace.clicked.connect(lambda checked, d=day: self.mw.change_day_routine_for(d))
        control_layout.addWidget(btn_replace)
        
        return control_widget

    def _get_empty_label(self, width):
        if self.header_pool:
            empty = self.header_pool.pop()
            empty.setText("")
        else:
            empty = QLabel()
        empty.setObjectName("EmptyCell")
        empty.setStyleSheet("")
        empty.setFixedHeight(36)
        empty.setFixedWidth(width)
        return empty