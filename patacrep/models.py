import datetime, os

from django.db import models
from django.dispatch import receiver
from django.utils import timezone

class Chord(models.Model):
    chord_id = models.AutoField(primary_key=True)
    song_id = models.PositiveIntegerField()
    artist = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    capo = models.IntegerField(default=0)
    capo_perso = models.IntegerField(default=0)
    edited = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    in_project = models.BooleanField(default=False)
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

    guitar_type = models.CharField(max_length=100, blank=True, null=True)
    votes = models.IntegerField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = ('artist', 'title')

    def __str__(self):
        return self.title + ' - ' + self.artist


@receiver(models.signals.post_delete, sender=Chord)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)

from django.forms import ModelForm

class ChordForm(ModelForm):
    class Meta:
        model = Chord
        fields = ['start_note']