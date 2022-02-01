from django.contrib import admin
from django.forms import ModelForm
from .models import Player
from .models import Match
from django.db.models import F, Q, ExpressionWrapper, IntegerField
from django.db.models import Value, Count, OuterRef, Subquery, Sum
from django.db.models.expressions import RawSQL
admin.site.site_header = 'Netstock Chess Club - Admin Site'


class PlayerForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(PlayerForm, self).__init__(*args, **kwargs)
        #self.initial['created_by'] = self.request.user
        if not self.request.user.is_superuser:
            self.fields['ranking'].widget.attrs['readonly'] = True
            self.fields['points'].widget.attrs['readonly'] = True
            
    class Meta:
        model = Player
        fields = '__all__'

class PlayerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'ranking', 'points', 'number_of_matches', 'number_of_wins', 'number_of_losses', 'number_of_draws', 'winning_ratio']
    form = PlayerForm
    readonly_fields = ['number_of_matches', 'number_of_wins', 'number_of_losses', 'number_of_draws', 'winning_ratio']

    def get_list_display_links(self, request, list_display):
            
        if has_groups(request.user, ["admins", "operators"]):
            return super().get_list_display_links(request, list_display)
        else:
            return ['None']     
        
             
    def get_form(self, request, *args, **kwargs):
        form = super(PlayerAdmin, self).get_form(request, *args, **kwargs)
        form.request = request
        return form         
    
    def number_of_matches(self, obj):
        return obj.num_matches
    def number_of_wins(self, obj):
        return obj.num_wins
    def number_of_losses(self, obj):
        return obj.num_losses
    def number_of_draws(self, obj):
        return obj.num_draws
    def winning_ratio(self, obj):
        return obj.win_ratio 

    number_of_matches.admin_order_field = 'num_matches'
    number_of_wins.admin_order_field = 'num_wins'
    number_of_losses.admin_order_field = 'num_losses'
    number_of_draws.admin_order_field = 'num_draws'
    winning_ratio.admin_order_field = 'win_ratio'
        
    def get_queryset(self, request):
        qs = super(PlayerAdmin, self).get_queryset(request)
        _rawSQL_matches = RawSQL("(SELECT COUNT(M1.id) FROM ChessAdminApp_match M1 WHERE M1.status = 'COMPLETED' AND M1.player_one_id = ChessAdminApp_player.id) + (SELECT COUNT(M2.id) FROM ChessAdminApp_match M2 WHERE M2.status = 'COMPLETED' AND M2.player_two_id = ChessAdminApp_player.id)", [])
        _rawSQL_wins = RawSQL("(SELECT COUNT(M.id) FROM ChessAdminApp_match M WHERE M.status = 'COMPLETED' AND M.winner_id = ChessAdminApp_player.id)", [])
        _rawSQL_losses = RawSQL("(SELECT COUNT(M1.id) FROM ChessAdminApp_match M1 WHERE M1.status = 'COMPLETED' AND M1.player_one_id = ChessAdminApp_player.id AND M1.match_result = 'WIN' AND M1.winner_id != ChessAdminApp_player.id) + (SELECT COUNT(M2.id) FROM ChessAdminApp_match M2 WHERE M2.status = 'COMPLETED' AND M2.player_two_id =  ChessAdminApp_player.id AND M2.match_result = 'WIN' AND M2.winner_id != ChessAdminApp_player.id)", [])
        _rawSQL_draws = RawSQL("(SELECT COUNT(M1.id) FROM ChessAdminApp_match M1 WHERE M1.status = 'COMPLETED' AND M1.player_one_id = ChessAdminApp_player.id AND M1.match_result = 'DRAW') + (SELECT COUNT(M2.id) FROM ChessAdminApp_match M2 WHERE M2.status = 'COMPLETED' AND M2.player_two_id =  ChessAdminApp_player.id AND M2.match_result = 'DRAW')", [])
        _rawSQL_win_ratio = RawSQL("(ifnull(((CAST((SELECT COUNT(M.id) FROM ChessAdminApp_match M WHERE M.status = 'COMPLETED' AND M.winner_id = ChessAdminApp_player.id) AS REAL) ) / (CAST((SELECT COUNT(M1.id) FROM ChessAdminApp_match M1 WHERE M1.status = 'COMPLETED' AND M1.player_one_id = ChessAdminApp_player.id) + (SELECT COUNT(M2.id) FROM ChessAdminApp_match M2 WHERE M2.status = 'COMPLETED' AND M2.player_two_id = ChessAdminApp_player.id) AS REAL )) * 100), 0))", [])
        qs = qs.annotate(num_matches=_rawSQL_matches, num_wins=_rawSQL_wins, num_losses=_rawSQL_losses, num_draws=_rawSQL_draws, win_ratio=_rawSQL_win_ratio )
        return qs
    
class MatchForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MatchForm, self).__init__(*args, **kwargs)
        self.fields['player_one_entry_ranking'].widget.attrs['readonly'] = True
        self.fields['player_two_entry_ranking'].widget.attrs['readonly'] = True
        self.fields['player_one_ranking_change'].widget.attrs['readonly'] = True
        self.fields['player_two_ranking_change'].widget.attrs['readonly'] = True
    class Meta:
        model = Match
        fields = '__all__'

class MatchAdmin(admin.ModelAdmin):
    list_display = ['scheduled_date','status','player_one','player_two']
    form = MatchForm
    
    def save_model(self, request, obj, form, change):
        #obj.created_by = request.user
       
        if request.user.is_superuser:
            super().save_model(request, obj, form, change)
            return
           
        if obj.id is None:
            if not obj.status=="SCHEDULED":
                raise Exception('OMG! The match needs to be Scheduled before it can be Played and Completed. Please follow the workflow and select the correct match status from the drop-down box.')
        else:
            previous=Match.objects.get(id=obj.id)
            if previous.status=="SCHEDULED" and (obj.status != "PLAYING" and obj.status != "CANCELED"):
                raise Exception('OMG! You are trying to Complete a match without being Played yet. Please follow the workflow and select the correct match status from the drop-down box.')
            if previous.status=="PLAYING" and (obj.status != "COMPLETED" and obj.status != "CANCELED"):
                raise Exception('OMG! You are trying to put the match in a status that has already been passed. Cannot put the match in a status of Scheduled once the play has started. The match has to either be Completed or Canceled.') 
            if previous.status=="COMPLETED" or previous.status=="CANCELED":
                raise Exception('OMG! You are trying to update a match that is already closed. Once a match reached a state of Completed ot Caneceld it can no longer be updated.')
        
        super().save_model(request, obj, form, change)


def has_groups(user, group):
    return user.groups.filter(name__in=group).exists()
            
admin.site.register(Player, PlayerAdmin)
admin.site.register(Match, MatchAdmin) 





