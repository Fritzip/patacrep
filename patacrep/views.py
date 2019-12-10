from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import DetailView

from .models import Chord, ChordForm
from .scripts import update_all, clean_chord, format_content

import random

def get_chord_name_from_id(pkid):
    return str(Chord.objects.get(pk=pkid))

def index(request):
    chords_list = Chord.objects.order_by('artist')#[:5]
    dartist = {}
    for chord in chords_list:
        try:
            dartist[chord.artist].append(chord)
        except :
            dartist[chord.artist] = [chord]

    context = {'dartist': dartist, 'nb_chords':Chord.objects.count()}

    if request.method == 'POST' and 'update' in request.POST:
            output = update_all() 
            output['new_to_db'] = [get_chord_name_from_id(pkid) for pkid in output['new_to_db']]
            output['already_in_db'] = [get_chord_name_from_id(pkid) for pkid in output['already_in_db']]
            output['duplicates'] = [get_chord_name_from_id(pkid) for pkid in output['duplicates']]
            context['output'] = output

    return render(request, 'patacrep/index.html', context)

class ChordDetail(DetailView):
    model = Chord
    template_name = 'patacrep/detail.html'

    def get_context_data(self, **kwargs):
        self.object.content = format_content(self.object.content)
        
        rcc = self.object.removed_content_confirmation.split(', ')

        new_content = []
        for i, line in enumerate(self.object.content.split('\n')):
            if str(i) not in rcc:
                new_content.append(line)

        self.object.content = '\n'.join(new_content)

        # Call the base implementation first to get a context
        context = super(ChordDetail, self).get_context_data(**kwargs)
        context['form'] = ChordForm

        sorted_chord_list = list(Chord.objects.order_by('artist', 'title').values_list('id', flat=True))
        idx = sorted_chord_list.index(self.object.id)

        next_id = None
        prev_id = None

        if idx < len(sorted_chord_list) - 1:
            next_id = sorted_chord_list[idx + 1]

        if idx > 0:
            prev_id = sorted_chord_list[idx - 1]

        rand_id = random.choice(sorted_chord_list)
            
        context['next'] = next_id
        context['prev'] = prev_id
        context['rand'] = rand_id

        qs_other_chord_of_artist = Chord.objects.filter(artist=self.object.artist).exclude(id=self.object.id)
        other_chord_of_artist = []

        for ch in qs_other_chord_of_artist:
            other_chord_of_artist.append((ch.id, ch.title))

        context['other_chords'] = other_chord_of_artist

        return context

def toggle_favorite(request):
    chord_pk = request.POST['chord_pk']
    chord = get_object_or_404(Chord, pk=chord_pk)
    chord.favorite = not chord.favorite
    chord.save()

    data = {
        'added': chord.favorite
    }
    return JsonResponse(data)

def change_start_note(request):
    chord_pk = request.POST['chord_pk']
    chord = get_object_or_404(Chord, pk=chord_pk)
    chord.start_note = request.POST['new_start_note']
    chord.save()

    data = {}
    return JsonResponse(data)

def clean(request):
    chord_pk = request.POST['chord_pk']
    clean_chord(chord_pk)
    
    data = {
        'pkid': chord_pk
    }
    return JsonResponse(data)


def save_edit(request):
    rm_lines = request.POST.getlist('rm_lines[]')
    chord_pk = request.POST['chord_pk']

    Chord.objects.filter(pk=chord_pk).update(removed_content_confirmation=", ".join(rm_lines))
    data = {
        'pkid': chord_pk
    }
    return JsonResponse(data)

def confirm_remove(request, chord_id):
    chord = get_object_or_404(Chord, pk=chord_id)

    rcc = chord.removed_content_confirmation.split(', ')
    wl = chord.warning_lines.split(', ')

    modified_lines = []
    for i, line in enumerate(chord.content.split('\n')):
        if str(i) in rcc:
            modified_lines.append((i, line, True, False))
        elif str(i) in wl:
            modified_lines.append((i, line, False, True))
        else:
            modified_lines.append((i, line, False, False))

    return render(request, 'patacrep/confirm_remove.html', {'chord': chord, 'modified_lines': modified_lines})

###########################################
# WIP

def edit(request, chord_id):
    chord = get_object_or_404(Chord, pk=chord_id)
    return render(request, 'patacrep/edit.html', {'chord': chord})

def next(request):
    chord_pk = request.POST['chord_pk']
    chord = Chord.objects.get(pk=chord_pk)
    chords = Chord.objects.order_by('artist')
    save_next = False
    for c in chords:
        if save_next:
            next_chord = c
            break
        if c.id == chord.id:
            save_next = True

    # json response
    print(next_chord.pk)
    data = {
        'pkid': next_chord.pk
    }
    return JsonResponse(data)

def save_and_next(request):
    # save
    modified_content = request.GET.get('modified_content', None)
    chord_pk = request.GET.get('chord_pk', None)
    Chord.objects.filter(pk=chord_pk).update(content=modified_content.rstrip())
    Chord.objects.filter(pk=chord_pk).update(edited=True)

    # get next
    chord = Chord.objects.get(pk=chord_pk)
    chords = Chord.objects.order_by('artist').filter(~Q(removed_content_confirmation = "")|~Q(warning_lines = ""))
    save_next = False
    for c in chords:
        print(c)
        if save_next:
            print("FOUND IIIIIIIIIIIIIiiiiiit")
            next_chord = c
            # break
            save_next = False
        if c.id == chord.id:
            save_next = True

    clean_chord(chord_pk)

    # json response
    data = {
        'pkid': next_chord.pk
    }
    return JsonResponse(data)

