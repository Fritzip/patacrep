from django.shortcuts import render

from .models import Chord

def artists(request):
    artist_list = list(set(map(lambda x : x['artist'], list(Chord.objects.values('artist')))))
    artist_list.sort()
    artist_list = [(artist,  Chord.objects.filter(artist=artist).count()) for artist in artist_list]
    return {'artist_list': artist_list}
