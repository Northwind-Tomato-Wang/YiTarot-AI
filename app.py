import sys
import os
import math
import random
import json
import re
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QStackedWidget, QTextEdit, 
                             QGraphicsOpacityEffect, QFrame, QDialog, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF, QPointF, QPoint, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont, QPixmap, 
                         QLinearGradient, QPainterPath, QTransform, QRadialGradient)

# ==========================================
#  辅助函数：资源路径
# ==========================================
def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ==========================================
#  配置与数据
# ==========================================
HEX_MAP = { "111111":"乾为天", "000000":"坤为地", "100010":"水雷屯", "010001":"山水蒙", "111010":"水天需", "010111":"天水讼", "010000":"地水师", "000010":"水地比", "111011":"风天小畜", "110111":"天泽履", "111000":"地天泰", "000111":"天地否", "101111":"天火同人", "111101":"火天大有", "001000":"地山谦", "000100":"雷地豫", "100110":"泽雷随", "011001":"山风蛊", "110000":"地泽临", "000011":"风地观", "100101":"火雷噬嗑", "101001":"山火贲", "000001":"山地剥", "100000":"地雷复", "100111":"天雷无妄", "111001":"山天大畜", "100001":"山雷颐", "011110":"泽风大过", "010010":"坎为水", "101101":"离为火", "001110":"泽山咸", "011100":"雷风恒", "001111":"天山遁", "111100":"雷天大壮", "000101":"火地晋", "101000":"地火明夷", "101011":"风火家人", "110101":"火泽睽", "001010":"水山蹇", "010100":"雷水解", "110001":"山泽损", "100011":"风雷益", "111110":"泽天夬", "011111":"天风姤", "000110":"泽地萃", "011000":"地风升", "010110":"泽水困", "011010":"水风井", "101110":"泽火革", "011101":"火风鼎", "100100":"震为雷", "001001":"艮为山", "001011":"风山渐", "110100":"雷泽归妹", "101100":"雷火丰", "001101":"火山旅", "011011":"巽为风", "110110":"兑为泽", "010011":"风水涣", "110010":"水泽节", "110011":"风泽中孚", "001100":"雷山小过", "101010":"水火既济", "010101":"火水未济" }

TAROT_DB = [
    {"n":"愚者"}, {"n":"魔术师"}, {"n":"女祭司"}, {"n":"皇后"}, {"n":"皇帝"},
    {"n":"教皇"}, {"n":"恋人"}, {"n":"战车"}, {"n":"力量"}, {"n":"隐士"},
    {"n":"命运之轮"}, {"n":"正义"}, {"n":"倒吊人"}, {"n":"死神"}, {"n":"节制"},
    {"n":"恶魔"}, {"n":"高塔"}, {"n":"星星"}, {"n":"月亮"}, {"n":"太阳"},
    {"n":"审判"}, {"n":"世界"}
]

SYSTEM_FONT = "Arial"
if sys.platform == "darwin": SYSTEM_FONT = "PingFang SC"
elif sys.platform == "win32": SYSTEM_FONT = "Microsoft YaHei"

GLOBAL_STYLE = f"""
QMainWindow {{ background-color: #050505; }}
QLabel {{ color: #d4af37; font-family: "{SYSTEM_FONT}"; font-weight: bold; }}
QLineEdit {{ 
    background-color: rgba(20,20,20,0.9); border: 1px solid #d4af37; 
    color: #fff; padding: 10px; border-radius: 5px; font-size: 16px; font-family: "{SYSTEM_FONT}";
}}
QPushButton {{
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #b8860b, stop:1 #d4af37);
    border: none; border-radius: 20px; color: #000; font-weight: bold; font-size: 16px; padding: 8px 20px; font-family: "{SYSTEM_FONT}";
}}
QPushButton:hover {{ background-color: #FFD700; }}
QPushButton:disabled {{ background-color: #333; color: #666; }}
QTextEdit {{
    background-color: rgba(10,10,10,0.9); border: 1px solid #333; border-radius: 10px;
    color: #ccc; font-size: 16px; line-height: 1.6; padding: 15px; font-family: "{SYSTEM_FONT}";
}}
"""

# ==========================================
#  线程：API 与 关键词
# ==========================================
class AIThread(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    def __init__(self, api_key, model, messages):
        super().__init__()
        self.api_key = api_key; self.model = model; self.messages = messages
    def run(self):
        if not self.api_key:
            self.msleep(1500)
            self.result_signal.emit("**【演示模式】**<br>未配置 API Key。<br>请配置后获取真实解读。")
            return
        try:
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            resp = requests.post(url, headers=headers, json={"model": self.model, "messages": self.messages}, timeout=30)
            data = resp.json()
            if "error" in data: self.error_signal.emit(data['error']['message'])
            else: self.result_signal.emit(data['choices'][0]['message']['content'])
        except Exception as e: self.error_signal.emit(str(e))

class KeywordThread(QThread):
    result_signal = pyqtSignal(list)
    def __init__(self, api_key, model, question):
        super().__init__()
        self.api_key = api_key; self.model = model; self.question = question
    def run(self):
        if not self.api_key:
            self.result_signal.emit(["星轨", "命运", "启示"])
            return
        try:
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            prompt = f"请从以下问题中提取3个最核心的关键词，词语控制在2-4字，不要任何标点符号，用空格隔开：{self.question}"
            resp = requests.post(url, headers=headers, json={"model": self.model, "messages": [{"role":"user","content":prompt}]}, timeout=10)
            content = resp.json()['choices'][0]['message']['content']
            self.result_signal.emit(content.split()[:3])
        except: self.result_signal.emit(["探索", "未知", "前行"])

# ==========================================
#  组件：星轨背景
# ==========================================
class StarBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stars = [{'r': random.randint(50, 900), 'angle': random.uniform(0, 360), 'size': random.uniform(1, 3), 'speed': random.uniform(0.02, 0.05)} for _ in range(150)]
        self.timer = QTimer(self); self.timer.timeout.connect(self.update); self.timer.start(30)
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#050505"))
        cx, cy = self.width()/2, self.height()/2
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255, 255, 255, 200))
        for s in self.stars:
            s['angle'] += s['speed']
            rad = math.radians(s['angle'])
            x = cx + s['r'] * math.cos(rad)
            y = cy + s['r'] * math.sin(rad)
            if 0<x<self.width() and 0<y<self.height(): p.drawEllipse(QPointF(x, y), s['size'], s['size'])

# ==========================================
#  组件：硬币
# ==========================================
class CoinWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.is_yang = True 
        self.scale_y = 1.0  
        self.anim_timer = QTimer(self); self.anim_timer.timeout.connect(self._animate_step)
        self.current_step = 0; self.total_steps = 0; self.final_is_yang = True

    def start_toss(self, result_is_yang):
        self.final_is_yang = result_is_yang
        self.current_step = 0
        self.total_steps = random.randint(13, 40) 
        self.anim_timer.start(30)

    def _animate_step(self):
        self.current_step += 1
        angle = self.current_step * 0.6
        self.scale_y = math.cos(angle)
        if self.scale_y < 0: self.is_yang = not self.is_yang
        if self.current_step >= self.total_steps:
            if abs(self.scale_y) > 0.9:
                self.anim_timer.stop(); self.scale_y = 1.0; self.is_yang = self.final_is_yang
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width()/2, self.height()/2; radius = 40
        painter.translate(cx, cy); painter.scale(1.0, abs(self.scale_y)) 
        if self.is_yang:
            grad = QRadialGradient(0, 0, radius); grad.setColorAt(0, QColor("#fbeea0")); grad.setColorAt(1, QColor("#d4af37"))
            painter.setBrush(QBrush(grad)); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(QPointF(0,0), radius, radius)
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(QColor("#8a6e3e"), 2)); painter.drawRect(-12, -12, 24, 24)
        else:
            painter.setBrush(QColor("#222")); pen = QPen(QColor("#d4af37")); pen.setWidth(3); painter.setPen(pen)
            painter.drawEllipse(QPointF(0,0), radius-2, radius-2)
            painter.setPen(QPen(QColor("#d4af37"), 2)); painter.drawRect(-12, -12, 24, 24)
        painter.setBrush(QColor("#050505")); painter.setPen(Qt.PenStyle.NoPen); painter.drawRect(-10, -10, 20, 20)

# ==========================================
#  组件：卦象
# ==========================================
class HexagramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 250); self.lines = [] 
    def add_line(self, is_yang, is_moving):
        self.lines.append({"isYang": is_yang, "isMoving": is_moving}); self.update() 
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        line_h, gap = 20, 15; start_y = self.height() - line_h - 10
        for i, line in enumerate(self.lines):
            y = start_y - i * (line_h + gap)
            color = QColor("#d13636") if line['isMoving'] else QColor("#d4af37")
            p.setBrush(QBrush(color)); p.setPen(Qt.PenStyle.NoPen)
            if line['isYang']: p.drawRoundedRect(10, y, 280, line_h, 4, 4)
            else: p.drawRoundedRect(10, y, 120, line_h, 4, 4); p.drawRoundedRect(170, y, 120, line_h, 4, 4)

class JellyHexagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 400); self.lines = []; self.offsets = [0.0] * 6; self.dragging_idx = -1; self.drag_start_x = 0
    def set_lines(self, hex_lines):
        self.lines = hex_lines; self.offsets = [0.0]*len(hex_lines); self.update()
    def mousePressEvent(self, e):
        y = e.pos().y(); start_y = 350
        for i in range(len(self.lines)):
            if abs(y - (start_y - i * 50)) < 25: self.dragging_idx = i; self.drag_start_x = e.pos().x(); break
    def mouseMoveEvent(self, e):
        if self.dragging_idx != -1:
            dx = max(-60, min(60, e.pos().x() - self.drag_start_x))
            for i in range(len(self.lines)):
                factor = max(0, 1 - abs(i - self.dragging_idx) * 0.3) 
                self.offsets[i] = dx * factor
            self.update()
    def mouseReleaseEvent(self, e):
        self.dragging_idx = -1; self.anim_timer = QTimer(self); self.anim_timer.timeout.connect(self.elastic_back); self.anim_timer.start(16)
    def elastic_back(self):
        all_zero = True
        for i in range(len(self.offsets)):
            self.offsets[i] *= 0.8 
            if abs(self.offsets[i]) > 0.5: all_zero = False
            else: self.offsets[i] = 0
        self.update(); 
        if all_zero: self.anim_timer.stop()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        start_y = 350; line_h = 24; base_w = 300; cx = self.width() / 2
        for i, line in enumerate(self.lines):
            off = self.offsets[i]; y = start_y - i * 50
            p.setBrush(QColor("#d13636") if line['isMoving'] else QColor("#d4af37"))
            p.setPen(Qt.PenStyle.NoPen)
            if line['isYang']: p.drawRoundedRect(QRectF(cx - base_w/2 + off, y, base_w, line_h), 4, 4)
            else:
                wh = base_w * 0.4
                p.drawRoundedRect(QRectF(cx - base_w/2 + off, y, wh, line_h), 4, 4)
                p.drawRoundedRect(QRectF(cx + base_w/2 - wh + off, y, wh, line_h), 4, 4)

# ==========================================
#  组件：加载动画 (修复：文字居中)
# ==========================================
class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset = 0
        self.timer = QTimer(self); self.timer.timeout.connect(self.animate)
        self.text = "正在连接星轨，请稍后..."; self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    def start(self): self.setVisible(True); self.timer.start(20)
    def stop(self): self.timer.stop(); self.setVisible(False)
    def animate(self): self.offset = (self.offset + 5) % (self.width() + self.height()); self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(SYSTEM_FONT, 16, QFont.Weight.Bold); p.setFont(font); p.setPen(QColor("#d4af37"))
        # 关键修复：直接居中显示，不再固定 Top=100
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text)
        
        pen_gold = QPen(QColor("#d4af37")); pen_gold.setWidth(4)
        pen_silver = QPen(QColor("#c0c0c0")); pen_silver.setWidth(4)
        w, h = self.width(), self.height()
        p.setPen(pen_gold); pos = self.offset % w; p.drawLine(int(pos), 0, int(pos + 100), 0)
        p.setPen(pen_silver); pos = (w - self.offset) % w; p.drawLine(int(pos), h, int(pos - 100), h)

# ==========================================
#  组件：塔罗牌
# ==========================================
class TarotCard(QLabel):
    clicked = pyqtSignal(int)
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index; self.setFixedSize(170, 300)
        self.is_face_up = False; self.is_revealed = False; self.img_file = ""; self.is_reversed = False; self.is_animating = False
        self.scale_factor = 1.0; self.flip_timer = QTimer(self); self.flip_timer.timeout.connect(self._animate_flip); self.flip_stage = 0; self.target_face_up = False 
        self.auto_back_timer = QTimer(self); self.auto_back_timer.setSingleShot(True); self.auto_back_timer.timeout.connect(self._auto_flip_back)
        self.show_back()

    def mousePressEvent(self, e):
        if self.is_animating: return
        self.clicked.emit(self.index)

    def show_back(self):
        self.is_face_up = False; self._update_pixmap("0.png", False)

    def reset_to_back(self):
        self.auto_back_timer.stop(); self.is_face_up = False; self.is_revealed = False; self.is_animating = False
        self.img_file = ""; self.is_reversed = False; self.scale_factor = 1.0; self._update_pixmap("0.png", False)

    def force_front(self, img_file, is_reversed):
        self.is_face_up = True; self.is_revealed = True; self.img_file = img_file; self.is_reversed = is_reversed
        self._update_pixmap(img_file, is_reversed)

    def reveal(self, img_file, is_reversed):
        if self.is_animating: return
        self.is_revealed = True; self.img_file = img_file; self.is_reversed = is_reversed; self.target_face_up = True; self._start_flip()

    def toggle_flip(self):
        if self.is_animating: return
        self.target_face_up = not self.is_face_up; self._start_flip()

    def _auto_flip_back(self):
        if not self.is_face_up and not self.is_animating: self.target_face_up = True; self._start_flip()

    def _start_flip(self):
        self.is_animating = True; self.flip_stage = 1; self.flip_timer.start(20)

    def _animate_flip(self):
        step = 0.12
        if self.flip_stage == 1:
            self.scale_factor -= step
            if self.scale_factor <= 0:
                self.scale_factor = 0; self.flip_stage = 2; self.is_face_up = self.target_face_up
        elif self.flip_stage == 2:
            self.scale_factor += step
            if self.scale_factor >= 1.0:
                self.scale_factor = 1.0; self.flip_timer.stop(); self.flip_stage = 0; self.is_animating = False
                if not self.is_face_up: self.auto_back_timer.start(3000)
                else: self.auto_back_timer.stop()
        
        if self.is_face_up: self._update_pixmap(self.img_file, self.is_reversed)
        else: self._update_pixmap("0.png", False)

    def _update_pixmap(self, path, is_reversed):
        full_path = resource_path(path)
        if not os.path.exists(full_path):
            self.setText(f"Missing\n{path}"); self.setStyleSheet("border: 2px solid red; color: red;"); return
        self.setStyleSheet("border: none; background: transparent;")
        pix = QPixmap(full_path)
        if is_reversed: pix = pix.transformed(QTransform().rotate(180), Qt.TransformationMode.SmoothTransformation)
        w = max(1, int(170 * self.scale_factor))
        pix = pix.scaled(w, 300, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(pix); self.setAlignment(Qt.AlignmentFlag.AlignCenter)

# ==========================================
#  主程序
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("易 · 塔 (Pure Python Visuals)")
        self.resize(1200, 800)
        
        self.api_key = ""; self.model = "qwen-plus"; self.user_q = ""
        self.hex_lines = []; self.tarot_data = []; self.chat_history = []
        self.bg = StarBackground(self)
        self.setCentralWidget(self.bg)
        self.stack = QStackedWidget(self.bg); self.stack.resize(1200, 800)
        
        self.init_start_ui()
        self.init_iching_ui()
        self.init_tarot_ui()
        self.init_result_ui()

        self.keyword_container = QWidget(self); self.keyword_container.setGeometry(0, 700, 1200, 100)
        self.keyword_layout = QHBoxLayout(self.keyword_container); self.keyword_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading = LoadingOverlay(self); self.loading.resize(1200, 800); self.loading.hide()
        self.btn_cfg = QPushButton("⚙", self); self.btn_cfg.move(1150, 750); self.btn_cfg.clicked.connect(self.show_config)

    def init_start_ui(self):
        self.page_start = QWidget()
        l = QVBoxLayout(self.page_start); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("星 轨 问 策"); lbl.setStyleSheet("font-size: 48px; letter-spacing: 10px;")
        self.input_q = QLineEdit(); self.input_q.setPlaceholderText("请输入困惑..."); self.input_q.setFixedWidth(500)
        btn = QPushButton("开 启 启 示"); btn.clicked.connect(self.on_start)
        l.addWidget(lbl); l.addSpacing(50); l.addWidget(self.input_q); l.addSpacing(30); l.addWidget(btn)
        self.stack.addWidget(self.page_start)

    def init_iching_ui(self):
        self.page_iching = QWidget()
        l = QVBoxLayout(self.page_iching)
        coin_layout = QHBoxLayout()
        self.coins = [CoinWidget() for _ in range(3)]
        for c in self.coins: coin_layout.addWidget(c)
        self.hex_display = HexagramWidget()
        self.lbl_hex_name = QLabel("")
        self.btn_toss = QPushButton("掷 铜 钱 (1/6)"); self.btn_toss.setFixedWidth(200); self.btn_toss.clicked.connect(self.on_toss)
        l.addStretch(); l.addLayout(coin_layout); l.addSpacing(30)
        l.addWidget(self.hex_display, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.lbl_hex_name, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.btn_toss, alignment=Qt.AlignmentFlag.AlignCenter); l.addStretch()
        self.stack.addWidget(self.page_iching)

    def init_tarot_ui(self):
        self.page_tarot = QWidget()
        l = QVBoxLayout(self.page_tarot)
        self.lbl_tarot_hint = QLabel("抽取：过去"); self.lbl_tarot_hint.setStyleSheet("font-size: 32px;")
        cl = QHBoxLayout()
        self.select_cards = []
        for i in range(3):
            c = TarotCard(i); c.clicked.connect(self.on_pick_card); cl.addWidget(c); self.select_cards.append(c)
        l.addStretch(); l.addWidget(self.lbl_tarot_hint, alignment=Qt.AlignmentFlag.AlignCenter); l.addLayout(cl); l.addStretch()
        self.stack.addWidget(self.page_tarot)

    def init_result_ui(self):
        self.page_result = QWidget()
        main = QVBoxLayout(self.page_result)
        top = QHBoxLayout()
        self.res_cards = []
        for i in range(3):
            c = TarotCard(i); c.clicked.connect(lambda _, idx=i: self.on_res_card_click(idx)); top.addWidget(c); self.res_cards.append(c)
        self.res_hex = JellyHexagram(); top.addWidget(self.res_hex)
        chat_box = QWidget(); chat_l = QVBoxLayout(chat_box)
        self.txt_history = QTextEdit(); self.txt_history.setReadOnly(True)
        input_l = QHBoxLayout()
        self.input_chat = QLineEdit(); btn = QPushButton("发送"); btn.clicked.connect(self.on_send_chat)
        input_l.addWidget(self.input_chat); input_l.addWidget(btn)
        chat_l.addWidget(self.txt_history); chat_l.addLayout(input_l)
        main.addLayout(top, stretch=1); main.addWidget(chat_box, stretch=1)
        self.stack.addWidget(self.page_result)

    def on_start(self):
        q = self.input_q.text()
        if not q: return
        self.user_q = q
        self.stack.setCurrentIndex(1)
        self.kw_thread = KeywordThread(self.api_key, self.model, q)
        self.kw_thread.result_signal.connect(self.show_keywords)
        self.kw_thread.start()

    def show_keywords(self, words):
        for i in reversed(range(self.keyword_layout.count())): self.keyword_layout.itemAt(i).widget().deleteLater()
        for w in words:
            lbl = QLabel(w); lbl.setStyleSheet("color: #FFD700; font-size: 24px; font-weight: bold;")
            eff = QGraphicsOpacityEffect(lbl); lbl.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity"); anim.setDuration(2000); anim.setStartValue(0); anim.setEndValue(1); anim.start()
            setattr(lbl, 'anim', anim)
            self.keyword_layout.addWidget(lbl)

    def on_toss(self):
        if len(self.hex_lines) >= 6: return
        self.btn_toss.setEnabled(False)
        coins_val = [random.choice([2, 3]) for _ in range(3)]
        total = sum(coins_val)
        for i, c in enumerate(self.coins): c.start_toss(coins_val[i] == 3)
        is_yang = (total % 2 != 0); is_moving = (total == 6 or total == 9)
        QTimer.singleShot(1300, lambda: self.finish_toss(is_yang, is_moving))

    def finish_toss(self, is_yang, is_moving):
        self.btn_toss.setEnabled(True)
        self.hex_lines.append({"isYang": is_yang, "isMoving": is_moving})
        self.hex_display.add_line(is_yang, is_moving)
        if len(self.hex_lines) < 6: self.btn_toss.setText(f"掷 铜 钱 ({len(self.hex_lines)+1}/6)")
        else:
            bin_str = "".join(['1' if l['isYang'] else '0' for l in self.hex_lines])
            name = HEX_MAP.get(bin_str, "未知")
            self.lbl_hex_name.setText(f"本卦：{name}")
            self.btn_toss.setText("进入塔罗")
            self.btn_toss.clicked.disconnect()
            self.btn_toss.clicked.connect(lambda: self.stack.setCurrentIndex(2))

    def on_pick_card(self, idx):
        if self.select_cards[idx].is_revealed: return
        current_step = len(self.tarot_data)
        if current_step >= 3: return
        d_idx = random.randint(0, len(TAROT_DB)-1); is_up = random.choice([True, False])
        pos = ["过去", "现在", "未来"][current_step]
        self.tarot_data.append({"n": TAROT_DB[d_idx]['n'], "img_idx": d_idx+1, "is_up": is_up, "pos": pos})
        self.select_cards[idx].reveal(f"{d_idx+1}.png", not is_up)
        QTimer.singleShot(1200, lambda: self.reset_drafting_round(current_step + 1))

    def reset_drafting_round(self, next_step):
        if next_step >= 3: self.go_final()
        else:
            self.lbl_tarot_hint.setText(f"抽取：{['过去','现在','未来'][next_step]}")
            for c in self.select_cards: c.reset_to_back()

    def go_final(self):
        self.stack.setCurrentIndex(3); self.loading.start()
        for i, data in enumerate(self.tarot_data):
            self.res_cards[i].force_front(f"{data['img_idx']}.png", not data['is_up'])
            self.start_idle_flip(i)
        self.res_hex.set_lines(self.hex_lines)
        self.call_ai()

    def start_idle_flip(self, idx):
        delay = 8000 + random.randint(0, 6000)
        QTimer.singleShot(delay, lambda: self.do_idle_flip(idx))

    def do_idle_flip(self, idx):
        c = self.res_cards[idx]
        if not c.is_animating and c.is_face_up:
            c.toggle_flip() 
            QTimer.singleShot(1500, lambda: self.restore_flip(idx))
        self.start_idle_flip(idx)

    def restore_flip(self, idx):
        c = self.res_cards[idx]
        if not c.is_face_up and not c.is_animating: c.toggle_flip()

    def on_res_card_click(self, idx):
        self.res_cards[idx].toggle_flip()

    def call_ai(self):
        bin_str = "".join(['1' if l['isYang'] else '0' for l in self.hex_lines])
        hex_name = HEX_MAP.get(bin_str, "")
        cards_str = ",".join([f"{t['pos']}:{t['n']}" for t in self.tarot_data])
        prompt = f"用户困惑：{self.user_q}\n周易：{hex_name}\n塔罗：{cards_str}\n请深度解析。格式要求：\n1. 不使用列表符号，用自然段落。\n2. 重点词汇用 **加粗** 标记。\n3. 语气神秘优雅。"
        self.chat_history.append({"role":"system", "content":prompt})
        self.ai_thread = AIThread(self.api_key, self.model, self.chat_history)
        self.ai_thread.result_signal.connect(self.on_ai_res)
        self.ai_thread.error_signal.connect(lambda e: self.txt_history.append(f"<font color='red'>{e}</font>"))
        self.ai_thread.finished.connect(self.loading.stop)
        self.ai_thread.start()

    def on_ai_res(self, content):
        self.chat_history.append({"role":"assistant", "content":content})
        html = re.sub(r'\*\*(.*?)\*\*', r"<font color='#FFD700'><b>\1</b></font>", content).replace("\n", "<br>")
        self.txt_history.append(html + "<br>")

    def on_send_chat(self):
        t = self.input_chat.text()
        if not t: return
        self.txt_history.append(f"<div align='right' style='color:#d4af37'>{t}</div>")
        self.chat_history.append({"role":"user", "content":t})
        self.input_chat.clear()
        self.loading.start()
        self.ai_thread = AIThread(self.api_key, self.model, self.chat_history)
        self.ai_thread.result_signal.connect(self.on_ai_res)
        self.ai_thread.finished.connect(self.loading.stop)
        self.ai_thread.start()

    def show_config(self):
        d = QDialog(self); f = QFormLayout(d)
        k = QLineEdit(self.api_key); k.setEchoMode(QLineEdit.EchoMode.Password)
        f.addRow("Key:", k); btn = QPushButton("Save")
        btn.clicked.connect(lambda: [setattr(self, 'api_key', k.text()), d.accept()])
        f.addRow(btn); d.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    app.setFont(QFont(SYSTEM_FONT, 10))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())