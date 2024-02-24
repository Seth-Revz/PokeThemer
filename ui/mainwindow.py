from PySide6.QtCore import (
    Qt,
    QDir,
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
    QFileDialog,
    QFileSystemModel,
    QListView,
    QTreeView,
    QHBoxLayout,
    QVBoxLayout,
    QStyledItemDelegate, 
    QFileIconProvider,
    QSizePolicy,
    QMessageBox,
)

from pokethemer import decomp_xml_image_areas, rebuild_xml_image_areas
import platform
import shutil

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TEMP_DIR = 'temp'

class Label(QLabel):

    def __init__(self):
        super(Label, self).__init__()
        self.pixmap_width: int = 1
        self.pixmapHeight: int = 1

    def setPixmap(self, pm: QPixmap) -> None:
        self.pixmap_width = pm.width()
        self.pixmapHeight = pm.height()

        self.updateMargins()
        super(Label, self).setPixmap(pm)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.updateMargins()
        super(Label, self).resizeEvent(a0)

    def updateMargins(self):
        if self.pixmap() is None:
            return
        pixmapWidth = self.pixmap().width()
        pixmapHeight = self.pixmap().height()
        if pixmapWidth <= 0 or pixmapHeight <= 0:
            return
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        if w * pixmapHeight > h * pixmapWidth:
            m = int((w - (pixmapWidth * h / pixmapHeight)) / 2)
            self.setContentsMargins(m, 0, m, 0)
        else:
            m = int((h - (pixmapHeight * w / pixmapWidth)) / 2)
            self.setContentsMargins(0, m, 0, m)

class NameDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if isinstance(index.model(), QFileSystemModel):
            if not index.model().isDir(index):
                option.text = index.model().fileInfo(index).completeBaseName()

    def setEditorData(self, editor, index):
        if isinstance(index.model(), QFileSystemModel):
            if not index.model().isDir(index):
                editor.setText(index.model().fileInfo(index).completeBaseName())
            else:
                super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(model, QFileSystemModel):
            fi = model.fileInfo(index)
            if not model.isDir(index):
                model.setData(index, editor.text() + "." + fi.suffix())
            else:
                super().setModelData(editor, model.index)

class EmptyIconProvider(QFileIconProvider):
    def icon(self, _):
        return QIcon()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_dir = None
        self.decomp_dir = 'theme_decomp'
        self.theme_entry_file = None
        self.selected_sprite_filename = None
        self.selected_sprite_fullpath = None

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

        self.save_theme_action = QAction('Save Theme', self)
        self.save_theme_action.triggered.connect(self.save_theme)
        self.save_theme_action.setVisible(False)
        self.toolbar.addAction(self.save_theme_action)

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
        self.model.setRootPath(f'{self.theme_dir}/{self.decomp_dir}')

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.sprite_list = QTreeView()
        self.sprite_list.setModel(self.proxy_model)
        self.sprite_list.setRootIndex(self.proxy_model.mapFromSource(self.model.index(f'{self.theme_dir}/{self.decomp_dir}')))
        delegate = NameDelegate(self.sprite_list)
        self.sprite_list.setItemDelegate(delegate)
        # self.sprite_list.setViewMode(QListView.ViewMode.ListMode)
        # self.sprite_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.sprite_list.setMinimumWidth(WINDOW_WIDTH // 3.5)
        self.sprite_list.selectionModel().currentChanged.connect(self.list_clicked)
        self.sprite_list.hideColumn(1)
        self.sprite_list.hideColumn(2)
        self.sprite_list.hideColumn(3)

        layout = QHBoxLayout(widget)
        layout.addWidget(self.sprite_list, alignment=Qt.AlignmentFlag.AlignLeft)

        self.sprite_image_label = Label() 
        # pixmap = QPixmap(f'{self.theme_dir}/main.png')
        # self.sprite_image_label.setPixmap(pixmap.scaled(QSize(WINDOW_WIDTH, WINDOW_HEIGHT), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.sprite_image_label.setScaledContents(True)

        layout.addWidget(self.sprite_image_label, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(widget)

        if self.replace_action.isVisible():
            self.replace_action.setVisible(False)
        if self.save_theme_action.isVisible():
            self.save_theme_action.setVisible(False)
        if not self.open_sprite_folder_action.isVisible():
            self.open_sprite_folder_action.setVisible(True)
        if not self.mass_replace_action.isVisible():
            self.mass_replace_action.setVisible(True)

    def open_theme(self):

        theme_dirname = QFileDialog.getExistingDirectory(self, 'Open Theme Folder')
        theme_basedir = QDir(theme_dirname).dirName()

        if theme_dirname == '':
            return
        
        if not QDir().exists(TEMP_DIR):
            QDir().mkdir(TEMP_DIR)

        if QDir().exists(f'{TEMP_DIR}/{theme_basedir}'):
            QDir(f'{TEMP_DIR}/{theme_basedir}').removeRecursively()
        
        # TODO implement with QT in the future.
        modifiable_theme = shutil.copytree(theme_dirname, f'{TEMP_DIR}/{theme_basedir}')

        self.theme_dir = modifiable_theme
        if QFile.exists(f'{self.theme_dir}/twl-themer-load.xml'):
            self.theme_entry_file = 'twl-themer-load.xml'
        elif QFile.exists(f'{self.theme_dir}/theme.xml'):
            self.theme_entry_file = 'theme.xml'
        else:
            print('unknown entry file')
            return
        

        decomp_xml_image_areas(f'{self.theme_dir}/{self.theme_entry_file}', self.theme_dir)
        self.display_theme()
        
        self.sprite_list.setCurrentIndex(self.sprite_list.indexAt(QPoint(0,0)))

    def save_theme(self):
        rebuild_xml_image_areas(self.theme_entry_file, self.theme_dir)
        self.open_directory(f'{self.theme_dir}/output')

    def list_clicked(self, current_selection, previous_selection):

        if not QFileInfo(self.model.filePath(self.proxy_model.mapToSource(current_selection))).isFile():
            return

        if not self.replace_action.isVisible():
            self.replace_action.setVisible(True)

        self.selected_sprite_filename = current_selection.data()
        self.selected_sprite_fullpath = self.model.filePath(self.proxy_model.mapToSource(current_selection))
        
        self.refresh_sprite_preview()

    def refresh_sprite_preview(self):
        pixmap = QPixmap(self.selected_sprite_fullpath)

        self.sprite_image_label.setPixmap(pixmap.scaled(QSize(pixmap.size().width(), pixmap.size().height()), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.sprite_image_label.setScaledContents(False)

    def single_replace_sprite(self, idx):
        size = QPixmap(f'{self.theme_dir}/{self.decomp_dir}/{self.selected_sprite_filename}').size()
        replacement_filename = QFileDialog.getOpenFileName(self, f'Select Replacement {self.selected_sprite_filename} - Size {size.width()}x{size.height()}')[0]
        
        if replacement_filename == '':
            return
        
        self.current_replacement_file = replacement_filename

        self.replace_sprite(self.current_replacement_file, f'{self.theme_dir}/{self.decomp_dir}/{self.selected_sprite_filename}')
        self.refresh_sprite_preview()

    def open_sprite_folder(self):
        self.open_directory(f'{self.theme_dir}/{self.decomp_dir}')

    def mass_replace_sprites(self):
        msgbox = QMessageBox()
        msgbox.setWindowIcon(QIcon('./ui/icon.png'))
        msgbox.setWindowTitle('Warning')
        msgbox.setText('Matching Sprite File Names' + ' '*30)
        msgbox.setInformativeText('Only files in the selected folder with names matching the dumped sprites will be replaced.')
        msgbox.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msgbox.setDefaultButton(QMessageBox.StandardButton.Ok)
        msgbox_return = msgbox.exec()

        if msgbox_return == QMessageBox.StandardButton.Cancel:
            return
        
        mass_replacement_folder = QFileDialog.getExistingDirectory(self, 'Select replacement sprites directory', self.theme_dir)

        sprite_qdir = QDir(f'{self.theme_dir}/{self.decomp_dir}')
        sprite_files = sprite_qdir.entryList(filters=QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)
        replacement_qdir = QDir(mass_replacement_folder)
        replacement_files = replacement_qdir.entryList(filters=QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)

        for f in replacement_files:
            if f in sprite_files:
                self.replace_sprite(f'{mass_replacement_folder}/{f}', f'{self.theme_dir}/{self.decomp_dir}/{f}')
                self.sprite_list.setCurrentIndex(self.model.index(f'{self.theme_dir}/{self.decomp_dir}/{f}'))

        self.refresh_sprite_preview()

    def replace_sprite(self, src: str, dst: str):
        if not QFile.exists(dst) or QFile.remove(dst):
            if not QFile.copy(src, dst):
                print('Could not copy file')
                return False
            else:
                if not self.save_atlas_action.isVisible():
                    self.save_atlas_action.setVisible(True)
        else:
            print('Could not remove file')
            return False

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
