from django.db import models


class Team(models.Model):
    team_id = models.CharField(max_length=20, unique=True)
    team_type = models.CharField(max_length=10)
    password = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.team_id


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=100)
    student_no = models.CharField(max_length=20)
    email = models.EmailField()
    year = models.CharField(max_length=20)
    gender = models.CharField(max_length=20)
    branch = models.CharField(max_length=50)
    residence = models.CharField(max_length=50)

    def __str__(self):
        return self.name