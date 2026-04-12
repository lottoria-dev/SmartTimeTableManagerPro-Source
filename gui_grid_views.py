from PySide6.QtWidgets import QLabel
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
            
            if is_this_pinned and is_split_mode:
                renderer.mw.header_left_layout.addWidget(lbl_h, 0, col, header_rows, 1)
                renderer.mw.left_layout.addWidget(lbl_c, 0, col, total_rows - header_rows, 1)
            else:
                renderer.mw.header_right_layout.addWidget(lbl_h, 0, col, header_rows, 1)
                renderer.mw.right_layout.addWidget(lbl_c, 0, col, total_rows - header_rows, 1)
            col += 1
    
    for r, (g, c) in enumerate(classes):
        row = r + 2 
        renderer.add_header(f"{g}-{c}", row, 0, is_pinned=True)
        
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
                    # 신규 생성 시에만 시그널을 연결하여 경고 메시지 방지
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
        renderer.add_header(f"{g}-{c}", row, 0, is_pinned=True)
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
                            # [수정] 정상반을 우선적으로 가져오고, 없으면 제외된 반을 렌더링
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
                renderer.mw.right_layout.addWidget(empty, p - 1, i+1)
                empty.show()

def render_subject(renderer):
    if not hasattr(renderer.mw, 'combo_sel'): return
    subj_name = renderer.mw.combo_sel.currentText()
    if not subj_name: return

    renderer.add_header("교시", 0, 0, is_pinned=True)
    for i, day in enumerate(config.DAYS):
        renderer.add_header(day, 0, i+1, is_pinned=False)

    for p in range(1, config.MAX_PERIODS + 1):
        renderer.add_header(f"{p}교시", p, 0, is_pinned=True)
        for i, day in enumerate(config.DAYS):
            limit = config.PERIODS_PER_DAY.get(day, 7)
            if limit < 1: limit = 7
            
            if p <= limit:
                matches = []
                classes = renderer.mw.logic.get_all_sorted_classes()
                for g, c in classes:
                    day_sched = renderer.mw.logic.schedule[str(g)][str(c)].get(day, {})
                    info = day_sched.get(p)
                    if info:
                        target_subject = info.get('subject')
                        if renderer.mw.is_subject_similar(target_subject, subj_name):
                            matches.append(f"{g}-{c}({info['teacher']})")
                
                if matches:
                    lbl = renderer.header_pool.pop() if renderer.header_pool else QLabel()
                    lbl.setText("\n".join(matches))
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setWordWrap(True)
                    lbl.setObjectName("SubjectMatchLabel") # [수정]
                    lbl.setStyleSheet("") 
                    lbl.setMinimumHeight(36)
                    lbl.setFixedWidth(90)
                    renderer.mw.right_layout.addWidget(lbl, p - 1, i+1)
                    lbl.show()
                else:
                    empty = renderer._get_empty_label(90) 
                    renderer.mw.right_layout.addWidget(empty, p - 1, i+1)
                    empty.show()