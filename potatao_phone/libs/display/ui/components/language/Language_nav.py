from libs.display.ui.components.language.Language_settings import LanguageSettings

class LanguageNav:
    def __init__(self):
        # Get the current language
        self.language_settings = LanguageSettings()

    def get_abbreviation(self):
        # Returns the abbreviation of the current language (e.g. "EN", "FR")
        return self.language_settings.get_abbreviation()

    def get_language(self):
        # Returns the full language name
        return self.language_settings.get_language()
    
