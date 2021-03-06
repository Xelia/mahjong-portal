from modeltranslation.translator import translator, TranslationOptions

from club.models import Club


class ClubTranslationOptions(TranslationOptions):
    fields = ['name', 'description']


translator.register(Club, ClubTranslationOptions)
