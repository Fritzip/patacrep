from django.contrib import admin

from .models import Chord

class ChordAdmin(admin.ModelAdmin):
    list_display=('title','artist', 'updated_at', 'created_at')
    search_fields =('chord_id', 'title', 'artist')
    list_filter = ('updated_at', 'created_at')
    ordering = ('-created_at',)

admin.site.register(Chord, ChordAdmin)