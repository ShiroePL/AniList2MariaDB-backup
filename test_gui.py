import sys
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
import gui_main

app = QApplication(sys.argv)
window = gui_main.MainWindow()
window.show()

# Take screenshot
pixmap = window.grab()
pixmap.save('/tmp/gui_screenshot.png')
print("Screenshot saved to /tmp/gui_screenshot.png")

app.quit()
