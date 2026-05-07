from PySide6.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
import config
from gui_components import ClickableFrame

def render_view(renderer):
    """모드별 화면 렌더링 알고리즘을 분기 처리하는 함수"""
    mode = renderer.mw.view_mode
    if mode == "ALL_WEEK": render_all_week(renderer)
    elif mode == "ALL_DAY": render_all_day(renderer)
    elif mode == "SINGLE": render_single(renderer)
    elif mode == "TEACHER": render_teacher(renderer)
    elif mode == "ALL_TEACHER": render_all_teacher(renderer)
    elif mode == "SUBJECT": render_subject(renderer)

def render_all_week(renderer):
    classes = renderer.mw.logic.get_all_sorted_classes()
    base_grades = renderer.get_base_grades(classes)
    
    if hasattr(renderer.mw, 'chk_only_changed') and renderer.mw.chk_only_changed.isChecked():
        changed_set = renderer.get_changed_classes()
        classes = [cls for cls in classes if (str(cls[0]), str(cls[1])) in changed_set]
        if not classes:
            lbl = QLabel("현재 변경된 학급 수업이 없습니다.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("EmptyMessage")
            # [UI 고급화] 빈 상태 메시지를 프리미엄 플로팅 카드 스타일로 변경
            lbl.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                color: #475569;
                font-size: 16px;
                font-weight: bold;
                padding: 30px;
            """)
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(20)
            effect.setXOffset(0)
            effect.setYOffset(4)
            effect.setColor(QColor(0, 0, 0, 15))
            lbl.setGraphicsEffect(effect)
            renderer.mw.right_layout.addWidget(lbl, 1, 0, 1, 10)
            return

    pinned_day = renderer.mw.combo_pinned_day.currentText() if hasattr(renderer.mw, 'combo_pinned_day') else "고정 안함"
    is_split_mode = True

    renderer.add_header("학반", 0, 0, rowspan=2, is_pinned=True)
    
    total_rows = len(classes) + 2  
    header_rows = 2

    col = 1
    for day in config.DAYS:
        limit = config.PERIODS_PER_DAY.get(day, 7)
        if limit < 1: limit = 7
        
        is_this_pinned = (day == pinned_day)
        
        control_widget = renderer.create_day_control_widget(day, base_grades)
        
        if is_this_pinned and is_split_mode:
            renderer.mw.header_left_layout.addWidget(control_widget, 0, col, 1, limit)
        else:
            renderer.mw.header_right_layout.addWidget(control_widget, 0, col, 1, limit)

        for p in range(1, limit + 1):
            renderer.add_header(str(p), 1, col, is_pinned=is_this_pinned)
            col += 1
            
        if day != config.DAYS[-1]:
            lbl_h = QLabel()
            lbl_h.setFixedWidth(4)
            lbl_h.setObjectName("SplitterLine")
            
            lbl_c = QLabel()
            lbl_c.setFixedWidth(4)
            lbl_c.setObjectName("SplitterLine")
            
            # [UI 고급화] 구분선(Splitter)을 은은한 페이드 아웃 그라데이션으로 변경하여 고급스러운 음각 효과 부여
            gradient_style = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(203, 213, 225, 0), stop:0.5 rgba(203, 213, 225, 0.8), stop:1 rgba(203, 213, 225, 0));"
            lbl_h.setStyleSheet(gradient_style)
            lbl_c.setStyleSheet(gradient_style)
            
            if is_this_pinned and is_split_mode:
                renderer.mw.header_left_layout.addWidget(lbl_h, 0, col, header_rows, 1)
                renderer.mw.left_layout.addWidget(lbl_c, 0, col, total_rows - header_rows, 1)
            else:
                renderer.mw.header_right_layout.addWidget(lbl_h, 0, col, header_rows, 1)
                renderer.mw.right_layout.addWidget(lbl_c, 0, col, total_rows - header_rows, 1)
            col += 1
    
    for r, (g, c) in enumerate(classes):
        row = r + 2 
        
        hr_teacher = renderer.mw.logic.homeroom_teachers.get(str(g), {}).get(str(c), "")
        tooltip_txt = f"담임: {hr_teacher}" if hr_teacher else ""
        
        renderer.add_header(f"{g}-{c}", row, 0, is_pinned=True, tooltip=tooltip_txt)
        
        col = 1
        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY.get(day, 7)
            if limit < 1: limit = 7
            
            is_this_pinned = (day == pinned_day)
            
            for p in range(1, limit + 1):
                renderer.add_cell(g, c, day, p, row, col, is_pinned=is_this_pinned)
                col += 1
                
            if day != config.DAYS[-1]: 
                col += 1

def render_all_teacher(renderer):
    pinned_day = renderer.mw.combo_pinned_day.currentText() if hasattr(renderer.mw, 'combo_pinned_day') else "고정 안함"
    is_split_mode = True

    renderer.add_header("교사(과목,시수)", 0, 0, rowspan=2, font_size="9pt", is_pinned=True)
    
    sort_mode = getattr(renderer.mw, 'teacher_sort_mode', "과목순")
    teachers = renderer.mw.logic.get_sorted_teachers(sort_mode)
    
    if hasattr(renderer.mw, 'chk_only_changed') and renderer.mw.chk_only_changed.isChecked():
        changed_set = renderer.get_changed_teachers()
        teachers = [t for t in teachers if t in changed_set]
        
        if not teachers:
            lbl = QLabel("현재 변경된 교사 수업이 없습니다.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("EmptyMessage")
            lbl.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                color: #475569;
                font-size: 16px;
                font-weight: bold;
                padding: 30px;
            """)
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(20)
            effect.setXOffset(0)
            effect.setYOffset(4)
            effect.setColor(QColor(0, 0, 0, 15))
            lbl.setGraphicsEffect(effect)
            renderer.mw.right_layout.addWidget(lbl, 1, 0, 1, 10)
            return
    
    total_rows = len(teachers) + 2
    header_rows = 2
    
    classes = renderer.mw.logic.get_all_sorted_classes()
    base_grades = renderer.get_base_grades(classes)
    
    col = 1
    for day in config.DAYS:
        limit = config.PERIODS_PER_DAY.get(day, 7)
        if limit < 1: limit = 7
        
        is_this_pinned = (day == pinned_day)
        
        control_widget = renderer.create_day_control_widget(day, base_grades)
        
        if is_this_pinned and is_split_mode:
            renderer.mw.header_left_layout.addWidget(control_widget, 0, col, 1, limit) 
        else:
            renderer.mw.header_right_layout.addWidget(control_widget, 0, col, 1, limit)
        
        for p in range(1, limit + 1):
            renderer.add_header(str(p), 1, col, is_pinned=is_this_pinned)
            col += 1
        
        if day != config.DAYS[-1]:
            lbl_h = QLabel()
            lbl_h.setFixedWidth(4)
            lbl_h.setObjectName("SplitterLine")
            
            lbl_c = QLabel()
            lbl_c.setFixedWidth(4)
            lbl_c.setObjectName("SplitterLine")
            
            gradient_style = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(203, 213, 225, 0), stop:0.5 rgba(203, 213, 225, 0.8), stop:1 rgba(203, 213, 225, 0));"
            lbl_h.setStyleSheet(gradient_style)
            lbl_c.setStyleSheet(gradient_style)
            
            if is_this_pinned and is_split_mode:
                renderer.mw.header_left_layout.addWidget(lbl_h, 0, col, header_rows, 1) 
                renderer.mw.left_layout.addWidget(lbl_c, 0, col, total_rows - header_rows, 1) 
            else:
                renderer.mw.header_right_layout.addWidget(lbl_h, 0, col, header_rows, 1)
                renderer.mw.right_layout.addWidget(lbl_c, 0, col, total_rows - header_rows, 1)
            col += 1

    for r, teacher in enumerate(teachers):
        row = r + 2
        subj = renderer.mw.logic.get_teacher_primary_subject(teacher)
        count = renderer.mw.logic.get_teacher_class_count(teacher)
        
        display_text = f"{teacher} ({subj},{count}h)" if subj else f"{teacher} ({count}h)"
        renderer.add_header(display_text, row, 0, font_size="9pt", is_pinned=True)
        
        col = 1
        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY.get(day, 7)
            if limit < 1: limit = 7
            
            is_this_pinned = (day == pinned_day) and is_split_mode
            
            for p in range(1, limit + 1):
                key = ("TEACHER_VIEW", teacher, day, p)
                
                if renderer.cell_pool:
                    cell = renderer.cell_pool.pop()
                    cell.data_key = key
                else:
                    cell = ClickableFrame(key)
                    cell.clicked.connect(renderer.mw.interaction_handler.handle_cell_click)
                    cell.right_clicked.connect(renderer.mw.interaction_handler.handle_right_click)
                    cell.cell_dropped.connect(renderer.mw.interaction_handler.handle_cell_drop)

                renderer._update_single_cell(cell, key)
                
                cell.setFixedHeight(36)
                cell.setFixedWidth(40) 
                
                if is_this_pinned:
                    renderer.mw.left_layout.addWidget(cell, row - header_rows, col)
                else:
                    renderer.mw.right_layout.addWidget(cell, row - header_rows, col)
                        
                renderer.mw.cell_widget_map[key] = cell
                cell.show()
                col += 1
            
            if day != config.DAYS[-1]:
                col += 1

def render_all_day(renderer):
    if not hasattr(renderer.mw, 'combo_sel'): return
    target_day = renderer.mw.combo_sel.currentText()
    if not target_day: return
    
    classes = renderer.mw.logic.get_all_sorted_classes()
    base_grades = renderer.get_base_grades(classes)
    
    renderer.add_header("학반", 0, 0, rowspan=2, is_pinned=True)
    
    limit = config.PERIODS_PER_DAY.get(target_day, 7)
    if limit < 1: limit = 7
    
    control_widget = renderer.create_day_control_widget(target_day, base_grades)
    renderer.mw.header_right_layout.addWidget(control_widget, 0, 1, 1, limit)
    
    for p in range(1, limit + 1):
        renderer.add_header(str(p), 1, p, is_pinned=False)
        
    for r, (g, c) in enumerate(classes):
        row = r + 2 
        
        hr_teacher = renderer.mw.logic.homeroom_teachers.get(str(g), {}).get(str(c), "")
        tooltip_txt = f"담임: {hr_teacher}" if hr_teacher else ""
        
        renderer.add_header(f"{g}-{c}", row, 0, is_pinned=True, tooltip=tooltip_txt)
        
        for p in range(1, limit + 1):
            renderer.add_cell(g, c, target_day, p, row, p, is_pinned=False)

def render_single(renderer):
    if not hasattr(renderer.mw, 'combo_sel'): return
    cls_str = renderer.mw.combo_sel.currentText()
    if not cls_str: return
    try: g, c = cls_str.split('-')
    except: return
    renderer.add_header("교시", 0, 0, is_pinned=True)
    for i, day in enumerate(config.DAYS):
        renderer.add_header(day, 0, i+1, is_pinned=False)
    for p in range(1, config.MAX_PERIODS + 1):
        renderer.add_header(f"{p}교시", p, 0, is_pinned=True)
        for i, day in enumerate(config.DAYS):
            limit = config.PERIODS_PER_DAY.get(day, 7)
            if limit < 1: limit = 7
            if p <= limit:
                renderer.add_cell(g, c, day, p, p, i+1, is_pinned=False)
            else:
                empty = renderer._get_empty_label(90) 
                # [수정] 단일 학급 뷰 빈 셀에도 명확한 실선 테두리 적용
                empty.setStyleSheet("background-color: rgba(248, 250, 252, 0.4); border: 1px solid #e2e8f0; border-radius: 6px;")
                renderer.mw.right_layout.addWidget(empty, p - 1, i+1)
                empty.show()

def render_teacher(renderer):
    if not hasattr(renderer.mw, 'combo_sel'): return
    t_name = renderer.mw.combo_sel.currentText()
    if not t_name: return
    renderer.add_header("교시", 0, 0, is_pinned=True)
    for i, day in enumerate(config.DAYS):
        renderer.add_header(day, 0, i+1, is_pinned=False)
    for p in range(1, config.MAX_PERIODS + 1):
        renderer.add_header(f"{p}교시", p, 0, is_pinned=True)
        for i, day in enumerate(config.DAYS):
            found = False
            if t_name in renderer.mw.logic.teachers_schedule:
                if day in renderer.mw.logic.teachers_schedule[t_name]:
                    if p in renderer.mw.logic.teachers_schedule[t_name][day]:
                        class_set = renderer.mw.logic.teachers_schedule[t_name][day][p]
                        if class_set:
                            normal_locs = [loc for loc in class_set if not renderer.mw.logic.is_excluded(loc[0], day)]
                            excluded_locs = [loc for loc in class_set if renderer.mw.logic.is_excluded(loc[0], day)]
                            target_locs = normal_locs if normal_locs else excluded_locs
                            
                            if target_locs:
                                info = target_locs[0]
                                g, c = str(info[0]), str(info[1])
                                renderer.add_cell(g, c, day, p, p, i+1, is_pinned=False)
                                found = True
            
            limit = config.PERIODS_PER_DAY.get(day, 7)
            if limit < 1: limit = 7
            if not found and p <= limit:
                empty = renderer._get_empty_label(90) 
                # [수정] 교사별 뷰 빈 셀에도 명확한 실선 테두리 적용
                empty.setStyleSheet("background-color: rgba(248, 250, 252, 0.4); border: 1px solid #e2e8f0; border-radius: 6px;")
                renderer.mw.right_layout.addWidget(empty, p - 1, i+1)
                empty.show()

def render_subject(renderer):
    if not hasattr(renderer.mw, 'combo_sel'): return
    subj_name = renderer.mw.combo_sel.currentText()
    if not subj_name: return

    renderer.add_header("교시", 0, 0, is_pinned=True)
    for i, day in enumerate(config.DAYS):
        renderer.add_header(day, 0, i+1, is_pinned=False)

    period_day_matches = {p: {d: [] for d in config.DAYS} for p in range(1, config.MAX_PERIODS + 1)}
    max_lines_per_period = {p: 1 for p in range(1, config.MAX_PERIODS + 1)}
    
    classes = renderer.mw.logic.get_all_sorted_classes()
    
    for p in range(1, config.MAX_PERIODS + 1):
        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY.get(day, 7)
            if limit < 1: limit = 7
            if p <= limit:
                for g, c in classes:
                    day_sched = renderer.mw.logic.schedule[str(g)][str(c)].get(day, {})
                    info = day_sched.get(p)
                    if info:
                        target_subject = info.get('subject')
                        if renderer.mw.is_subject_similar(target_subject, subj_name):
                            period_day_matches[p][day].append(f"{g}-{c}({info['teacher']})")
                
                lines = len(period_day_matches[p][day])
                if lines > max_lines_per_period[p]:
                    max_lines_per_period[p] = lines

    for p in range(1, config.MAX_PERIODS + 1):
        lines = max_lines_per_period[p]
        row_height = max(36, lines * 18 + 12) 
        
        header_lbl = renderer.header_pool.pop() if renderer.header_pool else QLabel()
        header_lbl.setText(f"{p}교시")
        header_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_lbl.setObjectName("GridHeader")
        header_lbl.setStyleSheet("")
        header_lbl.setToolTip("")
        header_lbl.setFixedHeight(row_height)
        header_lbl.setFixedWidth(60)
        
        renderer.mw.right_layout.addWidget(header_lbl, p - 1, 0)
        header_lbl.show()

        for i, day in enumerate(config.DAYS):
            limit = config.PERIODS_PER_DAY.get(day, 7)
            if limit < 1: limit = 7
            
            if p <= limit:
                matches = period_day_matches[p][day]
                if matches:
                    lbl = renderer.header_pool.pop() if renderer.header_pool else QLabel()
                    lbl.setText("\n".join(matches))
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setWordWrap(True)
                    lbl.setObjectName("SubjectMatchLabel")
                    
                    # [수정] 교과별 뷰 데이터 셀에도 학급 뷰와 동일한 명확한 실선 테두리(#e2e8f0) 적용
                    lbl.setStyleSheet("""
                        background-color: rgba(255, 255, 255, 0.85); 
                        border: 1px solid #e2e8f0; 
                        border-radius: 8px; 
                        padding: 4px;
                        color: #1e293b;
                        font-weight: 500;
                    """)
                    effect = QGraphicsDropShadowEffect()
                    effect.setBlurRadius(10)
                    effect.setXOffset(0)
                    effect.setYOffset(2)
                    effect.setColor(QColor(0, 0, 0, 15))
                    lbl.setGraphicsEffect(effect)
                    
                    lbl.setFixedHeight(row_height)
                    lbl.setFixedWidth(90)
                    renderer.mw.right_layout.addWidget(lbl, p - 1, i+1)
                    lbl.show()
                else:
                    empty = renderer._get_empty_label(90)
                    # [수정] 교과별 뷰 빈 셀에도 명확한 실선 테두리 적용
                    empty.setStyleSheet("background-color: rgba(248, 250, 252, 0.4); border: 1px solid #e2e8f0; border-radius: 6px;")
                    empty.setFixedHeight(row_height)
                    renderer.mw.right_layout.addWidget(empty, p - 1, i+1)
                    empty.show()