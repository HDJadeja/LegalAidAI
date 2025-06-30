from django.db import models

class LegalAdviceUser(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=20)

    def __str__(self):
        return self.username

class LegalAdviceFile(models.Model):
    user = models.ForeignKey(LegalAdviceUser,on_delete=models.CASCADE,related_name='files')
    file = models.FileField(upload_to='legal_files/')
    filename = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.filename} uploaded by {self.user.username}"

        
