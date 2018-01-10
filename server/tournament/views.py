from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from player.models import Player
from settings.models import TournamentType, City
from tournament.forms import TournamentRegistrationForm
from tournament.models import Tournament, TournamentResult, TournamentRegistration


def tournament_list(request, tournament_type=None, year=None):

    default_year_filter = 'all'
    try:
        current_year = year or default_year_filter
        if current_year != default_year_filter:
            current_year = int(current_year)
    except ValueError:
        current_year = default_year_filter

    years = [2018, 2017, 2016, 2015, 2014, 2013]

    if current_year != default_year_filter and current_year not in years:
        current_year = default_year_filter

    tournaments = Tournament.objects.all()

    if current_year != default_year_filter:
        tournaments = tournaments.filter(end_date__year=current_year)

    if tournament_type == 'ema':
        tournaments = tournaments.exclude(tournament_type__slug=TournamentType.CLUB)
    else:
        tournaments = tournaments.exclude(tournament_type__slug=TournamentType.FOREIGN_EMA)

    tournaments = tournaments.order_by('-end_date').prefetch_related('city')

    return render(request, 'tournament/list.html', {
        'tournaments': tournaments,
        'tournament_type': tournament_type,
        'years': years,
        'current_year': current_year,
        'page': tournament_type or 'tournament',
    })


def tournament_details(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)
    results = TournamentResult.objects.filter(tournament=tournament).order_by('place').prefetch_related('player')

    return render(request, 'tournament/details.html', {
        'tournament': tournament,
        'results': results,
        'page': 'tournament'
    })


def tournament_announcement(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)
    form = TournamentRegistrationForm(initial={'city': tournament.city.name_ru})
    registration_results = (TournamentRegistration.objects
                                                  .filter(tournament=tournament)
                                                  .prefetch_related('player')
                                                  .prefetch_related('city_object')
                                                  .order_by('created_on'))
    return render(request, 'tournament/announcement.html', {
        'tournament': tournament,
        'page': 'tournament',
        'form': form,
        'registration_results': registration_results
    })


@require_POST
@csrf_exempt
def tournament_registration(request, tournament_id):
    """
    csrf validation didn't work on the mobile safari, not sure why.
    Let's disable it for now, because it is not really important action
    """
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    form = TournamentRegistrationForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.tournament = tournament
        
        # it supports auto load objects only for Russian tournaments right now
        
        try:
            instance.player = Player.objects.get(first_name_ru=instance.first_name.title(), 
                                                 last_name_ru=instance.last_name.title())
        except (Player.DoesNotExist, Player.MultipleObjectsReturned):
            # TODO if multiple players are here, let's try to filter by city
            pass
        
        try:
            instance.city_object = City.objects.get(name_ru=instance.city)
        except City.DoesNotExist:
            pass
        
        instance.save()
        
        messages.success(request, _('Your registration was accepted!'))
    
    return redirect(tournament.get_url())
