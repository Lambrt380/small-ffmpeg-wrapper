# pip install pyqt6, and install ffmpeg separately
import re
import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


FORMATS = {
    "mp4": (["h.264", "h.265", "copy", "none"], ["aac", "mp3", "copy", "none"]),
    "mkv": (
        ["h.264", "h.265", "vp9", "copy", "none"],
        ["aac", "mp3", "opus", "flac", "copy", "none"],
    ),
    "webm": (["vp9", "copy", "none"], ["opus", "vorbis", "copy", "none"]),
    "mp3": (["none"], ["mp3"]),
    "wav": (["none"], ["pcm"]),
    "flac": (["none"], ["flac"]),
    "ogg": (["none"], ["vorbis", "opus"]),
    "m4a": (["none"], ["aac"]),
}
CODECS = {
    "h.264": "libx264",
    "h.265": "libx265",
    "vp9": "libvpx-vp9",
    "aac": "aac",
    "mp3": "libmp3lame",
    "opus": "libopus",
    "vorbis": "libvorbis",
    "flac": "flac",
    "pcm": "pcm_s16le",
    "copy": "copy",
}


class Converter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ffmpeg converter")
        self.resize(500, 270)
        self.setStyleSheet("QLineEdit, QComboBox, QPushButton { padding: 4px; }")

        self.input = QLineEdit()
        self.output = QLineEdit()
        self.format = QComboBox()
        self.format.addItems(FORMATS)
        self.video = QComboBox()
        self.audio = QComboBox()
        self.controls = [self.input, self.output, self.format, self.video, self.audio]

        layout = QVBoxLayout(self)
        form = QFormLayout()
        for label, field, browse in (
            ("input file", self.input, self.browse_input),
            ("save to", self.output, self.browse_output),
        ):
            row = QHBoxLayout()
            button = QPushButton("browse...")
            button.clicked.connect(browse)
            row.addWidget(field)
            row.addWidget(button)
            form.addRow(label, row)
            self.controls.append(button)
        form.addRow("format", self.format)
        form.addRow("video codec", self.video)
        form.addRow("audio codec", self.audio)
        layout.addLayout(form)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.status = QLabel("ready")
        self.status.setWordWrap(True)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        self.convert_button = QPushButton("convert")
        self.cancel_button = QPushButton("cancel")
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.convert_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_progress)
        self.process.readyReadStandardError.connect(self.read_errors)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.convert_button.clicked.connect(self.convert)
        self.cancel_button.clicked.connect(self.cancel)
        self.format.currentTextChanged.connect(self.update_format)
        self.update_format()

    def browse_input(self):
        filename, _ = QFileDialog.getOpenFileName(self, "pick a file")
        if filename:
            self.input.setText(filename)
            source = Path(filename)
            name = f"{source.stem}_converted.{self.format.currentText()}"
            self.output.setText(str(source.with_name(name)))

    def browse_output(self):
        extension = self.format.currentText()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "save it here",
            self.output.text(),
            f"{extension} (*.{extension})",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if filename:
            self.output.setText(str(Path(filename).with_suffix("." + extension)))

    def update_format(self):
        video, audio = FORMATS[self.format.currentText()]
        self.video.clear()
        self.audio.clear()
        self.video.addItems(video)
        self.audio.addItems(audio)
        self.video.setEnabled(len(video) > 1)
        target = Path(self.output.text())
        if target.name:
            self.output.setText(
                str(target.with_suffix("." + self.format.currentText()))
            )

    def set_busy(self, busy):
        for control in self.controls:
            control.setEnabled(not busy)
        if not busy:
            self.video.setEnabled(self.video.count() > 1)
        self.convert_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)

    def convert(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            QMessageBox.warning(
                self, "no ffmpeg", "can't find ffmpeg, install it and try again"
            )
            return
        if not self.input.text().strip() or not self.output.text().strip():
            QMessageBox.warning(
                self,
                "pick the files first",
                "pick an input file and somewhere to save it",
            )
            return
        try:
            source = Path(self.input.text()).expanduser().resolve()
            target = Path(self.output.text()).expanduser()
            target = target.with_suffix("." + self.format.currentText()).resolve()
        except (OSError, ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "path looks wrong", str(error))
            return
        if not source.is_file():
            QMessageBox.warning(self, "can't find it", "can't find the input file")
            return
        if source == target or (target.exists() and source.samefile(target)):
            QMessageBox.warning(
                self,
                "same file",
                "that's the input file, pick somewhere else to save it",
            )
            return
        video, audio = self.video.currentText(), self.audio.currentText()
        if video == "none" and audio == "none":
            QMessageBox.warning(
                self,
                "nothing to convert",
                "leave video or audio on so there's something to convert",
            )
            return
        self.output.setText(str(target))
        if target.exists():
            answer = QMessageBox.question(
                self,
                "replace this?",
                f"replace {target.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        args = ["-y", "-nostdin", "-i", str(source), "-progress", "pipe:1", "-nostats"]
        if video == "none":
            args += ["-vn"]
        else:
            args += ["-map", "0:V:0?", "-c:v", CODECS[video]]
        if audio == "none":
            args += ["-an"]
        else:
            args += ["-map", "0:a:0?", "-c:a", CODECS[audio]]
        args += [str(target)]

        self.duration = 0
        self.errors = ""
        self.cancelled = False
        self.progress.setRange(0, 0)
        self.status.setText("converting...")
        self.set_busy(True)
        self.process.start(ffmpeg, args)

    def read_errors(self):
        self.errors = (
            self.errors
            + bytes(self.process.readAllStandardError()).decode(errors="replace")
        )[-12000:]
        if not self.duration:
            match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", self.errors)
            if match:
                hours, minutes, seconds = map(float, match.groups())
                self.duration = hours * 3600 + minutes * 60 + seconds
                if self.duration:
                    self.progress.setRange(0, 100)

    def read_progress(self):
        while self.process.canReadLine():
            line = bytes(self.process.readLine()).decode(errors="replace").strip()
            if line.startswith("out_time_us=") and self.duration:
                try:
                    seconds = int(line.split("=", 1)[1]) / 1_000_000
                except ValueError:
                    continue
                self.progress.setValue(
                    max(0, min(99, int(seconds / self.duration * 100)))
                )

    def finished(self, code, exit_status):
        self.read_errors()
        self.read_progress()
        self.set_busy(False)
        self.progress.setRange(0, 100)
        if self.cancelled:
            self.progress.setValue(0)
            self.status.setText("stopped, might've left an unfinished file")
        elif code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            self.progress.setValue(100)
            self.status.setText("done :3")
        else:
            self.progress.setValue(0)
            self.status.setText("ffmpeg didn't like that")
            QMessageBox.critical(
                self, "ffmpeg error", self.errors[-2500:] or "ffmpeg stopped"
            )

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.set_busy(False)
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.status.setText("ffmpeg won't start")
            QMessageBox.critical(self, "ffmpeg error", self.process.errorString())

    def cancel(self):
        self.cancelled = True
        self.cancel_button.setEnabled(False)
        self.process.kill()

    def closeEvent(self, event):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.cancel()
            self.process.waitForFinished(2000)
        event.accept()


if __name__ == "__main__":
    mugen = QApplication(sys.argv)
    window = Converter()
    window.show()
    sys.exit(mugen.exec())
