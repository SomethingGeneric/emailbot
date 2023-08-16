import subprocess

class SystemResponder:
    def __init__(self):
        self.trigger = "$"
        self.trigger_start = True
    def process(self, message):
        msg = message.replace(self.trigger, "")
        return subprocess.check_output(["/bin/bash","-c", f'"{msg}"']).decode('utf-8').strip()