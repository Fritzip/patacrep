import datetime

from django.db import models
from django.utils import timezone

class Chord(models.Model):
    artist = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    capo = models.IntegerField()
    nbcol = models.IntegerField()
    edited = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    chords = models.CharField(max_length=100)
    content = models.TextField(blank=False)
    file = models.FileField()
    removed_content_confirmation = models.CharField(blank=True, max_length=200)
    warning_lines = models.CharField(blank=True, max_length=200)
    comment = models.TextField(blank=True)
    NOTES = (        
        ("-", "-"),
        ("A", "A"),
        ("A#", "A#"),
        ("B", "B"),
        ("C", "C"),
        ("C#", "C#"),
        ("D", "D"),
        ("D#", "D#"),
        ("E", "E"),
        ("F", "F"),
        ("F#", "F#"),
        ("G", "G"),
        ("G#", "G#"),
    )
    start_note = models.CharField(max_length=2,
                  choices=NOTES,
                  default="-")


    class Meta:
        unique_together = ('artist', 'title')

    def __str__(self):
        return self.title + ' - ' + self.artist