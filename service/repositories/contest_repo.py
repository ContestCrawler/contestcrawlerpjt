from contests.models import Contest


class ContestRepository():
    def __init__(self):
        pass
    

    def get_all(self):
        return Contest.objects.all()
    

    def get_filtered(self, conditions):
        return Contest.objects.filter(**conditions)


    def get_detail(self, pk):
        return Contest.objects.get(pk=pk)


    def get_distincted(self, column):
        return list(Contest.objects.values_list(column, flat=True))


    def get_image(self, pk):
        contest = Contest.objects.get(pk=pk)
        return contest.images.all()


    def get_attachment(self, pk):
        contest = Contest.objects.get(pk=pk)
        return contest.attachments.all()
    