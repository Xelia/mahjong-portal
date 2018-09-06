from collections import defaultdict
from datetime import date, timedelta
from random import random, randint

from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament
from utils.general import get_tournament_coefficient


class Rating(BaseModel):
    RR = 0
    EMA = 1
    CRR = 2
    ONLINE = 3

    TYPES = [
        [RR, 'RR'],
        [CRR, 'CRR'],
        [EMA, 'EMA'],
        [ONLINE, 'ONLINE']
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    type = models.PositiveSmallIntegerField(choices=TYPES)

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return self.name

    def is_online(self):
        return self.type == self.ONLINE


class RatingDelta(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_delta')
    tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, related_name='rating_delta')
    is_active = models.BooleanField(default=False)
    is_last = models.BooleanField(default=False)

    base_rank = models.DecimalField(decimal_places=2, max_digits=10)
    delta = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateField(default=None, null=True, blank=True, db_index=True)

    tournament_place = models.PositiveSmallIntegerField(default=0)

    def __unicode__(self):
        return self.tournament.name

    @property
    def coefficient_obj(self):
        return TournamentCoefficients.objects.get(rating=self.rating, tournament=self.tournament, date=self.date)

    @property
    def coefficient_value(self):
        coefficient_obj = self.coefficient_obj
        return get_tournament_coefficient(self.tournament_id, self.player, coefficient_obj.coefficient)


class RatingResult(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_results')

    score = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)
    place = models.PositiveIntegerField(default=None, null=True, blank=True)
    date = models.DateField(default=None, null=True, blank=True, db_index=True)
    is_last = models.BooleanField(default=False, db_index=True)

    rating_calculation = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.rating.name

    def get_deltas(self):
        return (RatingDelta.objects
                           .filter(player=self.player, rating=self.rating)
                           .filter(is_active=True)
                           .prefetch_related('player')
                           .prefetch_related('tournament')
                           .order_by('-tournament__end_date'))

    @classmethod
    def get_top10_graph_data(cls, rating):
        data_by_players = defaultdict(list)
        top_10_players = cls.objects.filter(rating=rating, is_last=True, place__lte=5).values_list('player_id', flat=True)
        for result in cls.objects.filter(rating=rating, player_id__in=top_10_players, date__gte=date.today() - timedelta(days=365)).order_by('date'):
            if data_by_players[result.player_id] and data_by_players[result.player_id][-1]['y'] == result.score:
                data_by_players[result.player_id].pop()
            data_by_players[result.player_id].append({'y': result.score, 'x': result.date.isoformat()})
        return [{
            'label': Player.objects.get(pk=player_id).full_name,
            'data': data_by_players[player_id],
            'fill': False,
            'borderColor': 'rgb({},{},{})'.format(randint(0, 255), randint(0, 255), randint(0, 255)),
            'cubicInterpolationMode': 'monotone',
        } for player_id in data_by_players]


class TournamentCoefficients(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rating_results')
    date = models.DateField(default=None, null=True, blank=True, db_index=True)

    coefficient = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    age = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)

    def __unicode__(self):
        return self.rating.name
