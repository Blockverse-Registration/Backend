from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Team(models.Model):
    team_id = models.CharField(max_length=20, unique=True)
    team_type = models.CharField(max_length=10)
    password = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.team_id


email_validator = RegexValidator(
    regex=r'^[a-zA-Z]+[0-9]{7}@akgec\.ac\.in$',
    message="Email must be like: firstname + studentno + @akgec.ac.in"
)

student_validator = RegexValidator(
    regex=r'^[0-9]{7}$',
    message="Student number must be 7 digits"
)


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")

    name = models.CharField(max_length=100)

    student_no = models.CharField(
        max_length=7,
        validators=[student_validator]
    )

    email = models.EmailField(
        validators=[email_validator]
    )

    year = models.CharField(max_length=20)
    gender = models.CharField(max_length=20)
    branch = models.CharField(max_length=50)
    residence = models.CharField(max_length=50)

    def clean(self):
        if self.year.lower() == "first year" and not self.student_no.startswith("25"):
            raise ValidationError("First year student numbers must start with 25")

        if self.year.lower() == "second year" and not self.student_no.startswith("24"):
            raise ValidationError("Second year student numbers must start with 24")

        if self.student_no not in self.email:
            raise ValidationError("Email must contain the student number")

    def __str__(self):
        return self.name