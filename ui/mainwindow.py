from PySide6.QtCore import (
    Qt,
    QDir,
    QDirIterator,
    QFile,
    QFileInfo,
    QPoint,
    QProcess,
    QSize,
    QSortFilterProxyModel,
)

from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QIcon,
    QPixmap, 
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QToolBar,
    QToolButton,
    QFileDialog,
    QInputDialog,
    QFileSystemModel,
    QLineEdit,
    QMenu,
    QTreeView,
    QHBoxLayout,
    QVBoxLayout,
    QFileIconProvider,
    QSizePolicy,
    QMessageBox,
)

from pokethemer import decomp_xml_image_areas, rebuild_xml_image_areas
import platform
import shutil

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
DEFAULT_OUTPUT_DIR = 'output'

class Label(QLabel):

    def __init__(self):
        super(Label, self).__init__()
        self.pixmap_width: int = 1
        self.pixmap_height: int = 1

    def setPixmap(self, pm: QPixmap) -> None:
        self.pixmap_width = pm.width()
        self.pixmap_height = pm.height()

        self.updateMargins()
        super(Label, self).setPixmap(pm)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.updateMargins()
        super(Label, self).resizeEvent(a0)

    def updateMargins(self):
        if self.pixmap() is None:
            return
        self.pixmap_width = self.pixmap().width()
        self.pixmap_height = self.pixmap().height()
        if self.pixmap_width <= 0 or self.pixmap_height <= 0:
            return
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        if w * self.pixmap_height > h * self.pixmap_width:
            m = int((w - (self.pixmap_width * h / self.pixmap_height)) / 2)
            self.setContentsMargins(m, 0, m, 0)
        else:
            m = int((h - (self.pixmap_height * w / self.pixmap_width)) / 2)
            self.setContentsMargins(0, m, 0, m)

class EmptyIconProvider(QFileIconProvider):
    def icon(self, _):
        return QIcon()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_dir = None
        self.theme_basedir = None
        self.decomp_dir = 'theme_decomp'
        self.theme_entry_file = None
        self.selected_sprite_filename = None
        self.selected_sprite_fullpath = None
        self.selected_sprite_size = None

        self.setWindowIcon(QIcon('./ui/icon.png'))
        self.setWindowTitle('PokeThemer')
        self.setGeometry(50, 50, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setMovable(False)
        self.toolbar.toggleViewAction().setEnabled(False)
        self.addToolBar(self.toolbar)

        self.open_theme_action = QAction('Open Theme', self)
        self.open_theme_action.triggered.connect(self.open_theme)
        self.toolbar.addAction(self.open_theme_action)

        self.replace_action = QAction('Replace Sprite', self)
        self.replace_action.triggered.connect(self.single_replace_sprite)
        self.replace_action.setVisible(False)
        self.toolbar.addAction(self.replace_action)

        self.save_toolbutton = QToolButton(self)
        self.save_toolbutton.setText('Save Theme')
        self.save_toolbutton.setStyleSheet('QToolButton::menu-indicator { image: none; }')
        self.save_toolbutton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.save_theme_action = QAction('Save', self)
        self.save_theme_action.triggered.connect(self.save_theme)

        self.save_as_theme_action = QAction('Save As', self)
        self.save_as_theme_action.triggered.connect(self.save_as_theme)

        self.save_menu = QMenu(self.save_toolbutton)
        self.save_menu.addAction(self.save_theme_action)
        self.save_menu.addAction(self.save_as_theme_action)
        self.save_toolbutton.setMenu(self.save_menu)
        self.save_toolbutton_action = self.toolbar.addWidget(self.save_toolbutton)
        self.save_toolbutton_action.setVisible(False)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)

        self.open_sprite_folder_action = QAction('Sprite Folder', self)
        self.open_sprite_folder_action.triggered.connect(self.open_sprite_folder)
        self.open_sprite_folder_action.setVisible(False)
        self.toolbar.addAction(self.open_sprite_folder_action)

        self.mass_replace_action = QAction('Mass Replace', self)
        self.mass_replace_action.triggered.connect(self.mass_replace_sprites)
        self.mass_replace_action.setVisible(False)
        self.toolbar.addAction(self.mass_replace_action)

        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        label = QLabel()
        label.setText("<font color='grey'>Open Theme<br /><br />Replace Sprites<br /><br />Save Theme</font>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = self.font()
        font.setPointSize(13)
        label.setFont(font)

        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(widget)

    def display_theme(self):
        widget = QWidget(self)
        self.model = QFileSystemModel()
        self.model.setIconProvider(EmptyIconProvider())
        self.model_root_path = self.model.setRootPath(f'{self.theme_dir}/{self.decomp_dir}')

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setAutoAcceptChildRows(True)

        self.sprite_list = QTreeView()
        self.sprite_list.setModel(self.proxy_model)
        self.sprite_list.setRootIndex(self.proxy_model.mapFromSource(self.model.index(f'{self.theme_dir}/{self.decomp_dir}')))
        # delegate = NameDelegate(self.sprite_list)
        # self.sprite_list.setItemDelegate(delegate)
        # self.sprite_list.setViewMode(QListView.ViewMode.ListMode)
        # self.sprite_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.sprite_list.setMinimumWidth(WINDOW_WIDTH // 3.5)
        self.sprite_list.selectionModel().currentChanged.connect(self.list_clicked)
        self.sprite_list.doubleClicked.connect(self.single_replace_sprite)
        self.sprite_list.hideColumn(1)
        self.sprite_list.hideColumn(2)
        self.sprite_list.hideColumn(3)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Filter')
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(WINDOW_WIDTH // 3.5)
        self.search_edit.setMaximumWidth(WINDOW_WIDTH // 3)
        self.search_edit.textEdited.connect(self.search_list)

        file_vbox = QVBoxLayout()
        file_vbox.addWidget(self.search_edit)
        file_vbox.addWidget(self.sprite_list)

        self.sprite_image_label = Label() 
        self.sprite_image_label.setScaledContents(True)
        self.sprite_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.size_label = QLabel()
        self.size_label.setStyleSheet("QLabel{font-size: 14pt;}")
        self.size_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        self.size_label.setScaledContents(True)
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignBottom)

        label_vbox = QVBoxLayout()
        label_vbox.addWidget(self.sprite_image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        label_vbox.addWidget(self.size_label, Qt.AlignmentFlag.AlignCenter|Qt.AlignmentFlag.AlignBottom)

        layout = QHBoxLayout(widget)
        layout.addLayout(file_vbox)
        layout.addLayout(label_vbox, 2)

        self.setCentralWidget(widget)

        if self.replace_action.isVisible():
            self.replace_action.setVisible(False)
        if self.save_toolbutton_action.isVisible():
            self.save_toolbutton_action.setVisible(False)
        if not self.open_sprite_folder_action.isVisible():
            self.open_sprite_folder_action.setVisible(True)
        if not self.mass_replace_action.isVisible():
            self.mass_replace_action.setVisible(True)

    def open_theme(self):

        theme_dirname = QFileDialog.getExistingDirectory(self, 'Open Theme Folder')
        self.theme_basedir = QDir(theme_dirname).dirName()

        if theme_dirname == '':
            return
        
        modifiable_theme = f'{theme_dirname}_pokethemer'

        if QDir().exists(modifiable_theme):
            QDir(modifiable_theme).removeRecursively()
        
        # TODO implement with QT in the future.
        modifiable_theme = shutil.copytree(theme_dirname, modifiable_theme)

        self.theme_dir = modifiable_theme
        if QFile.exists(f'{self.theme_dir}/twl-themer-load.xml'):
            self.theme_entry_file = 'twl-themer-load.xml'
        elif QFile.exists(f'{self.theme_dir}/theme.xml'):
            self.theme_entry_file = 'theme.xml'
        else:
            entry_dialog = QInputDialog()
            entry_dialog.setWindowIcon(QIcon('./ui/icon.png'))
            entry_dialog_text, entry_dialog_bool = entry_dialog.getText(self, 'Entry File', 'Default entry file <b>twl-themer-load.xml</b> not found,<br/> please provide entry file name.')

            if not entry_dialog_bool:
                self.theme_entry_file = None
                return

            self.theme_entry_file = entry_dialog_text

            if entry_dialog_text == '' or not QFile.exists(f'{self.theme_dir}/{self.theme_entry_file}'):
                msgbox = QMessageBox(self)
                msgbox.setWindowIcon(QIcon('./ui/icon.png'))
                msgbox.setWindowTitle('Error')
                msgbox.setText('Could not find specified file.')
                msgbox.setStandardButtons(QMessageBox.StandardButton.Ok)
                msgbox.setDefaultButton(QMessageBox.StandardButton.Ok)
                msgbox.exec()
                return

        decomp_xml_image_areas(f'{self.theme_dir}/{self.theme_entry_file}', self.theme_dir)
        self.display_theme()
        
        self.sprite_list.setCurrentIndex(self.sprite_list.indexAt(QPoint(0,0)))

    def save_theme(self):
        if not QDir().exists(DEFAULT_OUTPUT_DIR):
            QDir().mkdir(DEFAULT_OUTPUT_DIR)

        output_dir = f'{DEFAULT_OUTPUT_DIR}/{self.theme_basedir}'

        rebuild_xml_image_areas(f'{self.theme_dir}/{self.theme_entry_file}', self.theme_dir)

        if QDir().exists(output_dir):
            shutil.rmtree(output_dir)

        shutil.copytree(self.theme_dir, output_dir)
        shutil.rmtree(f'{output_dir}/theme_decomp')

        self.open_directory(output_dir)

    def save_as_theme(self):
        save_dir = QFileDialog.getExistingDirectory(self, 'Select where to save', './')
        save_dialog = QInputDialog()
        save_dialog.setWindowIcon(QIcon('./ui/icon.png'))
        save_dialog_text, save_dialog_bool = save_dialog.getText(self, 'Save As', 'Theme Name:')
        save_fullpath = f'{save_dir}/{save_dialog_text}'

        if not save_dialog_bool:
            return
        
        rebuild_xml_image_areas(f'{self.theme_dir}/{self.theme_entry_file}', self.theme_dir)

        shutil.copytree(self.theme_dir, save_fullpath)
        shutil.rmtree(f'{save_fullpath}/theme_decomp')

        self.open_directory(f'{save_fullpath}')

    def search_list(self, text):
        self.proxy_model.setFilterFixedString(text)
        # self.model.setRootPath(f'{self.theme_dir}/{self.decomp_dir}')
        self.sprite_list.setRootIndex(self.proxy_model.mapFromSource(self.model.index(f'{self.theme_dir}/{self.decomp_dir}')))
        
        if text != '':
            self.sprite_list.expandAll()
        else:
            self.sprite_list.collapseAll()

    def list_clicked(self, current_selection, previous_selection):

        if not QFileInfo(self.model.filePath(self.proxy_model.mapToSource(current_selection))).isFile():
            self.selected_sprite_filename = None
            self.selected_sprite_fullpath = None
            self.selected_sprite_size = None
            if self.replace_action.isVisible():
                self.replace_action.setVisible(False)
            self.refresh_sprite_preview()
            return

        if not self.replace_action.isVisible():
            self.replace_action.setVisible(True)

        self.selected_sprite_filename = current_selection.data()
        self.selected_sprite_fullpath = self.model.filePath(self.proxy_model.mapToSource(current_selection))
        self.selected_sprite_size = QPixmap(self.selected_sprite_fullpath).size()
        
        self.refresh_sprite_preview()

    def refresh_sprite_preview(self):
        if not self.selected_sprite_fullpath:
            return
        pixmap = QPixmap(self.selected_sprite_fullpath)
        w = pixmap.width()
        ratio = 1
        while w > 1600:
            ratio += 1
            w = pixmap.width() // ratio

        self.selected_sprite_size = pixmap.size()
        self.sprite_image_label.setPixmap(pixmap.scaled(QSize(pixmap.size().width() / ratio, pixmap.size().height()), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.sprite_image_label.setScaledContents(False)
        self.size_label.setText(f'{self.selected_sprite_size.width()} x {self.selected_sprite_size.height()}')

    def single_replace_sprite(self, idx):
        if not self.selected_sprite_filename:
            return
        
        replacement_filename = QFileDialog.getOpenFileName(self, f'Select Replacement {self.selected_sprite_filename}')[0]
        
        if replacement_filename == '':
            return
        
        self.current_replacement_file = replacement_filename

        self.replace_sprite(self.current_replacement_file, self.selected_sprite_fullpath)
        self.refresh_sprite_preview()

    def mass_replace_sprites(self):
        msgbox = QMessageBox()
        msgbox.setWindowIcon(QIcon('./ui/icon.png'))
        msgbox.setWindowTitle('Warning')
        msgbox.setText('<b>Matching Sprite Folder/File Names</b>')
        msgbox.setInformativeText('Only folders/files in the selected folder with names matching pattern of the dumped sprites will be replaced.')
        msgbox.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msgbox.setDefaultButton(QMessageBox.StandardButton.Ok)
        msgbox_return = msgbox.exec()

        if msgbox_return == QMessageBox.StandardButton.Cancel:
            return
        
        replacement_folder_fullpath = QFileDialog.getExistingDirectory(self, 'Select replacement sprites directory', self.theme_dir)
        main_fullpath = QDir(f'{self.theme_dir}/{self.decomp_dir}').absolutePath()

        sprite_qdir_iterator = QDirIterator(main_fullpath, '', filters=QDir.Filter.Files | QDir.Filter.NoDotAndDotDot, flags=QDirIterator.IteratorFlag.Subdirectories)
        replacement_qdir_iterator = QDirIterator(replacement_folder_fullpath, '', filters=QDir.Filter.Files | QDir.Filter.NoDotAndDotDot, flags=QDirIterator.IteratorFlag.Subdirectories)

        sprite_files = []
        while sprite_qdir_iterator.hasNext():
            sprite_files.append(sprite_qdir_iterator.next())

        while replacement_qdir_iterator.hasNext():
            replacement_file_fullpath = replacement_qdir_iterator.next()
            replacement_file_cutpath = replacement_file_fullpath.removeprefix(replacement_folder_fullpath)
            if replacement_file_cutpath in [fullpath.removeprefix(main_fullpath) for fullpath in sprite_files]:
                self.replace_sprite(replacement_file_fullpath, f'{self.theme_dir}/{self.decomp_dir}/{replacement_file_cutpath}')
                self.sprite_list.setCurrentIndex(self.model.index(replacement_file_fullpath))
                        
        self.refresh_sprite_preview()

    def replace_sprite(self, src: str, dst: str):
        if not QFile.exists(dst) or QFile.remove(dst):
            if QFile.copy(src, dst):
                if not self.save_toolbutton_action.isVisible():
                    self.save_toolbutton_action.setVisible(True)
            else:
                print('Could not copy file')
                return False
        else:
            print('Could not remove file')
            return False

    def open_sprite_folder(self):
        self.open_directory(f'{self.theme_dir}/{self.decomp_dir}')

    def open_directory(self, path: str):
        platform_os = platform.system()
        if platform_os == 'Windows':
            windows_is_shit = path.replace('/', '\\')
            QProcess.startDetached(f'explorer', arguments=[f"\e,{windows_is_shit}"])
        elif platform_os == 'Linux':
            QDesktopServices.openUrl(path)
        elif platform_os == 'Darwin':
            #No mac to test this so.
            QDesktopServices.openUrl(path)
        else:
            print('tf you running this on')
