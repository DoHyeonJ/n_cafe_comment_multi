from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton)

class AccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('계정 추가')
        layout = QVBoxLayout()

        # ID 입력
        id_layout = QHBoxLayout()
        id_label = QLabel('아이디:')
        self.id_input = QLineEdit()
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_input)

        # PW 입력
        pw_layout = QHBoxLayout()
        pw_label = QLabel('비밀번호:')
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        pw_layout.addWidget(pw_label)
        pw_layout.addWidget(self.pw_input)

        # 버튼
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('확인')
        cancel_btn = QPushButton('취소')
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(id_layout)
        layout.addLayout(pw_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_account_info(self):
        return self.id_input.text(), self.pw_input.text() 