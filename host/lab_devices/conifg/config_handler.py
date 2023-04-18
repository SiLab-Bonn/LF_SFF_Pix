import os

class update_config():
    def __init__(self, file_path):
        self._cached_stamp = os.stat(file_path).st_mtime
        self.file = file_path

    def check_config(self, dut):
        stamp = os.stat(self.file).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            if dut: dut.load_config(self.file)
            print('file has changed')
