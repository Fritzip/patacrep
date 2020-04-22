from django.contrib import admin

from .models import Chord

# admin.site.register(Chord)

class ChordAdmin(admin.ModelAdmin):
    list_display=('chord_id','title','artist')
    search_fields =('title','artist')

admin.site.register(Chord, ChordAdmin)