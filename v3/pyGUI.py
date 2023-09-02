import os, sys
from HP_assay_processing import resource_path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from HP_assay_processing import processing, resource_path
os.chdir(sys._MEIPASS)

# define a class that inherits all the functionalities that QWidget provides, so when we use Qwidget, we dont need to specify the method first
class Run_assay(QWidget):
    def __init__(self, parent = None):

        # make a text file if not exist
        file_path = os.path.join(os.path.dirname(__file__), 'processed_files.txt')
        if not os.path.exists(file_path):
            with open(file_path, 'w'):
                pass
        else:
            pass
        
        # initialize window and layout properties
        super(Run_assay, self).__init__(parent)
        self.resize(200,200)
        self.setWindowTitle('Hydroxyproline Calculator')

        # create a layout
        self.vbox = QVBoxLayout()
        #self.hbox = QHBoxLayout()

        # place widgets inside the window
        self.label = QLabel("calculates percent collagen in hide sample")
        self.label.setFont(QFont('Arial', 20))
        #self.label.move(10,10)

        # set the layout of our window as
        self.setLayout(self.vbox)

        # initiate UI buttons
        self.ButtonUI()

    def ButtonUI(self):
        
        self.run_button = QPushButton("run")
        self.run_button.setFont(QFont('Times',20))
        self.quit_button = QPushButton("quit")
        self.quit_button.setFont(QFont('Times',20))

        # pack the widgets in our vbox
        self.vbox.addWidget(self.label)
        self.vbox.addWidget(self.run_button)
        self.vbox.addWidget(self.quit_button)

        self.run_button.clicked.connect(self.calculation)
        #self.run_button.clicked.connect(self.show_info_messagebox)
        self.quit_button.clicked.connect(self.close)

        self.show()
    
    def calculation(self):
        path = resource_path('HP_assay')
        processing(path)
        self.show_info_messagebox()

    def show_info_messagebox(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
    
        # setting message for Message Box
        msg.setText("calculation completed")
        
        # setting Message box window title
        msg.setWindowTitle("Information MessageBox")
        
        # declaring buttons on Message Box
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        
        # start the app
        retval = msg.exec_()


# # connect the PushButton to a function
# run_button.clicked.connect(calculation)

    

# def main():
#    app = QApplication(sys.argv)
#    ex = Run_assay()
#    #ex.show()
#    sys.exit(app.exec_())
if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = Run_assay()
   #ex.show()
   sys.exit(app.exec_())
#    main()

# def startprocess(self):
# # start application
# app = QApplication(sys.argv)

# # create a window
# window = QWidget()

# # create a layout
# vbox = QVBoxLayout()

# # place widgets inside the window
# text_1=QLineEdit()
# text_2=QLineEdit()
# run_button = QPushButton("run")

# run_btn = QPushButton("run")
# def calculation():
#     file_path = os.path.join(os.path.dirname(__file__), 'processed_files.txt')
#     if not os.path.exists(file_path):
#         with open(file_path, 'w'):
#             pass
#     else:
#         pass
#     path = resource_path('HP_assay')
#     print(path)
#     processing(path)
#     # data_1=text_1.text()
#     # text_2.setText(data_1)
    

# # connect the PushButton to a function
# run_button.clicked.connect(calculation)

# # pack the widgets in our vbox 
# vbox.addWidget(text_1)
# vbox.addWidget(text_2)
# vbox.addWidget(run_button)

# # set the layout of our window as
# window.setLayout(vbox)


# window.show()
# sys.exit(app.exec_())