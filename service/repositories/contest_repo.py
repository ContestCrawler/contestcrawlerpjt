from contests.models import Contest


class ContestRepository():
    def __init__(self):
        pass
    

    def get_all(self):
        return Contest.objects.all()
    

    def get_filtered(self, conditions):
        return Contest.objects.filter(**conditions)


