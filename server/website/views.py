from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import translation
from django.utils.translation import get_language
from haystack.forms import ModelSearchForm

from club.models import Club
from player.models import Player
from player.tenhou.models import TenhouNickname
from rating.models import Rating, RatingResult
from settings.models import City
from tournament.models import Tournament, TournamentResult


def home(request):
    rating = Rating.objects.get(type=Rating.RR)
    rating_results = (RatingResult.objects
                                  .filter(rating=rating)
                                  .filter(is_last=True)
                                  .prefetch_related('player')
                                  .prefetch_related('player__city')
                                  .order_by('place'))[:16]

    upcoming_tournaments = (Tournament.public
                                      .filter(is_upcoming=True)
                                      .exclude(tournament_type=Tournament.FOREIGN_EMA)
                                      .prefetch_related('city')
                                      .order_by('start_date'))

    return render(request, 'website/home.html', {
        'page': 'home',
        'rating_results': rating_results,
        'rating': rating,
        'upcoming_tournaments': upcoming_tournaments
    })


def about(request):
    template = 'about_en.html'
    if get_language() == 'ru':
        template = 'about_ru.html'

    return render(request, 'website/{}'.format(template), {
        'page': 'about'
    })


def contacts(request):
    template = 'contacts_en.html'
    if get_language() == 'ru':
        template = 'contacts_ru.html'

    return render(request, 'website/{}'.format(template), {
        'page': 'contacts'
    })


def search(request):
    query = request.GET.get('q', '')

    search_form = ModelSearchForm(request.GET, load_all=True)
    results = search_form.search()

    query_list = [x.object for x in results]
    players = [x for x in query_list if x.__class__ == Player]

    return render(request, 'website/search.html', {
        'players': players,
        'search_query': query
    })


def city_page(request, slug):
    city = get_object_or_404(City, slug=slug)

    clubs = Club.objects.filter(city=city).prefetch_related('city')
    tournaments = Tournament.public.filter(city=city).order_by('-end_date').prefetch_related('city')

    players = Player.objects.filter(city=city).prefetch_related('city')
    for player in players:
        player.rank = -1

        tenhou_object = player.tenhou_object
        if tenhou_object:
            player.rank = tenhou_object.rank
            player.rank_display = tenhou_object.get_rank_display()

    players = sorted(players, key=lambda x: (-x.rank, x.full_name))

    return render(request, 'website/city.html', {
        'city': city,
        'clubs': clubs,
        'players': players,
        'tournaments': tournaments
    })


def players_api(request):
    translation.activate('ru')

    players = (Player.objects
               .filter(country__code='RU')
               .prefetch_related('city')
               .prefetch_related('tenhou')
               .order_by('id'))

    data = []
    for player in players:
        tenhou_query = player.tenhou.filter(is_main=True).first()
        tenhou_data = None
        if tenhou_query:
            tenhou_data = {
                'username': tenhou_query.tenhou_username,
                'rank': tenhou_query.get_rank_display(),
                'date': tenhou_query.username_created_at.strftime('%Y-%m-%d')
            }

        data.append({
            'id': player.id,
            'name': player.full_name,
            'city': player.city and player.city.name or '',
            'ema_id': player.ema_id or '',
            'tenhou': tenhou_data
        })
    return JsonResponse(data, safe=False)


def online_tournament_rules(request):
    return render(request, 'website/rules.html')


def iormc_2018(request):
    spring_id = 294
    summer_id = 310
    winter_id = 323

    tournament_ids = [spring_id, summer_id, winter_id]
    results = TournamentResult.objects.filter(tournament_id__in=tournament_ids).prefetch_related('player')
    data = {}
    for result in results:
        if result.player.is_hide or result.player.is_replacement:
            continue

        if not data.get(result.player_id):
            data[result.player_id] = {
                'player': result.player,
                'first': 0,
                'second': 0,
                'third': 0,
                'total': 0,
                'number_of_played': 0
            }

        if result.tournament_id == spring_id:
            data[result.player_id]['first'] = result.scores
            data[result.player_id]['number_of_played'] += 1

        if result.tournament_id == summer_id:
            data[result.player_id]['second'] = result.scores
            data[result.player_id]['number_of_played'] += 1

        if result.tournament_id == winter_id:
            data[result.player_id]['third'] = result.scores
            data[result.player_id]['number_of_played'] += 1

    for key, value in data.items():
        if data[key]['number_of_played'] <= 2:
            data[key]['total'] = value['first'] + value['second'] + value['third']
        else:
            first = value['first'] + value['second']
            second = value['first'] + value['third']
            third = value['second'] + value['third']

            data[key]['total'] = max([first, second, third])

    data = sorted(data.values(), key=lambda x: (x['number_of_played'] >= 2, x['total']), reverse=True)

    return render(request, 'website/iormc.html', {
        'data': data
    })
