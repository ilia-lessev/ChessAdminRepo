from django.http import HttpResponse
import csv
from ..models import RankingEventData
    
def getRankingHistory(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    writer = csv.DictWriter(response, fieldnames=['date','name','points','winratio','rank'])
    writer.writeheader()
    _rankingEvents = RankingEventData.objects.all()
    for rankEvent in _rankingEvents.iterator():
        _ratio = 1 #(rankEvent.points / 1.5)  
        writer.writerow({'date':rankEvent.date.replace(tzinfo=None).isoformat(), 'name': rankEvent.name, 'points': rankEvent.points * _ratio, 'winratio': rankEvent.winratio,'rank': rankEvent.rank})
    return response