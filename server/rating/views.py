import json
from datetime import datetime

import pytz
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404

from rating.models import Rating, RatingResult, RatingDelta
from tournament.models import Tournament


def rating_list(request):
    ratings = Rating.objects.all().order_by('order')

    return render(request, 'rating/list.html', {
        'ratings': ratings,
        'page': 'rating'
    })


def rating_details(request, slug, year=None, month=None, day=None):
    rating = get_object_or_404(Rating, slug=slug)

    rating_date = datetime.now().date()
    is_last = True
    if year and month and day:
        try:
            rating_date = datetime(int(year), int(month), int(day)).date()
            is_last = False
        except:
            raise Http404

    rating_results = (RatingResult.objects
                                  .filter(rating=rating)
                                  .prefetch_related('player')
                                  .prefetch_related('player__city')
                                  .prefetch_related('player__country')
                                  .order_by('place'))

    closest_date = RatingResult.objects.filter(rating=rating, date__lte=rating_date)
    if closest_date.exists():
        closest_date = closest_date.last().date
    else:
        raise Http404

    rating_results = rating_results.filter(date=closest_date)

    if rating.is_online():
        rating_results = rating_results.prefetch_related('player__tenhou')

    render_as_json = request.GET.get('json')
    if render_as_json is not None:
        data = []
        for rating_result in rating_results:
            data.append({
                'id': rating_result.player.id,
                'place': rating_result.place,
                'scores': float(rating_result.score),
                'name': rating_result.player.full_name,
                'city': rating_result.player.city.name
            })
        return JsonResponse(data, safe=False)

    graph_data = json.dumps(RatingResult.get_top10_graph_data(rating), default=float)

    return render(request, 'rating/details.html', {
        'rating': rating,
        'rating_results': rating_results,
        'rating_date': rating_date,
        'is_last': is_last,
        'page': 'rating',
        'graph_data': graph_data,
    })


def rating_tournaments(request, slug):
    rating = get_object_or_404(Rating, slug=slug)
    tournament_ids = (RatingDelta.objects
                      .filter(rating=rating)
                      .filter(is_active=True)
                      .values_list('tournament_id', flat=True))
    tournaments = (Tournament.public
                   .filter(id__in=tournament_ids)
                   .prefetch_related('city')
                   .prefetch_related('country')
                   .order_by('-end_date'))
    return render(request, 'rating/rating_tournaments.html', {
        'rating': rating,
        'tournaments': tournaments,
        'page': 'rating'
    })
