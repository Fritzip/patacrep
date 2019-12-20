import datetime

from django.db import models
from django.utils import timezone

class Chord(models.Model):
    artist = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    capo = models.IntegerField()
    edited = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    chords = models.CharField(max_length=100)
    content = models.TextField(blank=False)
    file = models.FileField()
    deleted_lines = models.CharField(blank=True, max_length=200)
    warning_lines = models.CharField(blank=True, max_length=200)
    handled_lines = models.CharField(blank=True, max_length=200)

    comment = models.TextField(blank=True)
    NOTES = (        
        ("-", "-"),
        ("a", "A"),
        ("as", "A#"),
        ("b", "B"),
        ("c", "C"),
        ("cs", "C#"),
        ("d", "D"),
        ("ds", "D#"),
        ("e", "E"),
        ("f", "F"),
        ("fs", "F#"),
        ("g", "G"),
        ("gs", "G#"),
    )
    start_note = models.CharField(max_length=2,
                  choices=NOTES,
                  default="-")


    class Meta:
        unique_together = ('artist', 'title')

    def __str__(self):
        return self.title + ' - ' + self.artist

from django.forms import ModelForm

class ChordForm(ModelForm):
    class Meta:
        model = Chord
        fields = ['start_note']