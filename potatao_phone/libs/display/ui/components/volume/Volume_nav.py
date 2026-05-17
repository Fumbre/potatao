from libs.display.ui.components.volume.Volume_settings import VolumeSettings

class VolumeNav:
    def __init__(self, ui):
        # Reference to the OledUI instance for drawing
        self.ui = ui

        # VolumeSettings instance to read the potentiometer
        self.volume_settings = VolumeSettings()

    def get_volume(self):
        # Reads and returns the current volume percentage
        return self.volume_settings.read()
    
