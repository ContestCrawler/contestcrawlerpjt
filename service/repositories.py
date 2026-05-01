from contests.models import Contest


class Repository():
    def __init__(self):
        pass
    

    # 필터링 조건이 없으면 전체 데이터 반환, 조건이 있다면 조건에 따른 필터링 결과 반환
    def get_data(self, conditions=None):
        if conditions == None:
            return Contest.objects.all()
        
        return Contest.objects.filter(**conditions)



