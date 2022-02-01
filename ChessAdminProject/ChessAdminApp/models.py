from django.db import models
from django.db.models import F, Q
from django.forms import ModelForm
from datetime import datetime
import math
from django.conf import settings
from computed_property import ComputedIntegerField
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

MATCH_RESULT_CHOICES = [("WIN", "WIN"), ("DRAW", "DRAW"),]
MATCH_STATUS_CHOICES = [("SCHEDULED", "SCHEDULED"),("PLAYING", "PLAYING"),("COMPLETED", "COMPLETED"),("CANCELED", "CANCELED")]
BOOLEAN_CHOICES = [(True,'Yes'),(False,'No')]
        
class Player(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_joined = models.DateTimeField(null=True, blank=True)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(max_length=100, null=True, blank=True, choices=BOOLEAN_CHOICES)
    ranking = models.IntegerField(null=True, blank=True, default=0)
    points = models.IntegerField(null=True, blank=True, default=0)
                                
    def __str__(self):
        return f"Player: {self.first_name} {self.last_name}  | Current Ranking: {self.ranking}  "
        
    def save(self, *args, **kwargs):
        _all_players_count = Player.objects.count()
        if self._state.adding:
            self.ranking = _all_players_count + 1
            
        super().save(*args, **kwargs)  # Call the "real" save() method.
        
    class Meta:                                                                                                          
        verbose_name_plural = " Players"
    
class Match(models.Model):
    scheduled_date = models.DateTimeField(null=True, blank=True, default=datetime.now)
    status = models.CharField(max_length=50, null=True, blank=False, choices=MATCH_STATUS_CHOICES, default='SCHEDULED')
    player_one = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player_one', null=True, blank=True)
    player_two = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player_two', null=True, blank=True)
    venue = models.CharField(max_length=100, null=True, blank=True)
    match_result = models.CharField(max_length=100, null=True, blank=True, choices=MATCH_RESULT_CHOICES)
    winner = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='winner', null=True, blank=True)
    player_one_entry_ranking = models.IntegerField(null=True, blank=True)
    player_two_entry_ranking = models.IntegerField(null=True, blank=True)
    player_one_ranking_change = models.IntegerField(null=True, blank=True)
    player_two_ranking_change = models.IntegerField(null=True, blank=True)
    player_one_points_change = models.IntegerField(null=True, blank=True)
    player_two_points_change = models.IntegerField(null=True, blank=True)
    follow_live = models.CharField(max_length=255, null=True, blank=True, default='https://<LINK TO BE COMPLETED>')
      
    def __str__(self):
        return f"Current Status: {self.status}  |  Date: {self.scheduled_date}  |  {self.player_one.first_name} {self.player_one.last_name} vs {self.player_two.first_name} {self.player_two.last_name}" if self.player_one and self.player_two else f"Current Status: {self.status}  |  Date: {self.scheduled_date}"
        
    def save(self, *args, **kwargs):
        
        if self.status == "PLAYING":
            self.player_one_entry_ranking = self.player_one.ranking
            self.player_two_entry_ranking = self.player_two.ranking
        
        if self.status == "COMPLETED":
        
            _player_one_entry_ranking = self.player_one.ranking
            _player_two_entry_ranking = self.player_two.ranking
            self.player_one_entry_ranking = self.player_one.ranking
            self.player_two_entry_ranking = self.player_two.ranking
            
            _higher_rank_value=_player_one_entry_ranking if _player_one_entry_ranking < _player_two_entry_ranking else _player_two_entry_ranking    
            _lower_rank_value=_player_one_entry_ranking if _player_one_entry_ranking > _player_two_entry_ranking else _player_two_entry_ranking
            
            if self.match_result == "DRAW":
                _higher_rank_shift=0
                _lower_rank_shift = 0 if (_lower_rank_value - _higher_rank_value) == 1 else -1
                if _player_one_entry_ranking < _player_two_entry_ranking:
                    self.player_one_ranking_change = _higher_rank_shift
                    self.player_two_ranking_change = _lower_rank_shift
                else:
                    self.player_one_ranking_change = _lower_rank_shift
                    self.player_two_ranking_change = _higher_rank_shift
                _player_to_shift = Player.objects.get(ranking=_lower_rank_value-1)      
                _player_to_shift.ranking += 1
                _player_to_shift.save()
                self.player_one.ranking = _player_one_entry_ranking + self.player_one_ranking_change 
                self.player_one.save()   
                self.player_two.ranking = _player_two_entry_ranking + self.player_two_ranking_change
                self.player_two.save()
            
            if self.match_result == "WIN":
                _rank_difference = abs(_player_one_entry_ranking - _player_two_entry_ranking)
                _winner_points = 0 
                _looser_points = 0 
                 
                if ((_player_one_entry_ranking < _player_two_entry_ranking and self.winner == self.player_one) or (_player_two_entry_ranking < _player_one_entry_ranking and self.winner == self.player_two)):
                    self.player_one_ranking_change = 0
                    self.player_two_ranking_change = 0
                    _winner_points = 5 if (_rank_difference>=15) else 8 if (_rank_difference>=10) else 10
                    _looser_points = -5 if (_rank_difference>=15) else -8 if (_rank_difference>=10) else -10
                
                    if (self.winner == self.player_one):
                        self.player_one_points_change = _winner_points
                        self.player_two_points_change = _looser_points
                    else:
                        self.player_one_points_change = _looser_points
                        self.player_two_points_change = _winner_points 
                    
                else:
                    _winner_points = 50 if (_rank_difference>=15) else 25 if (_rank_difference>=10) else 15
                    _looser_points = -50 if (_rank_difference>=15) else -25 if (_rank_difference>=10) else -15
                    
                    _higher_rank_shift=0 if ((_lower_rank_value - _higher_rank_value)==2) else 1
                    _lower_rank_shift=-1 if ((_lower_rank_value - _higher_rank_value)==1) else math.floor((_lower_rank_value - _higher_rank_value) / 2) * -1
                    _player_to_shift = Player.objects.get(ranking=_higher_rank_value+1)       
                    _player_to_shift.ranking -= _higher_rank_shift
                    _player_to_shift.save()
                    
                    self.player_one_points_change = 0
                    self.player_two_points_change = 0
                    self.player_one_ranking_change = 0
                    self.player_two_ranking_change = 0
                    
                    if (self.winner == self.player_one):
                        self.player_one_ranking_change = _lower_rank_shift 
                        self.player_two_ranking_change = _higher_rank_shift # if ((_lower_rank_value - _higher_rank_value)!=2) else 0
                        self.player_one_points_change = _winner_points
                        self.player_two_points_change = _looser_points
                        Player.objects.filter(ranking__gte=(_player_one_entry_ranking + self.player_one_ranking_change),ranking__lte=_lower_rank_value).update(ranking=F('ranking')+1)    #,ranking__lte=_lower_rank_value,ranking!=_lower_rank_value
                    if (self.winner == self.player_two):
                        self.player_one_ranking_change = _higher_rank_shift #if ((_lower_rank_value - _higher_rank_value)!=2) else 0
                        self.player_two_ranking_change = _lower_rank_shift 
                        self.player_one_points_change = _looser_points
                        self.player_two_points_change = _winner_points
                        Player.objects.filter(ranking__gte=(_player_two_entry_ranking + self.player_two_ranking_change), ranking__lte=_lower_rank_value).update(ranking=F('ranking')+1)
                    
                _cur_player_one_points = self.player_one.points
                _cur_player_two_points = self.player_two.points
                if ((_cur_player_one_points + self.player_one_points_change) < 0):
                    self.player_one_points_change = _cur_player_one_points * -1    
                if ((_cur_player_two_points + self.player_two_points_change) < 0):
                    self.player_two_points_change = _cur_player_two_points * -1 
                
                self.player_one.ranking = _player_one_entry_ranking + self.player_one_ranking_change 
                self.player_one.points += self.player_one_points_change 
                self.player_one.save()   
                
                self.player_two.ranking = _player_two_entry_ranking + self.player_two_ranking_change
                self.player_two.points += self.player_two_points_change 
                self.player_two.save()
        
        super().save(*args, **kwargs)  
        
    class Meta:                                                                                                          
        constraints = [                      
            models.CheckConstraint(name='1_two_players_required', check=(Q(player_one__isnull=False, player_two__isnull=False)) & ~Q(player_one=F('player_two'))),
            models.CheckConstraint(name='2_complete_match_result', check=(Q(status='SCHEDULED', match_result__isnull=True) | Q(status='PLAYING', match_result__isnull=True) | Q(status='COMPLETED', match_result__isnull=False) | Q(status='CANCELED', match_result__isnull=True) )),
            models.CheckConstraint(name='3_winner_on_complete', check=(Q(match_result__isnull=True, winner__isnull=True) | Q(match_result__isnull=False, match_result='DRAW', winner__isnull=True) | Q(match_result__isnull=False, match_result='WIN', winner__isnull=False))),                                                                                                                                      
            models.CheckConstraint(name='4_winner_is_in_match', check=( Q(match_result='DRAW', winner__isnull=True) | Q(match_result='WIN', winner=F('player_one')) | Q(match_result='WIN', winner=F('player_two')) )),                                                                                                                                     
            models.CheckConstraint(name='5_playing_entry_ranks', check=(Q(status='SCHEDULED', player_one_entry_ranking__isnull=True, player_two_entry_ranking__isnull=True) | Q(status='PLAYING', player_one_entry_ranking__isnull=False, player_two_entry_ranking__isnull=False) | Q(status='COMPLETED', player_one_entry_ranking__isnull=False, player_two_entry_ranking__isnull=False) | Q(status='CANCELED'))),
            models.CheckConstraint(name='6_complete_match_ranking', check=(Q(match_result__isnull=True, player_one_ranking_change__isnull=True, player_two_ranking_change__isnull=True) | Q(match_result__isnull=False, player_one_ranking_change__isnull=False, player_two_ranking_change__isnull=False) ))]
            
        verbose_name_plural = "Matches"

class RankingEventData(models.Model):
    date = models.DateTimeField()
    name = models.CharField(max_length=50)
    points = models.IntegerField()
    rank = models.IntegerField()
    winratio =  models.DecimalField(max_digits = 5, decimal_places = 2)
    match_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.date} : {self.name}"
    
    class Meta:                                                                                                          
        verbose_name_plural = "Ranking events data"
        
class RankingEvent(models.Model):
    date_created = models.DateTimeField(null=True, blank=True)
    
                                
    def __str__(self):
        return f"Ranking Event: {self.id} - {self.date_created}"
        
    def save(self, *args, **kwargs):
    
        players_set = Player.objects.filter(is_active=True)
        for player in players_set.iterator():
            matches_set = Match.objects.filter(status='COMPLETED')        
            _matches_count = 0
            _matches_won = 0
            for match in matches_set.iterator():
                if match.player_one == player or match.player_two == player:
                    _matches_count += 1    
                if match.winner == player:
                    _matches_won += 1
            
            _win_ratio = 0
            if _matches_count > 0 :
                _win_ratio = _matches_won / _matches_count * 100           
                    
            RankingEventData.objects.create(date=self.date_created,name=player.first_name + ' ' + player.last_name,points=player.points,rank=player.ranking,winratio=_win_ratio,match_count=_matches_count)
        
        super().save(*args, **kwargs)  # Call the "real" save() method.

        
        
  