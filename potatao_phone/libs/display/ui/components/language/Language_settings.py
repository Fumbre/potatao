from machine import Pin

LANGUAGES = [
    'Afrikaans', 'Albanian', 'Amharic', 'Arabic', 'Armenian', 'Azerbaijani',
    'Basque', 'Belarusian', 'Bengali', 'Bosnian', 'Bulgarian',
    'Catalan', 'Cebuano', 'Chinese Simp', 'Chinese Trad',
    'Corsican', 'Croatian', 'Czech',
    'Danish', 'Dutch',
    'English', 'Esperanto', 'Estonian',
    'Finnish', 'French', 'Frisian',
    'Galician', 'Georgian', 'German', 'Greek', 'Gujarati',
    'Haitian Cre', 'Hausa', 'Hawaiian', 'Hebrew', 'Hindi', 'Hmong', 'Hungarian',
    'Icelandic', 'Igbo', 'Indonesian', 'Irish', 'Italian',
    'Japanese', 'Javanese',
    'Kannada', 'Kazakh', 'Khmer', 'Korean', 'Kurdish', 'Kyrgyz',
    'Lao', 'Latin', 'Latvian', 'Lithuanian', 'Luxembourgish',
    'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Maori',
    'Marathi', 'Mongolian', 'Myanmar',
    'Nepali', 'Norwegian',
    'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi',
    'Romanian', 'Russian',
    'Samoan', 'Scottish Gael', 'Serbian', 'Sesotho', 'Shona',
    'Sindhi', 'Sinhala', 'Slovak', 'Slovenian', 'Somali', 'Spanish',
    'Sundanese', 'Swahili', 'Swedish',
    'Tajik', 'Tamil', 'Telugu', 'Thai', 'Turkish',
    'Ukrainian', 'Urdu', 'Uzbek',
    'Vietnamese',
    'Welsh',
    'Xhosa',
    'Yiddish', 'Yoruba',
    'Zulu'
]

class LanguageSettings:
    def __init__(self):
        self.current_index = 0

    def next(self):
        # Go to the next language
        self.current_index = (self.current_index + 1) % len(LANGUAGES)

    def previous(self):
        # Go back to the previous language
        self.current_index = (self.current_index - 1) % len(LANGUAGES)

    def get_language(self):
        # Returns the full language name
        return LANGUAGES[self.current_index]

    def get_abbreviation(self):
        # Returns language abreviated in uppercase (e.g. "EN", "FR")
        return LANGUAGES[self.current_index][:2].upper()
    
    