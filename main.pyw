# Multithreaded comic book downloader.
# Currently only supports Litterbox Comics, XKCD, and ExoComics.

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6 import uic, QtCore
from modules import exocomics, xkcd, lbc
import sys, threading, os, time
dir_path = os.path.dirname(os.path.realpath(__file__))

class Window(QMainWindow):
    comic_threads = []
    xkcd_prog_changed = QtCore.pyqtSignal(int)
    lbc_prog_changed = QtCore.pyqtSignal(int)
    exo_prog_changed = QtCore.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        uic.loadUi(fr'{dir_path}\modules\comic_downloader.ui', self)
        self.setWindowTitle('Comic Downloader')
        self.resize(236,350)
        self.start_button.clicked.connect(self.StartDownload)
        self.xkcd_prog.hide()
        self.lbc_prog.hide()
        self.exo_prog.hide()
        self.console.hide()
        self.xkcd_prog_changed.connect(self.xkcd_prog.setValue)
        self.lbc_prog_changed.connect(self.lbc_prog.setValue)
        self.exo_prog_changed.connect(self.exo_prog.setValue)
        
    def CleanUp(self):
        xkcd.stop_threads = True
        exocomics.stop_threads = True
        lbc.stop_threads = True

        all_threads = xkcd.downloadThreads + exocomics.downloadThreads + lbc.downloadThreads

        for thread in all_threads:
            while thread.is_alive():
                time.sleep(5)
        
        for thread in self.comic_threads:
            while thread.is_alive():
                time.sleep(5)

    def closeEvent(self, event):
        self.setWindowTitle('Stopping threads, please wait...')
        self.CleanUp()
        event.accept()

    def StartDownload(self):
        self.resize(711,350)
        self.console.show()
        self.comics = {'ExoComics': self.exo_check.isChecked(), 'XKCD': self.xkcd_check.isChecked(), 'Litterbox Comics': self.lbc_check.isChecked()}
        for comic, status in self.comics.items():
            if status == True:
                if comic == 'Litterbox Comics':
                    self.console.append('Starting Litterbox Comics.')
                    max_page = lbc.LBCMaxPage()
                    self.lbc_prog.setMaximum(max_page)
                    self.lbc_prog.show()
                    lbc_thread = threading.Thread(target=lbc.StartLBC, args=[max_page])
                    lbc_update = threading.Thread(target=self.UpdateLBCProg, args=[max_page])
                    self.comic_threads.append(lbc_update)
                    lbc_update.start()
                    lbc_thread.start()
                elif comic == 'ExoComics':
                    self.console.append('Starting ExoComics.')
                    max_page = exocomics.ECMaxPage()
                    self.exo_prog.setMaximum(max_page)
                    self.exo_prog.show()
                    exo_thread = threading.Thread(target=exocomics.StartExo)
                    exo_update = threading.Thread(target=self.UpdateExoProg, args=[max_page])
                    self.comic_threads.append(exo_update)
                    exo_update.start()
                    exo_thread.start()
                elif comic == 'XKCD':
                    self.console.append('Starting XKCD.')
                    max_page = xkcd.XKCDMaxPage()
                    self.xkcd_prog.setMaximum(max_page)
                    self.xkcd_prog.show()
                    xkcd_thread = threading.Thread(target=xkcd.StartXKCD)
                    xkcd_update = threading.Thread(target=self.UpdateXKCDProg, args=[max_page])
                    self.comic_threads.append(xkcd_update)
                    xkcd_update.start()
                    xkcd_thread.start()
                
    def UpdateExoProg(self, max_page):
        cur_page = (exocomics.pages_downloaded + exocomics.page_errors)
        while cur_page != int(max_page) and exocomics.stop_threads == False:
            cur_page = (exocomics.pages_downloaded + exocomics.page_errors)
            self.exo_prog_changed.emit(cur_page)
        self.console.append(f'Finished ExoComics with {exocomics.page_errors} errors.')
        self.console.append(f'Errors on pages {",".join(exocomics.comic_error)}')

    def UpdateXKCDProg(self, max_page):
        cur_page = (xkcd.pages_downloaded + xkcd.page_errors)
        while cur_page != int(max_page) and xkcd.stop_threads == False:
            cur_page = (xkcd.pages_downloaded + xkcd.page_errors)
            self.xkcd_prog_changed.emit(cur_page)
        self.console.append(f'Finished XKCD with {xkcd.page_errors} errors.')
        self.console.append(f'Errors on pages {",".join(xkcd.comic_error)}')

    def UpdateLBCProg(self, max_page):
        cur_page = (lbc.pages_downloaded)
        while cur_page != int(max_page) and lbc.stop_threads == False:
            cur_page = (lbc.pages_downloaded)
            self.lbc_prog_changed.emit(cur_page)
        self.console.append(f'Finished Litterbox Comics.')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())