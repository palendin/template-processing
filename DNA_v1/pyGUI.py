# switch to venv interpreter

import os, sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from HP_assay_processing import processing, reprocessing, resource_path
import traceback
#os.chdir(sys._MEIPASS) # applies only when pyinstall on MAC

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Custom exception handler to display error messages
    """
    # Print the error message to the console
    traceback.print_exception(exc_type, exc_value, exc_traceback)

    # You can also display a message box or a dialog to the user here
    error_message = f"An error occurred: {exc_value}" # display console error (even if the exception comes from another script)
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Error")
    msg_box.setText(error_message)
    msg_box.exec_()

# Set the custom exception handler, which does not exit the program
sys.excepthook = handle_exception

# define a class that inherits all the functionalities that QWidget provides, so when we use Qwidget, we dont need to specify the method first
class Run_assay(QWidget):
    def __init__(self, parent = None):

        # # make a text file if not exist
        # file_path = os.path.join(os.path.dirname(__file__), 'processed_files.txt')
        # if not os.path.exists(file_path):
        #     with open(file_path, 'w'):
        #         pass
        # else:
        #     pass
        
        # initialize window and layout properties
        super(Run_assay, self).__init__(parent)
        self.resize(300,350)
        self.setWindowTitle('DNA Calculator')

        # create a layout
        self.vbox = QVBoxLayout()
        self.instruction_text_layout = QHBoxLayout()
        
        # place widgets inside the window
        self.label = QLabel("Calculates DNA mass per area")
        self.label.setFont(QFont('Arial', 20))
        
        # set the layout of our window as
        self.setLayout(self.vbox)
        #self.setLayout(self.hbox)

        # initiate UI buttons
        self.ButtonUI()

    def ButtonUI(self):
        
        # create input box text
        self.instruction = QLabel('Enter a DNA experiment ID:')
        self.instruction.setFont(QFont('Arial', 15))

        # create user input box
        self.input_box = QLineEdit()

        # create button
        self.run_button = QPushButton("run")
        self.run_button.setFont(QFont('Times',15))
        self.quit_button = QPushButton("quit")
        self.quit_button.setFont(QFont('Times',15))
        self.rerun_button = QPushButton("recalculate")
        self.rerun_button.setFont(QFont('Times',15))

        # create text
        self.label1 = QLabel('Use recalculate after data check')
        self.label1.setFont(QFont('Arial', 15))

        # pack the widgets in our vbox
        self.vbox.addWidget(self.label)
        
        # create horizontal layout for text instruction
        self.instruction_text_layout.addWidget(self.instruction)  
        # add input box to horizontal layout from text instruction
        self.instruction_text_layout.addWidget(self.input_box)
        self.vbox.addLayout(self.instruction_text_layout)
        

        self.vbox.addWidget(self.run_button)
        self.vbox.addWidget(self.quit_button)

        self.vbox.addWidget(self.label1)
        self.vbox.addWidget(self.rerun_button)

        # add methods into the button
        self.run_button.clicked.connect(self.calculation)
        #self.run_button.clicked.connect(self.show_info_messagebox)
        self.quit_button.clicked.connect(self.close)

        self.rerun_button.clicked.connect(self.recalculate)

        self.show()
    
    def calculation(self):
        exp_input = self.input_box.text()
        processing(exp_input)

        # show message box after completion
        self.show_info_messagebox()
    
    def recalculate(self):
        exp_input = self.input_box.text()
        reprocessing(exp_input)
    
    # show message box after completion
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

if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = Run_assay()
   #ex.show()
   sys.exit(app.exec_())

