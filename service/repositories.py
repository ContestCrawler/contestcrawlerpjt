from contests.models import Contest


class Repository():
    def __init__(self):
        pass


    def get_all_data(self):
        return Contest.objects.all()


    def get_filtered_date(self, conditions):
        return Contest.objects.filter(conditions)
    

    def get_data(self, conditions=None):
        return Contest.objects.filter(conditions)



