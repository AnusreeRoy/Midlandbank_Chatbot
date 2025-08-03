from django.db import models 
class Product(models.Model):
    ProductCode = models.CharField(db_column="ProductCode", max_length=20, unique=True)  # Explicit column mapping
    ProductName = models.CharField(db_column="ProductName", max_length=100)
    ProductType = models.CharField(db_column="ProductType", max_length=50)
    Category    = models.CharField(db_column="Category", max_length=50)
    IslamicYN   = models.CharField(db_column="IslamicYN", max_length=10)

    class Meta:
        db_table = "products"  # Explicitly mapped

    def __str__(self):
        return f"{self.ProductName} ({self.ProductType})"

class Requirement(models.Model):
    ProductCode = models.ForeignKey(Product, on_delete=models.CASCADE, db_column="ProductCode")  # Explicit mapping
    DocumentName = models.TextField(db_column="DocumentName")
    DocumentType = models.CharField(db_column="DocumentType", max_length=50)

    class Meta:
        db_table = "requirements"
        managed = False  #Prevents Django from modifying MySQL structure

    def __str__(self):
        return f"{self.DocumentName} ({self.DocumentType})"
