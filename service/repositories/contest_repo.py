from contests.models import Contest, ContestImage, ContestAttachment


class ContestRepository():
    def __init__(self):
        pass
    

    def save(self, contest: Contest):
        contest.save()
        pass


    def get_all(self):
        return Contest._objects.all()
    

    def get_filtered(self, conditions: dict):
        return Contest._objects.filter(**conditions)


    def get(self, pk):
        return Contest._objects.get(pk=pk)


    def get_distincted(self, column):
        return list(Contest._objects.values_list(column, flat=True))


    def get_image(self, pk):
        contest = Contest._objects.get(pk=pk)
        return contest.images.all()


    def get_attachment(self, pk):
        contest = Contest._objects.get(pk=pk)
        return contest.attachments.all()
    

    def find_contest(self, title):
        contests = Contest._objects.filter(title=title)
        return contests.exists()
    

class ContestImageRepository():
    def __init__(self):
        pass


    def save(self, contest_image: ContestImage):
        contest_image.save()


class ContestAttachmentRepository():
    def __init__(self):
        pass


    def save(self, contest_attachment: ContestAttachment):
        contest_attachment.save()