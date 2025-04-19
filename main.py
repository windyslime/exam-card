import sys
import json
import datetime
from PyQt6.QtCore import Qt, QTimer, QDateTime, QEasingCurve
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QFont, QIcon
from qfluentwidgets import FlowLayout, SwitchButton, PushButton, ComboBox, LineEdit, SpinBox, MessageBox
from qfluentwidgets import FluentIcon, InfoBar, Dialog, setTheme, Theme, ToolTipFilter

class ExamCard(QWidget):
    def __init__(self):
        super().__init__()
        self.exams = []
        self.current_exam = None
        self.time_offset = 0
        self.exam_room = "默认考场"
        self.zoom_factor = 1.0
        self.is_dark_mode = False
        self.custom_message = ""
        self.message_expiry = None
        
        self.init_ui()
        self.load_settings()
        self.start_timer()
        
    def init_ui(self):
        # 设置窗口基本属性
        self.setWindowTitle("考试看板")
        self.setMinimumSize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 顶部布局 - 标题和按钮
        top_layout = QHBoxLayout()
        
        # 标题
        self.title_label = QLabel("考试看板")
        self.title_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        top_layout.addWidget(self.title_label, 1)
        
        # 设置按钮
        self.settings_btn = PushButton("设置")
        self.settings_btn.setIcon(FluentIcon.SETTING)
        self.settings_btn.clicked.connect(self.open_settings)
        top_layout.addWidget(self.settings_btn)
        
        # 全屏按钮
        self.fullscreen_btn = PushButton("全屏")
        self.fullscreen_btn.setIcon(FluentIcon.FULL_SCREEN)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        top_layout.addWidget(self.fullscreen_btn)
        
        main_layout.addLayout(top_layout)
        
        # 中间部分 - 使用FlowLayout
        self.flow_layout = FlowLayout()
        self.flow_layout.setAnimation(250, QEasingCurve.Type.OutQuad)
        self.flow_layout.setContentsMargins(10, 10, 10, 10)
        self.flow_layout.setVerticalSpacing(20)
        self.flow_layout.setHorizontalSpacing(20)
        
        # 时间显示
        self.time_widget = QWidget()
        self.time_widget.setObjectName("timeWidget")
        time_layout = QVBoxLayout(self.time_widget)
        
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_layout.addWidget(self.time_label)
        
        self.flow_layout.addWidget(self.time_widget)
        
        # 考试状态显示
        self.status_widget = QWidget()
        self.status_widget.setObjectName("statusWidget")
        status_layout = QVBoxLayout(self.status_widget)
        
        self.exam_status_label = QLabel("考试状态")
        self.exam_status_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        status_layout.addWidget(self.exam_status_label)
        
        self.status_label = QLabel("未开始")
        self.status_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: blue;")
        status_layout.addWidget(self.status_label)
        
        self.flow_layout.addWidget(self.status_widget)
        
        # 考试信息表格
        self.exam_table_widget = QWidget()
        self.exam_table_widget.setObjectName("examTableWidget")
        self.exam_table_layout = QVBoxLayout(self.exam_table_widget)
        
        # 表头
        header_layout = QHBoxLayout()
        headers = ["时间", "科目", "开始", "结束", "状态"]
        for header in headers:
            label = QLabel(header)
            label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(label)
        
        self.exam_table_layout.addLayout(header_layout)
        self.flow_layout.addWidget(self.exam_table_widget)
        
        # 自定义消息区域
        self.message_widget = QWidget()
        self.message_widget.setObjectName("messageWidget")
        message_layout = QVBoxLayout(self.message_widget)
        
        self.message_label = QLabel("点击编辑消息")
        self.message_label.setFont(QFont("Microsoft YaHei", 16))
        self.message_label.setWordWrap(True)
        self.message_label.mousePressEvent = self.edit_message
        message_layout.addWidget(self.message_label)
        
        self.flow_layout.addWidget(self.message_widget)
        
        main_layout.addLayout(self.flow_layout)
        
        # 底部状态栏
        bottom_layout = QHBoxLayout()
        
        self.room_label = QLabel(f"考场: {self.exam_room}")
        bottom_layout.addWidget(self.room_label)
        
        bottom_layout.addStretch(1)
        
        self.load_config_btn = PushButton("加载配置")
        self.load_config_btn.setIcon(FluentIcon.FOLDER)
        self.load_config_btn.clicked.connect(self.load_config_file)
        bottom_layout.addWidget(self.load_config_btn)
        
        main_layout.addLayout(bottom_layout)
        
        # 设置样式
        self.apply_style()
    
    def apply_style(self):
        # 应用主题
        if self.is_dark_mode:
            setTheme(Theme.DARK)
            self.setStyleSheet("""
                QWidget { background-color: #1e1e1e; color: white; }
                #timeWidget, #statusWidget, #examTableWidget, #messageWidget { 
                    background-color: #2d2d2d; 
                    border-radius: 10px; 
                    padding: 15px; 
                }
            """)
        else:
            setTheme(Theme.LIGHT)
            self.setStyleSheet("""
                QWidget { background-color: #f5f5f5; color: black; }
                #timeWidget, #statusWidget, #examTableWidget, #messageWidget { 
                    background-color: white; 
                    border-radius: 10px; 
                    border: 1px solid #e0e0e0;
                    padding: 15px; 
                }
            """)
    
    def start_timer(self):
        # 创建定时器更新时间和考试状态
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_and_status)
        self.timer.start(1000)  # 每秒更新一次
    
    def update_time_and_status(self):
        # 获取当前时间（考虑偏移）
        current_time = QDateTime.currentDateTime().addSecs(self.time_offset)
        time_str = current_time.toString("HH:mm:ss")
        self.time_label.setText(time_str)
        
        # 更新考试状态
        self.update_exam_status(current_time)
    
    def update_exam_status(self, current_time):
        if not self.exams:
            self.status_label.setText("无考试安排")
            self.status_label.setStyleSheet("color: gray;")
            return
        
        # 清除旧的考试行
        for i in reversed(range(self.exam_table_layout.count())):
            if i > 0:  # 保留表头
                item = self.exam_table_layout.itemAt(i)
                if item:
                    layout = item.layout()
                    if layout:
                        for j in reversed(range(layout.count())):
                            layout.itemAt(j).widget().deleteLater()
                    layout.deleteLater()
        
        # 添加新的考试行
        current_exam = None
        next_exam = None
        
        for exam in self.exams:
            row_layout = QHBoxLayout()
            
            # 转换时间字符串为QDateTime对象
            date_str = exam["date"]
            start_time = QDateTime.fromString(f"{date_str} {exam['start_time']}", "yyyy-MM-dd HH:mm")
            end_time = QDateTime.fromString(f"{date_str} {exam['end_time']}", "yyyy-MM-dd HH:mm")
            
            # 显示日期和时间段
            time_label = QLabel(f"{date_str}\n{exam['period']}")
            time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(time_label)
            
            # 科目
            subject_label = QLabel(exam["subject"])
            subject_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(subject_label)
            
            # 开始时间
            start_label = QLabel(exam["start_time"])
            start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(start_label)
            
            # 结束时间
            end_label = QLabel(exam["end_time"])
            end_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(end_label)
            
            # 状态
            status = ""
            status_color = ""
            
            if current_time < start_time:
                status = "未开始"
                status_color = "blue"
                if not next_exam or start_time < QDateTime.fromString(f"{next_exam['date']} {next_exam['start_time']}", "yyyy-MM-dd HH:mm"):
                    next_exam = exam
            elif current_time > end_time:
                status = "已结束"
                status_color = "gray"
            else:
                status = "进行中"
                status_color = "green"
                current_exam = exam
            
            status_label = QLabel(status)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet(f"color: {status_color};")
            row_layout.addWidget(status_label)
            
            self.exam_table_layout.addLayout(row_layout)
        
        # 更新当前考试状态
        if current_exam:
            self.current_exam = current_exam
            self.exam_status_label.setText(f"当前科目: {current_exam['subject']}")
            
            # 计算剩余时间
            end_time = QDateTime.fromString(f"{current_exam['date']} {current_exam['end_time']}", "yyyy-MM-dd HH:mm")
            remaining_secs = current_time.secsTo(end_time)
            hours = remaining_secs // 3600
            minutes = (remaining_secs % 3600) // 60
            seconds = remaining_secs % 60
            
            self.status_label.setText(f"进行中 - 剩余 {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.status_label.setStyleSheet("color: green;")
        elif next_exam:
            self.current_exam = None
            self.exam_status_label.setText(f"下一科目: {next_exam['subject']}")
            
            # 计算等待时间
            start_time = QDateTime.fromString(f"{next_exam['date']} {next_exam['start_time']}", "yyyy-MM-dd HH:mm")
            waiting_secs = current_time.secsTo(start_time)
            hours = waiting_secs // 3600
            minutes = (waiting_secs % 3600) // 60
            seconds = waiting_secs % 60
            
            self.status_label.setText(f"等待中 - {hours:02d}:{minutes:02d}:{seconds:02d} 后开始")
            self.status_label.setStyleSheet("color: blue;")
        else:
            self.current_exam = None
            self.exam_status_label.setText("考试状态")
            self.status_label.setText("所有考试已结束")
            self.status_label.setStyleSheet("color: gray;")
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("全屏")
            self.fullscreen_btn.setIcon(FluentIcon.FULL_SCREEN)
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("退出全屏")
            self.fullscreen_btn.setIcon(FluentIcon.CANCEL)
    
    def open_settings(self):
        dialog = Dialog("考试看板设置", self)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog.contentWidget)
        
        # 时间偏移设置
        offset_layout = QHBoxLayout()
        offset_label = QLabel("时间偏移(秒):")
        offset_layout.addWidget(offset_label)
        
        self.offset_spinbox = SpinBox(dialog)
        self.offset_spinbox.setValue(self.time_offset)
        self.offset_spinbox.setRange(-3600, 3600)
        offset_layout.addWidget(self.offset_spinbox)
        
        layout.addLayout(offset_layout)
        
        # 考场信息设置
        room_layout = QHBoxLayout()
        room_label = QLabel("考场信息:")
        room_layout.addWidget(room_label)
        
        self.room_edit = LineEdit(dialog)
        self.room_edit.setText(self.exam_room)
        room_layout.addWidget(self.room_edit)
        
        layout.addLayout(room_layout)
        
        # 页面缩放设置
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("页面缩放:")
        zoom_layout.addWidget(zoom_label)
        
        self.zoom_combo = ComboBox(dialog)
        for zoom in ["0.8", "0.9", "1.0", "1.1", "1.2", "1.5", "2.0"]:
            self.zoom_combo.addItem(zoom)
        
        current_zoom = str(self.zoom_factor)
        index = self.zoom_combo.findText(current_zoom)
        if index >= 0:
            self.zoom_combo.setCurrentIndex(index)
        else:
            self.zoom_combo.setCurrentText("1.0")
        
        zoom_layout.addWidget(self.zoom_combo)
        
        layout.addLayout(zoom_layout)
        
        # 主题设置
        theme_layout = QHBoxLayout()
        theme_label = QLabel("暗色模式:")
        theme_layout.addWidget(theme_label)
        
        self.theme_switch = SwitchButton(dialog)
        self.theme_switch.setChecked(self.is_dark_mode)
        theme_layout.addWidget(self.theme_switch)
        
        layout.addLayout(theme_layout)
        
        # 保存按钮
        save_btn = PushButton("保存设置")
        save_btn.clicked.connect(lambda: self.save_settings(dialog))
        layout.addWidget(save_btn)
        
        dialog.show()
    
    def save_settings(self, dialog=None):
        if dialog:
            self.time_offset = self.offset_spinbox.value()
            self.exam_room = self.room_edit.text()
            self.zoom_factor = float(self.zoom_combo.currentText())
            self.is_dark_mode = self.theme_switch.isChecked()
            
            # 关闭对话框
            dialog.close()
        
        # 保存到Cookie（这里使用JSON文件模拟）
        settings = {
            "time_offset": self.time_offset,
            "exam_room": self.exam_room,
            "zoom_factor": self.zoom_factor,
            "is_dark_mode": self.is_dark_mode,
            "custom_message": self.custom_message,
            "message_expiry": self.message_expiry.isoformat() if self.message_expiry else None
        }
        
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            # 应用设置
            self.apply_settings()
            
            InfoBar.success(
                title="成功",
                content="设置已保存",
                parent=self
            )
        except Exception as e:
            MessageBox(
                "保存失败",
                str(e),
                self
            )
    
    def load_settings(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            self.time_offset = settings.get("time_offset", 0)
            self.exam_room = settings.get("exam_room", "默认考场")
            self.zoom_factor = settings.get("zoom_factor", 1.0)
            self.is_dark_mode = settings.get("is_dark_mode", False)
            self.custom_message = settings.get("custom_message", "")
            
            # 处理消息过期时间
            expiry_str = settings.get("message_expiry")
            if expiry_str:
                try:
                    self.message_expiry = datetime.datetime.fromisoformat(expiry_str)
                    # 检查是否已过期
                    if datetime.datetime.now() > self.message_expiry:
                        self.custom_message = ""
                        self.message_expiry = None
                except:
                    self.message_expiry = None
            else:
                self.message_expiry = None
            
            # 应用设置
            self.apply_settings()
        except FileNotFoundError:
            # 文件不存在，使用默认设置
            self.apply_settings()
        except Exception as e:
            MessageBox(
                "加载设置失败",
                str(e),
                self
            )
    
    def apply_settings(self):
        # 应用样式
        self.apply_style()
        
        # 更新缩放
        font = self.font()
        font.setPointSizeF(font.pointSizeF() * self.zoom_factor)
        QApplication.instance().setFont(font)
        
        # 更新考场信息
        self.room_label.setText(f"考场: {self.exam_room}")
        
        # 更新自定义消息
        if self.custom_message:
            self.message_label.setText(self.custom_message)
        else:
            self.message_label.setText("点击编辑消息")
        
        # 刷新布局
        self.flow_layout.removeAllWidgets()
        self.flow_layout.addWidget(self.time_widget)
        self.flow_layout.addWidget(self.status_widget)
        self.flow_layout.addWidget(self.exam_table_widget)
        self.flow_layout.addWidget(self.message_widget)
    
    def edit_message(self, event):
        # Initialize like in open_settings
        dialog = Dialog("编辑消息", self)
        # Use contentWidget like in open_settings
        layout = QVBoxLayout(dialog.contentWidget)
        message_edit = LineEdit(dialog.contentWidget) # Set parent to contentWidget
        message_edit.setText(self.custom_message)
        message_edit.setPlaceholderText("输入要显示的消息")
        layout.addWidget(message_edit)
        save_btn = PushButton("保存消息", dialog.contentWidget) # Set parent to contentWidget
        save_btn.clicked.connect(lambda: self.save_message(message_edit.text(), dialog))
        layout.addWidget(save_btn)
        dialog.show()
    
    def save_message(self, message, dialog):
        self.custom_message = message
        
        # 设置3天后过期
        self.message_expiry = datetime.datetime.now() + datetime.timedelta(days=3)
        
        # 更新显示
        if self.custom_message:
            self.message_label.setText(self.custom_message)
        else:
            self.message_label.setText("点击编辑消息")
        
        # 保存设置
        self.save_settings()
        
        dialog.close()
    
    def load_config_file(self):
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择配置文件",
            "",
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                if "exams" in config:
                    self.exams = config["exams"]
                    InfoBar.success(
                        title="成功",
                        content=f"已加载 {len(self.exams)} 个考试安排",
                        parent=self
                    )
                else:
                    MessageBox(
                        "格式错误",
                        "配置文件中未找到考试安排",
                        self
                    )
            except Exception as e:
                MessageBox(
                    "加载失败",
                    str(e),
                    self
                )

def main():
    app = QApplication(sys.argv)
    window = ExamCard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()