import os,random, json

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import DetailView

from datetime import datetime, timedelta

from .models import Chord, ChordForm
from .scripts import update_all, clean_chord, format_content, comma_sep_int_string_to_list, int_list_to_comma_sep_string

def get_chord_name_from_id(pkid):
    return str(Chord.objects.get(pk=pkid))

def index(request):
    chords_list = Chord.objects.values('chord_id','artist','title','favorite','in_project','edited','warning_lines').order_by('artist')
    last_n_days = datetime.today() - timedelta(days=14)
    last_created = Chord.objects.filter(created_at__gte=last_n_days).order_by('-created_at').values_list('chord_id', flat=True)[:30]
    dartist = {}
    for chord in chords_list:
        try:
            dartist[chord['artist']].append(chord)
        except :
            dartist[chord['artist']] = [chord]

    context = {'dartist': dartist, 'last_created': last_created, 'nb_chords':Chord.objects.count(), 'nb_warn': Chord.objects.filter(~Q(warning_lines__exact='')).count()}

    return render(request, 'patacrep/index.html', context)

def update(request):
    context = {'nb_chords':Chord.objects.count()}

    if request.user.is_superuser:
            output = update_all() 
            output['new_to_db'] = [get_chord_name_from_id(pkid) for pkid in output['new_to_db']]
            output['updated_in_db'] = [get_chord_name_from_id(pkid) for pkid in output['updated_in_db']]
            output['already_in_db'] = [get_chord_name_from_id(pkid) for pkid in output['already_in_db']]
            # output['duplicates'] = [get_chord_name_from_id(pkid) for pkid in output['duplicates']]
            d = {}
            for pkid, filename in output['duplicates']:
                if pkid in d:
                    d[pkid].append(filename)
                else:
                    d[pkid] = [filename]

            pkids = list(d.keys())
            for pkid in pkids:
                d[pkid].append(os.path.basename(Chord.objects.only('file').get(pk=pkid).file.name))
                d[get_chord_name_from_id(pkid)] = d.pop(pkid)

            output['duplicates'] = d
            context['output'] = output

    return render(request, 'patacrep/update.html', context)

class ChordDetail(DetailView):
    model = Chord
    template_name = 'patacrep/detail.html'

    def get_context_data(self, **kwargs):
        self.object.content = format_content(self.object.content)
        
        deleted_lines = comma_sep_int_string_to_list(self.object.deleted_lines)
        new_content = []
        for i, line in enumerate(self.object.content.split('\n')):
            if i not in deleted_lines:
                new_content.append(line)

        self.object.content = '\n'.join(new_content)

        # Call the base implementation first to get a context
        context = super(ChordDetail, self).get_context_data(**kwargs)
        context['form'] = ChordForm

        sorted_chord_list = list(Chord.objects.order_by('artist', 'title').values_list('chord_id', flat=True))
        idx = sorted_chord_list.index(self.object.chord_id)

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

        qs_other_chord_of_artist = Chord.objects.filter(artist=self.object.artist).exclude(pk=self.object.chord_id)
        other_chord_of_artist = []

        for ch in qs_other_chord_of_artist:
            other_chord_of_artist.append((ch.chord_id, ch.title))

        context['other_chords'] = other_chord_of_artist

        return context

from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin

class ChordDelete(UserPassesTestMixin, DeleteView):
    model = Chord
    success_url = reverse_lazy('patacrep:index')

    def test_func(self):
        return self.request.user.is_superuser and not self.get_object().edited

from django.contrib.auth.decorators import login_required

def toggle_favorite(request):
    success = False
    added = False
    message = ""
    if request.user.is_superuser:
        chord_pk = request.POST['chord_pk']
        chord = get_object_or_404(Chord, pk=chord_pk)
        chord.favorite = not chord.favorite
        added = chord.favorite
        chord.save()
        success = True
        if chord.favorite:
            message = "Successfully added to favorite"
        else:
            message = "Successfully removed from favorite"
    else:
        message = "You need admin privilege for that"

    data = {
        'added' : added,
        'success' : success,
        'message': message
    }
    return JsonResponse(data)

def toggle_project(request):
    success = False
    added = False
    message = ""
    if request.user.is_superuser:
        chord_pk = request.POST['chord_pk']
        chord = get_object_or_404(Chord, pk=chord_pk)
        chord.in_project = not chord.in_project
        added = chord.in_project
        chord.save()
        success = True
        if chord.in_project:
            message = "Successfully added to project"
        else:
            message = "Successfully removed from project"
    else:
        message = "You need admin privilege for that"

    data = {
        'added' : added,
        'success' : success,
        'message': message
    }
    return JsonResponse(data)

def toggle_edited(request):
    success = False
    added = False
    message = ""
    if request.user.is_superuser:
        chord_pk = request.POST['chord_pk']
        chord = get_object_or_404(Chord, pk=chord_pk)
        chord.edited = not chord.edited
        added = chord.edited
        chord.save()
        success = True
        if chord.edited:
            message = "Chord is now edited"
        else:
            message = "Chord is now unedited"
    else:
        message = "You need admin privilege for that"

    data = {
        'added' : added,
        'success' : success,
        'message': message
    }
    return JsonResponse(data)

def change_start_note(request):
    success = False
    message = ""
    if request.user.is_superuser:
        chord_pk = request.POST['chord_pk']
        chord = get_object_or_404(Chord, pk=chord_pk)
        chord.start_note = request.POST['new_start_note']
        chord.save()
        message = "New start note set to : {}".format(chord.get_start_note_display())
        success = True
    else:
        message = "You need admin privilege for that"
    data = {
        'success': success,
        'message': message,
    }
    return JsonResponse(data)

def change_capo(request):
    success = False
    message = ""
    if request.user.is_superuser:
        chord_pk = request.POST['chord_pk']
        chord = get_object_or_404(Chord, pk=chord_pk)
        chord.capo_perso = request.POST['new_capo']
        chord.save()
        message = "Capo perso set to : {}".format(chord.capo_perso)
        success = True
    else:
        message = "You need admin privilege for that"
    data = {
        'success': success,
        'message': message,
    }
    return JsonResponse(data)

@login_required
def clean(request):
    chord_pk = request.POST['chord_pk']
    clean_chord(chord_pk)
    
    data = {
        'pkid': chord_pk
    }
    return JsonResponse(data)

@login_required
def save_edit(request):
    rm_lines = list(map(int, request.POST.getlist('rm_lines[]')))
    warn_lines = list(map(int, request.POST.getlist('warn_lines[]')))
    edited_lines = request.POST['edited_lines']
    edited_lines = json.loads(edited_lines)

    chord_pk = request.POST['chord_pk']
    chord = get_object_or_404(Chord, pk=chord_pk)

    handled_lines = comma_sep_int_string_to_list(chord.handled_lines)
    old_warn_lines = comma_sep_int_string_to_list(chord.warning_lines)
    old_deleted_lines = comma_sep_int_string_to_list(chord.deleted_lines)

    for old_warn_line in old_warn_lines:
        if old_warn_line not in warn_lines:
            handled_lines.append(old_warn_line)

    for old_auto_deleted_line in old_deleted_lines:
        if old_auto_deleted_line not in rm_lines:
            handled_lines.append(old_auto_deleted_line)

    if edited_lines:
        modlines = list(map(int, edited_lines.keys()))

        content = getattr(chord, 'content')

        new_content = []
        for i, line in enumerate(content.split('\n')):
            if i in modlines:
                new_content.append(edited_lines[str(i)])
                handled_lines.append(i)
            else:
                new_content.append(line)

        chord.content = '\n'.join(new_content)
        chord.edited = True
    
    chord.deleted_lines=int_list_to_comma_sep_string(rm_lines)
    chord.warning_lines=int_list_to_comma_sep_string(warn_lines)
    chord.handled_lines=int_list_to_comma_sep_string(handled_lines)

    chord.save()

    data = {
        'pkid': chord_pk
    }
    return JsonResponse(data)

@login_required
def confirm_remove(request, chord_id):
    chord = get_object_or_404(Chord, pk=chord_id)

    deleted_lines = comma_sep_int_string_to_list(chord.deleted_lines)
    warning_lines = comma_sep_int_string_to_list(chord.warning_lines)

    modified_lines = []
    for i, line in enumerate(chord.content.split('\n')):
        line = line.replace('\r', '')
        if i in deleted_lines:
            modified_lines.append((i, line, True, False))
        elif i in warning_lines:
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
    chords = Chord.objects.order_by('artist').filter(~Q(deleted_lines = "")|~Q(warning_lines = ""))
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

