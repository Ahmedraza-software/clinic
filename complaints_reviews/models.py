from django.db import models
from django.conf import settings


class ComplaintReview(models.Model):
    TYPE_COMPLAINT = 'complaint'
    TYPE_REVIEW = 'review'
    TYPE_CHOICES = [
        (TYPE_COMPLAINT, 'Complaint'),
        (TYPE_REVIEW, 'Review'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints_reviews')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=255)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.get_type_display()}: {self.subject}"

# Create your models here.
