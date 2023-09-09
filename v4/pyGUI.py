import os, sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from HP_assay_processing import processing, reprocessing, resource_path
import traceback
#os.chdir(sys._MEIPASS) # applies only when pyinstall on MAC

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Custom exception handler to display error messages.
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

# Set the custom exception handler
sys.excepthook = handle_exception

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
        self.hbox = QHBoxLayout()

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

        self.label1 = QLabel('Use recalculate after data check')
        self.label1.setFont(QFont('Arial', 20))

        self.rerun_button = QPushButton("recalculate")
        self.rerun_button.setFont(QFont('Times',20))

        # pack the widgets in our vbox
        self.vbox.addWidget(self.label)
        self.vbox.addWidget(self.run_button)
        self.vbox.addWidget(self.quit_button)

        self.vbox.addWidget(self.label1)
        self.vbox.addWidget(self.rerun_button)

        self.run_button.clicked.connect(self.calculation)
        #self.run_button.clicked.connect(self.show_info_messagebox)
        self.quit_button.clicked.connect(self.close)

        self.rerun_button.clicked.connect(self.recalculate)

        self.show()
    
    def calculation(self):
        path = resource_path('HP_assay')
        processing(path)

        # show message box after completion
        self.show_info_messagebox()
    
    def recalculate(self):
        path = resource_path('HP_assay')
        reprocessing(path)
        
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

